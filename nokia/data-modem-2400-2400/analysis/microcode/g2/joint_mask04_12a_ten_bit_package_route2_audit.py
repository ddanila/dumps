"""Audit the frozen revised gate against its fresh held-81 challenge."""

import hashlib
import json
from pathlib import Path

from joint_mask04_12a_0d_feature_graph import solve
from joint_mask04_12a_ten_bit_package_route2 import CAPTURES, FEATURES, STEPS, gate_phase

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
RAW = tuple(RESULTS / f'joint-mask04-12a-ten-bit-package-route2-mode81-holdout-{n}.json'
            for n in (173, 175))
SUMMARY = RESULTS / 'joint-mask04-12a-ten-bit-package-route2-mode81-holdout.json'
OUT = RESULTS / 'joint-mask04-12a-ten-bit-package-route2-audit.json'


def run(out=OUT):
    cases = [case for path in (*CAPTURES, *RAW)
             for case in json.loads(path.read_text())['cases']]
    graph = solve(cases, FEATURES, STEPS)
    if (len(cases), graph['state_codes'], graph['directed_conflicts'],
            graph['components']) != (66, 60, 0, [40, 20]):
        raise ValueError('expanded ten-bit phase graph changed')
    old = json.loads((RESULTS / 'joint-mask04-12a-ten-bit-package-route2.json').read_text())[
        'phase_graph']['relative_phase']
    new = {key: dict(inferred_phase=value,
                     frozen_gate_phase=(gate_phase(int(key, 16)) - 3) & 3)
           for key, value in graph['relative_phase'].items() if key not in old}
    expected = {'12D': (2, 1), '136': (1, 1),
                '181': (0, 0), '31C': (3, 3)}
    if {key: tuple(row.values()) for key, row in new.items()} != expected:
        raise ValueError('new state predictions changed')
    labels = {int(key, 16): (phase + 3) & 3
              for key, phase in graph['relative_phase'].items()}
    product_hits = [state for state in labels
                    if all((state >> bit) & 1 for bit in (3, 5, 8))]
    if 0x12D not in product_hits or any(not (labels[state] & 1)
                                       for state in product_hits):
        raise ValueError('candidate three-literal product changed')
    rows = []
    for case in json.loads(SUMMARY.read_text())['cases']:
        wrong = case['gate_wrong_indices']
        fail = case['carrier_offset'] == 175
        if (len(wrong) != (12 if fail else 0) or
                case['recovered_matches_offered'] == fail or
                case['controller_matches_payload'] == fail or
                case['clipped_samples'] or
                any('12D' not in (case['captured_keys'][i],
                                  case['captured_keys'][i - 1]) for i in wrong)):
            raise ValueError('held-81 result classification changed')
        rows.append(dict(carrier_offset=case['carrier_offset'],
                         selector=case['selector'],
                         wrong_dibits=len(wrong),
                         exact_line=case['recovered_matches_offered'],
                         exact_payload=case['controller_matches_payload'],
                         clipped_samples=case['clipped_samples'],
                         unseen_keys=case['unseen_keys']))
    paths = (Path(__file__), SUMMARY, *CAPTURES, *RAW,
             HERE / 'joint_mask04_12a_ten_bit_package_route2.py',
             HERE / 'joint_mask04_12a_ten_bit_package_route2_mode81_holdout.py',
             HERE / 'joint_mask04_12a_0d_feature_graph.py')
    report = dict(experiment='frozen revised ten-bit gate fresh held-81 audit',
                  fixture=dict(streams=len(cases), symbols=65 * len(cases),
                               phase_convention=STEPS),
                  phase_graph=graph, new_key_predictions=new,
                  candidate_phase_bit0_product=dict(bits=[3, 5, 8],
                                                    observed_hits=[f'{state:03X}'
                                                                   for state in sorted(product_hits)],
                                                    observed_off_hits=0),
                  holdout_cases=rows,
                  limitations=[
                      'Carrier-175 defeats the frozen revised gate at unseen state 12D; a further gate revision must be tested on another fresh stream.',
                      'The graph remains two disconnected components; physical capture and serial nets remain assumed.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print(result['phase_graph']['state_codes'], result['new_key_predictions'])
