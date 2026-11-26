"""Audit frozen row-phase gates across gain and classify unseen-state errors."""

import hashlib
import json
from pathlib import Path

from joint_mask04_12a_multivisit_phase_screen import HERE, INPUTS, SELECTED, score, solve
from joint_mask04_12a_row0_boolean import phase

LOGIC = HERE / 'results/joint-mask04-12a-row0-boolean.json'
GAIN = HERE / 'results/joint-mask04-12a-row0-boolean-gain.json'
DEVELOPMENT = (HERE / 'results/joint-mask04-12a-row0-fresh-0.json',
               HERE / 'results/joint-mask04-12a-row0-fresh-64.json')


def run(out=HERE / 'results/joint-mask04-12a-row0-boolean-gain-audit.json'):
    model = json.loads(LOGIC.read_text())
    covers = [tuple(tuple(-1 if char == '*' else int(char) for char in cube)
                    for cube in row['cubes']) for row in model['phase_bits']]
    known = set(model['state_phase'])
    development = [case for path in (*INPUTS, *DEVELOPMENT)
                   for case in json.loads(path.read_text())['cases']]
    challenge = json.loads(GAIN.read_text())['cases']
    all_phases, conflicts, components = solve(
        development + challenge, SELECTED,
        tuple(model['fixture']['phase_convention']))
    if conflicts or len(components) != 1:
        raise ValueError('post-hoc gain phase graph changed')
    new_phases = {f'{key:02X}': dict(gate=phase(key, covers),
                                    post_hoc_graph=value)
                  for key, value in sorted(all_phases.items())
                  if f'{key:02X}' not in known}
    rows = []
    for case in challenge:
        result = case['boolean_phase']
        states = result['states']
        known_errors = [i for i in result['wrong_indices']
                        if states[i - 1] in known and states[i] in known]
        aligned = result['readout']['controller_handoffs']
        aligned = aligned['66'] if aligned else None
        rows.append(dict(selector=case['selector'], level=case['level'],
                         payload=case['payload'],
                         Boolean_wrong_indices=result['wrong_indices'],
                         known_state_wrong_indices=known_errors,
                         payload_wrong=sum(i >= 33 for i in result['wrong_indices']),
                         new_states=result['new_states'],
                         reference_wrong_indices=case['reference_wrong_indices'],
                         recovered_line_bytes=result['readout']['recovered_line_bytes'],
                         line_matches_offered=result['readout']['recovered_matches_offered'],
                         aligned_decoded_bytes=(aligned['decoded_bytes'] if aligned else None),
                         aligned_errors=(aligned['errors'] if aligned else None),
                         aligned_overruns=(aligned['overruns'] if aligned else None)))
    graph = {str(level): {key: value for key, value in score(
        development + [case for case in challenge if case['level'] == level],
        SELECTED).items() if key in ('minimum_conflicts', 'observed_states',
                                     'component_sizes', 'zero_conventions')}
             for level in (0.75, 1.0, 1.25)}
    paths = (Path(__file__), LOGIC, GAIN, *INPUTS, *DEVELOPMENT,
             HERE / 'joint_mask04_12a_multivisit_phase_screen.py',
             HERE / 'joint_mask04_12a_row0_boolean.py',
             HERE / 'joint_mask04_12a_row0_boolean_gain.py')
    report = dict(experiment='frozen row-0 Boolean phase gates across fixed line gain',
                  fixture=dict(levels=[0.75, 1.0, 1.25],
                               development_states=len(known),
                               post_hoc_states=len(all_phases),
                               phase_feature=SELECTED,
                               decisions_per_case=64,
                               payload_dibits_per_case=32),
                  new_state_phases=new_phases,
                  outcomes=rows,
                  graph_compatibility=graph,
                  limitations=[
                      'The post-hoc state phases use the new gain-case payload labels and cannot validate a revised gate rule.',
                      'These levels scale one assumed analog line; no physical AGC, ADC range or latch clock is established.',
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    print('new phases', new_phases,
          'wrong', [(row['selector'], row['level'], len(row['Boolean_wrong_indices']))
                   for row in rows], flush=True)
    return report


if __name__ == '__main__':
    run()
