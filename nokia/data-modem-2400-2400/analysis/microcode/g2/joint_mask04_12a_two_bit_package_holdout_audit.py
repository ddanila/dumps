"""Audit unseen-key phase constraints after the package-route holdout."""

import hashlib
import json
from pathlib import Path

from joint_mask04_12a_0d_feature_graph import solve
from joint_mask04_12a_two_bit_package_route import CAPTURES, FEATURES, STEPS, gate_phase

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
RAW = tuple(RESULTS / f'joint-mask04-12a-two-bit-package-holdout-{n}.json'
            for n in (161, 163))
PRIOR = RESULTS / 'joint-mask04-12a-two-bit-gain1-frozen37-audit.json'
SUMMARY = RESULTS / 'joint-mask04-12a-two-bit-package-holdout.json'
OUT = RESULTS / 'joint-mask04-12a-two-bit-package-holdout-audit.json'


def run(out=OUT):
    cases = [case for path in (*CAPTURES, *RAW)
             for case in json.loads(path.read_text())['cases']]
    if len(cases) != 46 or any(len(case['multi_visit_symbols']) != 65
                                for case in cases):
        raise ValueError('joined case count changed')
    graph = solve(cases, FEATURES, STEPS)
    if (graph['state_codes'], graph['directed_conflicts'], graph['components']) != (45, 0, [45]):
        raise ValueError('joined phase graph changed')
    old = json.loads(PRIOR.read_text())['phase_graph']['relative_phase']
    checks = []
    for code, actual in graph['relative_phase'].items():
        if code in old:
            continue
        predicted = (gate_phase(int(code, 16)) - 1) & 3
        checks.append(dict(code=code, inferred_phase=actual,
                           frozen_gate_phase=predicted,
                           agrees=predicted == actual))
    if [(row['code'], row['inferred_phase'], row['frozen_gate_phase'])
            for row in checks] != [('0F5', 1, 1), ('101', 0, 3), ('141', 0, 3)]:
        raise ValueError('unseen-key gate predictions changed')
    summary = json.loads(SUMMARY.read_text())
    expected = [(161, '40', 0, True), (161, '60', 0, True),
                (163, '40', 17, False), (163, '60', 13, False)]
    if [(row['carrier_offset'], row['selector'],
         len(row['gate_wrong_indices']), row['controller_matches_payload'])
            for row in summary['cases']] != expected:
        raise ValueError('holdout controller classification changed')
    paths = (Path(__file__), PRIOR, SUMMARY, *CAPTURES, *RAW,
             HERE / 'joint_mask04_12a_two_bit_package_route.py',
             HERE / 'joint_mask04_12a_two_bit_package_holdout.py',
             HERE / 'joint_mask04_12a_0d_feature_graph.py')
    report = dict(experiment='unseen-state audit of the frozen package route',
                  fixture=dict(streams=len(cases), symbols=65 * len(cases),
                               phase_convention=STEPS),
                  phase_graph=graph, new_key_predictions=checks,
                  holdout_cases=[dict(carrier_offset=row['carrier_offset'],
                                      selector=row['selector'],
                                      unseen_keys=row['unseen_keys'],
                                      wrong_dibits=len(row['gate_wrong_indices']),
                                      exact_line=row['recovered_matches_offered'],
                                      exact_payload=row['controller_matches_payload'],
                                      clipped_samples=row['clipped_samples'])
                                 for row in summary['cases']],
                  limitations=[
                      'The graph uses the failed holdout to infer the new phases; it is development evidence for any revised circuit.',
                      'The package route remains an assumed logical netlist, not identified physical wiring.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print(result['phase_graph']['state_codes'], result['new_key_predictions'])
