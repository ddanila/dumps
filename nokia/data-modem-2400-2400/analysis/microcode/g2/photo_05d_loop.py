"""Screen the q1 photo-candidate D-fed 05D–063 loop and reset reachability."""
import copy
import hashlib
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path.insert(0, str(ASSUMED))
from common import read, save
from execute import execute

MAPPING = HERE / 'results/photo-variant-rom-loop/q1-witness-mapping.json'
SCENARIO = HERE / 'results/photo-variant-rom-loop/q1-mixed-bank-scenario.json'
GATES = ASSUMED / 'results/rom-gate-study/report.json'
ROM = HERE.parents[2] / 'am27s31dc-prom/nokia-modem-am27s31dc.bin'
GATE_INDEX = 47


def run(out):
    out.mkdir(parents=True, exist_ok=True)
    mapping = read(MAPPING)
    base = read(SCENARIO)
    gate = read(GATES)['fits'][GATE_INDEX]
    if 0x05E not in gate['pcs'] or 0x061 not in gate['pcs']:
        raise ValueError('diagnostic gate no longer selects both loop reads')
    address = base['io']['read']['address']
    address.pop('bank_by_pc', None)
    address['pcs'] = gate['pcs']
    address['evidence'] += '; 05D local entry is a diagnostic hypothesis'
    rom = ROM.read_bytes()
    cases = []
    for bank in (0, 256):
        reset_reached = []
        reset_final_pcs = Counter()
        local_final_pcs = Counter()
        local_q_changes = []
        local_clean = 0
        for q in range(256):
            scenario = copy.deepcopy(base)
            scenario['initial']['q'] = q
            scenario['io']['read']['address']['bank'] = bank
            reset = execute(mapping, scenario, 512, mode='integrated', trace_limit=0)
            if not reset['clean']:
                raise ValueError('reset sweep stopped')
            reset_final_pcs[f'{reset["final_state"]["pc"]:03X}'] += 1
            if any(reset['address_counts'].get(pc, 0) for pc in (0x05D, 0x05E, 0x061)):
                reset_reached.append(q)
            scenario['initial']['pc'] = 0x05D
            local = execute(mapping, scenario, 128, mode='integrated', trace_limit=0)
            local_clean += local['clean']
            local_final_pcs[f'{local["final_state"]["pc"]:03X}'] += 1
            if local['final_state']['q'] != q:
                local_q_changes.append(q)
        cases.append(dict(bank=bank, reset_reached_q=reset_reached,
                          reset_final_pcs=dict(reset_final_pcs),
                          local_clean=local_clean,
                          local_final_pcs=dict(local_final_pcs),
                          local_q_changes=local_q_changes))
    witnesses = []
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary)
        for bank in (0, 256):
            for q in (0, 1, 127, 255):
                scenario = copy.deepcopy(base)
                scenario['initial'].update(pc=0x05D, q=q)
                scenario['io']['read']['address']['bank'] = bank
                result = execute(mapping, scenario, 128, mode='integrated',
                                 out=path, trace_limit=128)
                trace = [json.loads(line) for line in
                         (path / 'trace.jsonl').read_text().splitlines()]
                sites = {}
                for pc in (0x05E, 0x061):
                    rows = [row for row in trace if row['pc'] == pc and
                            row.get('external_read', {}).get('selected_by_alu')]
                    tuples = sorted({(row['external_read']['address'],
                                      row['external_read']['value'], row['alu']['y'])
                                     for row in rows})
                    expected_address = bank + ((q + 1) & 255)
                    expected = (expected_address, rom[expected_address],
                                (q + rom[expected_address]) & 255)
                    if tuples != [expected]:
                        raise ValueError('local ROM read is not stationary Q-indexed add')
                    sites[f'{pc:03X}'] = dict(visits=len(rows),
                                             address=expected_address,
                                             rom_value=expected[1], alu_y=expected[2])
                witnesses.append(dict(bank=bank, initial_q=q, sites=sites,
                                      final_pc=f'{result["final_state"]["pc"]:03X}',
                                      final_q=result['final_state']['q'],
                                      trace_digest=result['trace_digest']))
                if bank == 0 and q == 127:
                    for filename in ('trace.jsonl', 'scenario.json'):
                        (out / f'witness-{filename}').write_bytes(
                            (path / filename).read_bytes())
    report = dict(status='photo-candidate-local-loop-not-transmitter',
                  gate_index=GATE_INDEX, gate_terms=gate['terms'],
                  gate_selected_pcs=len(gate['pcs']), cases=cases,
                  witnesses=witnesses,
                  source_sha256={str(p.relative_to(HERE.parents[2])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (MAPPING, SCENARIO, GATES, ROM,
                                           ASSUMED / 'execute.py', Path(__file__))},
                  limitations=[
                      'The ROM gate is fitted to diagnostic labels, not measured wiring.',
                      'The 05D entry is forced only for the local test; reset never reaches it in this fixture.',
                      'The q1 photo mapping, startup state, branch conditions and ROM bank are hypotheses.',
                      'A fixed local Q does not rule out another caller updating Q between invocations.',
                      'No physical output site or line signal is observed.'])
    save(out / 'report.json', report)
    return report


if __name__ == '__main__':
    result = run(HERE / 'results/photo-05d-loop')
    print([(case['bank'], len(case['reset_reached_q']), case['local_final_pcs'])
           for case in result['cases']])
