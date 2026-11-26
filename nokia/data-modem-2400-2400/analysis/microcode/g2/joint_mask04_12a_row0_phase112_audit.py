"""Audit the frozen row-phase gates' offset-112 holdout failure."""

import hashlib
import json
from pathlib import Path

from joint_mask04_12a_multivisit_phase_screen import HERE, SELECTED, solve
from joint_mask04_12a_row0_boolean import phase
from joint_mask04_12a_row0_boolean_twenty import DEVELOPMENT, INPUTS

MODEL = HERE / 'results/joint-mask04-12a-row0-boolean-twenty.json'
HOLDOUT = HERE / 'results/joint-mask04-12a-row0-boolean-phase112.json'
OUT = HERE / 'results/joint-mask04-12a-row0-phase112-audit.json'


def run(out=OUT):
    model = json.loads(MODEL.read_text())
    holdout = json.loads(HOLDOUT.read_text())
    development = [case for path in (*INPUTS, *DEVELOPMENT)
                   for case in json.loads(path.read_text())['cases']]
    convention = tuple(model['fixture']['phase_convention'])
    potentials, conflicts, components = solve(
        development + holdout['cases'], SELECTED, convention)
    known = {int(key, 16): value for key, value in model['state_phase'].items()}
    if (conflicts or len(components) != 1 or len(potentials) != len(known) + 2 or
            any(potentials[key] != value for key, value in known.items())):
        raise ValueError('combined graph does not extend the frozen development map')
    new = {key: value for key, value in potentials.items() if key not in known}
    if new != {0x12: 3, 0x5E: 0}:
        raise ValueError('unseen phase states changed')
    covers = [tuple(tuple(-1 if char == '*' else int(char) for char in cube)
                    for cube in bit['cubes']) for bit in model['phase_bits']]
    frozen_new = {f'{key:02X}': phase(key, covers) for key in new}
    if frozen_new != {'12': 3, '5E': 1}:
        raise ValueError('frozen gate extrapolation changed')
    inverse = {step: dibit for dibit, step in enumerate(convention)}
    outcomes = []
    for case in holdout['cases']:
        gate = case['boolean_phase']
        states = [int(value, 16) for value in gate['states']]
        expected = case['expected_dibits']
        predicted = [inverse[(potentials[b] - potentials[a]) & 3]
                     for a, b in zip(states, states[1:])]
        if predicted != expected[1:]:
            raise ValueError('diagnostic extended map is not exact')
        wrong = gate['wrong_indices']
        if not wrong or any(0x5E not in (states[i-1], states[i]) for i in wrong):
            raise ValueError('frozen errors do not all touch state 5E')
        if set(wrong) & {index + 1 for index in case['reference_wrong_indices']}:
            raise ValueError('reference and gate errors unexpectedly overlap')
        outcomes.append(dict(selector=case['selector'],
                             payload=case['payload'],
                             reference_wrong_indices_zero_based=case['reference_wrong_indices'],
                             frozen_gate_wrong_indices_one_based=wrong,
                             frozen_gate_errors=len(wrong),
                             unseen_states=gate['new_states'],
                             diagnostic_relabel_errors=0,
                             affected_state='5E'))
    paths = (Path(__file__), MODEL, HOLDOUT, *INPUTS, *DEVELOPMENT,
             HERE / 'joint_mask04_12a_multivisit_phase_screen.py',
             HERE / 'joint_mask04_12a_row0_boolean.py')
    report = dict(experiment='offset-112 frozen 20-state gate holdout audit',
                  fixture=dict(R1_offset=112, level=1.0,
                               development_cases=len(development),
                               observed_states=len(potentials),
                               development_states=len(known),
                               combined_graph_conflicts=conflicts),
                  new_state_phases={f'{key:02X}': value for key, value in sorted(new.items())},
                  frozen_gate_new_state_phases=frozen_new,
                  outcomes=outcomes,
                  limitations=[
                      'The 5E phase inferred from holdout labels is a post-hoc diagnostic, not a validated revised gate.',
                      'The independent reference decoder also misses one or two dibits in this phase-112 fixture.',
                      'ADC, row latch, phase logic, analog filter and USART nets remain assumed.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    print('phase112', [(row['selector'], row['frozen_gate_errors'])
                       for row in outcomes], 'new', report['new_state_phases'], flush=True)
    return report


if __name__ == '__main__':
    run()
