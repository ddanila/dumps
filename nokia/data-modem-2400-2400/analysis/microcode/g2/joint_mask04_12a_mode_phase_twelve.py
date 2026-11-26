"""Revise the changed-mode gate after the phase-120 unseen-state failure."""

import hashlib
import json
from pathlib import Path

from joint_mask04_12a_multivisit_phase_screen import HERE, SELECTED, solve
from joint_mask04_12a_row0_boolean import minimize, phase
from joint_mask04_12a_row0_serial_timing import covers_from_model

BASE = HERE / 'results/joint-mask04-12a-mode-phase-holdout.json'
CALL = HERE / 'results/joint-mask04-12a-row-mode-edge.json'
PHASE112 = HERE / 'results/joint-mask04-12a-row0-boolean-phase112.json'
PHASE120 = HERE / 'results/joint-mask04-12a-mode-fresh-phase120.json'
OUT = HERE / 'results/joint-mask04-12a-mode-phase-twelve.json'


def run(out=OUT):
    base = json.loads(BASE.read_text())
    call = json.loads(CALL.read_text())
    phase112 = json.loads(PHASE112.read_text())
    phase120 = json.loads(PHASE120.read_text())
    first = next(case for case in phase112['cases'] if case['selector'] == '40')
    cases = [dict(multi_visit_symbols=first['multi_visit_symbols'],
                  expected_dibits=first['expected_dibits'])]
    cases.extend(dict(multi_visit_symbols=case['states'],
                      expected_dibits=first['expected_dibits'])
                 for case in call['cases'])
    cases.extend(phase120['cases'])
    convention = tuple(base['fixture']['phase_convention'])
    potentials, conflicts, components = solve(cases, SELECTED, convention)
    old = {int(key, 16): value for key, value in
           base['trained_state_phase'].items()}
    if conflicts or len(components) != 1 or len(potentials) != 12:
        raise ValueError('expanded mode phase graph changed')
    anchor = min(old)
    offset = (old[anchor] - potentials[anchor]) & 3
    anchored = {state: (value + offset) & 3
                for state, value in potentials.items()}
    if any(anchored[state] != label for state, label in old.items()):
        raise ValueError('new phase graph conflicts with frozen development')
    previous = covers_from_model(base)
    changed = {f'{state:02X}': dict(frozen=phase(state, previous),
                                   graph=anchored[state])
               for state in anchored.keys() - old.keys()
               if phase(state, previous) != anchored[state]}
    if changed != {'36': dict(frozen=1, graph=0)}:
        raise ValueError(('unseen-state failure changed', changed))
    optimized = [minimize(anchored, bit) for bit in (0, 1)]
    covers = [row[2] for row in optimized]
    if any(phase(state, covers) != value for state, value in anchored.items()):
        raise ValueError('new Boolean cover changes a trained state')
    paths = (Path(__file__), BASE, CALL, PHASE112, PHASE120,
             HERE / 'joint_mask04_12a_multivisit_phase_screen.py',
             HERE / 'joint_mask04_12a_row0_boolean.py')
    report = dict(experiment='12-state changed-mode phase gates after phase-120 challenge',
                  fixture=dict(development_cases=len(cases),
                               development_states=len(anchored),
                               graph_conflicts=conflicts,
                               phase_convention=convention,
                               feature=SELECTED),
                  prior_unseen_state_failures=changed,
                  trained_state_phase={f'{state:02X}': value
                                       for state, value in sorted(anchored.items())},
                  phase_bits=[dict(bit=bit, product_terms=optimized[bit][0],
                                   literals=optimized[bit][1],
                                   cubes=[''.join('*' if x < 0 else str(x) for x in cube)
                                          for cube in covers[bit]])
                              for bit in (0, 1)],
                  limitations=[
                      'The failed fresh phase-120 pair is now development data; it cannot validate this revised gate.',
                      'Unobserved states receive Boolean extrapolations, not identified Nokia logic.',
                      'The mode input, capture, line and USART wiring remain assumed.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    print('12-state phase gates', report['phase_bits'], flush=True)
    return report


if __name__ == '__main__':
    run()
