"""Audit unseen-state transfer in the frozen phase-120 holdout."""

import hashlib
import json
from pathlib import Path

from joint_mask04_12a_multivisit_phase_screen import HERE, INPUTS, SELECTED, solve
from joint_mask04_12a_row0_boolean import phase
from joint_mask04_12a_row0_boolean_twenty import DEVELOPMENT

PHASE112 = HERE / 'results/joint-mask04-12a-row0-boolean-phase112.json'
MODEL = HERE / 'results/joint-mask04-12a-row0-boolean-twentytwo.json'
HOLDOUT = HERE / 'results/joint-mask04-12a-row0-twentytwo-phase120.json'
OUT = HERE / 'results/joint-mask04-12a-row0-phase120-audit.json'


def run(out=OUT):
    model = json.loads(MODEL.read_text())
    holdout = json.loads(HOLDOUT.read_text())
    development = [case for path in (*INPUTS, *DEVELOPMENT, PHASE112)
                   for case in json.loads(path.read_text())['cases']]
    convention = tuple(model['fixture']['phase_convention'])
    potentials, conflicts, components = solve(development, SELECTED, convention)
    known = {int(key, 16): value for key, value in model['state_phase'].items()}
    if (len(development) != 24 or conflicts or len(components) != 1 or
            len(known) != 22 or len(potentials) != len(known) or
            any(potentials[key] != value for key, value in known.items())):
        raise ValueError('22-state development graph changed')
    constraints = set()
    for case in holdout['cases']:
        states = [int(value, 16) for value in case['states']]
        expected = case['expected_dibits']
        for index, (before, after) in enumerate(zip(states, states[1:]), 1):
            step = convention[expected[index]]
            if before in known and after == 0x59:
                constraints.add((known[before] + step) & 3)
            elif before == 0x59 and after in known:
                constraints.add((known[after] - step) & 3)
    if constraints != {2}:
        raise ValueError(('unseen state has conflicting anchors', constraints))
    potentials[0x59] = 2
    holdout_conflicts = sum(
        ((potentials[int(case['states'][index], 16)] -
          potentials[int(case['states'][index-1], 16)]) & 3) !=
        convention[case['expected_dibits'][index]]
        for case in holdout['cases']
        for index in range(1, len(case['states'])))
    if holdout_conflicts:
        raise ValueError(('holdout phase graph conflict', holdout_conflicts))
    covers = [tuple(tuple(-1 if char == '*' else int(char) for char in cube)
                    for cube in bit['cubes']) for bit in model['phase_bits']]
    if phase(0x59, covers) != 2:
        raise ValueError('frozen gate misses unseen state 59')
    outcomes = []
    for case in holdout['cases']:
        source = [int(value, 16) for value in case['payload']]
        handoffs = case['readout']['controller_handoffs']
        count = case['states'].count('59')
        if (case['unseen_states'] != ['59'] or count < 30 or
                case['reference_wrong_indices_zero_based'] or
                case['wrong_indices_one_based'] or
                not case['readout']['recovered_matches_offered'] or
                handoffs['66']['decoded_bytes'] != source or
                handoffs['66']['errors'] or handoffs['66']['overruns'] or
                handoffs['65']['decoded_bytes'] == source or
                handoffs['67']['decoded_bytes'] == source):
            raise ValueError(('phase-120 holdout behavior changed', case['selector']))
        outcomes.append(dict(selector=case['selector'],
                             state_59_symbols=count,
                             reference_errors=0,
                             gate_errors=0,
                             offered_line_bytes_recovered=True,
                             aligned_source_bytes_recovered=True,
                             one_bit_early_source_recovered=False,
                             one_bit_late_source_recovered=False))
    paths = (Path(__file__), MODEL, HOLDOUT, PHASE112, *INPUTS, *DEVELOPMENT,
             HERE / 'joint_mask04_12a_multivisit_phase_screen.py',
             HERE / 'joint_mask04_12a_row0_boolean.py')
    report = dict(experiment='frozen 22-state row-phase gate transfer to unseen state 59',
                  fixture=dict(R1_offset=120, development_cases=len(development),
                               development_states=len(known),
                               combined_states=len(potentials),
                               combined_graph_conflicts=conflicts + holdout_conflicts,
                               components=len(components)),
                  unseen_state=dict(code='59', graph_phase=2, frozen_gate_phase=2),
                  outcomes=outcomes,
                  limitations=[
                      'This holdout constrains an external gate model, not an executed DSC phase decision.',
                      'The line shift, ADC input, row capture, logic, RxD/RxC and SYNDET remain assumed routes.',
                      'One unseen state and two payloads do not establish arbitrary carrier/gain robustness.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    print('phase120 unseen', report['unseen_state'], outcomes, flush=True)
    return report


if __name__ == '__main__':
    run()
