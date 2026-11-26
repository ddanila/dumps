"""Independently infer the new 3D phase and audit full serial replay."""

import hashlib
import json
from pathlib import Path

from joint_mask04_12a_multivisit_phase_screen import SELECTED, sample_state
from joint_mask04_12a_row0_boolean import phase
from joint_mask04_12a_row0_serial_timing import covers_from_model
from photo_u15_u19_u21_phase_route import circuit

HERE = Path(__file__).resolve().parent
MODEL = HERE / 'results/joint-mask04-12a-mode-phase-twelve.json'
RUN = HERE / 'results/joint-mask04-12a-mode-phase125-challenge.json'
OUT = HERE / 'results/joint-mask04-12a-mode-phase125-audit.json'


def run(out=OUT):
    model = json.loads(MODEL.read_text())
    challenge = json.loads(RUN.read_text())
    labels = {int(code, 16): value for code, value in
              model['trained_state_phase'].items()}
    covers = covers_from_model(model)
    steps = model['fixture']['phase_convention']
    cases = []
    for case in challenge['cases']:
        states = [sample_state(symbol, SELECTED)
                  for symbol in case['multi_visit_symbols']]
        expected = case['expected_dibits']
        anchors = []
        for index, state in enumerate(states):
            if state != 0x3D:
                continue
            if index and states[index - 1] in labels:
                anchors.append((labels[states[index - 1]] +
                                steps[expected[index]]) & 3)
            if index + 1 < len(states) and states[index + 1] in labels:
                anchors.append((labels[states[index + 1]] -
                                steps[expected[index + 1]]) & 3)
        crossings = [index for index in range(1, len(states))
                     if (states[index - 1] == 0x3D) != (states[index] == 0x3D)]
        serial = case['package_circuit_serial']
        payload = [int(value, 16) for value in case['payload']]
        if (len(states) != 65 or set(states) - set(labels) != {0x3D} or
                not anchors or set(anchors) != {1} or
                phase(0x3D, covers) != 0 or circuit(0x3D, 1) != 1 or
                case['frozen_gate_wrong_indices'] != crossings or
                case['reference_wrong_indices'] or
                case['package_circuit_wrong_indices'] or
                serial['wrong_decision_indices'] or
                serial['unknown_rxc_edges'] or
                not serial['recovered_matches_offered'] or
                serial['controller_decoded_bytes'] != payload or
                serial['controller_errors'] or serial['controller_overruns'] or
                serial['minimum_setup_cycles'] != 2961):
            raise ValueError(('phase-125 audit failed', case['selector']))
        cases.append(dict(selector=case['selector'],
                          new_state='3D', independent_anchor_constraints=len(anchors),
                          inferred_phase=1, frozen_cover_phase=0,
                          package_circuit_phase=1,
                          old_cover_errors=len(crossings),
                          package_circuit_errors=0,
                          reference_errors=0,
                          exact_line_and_controller_bytes=True))
    if len(cases) != 2 or [case['old_cover_errors'] for case in cases] != [14, 8]:
        raise ValueError('phase-125 case coverage changed')
    paths = (Path(__file__), MODEL, RUN,
             HERE / 'photo_u15_u19_u21_phase_route.py')
    report = dict(experiment='new-state 3D independent phase and serial audit',
                  cases=cases,
                  limitations=[
                      'The reference dibits and previous state labels infer phase 1 for 3D under the existing phase convention; this is still a model of the assumed board route.',
                      'The package equations have not been traced to physical pins and remain untested on further unseen states or a measured line.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(run()['cases'])
