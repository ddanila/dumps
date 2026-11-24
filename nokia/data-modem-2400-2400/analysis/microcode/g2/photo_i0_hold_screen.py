"""Screen a latched-I0/high, read-valid-E2/low timing hypothesis across mappings."""

import copy
import hashlib
import json
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
from common import save
from execute import execute
from controller_bit_dispatch import controller_stream, groups_for
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

INPUT_PC = 0x38E
CYCLES = 1580


def hold_candidate(base):
    scenario = copy.deepcopy(base)
    scenario['name'] += '; hypothetical held U5 Q0=1 while U10 E2=0'
    scenario['inputs']['instruction_bit_overrides']['0'] = dict(
        value=1, status='hypothesis', evidence=(
            'U5 Q0 holds a previous high value or has a different driver; '
            'no such capture path is traced. U10 E2 is low during PROM reads.'))
    scenario['inputs']['register_address_bit_overrides']['a']['1'] = dict(
        value=0, status='hypothesis', evidence=(
            'U2 A1 follows the candidate U10 E2-side net during read-valid E2=0.'))
    return scenario


def run(out):
    _, base = fixture()
    _, bits = controller_stream()
    cases = []
    for name, path in MAPPINGS.items():
        mapping = mapped(path)
        scenario = hold_candidate(base)
        scenario['io']['read']['pc_sequences'][str(INPUT_PC)] = bits
        q_rows = []
        for q in range(256):
            scenario['initial']['q'] = q
            result = execute(mapping, scenario, 512, mode='integrated', trace_limit=0)
            if not result['clean']:
                raise ValueError(f'{name} Q={q} stopped')
            q_rows.append(dict(q=q, input_visits=result['address_counts'].get(INPUT_PC, 0),
                               selected_rom_reads=result['rom_reads']['selected_by_alu'],
                               output_392=result['address_counts'].get(0x392, 0),
                               output_396=result['address_counts'].get(0x396, 0),
                               final_pc=f'{result["final_state"]["pc"]:03X}'))
        scenario['initial']['q'] = 5
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            result = execute(mapping, scenario, CYCLES, mode='integrated',
                             out=target, trace_limit=CYCLES)
            trace = [json.loads(line) for line in
                     (target/'trace.jsonl').read_text().splitlines()]
        inputs = [row['external_read']['value'] for row in trace
                  if row['pc'] == INPUT_PC]
        groups = groups_for(trace)
        if not result['clean'] or inputs != bits or len(groups) != len(bits):
            raise ValueError(f'{name} controller stream incomplete')
        first_input = next(row['cycle'] for row in trace if row['pc'] == INPUT_PC)
        rom = defaultdict(list)
        for row in trace:
            event = row.get('external_read', {})
            if (row['cycle'] > first_input and event.get('selected_by_alu')
                    and 'address' in event):
                rom[f'{row["pc"]:03X}'].append(event['address'])
        by_bit = defaultdict(set)
        for bit, group in zip(bits[1:], groups[1:]):
            by_bit[bit].add(tuple(group['bytes']))
        cases.append(dict(mapping=name, q_sweep=dict(
            runs=256,
            active_input_q=[row['q'] for row in q_rows if row['input_visits'] > 2],
            many_rom_q=[row['q'] for row in q_rows if row['selected_rom_reads'] > 10],
            output_q=[row['q'] for row in q_rows
                      if max(row['output_392'], row['output_396']) > 2],
            final_pc_counts=dict(sorted(Counter(row['final_pc'] for row in q_rows).items()))),
            controller_run=dict(initial_q=5, cycles=CYCLES, bits_consumed=len(inputs),
                rom_after_first_input={pc: dict(visits=len(addresses),
                                                addresses=sorted(set(addresses)))
                                       for pc, addresses in sorted(rom.items())},
                group_patterns_after_first={str(bit): [list(group) for group in sorted(by_bit[bit])]
                                            for bit in (0, 1)},
                output_392=result['address_counts'].get(0x392, 0),
                output_396=result['address_counts'].get(0x396, 0),
                trace_digest=result['trace_digest'])))
    if any(row['controller_run']['bits_consumed'] != 128 for row in cases):
        raise ValueError('controller bit count changed')
    paths = [Path(__file__), HERE/'photo_controller_path.py',
             HERE/'photo_mapping_q_sweep.py', HERE/'photo_mapping_stream_screen.py',
             HERE/'controller_bit_dispatch.py', HERE/'photo-a-input-constraint.json',
             HERE/'photo-i7-constraint.json', ASSUMED/'execute.py',
             HERE.parent/'model.py', *MAPPINGS.values()]
    report = dict(status='read-valid held-I0 diagnostic, not recovered latch timing',
                  fixture=dict(u10_e2_read_phase=0, u11_e4_read_phase=1,
                               held_u5_q0_to_u2_i0=1, direct_e2_to_u2_a1=0,
                               initial_ram=[0]*16, q_seeds=256,
                               cycles_per_seed=512, controller_bits=len(bits),
                               assumed_input_pc='38E'),
                  cases=cases,
                  limitations=[
                      'U5 cannot capture E2=1 and valid U10 data bits on one simple edge; '
                      'a separate hold circuit or different I0 driver is untraced.',
                      'The five mappings, ROM gate, controller-to-D38E route and DAC output site are hypotheses.',
                      'The Q=5 trace is one startup state; the all-Q sweep records counts, not sample waveforms.',
                      'Repeated addresses at selected ROM reads do not demonstrate modulation.'],
                  source_sha256={str(path.relative_to(HERE.parent)):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.parent.mkdir(parents=True, exist_ok=True)
    save(out, report)
    return report


if __name__ == '__main__':
    report = run(HERE/'results/photo-i0-hold-screen.json')
    for row in report['cases']:
        print(row['mapping'], len(row['q_sweep']['active_input_q']),
              row['controller_run']['rom_after_first_input'],
              row['controller_run']['group_patterns_after_first'])
