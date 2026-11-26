"""Audit frozen Boolean row-phase holdouts and unseen-state prediction."""

import hashlib
import json
from pathlib import Path

from joint_mask04_12a_multivisit_phase_screen import HERE, INPUTS, SELECTED, solve
from joint_mask04_12a_row0_boolean import phase

LOGIC = HERE / 'results/joint-mask04-12a-row0-boolean.json'
DEVELOPMENT = (HERE / 'results/joint-mask04-12a-row0-fresh-0.json',
               HERE / 'results/joint-mask04-12a-row0-fresh-64.json')
HOLDOUTS = (HERE / 'results/joint-mask04-12a-row0-fresh-24.json',
            HERE / 'results/joint-mask04-12a-row0-fresh-88.json')


def run(out=HERE / 'results/joint-mask04-12a-row0-boolean-fresh-audit.json'):
    model = json.loads(LOGIC.read_text())
    covers = [tuple(tuple(-1 if char == '*' else int(char) for char in cube)
                    for cube in row['cubes']) for row in model['phase_bits']]
    training = [case for path in (*INPUTS, *DEVELOPMENT)
                for case in json.loads(path.read_text())['cases']]
    holdouts = [case for path in HOLDOUTS
                for case in json.loads(path.read_text())['cases']]
    before, before_conflicts, before_components = solve(
        training, SELECTED, tuple(model['fixture']['phase_convention']))
    after, after_conflicts, after_components = solve(
        training + holdouts, SELECTED, tuple(model['fixture']['phase_convention']))
    if before_conflicts or after_conflicts or len(before_components) != 1 or len(after_components) != 1:
        raise ValueError('phase graph changed')
    novel = sorted(f'{value:02X}' for value in after if value not in before)
    outcomes = []
    for path in HOLDOUTS:
        offset = int(path.stem.rsplit('-', 1)[1])
        for case in json.loads(path.read_text())['cases']:
            result = case['boolean_phase']
            aligned = result['readout']['controller_handoffs']['66']
            outcomes.append(dict(offset=offset, selector=case['selector'],
                                 payload=case['payload'],
                                 new_states=result['new_states'],
                                 Boolean_wrong_indices=result['wrong_indices'],
                                 reference_wrong_indices=case['reference_wrong_indices'],
                                 recovered_line_bytes=result['readout']['recovered_line_bytes'],
                                 line_matches_offered=result['readout']['recovered_matches_offered'],
                                 aligned_decoded_bytes=aligned['decoded_bytes'],
                                 aligned_completed=aligned['completed'],
                                 aligned_consumed=aligned['consumed'],
                                 aligned_errors=aligned['errors'],
                                 aligned_overruns=aligned['overruns']))
    paths = (Path(__file__), LOGIC, *INPUTS, *DEVELOPMENT, *HOLDOUTS,
             HERE / 'joint_mask04_12a_row0_boolean.py',
             HERE / 'joint_mask04_12a_row0_boolean_fresh.py')
    report = dict(experiment='frozen row-0 Boolean gates on unseen phase state',
                  fixture=dict(development_cases=len(training),
                               holdout_cases=len(holdouts),
                               decisions_per_case=64,
                               payload_dibits_per_case=32,
                               phase_feature=SELECTED,
                               development_states=len(before),
                               holdout_states=len(after),
                               newly_observed_states=novel),
                  unseen_state_phase={key: dict(gate=phase(int(key, 16), covers),
                                                post_hoc_graph=after[int(key, 16)])
                                      for key in novel},
                  outcomes=outcomes,
                  limitations=[
                      'The gates were fitted to 14 development states; the holdout exercises one new state, not all 114 unobserved input combinations.',
                      'The ADC, row-0 capture, external phase logic and USART wiring remain untraced.',
                      'The R1 offsets are diagnostic interventions, not identified controller commands.',
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    print('new states', report['unseen_state_phase'],
          'outcomes', [(r['offset'], r['selector'], len(r['Boolean_wrong_indices']),
                       r['line_matches_offered'], r['aligned_errors'])
                      for r in outcomes], flush=True)
    return report


if __name__ == '__main__':
    run()
