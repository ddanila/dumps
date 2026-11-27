"""Extend the frozen two-bit phase graph after its first unseen-key holdout."""

import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from joint_mask04_12a_0d_feature_graph import INPUTS, solve
from joint_mask04_12a_row1_holdout_graph_audit import RAW
from joint_mask04_12a_two_bit_phase_holdout import state_key
import joint_mask04_12a_row0_serial_timing as serial
import joint_mask04_buffered_serial_handoff as handoff
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
NEW = tuple(RESULTS / f'joint-mask04-12a-two-bit-phase-holdout-{n}.json'
            for n in (145, 147))
OUT = RESULTS / 'joint-mask04-12a-two-bit-phase-extension.json'
STEPS = (2, 1, 3, 0)


def run(out=OUT):
    cases = [case for path in (*INPUTS, *RAW, *NEW)
             for case in json.loads(path.read_text())['cases']]
    if len(cases) != 26 or any(len(case['multi_visit_symbols']) != 65
                                for case in cases):
        raise ValueError('phase-graph case count changed')
    graph = solve(cases, (('46', 'row0', 1), ('94', 'y3f8', 4)), STEPS)
    if (graph['state_codes'], graph['directed_conflicts'], graph['components']) != (33, 0, [33]):
        raise ValueError('two-bit phase graph changed')
    if {key: graph['relative_phase'][key] for key in ('1DB', '1CC')} != {'1DB': 3, '1CC': 2}:
        raise ValueError('new-key phase constraints changed')
    table = {int(key, 16): value for key, value in graph['relative_phase'].items()}
    inverse = {step: dibit for dibit, step in enumerate(STEPS)}

    def captured(symbol, variant, covers):
        key = state_key(symbol)
        return table[key], serial.Y3F8_CYCLE + 94 * serial.CYCLES_PER_VISIT, key

    checks = []
    with tempfile.TemporaryDirectory() as temporary:
        exe, controller_sha = handoff.compiled_controller(temporary)
        for path in NEW:
            for case in json.loads(path.read_text())['cases']:
                selector = case['selector']
                payload = [int(value, 16) for value in case['payload']]
                offered = line_octets(payload, 5 if selector == '40' else 18)
                with patch.object(serial, 'captured_phase', captured):
                    score = serial.replay(dict(case, offered_line_bytes=[
                        f'{value:02X}' for value in offered]),
                        serial.VARIANTS['aligned'], None, inverse, exe)
                check = dict(carrier_offset=int(path.stem.rsplit('-', 1)[-1]),
                             selector=selector,
                             wrong_decisions=len(score['wrong_decision_indices']),
                             exact_line=score['recovered_matches_offered'],
                             exact_controller=score['controller_decoded_bytes'] == payload,
                             minimum_setup_cycles=score['minimum_setup_cycles'])
                if (check['wrong_decisions'] != 0 or not check['exact_line'] or
                        not check['exact_controller']):
                    raise ValueError(('extended-table replay failed', check))
                checks.append(check)
    paths = (Path(__file__), *INPUTS, *RAW, *NEW,
             HERE / 'joint_mask04_12a_two_bit_phase_holdout.py',
             HERE / 'joint_mask04_12a_0d_feature_graph.py')
    report = dict(experiment='33-code two-bit development phase graph',
                  fixture=dict(streams=len(cases), symbols=65 * len(cases),
                               phase_convention=STEPS,
                               controller_probe_sha256=controller_sha),
                  phase_graph=graph, development_replay=checks,
                  limitations=[
                      'The 145/147 streams supplied the two new labels; replay on them is development evidence, not a new holdout.',
                      'The table remains a graph lookup under assumed capture, line and serial connections.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print(result['phase_graph']['state_codes'], result['development_replay'])
