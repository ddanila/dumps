"""Audit the first frozen ten-bit package gate on fresh held-81 data."""

import hashlib
import json
from pathlib import Path

from joint_mask04_12a_0d_feature_graph import solve
from joint_mask04_12a_ten_bit_package_route import CAPTURES, FEATURES, STEPS, gate_phase

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
RAW = tuple(RESULTS / f'joint-mask04-12a-ten-bit-package-mode81-holdout-{n}.json'
            for n in (169, 171))
SUMMARY = RESULTS / 'joint-mask04-12a-ten-bit-package-mode81-holdout.json'
OUT = RESULTS / 'joint-mask04-12a-ten-bit-mode81-audit.json'


def run(out=OUT):
    cases = [case for path in (*CAPTURES, *RAW)
             for case in json.loads(path.read_text())['cases']]
    graph = solve(cases, FEATURES, STEPS)
    if (len(cases), graph['state_codes'], graph['directed_conflicts'],
            graph['components']) != (62, 56, 0, [38, 18]):
        raise ValueError('joined ten-bit phase graph changed')
    old = json.loads((RESULTS / 'joint-mask04-12a-ten-bit-package-route.json').read_text())[
        'phase_graph']['relative_phase']
    new = {key: dict(inferred_phase=value,
                     frozen_gate_phase=(gate_phase(int(key, 16)) - 3) & 3)
           for key, value in graph['relative_phase'].items() if key not in old}
    if new != {'135': dict(inferred_phase=1, frozen_gate_phase=1),
               '32C': dict(inferred_phase=2, frozen_gate_phase=1)}:
        raise ValueError('unseen-state gate prediction changed')
    summary = json.loads(SUMMARY.read_text())['cases']
    checks = []
    for case in summary:
        wrong = case['gate_wrong_indices']
        if (not wrong or case['recovered_matches_offered'] or
                case['controller_matches_payload'] or case['clipped_samples'] or
                any(case['captured_keys'][i] != '32C' and
                    case['captured_keys'][i - 1] != '32C' for i in wrong)):
            raise ValueError('held-81 failure classification changed')
        checks.append(dict(carrier_offset=case['carrier_offset'],
                           selector=case['selector'],
                           unseen_keys=case['unseen_keys'],
                           wrong_dibits=len(wrong),
                           exact_line=case['recovered_matches_offered'],
                           exact_payload=case['controller_matches_payload'],
                           clipped_samples=case['clipped_samples']))
    if [row['wrong_dibits'] for row in checks] != [12, 7, 16, 10]:
        raise ValueError('held-81 wrong-dibit counts changed')
    paths = (Path(__file__), SUMMARY, *CAPTURES, *RAW,
             HERE / 'joint_mask04_12a_ten_bit_package_route.py',
             HERE / 'joint_mask04_12a_ten_bit_package_mode81_holdout.py',
             HERE / 'joint_mask04_12a_0d_feature_graph.py')
    report = dict(experiment='frozen ten-bit package gate held-81 failure audit',
                  fixture=dict(streams=len(cases), symbols=65 * len(cases),
                               phase_convention=STEPS),
                  phase_graph=graph, new_key_predictions=new,
                  holdout_cases=checks,
                  limitations=[
                      'The 169/171 streams supply the new phase constraints; any revised circuit fitted to them requires another fresh holdout.',
                      'The graph still has two disconnected components and does not identify physical latch/gate nets.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print(result['phase_graph']['state_codes'], result['new_key_predictions'])
