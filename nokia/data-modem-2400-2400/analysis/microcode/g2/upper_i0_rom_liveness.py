"""Check whether the upper-I0 polarity variant sustains ROM/output motion."""

import copy
import hashlib
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
from common import save
from execute import execute
from independent_slice_addresses import mapping_for
from photo_controller_path import fixture
from photo_mapping_stream_screen import MAPPINGS
from split_slice_probe import split_scenario

CYCLES = 1000
INPUT_PC = 0x38E
LOOP_PCS = (0x389, 0x38A, 0x38C, 0x38E, 0x38F,
            0x39E, 0x39F, 0x3A0, 0x3A1, 0x390)
ROM_PCS = (0x389, 0x38A, 0x38C)


def candidate_mapping():
    mapping = mapping_for('b')
    token = mapping['fields']['i_high']['bits'][0]
    mapping['fields']['i_high']['bits'][0] = token[1:] if token.startswith('!') else '!' + token
    mapping['fields']['i_high']['evidence'] += (
        '; diagnostic upper I0 polarity inversion; physical inverter untraced')
    return mapping


def scenario_for(base, q, bit, banks=None):
    scenario = copy.deepcopy(base)
    scenario['name'] += f'; upper I0 flipped, initial Q={q:02X}, held D4={bit}'
    scenario['initial']['q'] = q
    scenario['io']['read']['pc_sequences'][str(INPUT_PC)] = [16 * bit]
    if banks is not None:
        scenario['io']['read']['address']['bank_by_pc'] = {
            str(pc): bank for pc, bank in zip(ROM_PCS, banks)}
    return scenario


def trace_run(mapping, scenario):
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, CYCLES, mode='integrated',
                         out=temporary, trace_limit=CYCLES)
        trace = [json.loads(line) for line in
                 (Path(temporary) / 'trace.jsonl').read_text().splitlines()]
    if not result['clean'] or len(trace) != CYCLES:
        raise ValueError('upper-I0 trace did not complete')
    return result, trace


def plateaus(trace):
    sites = {}
    for pc in LOOP_PCS:
        rows = [row for row in trace if row['pc'] == pc]
        if len(rows) < 20:
            raise ValueError(f'loop site {pc:03X} did not repeat')
        tail = rows[8:]
        sites[f'{pc:03X}'] = dict(visits=len(rows),
            tail_y=sorted({row['alu']['y'] for row in tail}),
            tail_q=sorted({row['q'] for row in tail}),
            first_12_y=[row['alu']['y'] for row in rows[:12]])
        if pc in ROM_PCS:
            selected = [row['external_read'] for row in tail
                        if row['external_read'].get('selected_by_alu')]
            sites[f'{pc:03X}']['tail_rom'] = sorted({
                (event['address'], event['value']) for event in selected})
            sites[f'{pc:03X}']['selected_tail_reads'] = len(selected)
    return sites


def run(out=HERE / 'results/upper-i0-rom-liveness.json'):
    _, unmodified = fixture()
    base = split_scenario(unmodified)
    mapping = candidate_mapping()
    eligible = []
    funnel = Counter()
    # First inspect all Q values without retaining 512 full traces.
    for q in range(256):
        pair = []
        for bit in (0, 1):
            scenario = scenario_for(base, q, bit)
            result = execute(mapping, scenario, CYCLES, mode='integrated',
                             trace_limit=0)
            visits = result['address_counts'].get(0x389, 0)
            pair.append(dict(bit=bit, visits=visits, clean=result['clean'],
                             selected_rom_addresses=len(result['rom_reads']['address_counts'])))
        if all(row['clean'] and row['visits'] >= 20 for row in pair):
            eligible.append(dict(q=q, screening=pair))
        else:
            funnel['ineligible'] += 1
    cases = []
    for entry in eligible:
        for bit in (0, 1):
            result, trace = trace_run(mapping, scenario_for(base, entry['q'], bit))
            sites = plateaus(trace)
            cases.append(dict(q=entry['q'], bit=bit,
                              selected_rom_addresses_full_run=(
                                  entry['screening'][bit]['selected_rom_addresses']),
                              sites=sites, trace_digest=result['trace_digest']))
    bank_cases = []
    for bit in (0, 1):
        for mask in range(8):
            banks = tuple(256 if mask >> index & 1 else 0
                          for index in range(3))
            result, trace = trace_run(mapping, scenario_for(base, 5, bit, banks))
            bank_cases.append(dict(bit=bit, banks=list(banks),
                                   sites=plateaus(trace),
                                   trace_digest=result['trace_digest']))
    all_plateau = all(
        len(site['tail_y']) == 1 and len(site['tail_q']) == 1 and
        (pc not in {f'{p:03X}' for p in ROM_PCS} or len(site['tail_rom']) == 1)
        for case in [*cases, *bank_cases]
        for pc, site in case['sites'].items())
    paths = [Path(__file__), HERE / 'independent_slice_addresses.py',
             HERE / 'independent_slice_fields.py',
             HERE / 'photo_controller_path.py', HERE / 'split_slice_probe.py',
             ASSUMED / 'execute.py', HERE.parent / 'model.py', MAPPINGS['q3'],
             HERE.parents[2] / 'am27s31dc-prom/nokia-modem-am27s31dc.bin']
    report = dict(status='upper-I0-polarity ROM liveness under held D4 input',
                  fixture=dict(mapping=mapping['name'], cycles=CYCLES,
                               q_values_screened=256, held_d4=[0, 1],
                               input_pc='38E', loop_pcs=[f'{pc:03X}' for pc in LOOP_PCS],
                               plateau_after_visit=8, bank_screen_q=5),
                  totals=dict(screened_runs=512, eligible_q=len(eligible),
                              ineligible_q=funnel['ineligible'],
                              traced_runs=len(cases), bank_runs=len(bank_cases),
                              all_repeated_sites_plateau=all_plateau),
                  eligible_q=eligible, cases=cases, bank_cases=bank_cases,
                  limitations=[
                      'Upper I0 polarity, high B field, split instruction links and D38E controller route are untraced.',
                      'Held D4 levels test sustained motion; the real controller stream is not replayed here.',
                      'A constant ALU Y at a PC is not a DAC measurement; a different latch path or mapping remains possible.',
                      'The ROM-address count over an entire run includes startup and must not be read as recurring liveness.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    print(run()['totals'])
