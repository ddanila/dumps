"""Audit the failed eight-state challenge and frozen 12-state holdout."""

import hashlib
import json
from pathlib import Path

from joint_mask04_12a_multivisit_phase_screen import HERE, SELECTED, solve
from joint_mask04_12a_row0_boolean import phase
from joint_mask04_12a_row0_serial_timing import covers_from_model

MODEL = HERE / 'results/joint-mask04-12a-mode-phase-twelve.json'
FAILED = HERE / 'results/joint-mask04-12a-mode-fresh-phase120.json'
HOLDOUT = HERE / 'results/joint-mask04-12a-mode-twelve-holdout.json'
CALL = HERE / 'results/joint-mask04-12a-row-mode-edge.json'
PHASE112 = HERE / 'results/joint-mask04-12a-row0-boolean-phase112.json'
OUT = HERE / 'results/joint-mask04-12a-mode-twelve-audit.json'


def run(out=OUT):
    model = json.loads(MODEL.read_text())
    failed = json.loads(FAILED.read_text())
    holdout = json.loads(HOLDOUT.read_text())
    call = json.loads(CALL.read_text())
    phase112 = json.loads(PHASE112.read_text())
    covers = covers_from_model(model)
    labels = {int(key, 16): value for key, value in
              model['trained_state_phase'].items()}
    convention = tuple(model['fixture']['phase_convention'])
    if model['prior_unseen_state_failures'] != {
            '36': dict(frozen=1, graph=0)}:
        raise ValueError('prior unseen-state correction changed')
    first = next(case for case in phase112['cases'] if case['selector'] == '40')
    combined = [dict(multi_visit_symbols=first['multi_visit_symbols'],
                     expected_dibits=first['expected_dibits'])]
    combined.extend(dict(multi_visit_symbols=case['states'],
                         expected_dibits=first['expected_dibits'])
                    for case in call['cases'])
    combined.extend(failed['cases'] + holdout['cases'])
    potentials, conflicts, components = solve(combined, SELECTED, convention)
    if conflicts or len(components) != 1 or set(potentials) != set(labels):
        raise ValueError(('phase-120 graph changed', conflicts, len(potentials)))
    anchor = min(labels)
    offset = (labels[anchor] - potentials[anchor]) & 3
    if any(((value + offset) & 3) != labels[state] or
           phase(state, covers) != labels[state]
           for state, value in potentials.items()):
        raise ValueError('holdout phase graph disagrees with frozen gates')
    outcomes = []
    for case in holdout['cases']:
        expected = [int(value, 16) for value in case['payload']]
        if (case['unseen_states'] or case['frozen_gate_wrong_indices'] or
                not case['recovered_matches_offered'] or
                case['controller_decoded_bytes'] != expected or
                case['controller_errors'] or case['controller_overruns'] or
                case['minimum_setup_cycles'] != 2961):
            raise ValueError(('mode holdout changed', case['selector']))
        outcomes.append(dict(selector=case['selector'],
                             reference_errors=len(case['reference_wrong_indices']),
                             gate_errors=0, offered_line_bytes_recovered=True,
                             decoded_source_bytes=case['controller_decoded_bytes'],
                             old_gate_errors=len(case['old_gate_wrong_indices'])))
    paths = (Path(__file__), MODEL, FAILED, HOLDOUT, CALL, PHASE112,
             HERE / 'joint_mask04_12a_multivisit_phase_screen.py')
    report = dict(experiment='frozen 12-state changed-mode phase holdout audit',
                  fixture=dict(failed_development_cases=len(failed['cases']),
                               new_holdout_cases=len(holdout['cases']),
                               phase_offset=120,
                               graph_states=len(potentials),
                               graph_conflicts=conflicts,
                               graph_components=len(components)),
                  outcomes=outcomes,
                  limitations=[
                      'The phase-120 failed pair is development data for the revised gate; the later pair alone is its holdout.',
                      'No new state appears in the holdout; this does not establish arbitrary phase/gain robustness.',
                      'The phase gates and mode/serial wiring are external assumptions, not identified Nokia circuitry.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(run()['outcomes'])
