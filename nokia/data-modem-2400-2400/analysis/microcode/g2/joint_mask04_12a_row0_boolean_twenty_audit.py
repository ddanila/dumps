"""Audit revised row-phase gates on fresh data, carrier phase and gain."""

import hashlib
import json
from pathlib import Path

from joint_mask04_12a_multivisit_phase_screen import HERE

LOGIC = HERE / 'results/joint-mask04-12a-row0-boolean-twenty.json'
HOLDOUT = HERE / 'results/joint-mask04-12a-row0-boolean-twenty-fresh-88.json'


def run(out=HERE / 'results/joint-mask04-12a-row0-boolean-twenty-audit.json'):
    model = json.loads(LOGIC.read_text())
    holdout = json.loads(HOLDOUT.read_text())
    known = set(model['state_phase'])
    outcomes = []
    for case in holdout['cases']:
        result = case['boolean_phase']
        handoffs = result['readout']['controller_handoffs']
        source = [int(value, 16) for value in case['payload']]
        outcomes.append(dict(selector=case['selector'], level=case['level'],
                             payload=case['payload'],
                             reference_wrong_indices=case['reference_wrong_indices'],
                             Boolean_wrong_indices=result['wrong_indices'],
                             observed_states=sorted(set(result['states'])),
                             unseen_states=sorted(set(result['states']) - known),
                             line_bytes=result['readout']['recovered_line_bytes'],
                             line_matches_offered=result['readout']['recovered_matches_offered'],
                             aligned_decoded_bytes=handoffs['66']['decoded_bytes'],
                             aligned_matches_source=handoffs['66']['decoded_bytes'] == source,
                             aligned_errors=handoffs['66']['errors'],
                             aligned_overruns=handoffs['66']['overruns'],
                             early_matches_source=handoffs['65']['decoded_bytes'] == source,
                             late_matches_source=handoffs['67']['decoded_bytes'] == source))
    paths = (Path(__file__), LOGIC, HOLDOUT,
             HERE / 'joint_mask04_12a_row0_boolean_twenty.py',
             HERE / 'joint_mask04_12a_row0_boolean_twenty_fresh.py')
    report = dict(experiment='frozen 20-state row-phase gates on new data and gain',
                  fixture=dict(holdout_cases=len(outcomes),
                               levels=[0.75, 1.0, 1.25],
                               R1_offset=88,
                               development_states=len(known),
                               decisions_per_case=64,
                               payload_dibits_per_case=32),
                  outcomes=outcomes,
                  limitations=[
                      'All holdout states were already among the 20 development states; this does not test a new state.',
                      'ADC timing, row latch, analog path, Boolean gates and USART wires remain photo-compatible assumptions.',
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    print('outcomes', [(row['selector'], row['level'],
                        len(row['Boolean_wrong_indices']),
                        row['line_matches_offered'],
                        row['aligned_matches_source'], row['unseen_states'])
                       for row in outcomes], flush=True)
    return report


if __name__ == '__main__':
    run()
