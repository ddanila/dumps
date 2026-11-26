"""Audit frozen changed-mode phase gates on phase-128 real-PROM holdouts."""

import hashlib
import json
from pathlib import Path

from joint_mask04_12a_multivisit_phase_screen import HERE, SELECTED, sample_state
from joint_mask04_12a_row0_boolean import phase
from joint_mask04_12a_row0_serial_timing import covers_from_model

MODEL = HERE / 'results/joint-mask04-12a-mode-phase-twelve.json'
HOLDOUT = HERE / 'results/joint-mask04-12a-mode-phase128-challenge.json'
OUT = HERE / 'results/joint-mask04-12a-mode-phase128-audit.json'


def run(out=OUT):
    model = json.loads(MODEL.read_text())
    holdout = json.loads(HOLDOUT.read_text())
    covers = covers_from_model(model)
    labels = {int(key, 16): value for key, value in
              model['trained_state_phase'].items()}
    inverse = {step: dibit for dibit, step in
               enumerate(model['fixture']['phase_convention'])}
    outcomes = []
    if holdout['fixture']['R1_offset'] != 128 or len(holdout['cases']) != 2:
        raise ValueError('phase-128 fixture changed')
    for case in holdout['cases']:
        states = [sample_state(symbol, SELECTED)
                  for symbol in case['multi_visit_symbols']]
        phases = [phase(state, covers) for state in states]
        wrong = [index for index, (before, after) in enumerate(
            zip(phases, phases[1:]), 1)
            if inverse[(after - before) & 3] != case['expected_dibits'][index]]
        expected_payload = [int(value, 16) for value in case['payload']]
        if (len(states) != 65 or set(states) - set(labels) or
                any(phase(state, covers) != labels[state] for state in states) or
                wrong or case['frozen_gate_wrong_indices'] or
                case['reference_wrong_indices'] or
                not case['recovered_matches_offered'] or
                case['controller_decoded_bytes'] != expected_payload or
                case['controller_errors'] or case['controller_overruns'] or
                case['minimum_setup_cycles'] != 2961 or
                states.count(0x09) != 32):
            raise ValueError(('phase-128 holdout changed', case['selector']))
        outcomes.append(dict(selector=case['selector'],
                             state_09_symbols=states.count(0x09),
                             observed_states=len(set(states)),
                             unseen_states=0, reference_errors=0,
                             gate_errors=0, exact_line_bytes=True,
                             exact_controller_bytes=True))
    paths = (Path(__file__), MODEL, HOLDOUT,
             HERE / 'joint_mask04_12a_multivisit_phase_screen.py')
    report = dict(experiment='frozen 12-state changed-mode gate phase-128 holdout audit',
                  fixture=dict(R1_offset=128, assumed_mode='81-to-A1 at D3EB',
                               frozen_line_shift=5, cases=2),
                  outcomes=outcomes,
                  limitations=[
                      'The phase-128 streams visit only previously labeled states, so this does not test Boolean extrapolation.',
                      'The line, mode, latch, logic and USART routes remain assumed; no physical serial net is identified.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(run()['outcomes'])
