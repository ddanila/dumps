"""Fit compact phase gates after moving the failed phase-112 pair to development."""

import hashlib
import json
from pathlib import Path

from joint_mask04_12a_multivisit_phase_screen import HERE, INPUTS, SELECTED, solve
from joint_mask04_12a_row0_boolean import minimize, phase
from joint_mask04_12a_row0_boolean_twenty import DEVELOPMENT

PHASE112 = HERE / 'results/joint-mask04-12a-row0-boolean-phase112.json'
PRIOR = HERE / 'results/joint-mask04-12a-row0-boolean-twenty.json'
OUT = HERE / 'results/joint-mask04-12a-row0-boolean-twentytwo.json'


def run(out=OUT):
    prior = json.loads(PRIOR.read_text())
    cases = [case for path in (*INPUTS, *DEVELOPMENT, PHASE112)
             for case in json.loads(path.read_text())['cases']]
    convention = tuple(prior['fixture']['phase_convention'])
    potentials, conflicts, components = solve(cases, SELECTED, convention)
    if (len(cases) != 24 or conflicts or len(components) != 1 or
            len(potentials) != 22 or potentials[0x5E] != 0):
        raise ValueError('22-state development graph changed')
    old = {int(key, 16): value for key, value in prior['state_phase'].items()}
    if any(potentials[key] != value for key, value in old.items()):
        raise ValueError('prior 20-state phase assignment changed')
    optimized = [minimize(potentials, bit) for bit in (0, 1)]
    covers = [row[2] for row in optimized]
    if any(phase(value, covers) != expected for value, expected in potentials.items()):
        raise ValueError('new gates change a development phase')
    paths = (Path(__file__), PRIOR, PHASE112, *INPUTS, *DEVELOPMENT,
             HERE / 'joint_mask04_12a_multivisit_phase_screen.py',
             HERE / 'joint_mask04_12a_row0_boolean.py')
    report = dict(experiment='22-state Boolean row-phase gates including failed phase-112 pair',
                  fixture=dict(development_cases=len(cases),
                               development_states=len(potentials),
                               phase_convention=convention,
                               feature=SELECTED),
                  phase_bits=[dict(bit=bit, product_terms=optimized[bit][0],
                                   literals=optimized[bit][1],
                                   cubes=[''.join('*' if x < 0 else str(x) for x in cube)
                                          for cube in covers[bit]])
                              for bit in (0, 1)],
                  state_phase={f'{key:02X}': value
                               for key, value in sorted(potentials.items())},
                  limitations=[
                      'The phase-112 labels are development data and cannot validate these gates.',
                      'Unobserved state outputs are extrapolations, not identified Nokia logic.',
                      'ADC, row capture, logic and USART connections remain explicit circuit assumptions.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    print('22-state gates', report['phase_bits'], flush=True)
    return report


if __name__ == '__main__':
    run()
