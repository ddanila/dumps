"""Fit revised compact row-phase gates to the expanded 20-state graph."""

import hashlib
import json
from pathlib import Path

from joint_mask04_12a_multivisit_phase_screen import HERE, INPUTS, SELECTED, solve
from joint_mask04_12a_row0_boolean import minimize, phase

DEVELOPMENT = (HERE / 'results/joint-mask04-12a-row0-fresh-0.json',
               HERE / 'results/joint-mask04-12a-row0-fresh-64.json',
               HERE / 'results/joint-mask04-12a-row0-boolean-gain.json')
PRIOR = HERE / 'results/joint-mask04-12a-row0-boolean.json'


def run(out=HERE / 'results/joint-mask04-12a-row0-boolean-twenty.json'):
    cases = [case for path in (*INPUTS, *DEVELOPMENT)
             for case in json.loads(path.read_text())['cases']]
    if len(cases) != 22:
        raise ValueError('revised development case count changed')
    convention = (2, 1, 3, 0)
    potentials, conflicts, components = solve(cases, SELECTED, convention)
    if conflicts or len(components) != 1 or len(potentials) != 20:
        raise ValueError('revised row-0 phase graph changed')
    optimized = [minimize(potentials, bit) for bit in (0, 1)]
    covers = [row[2] for row in optimized]
    if any(phase(value, covers) != expected
           for value, expected in potentials.items()):
        raise ValueError('revised gates change a development phase')
    earlier = json.loads(PRIOR.read_text())
    paths = (Path(__file__), PRIOR, *INPUTS, *DEVELOPMENT,
             HERE / 'joint_mask04_12a_multivisit_phase_screen.py',
             HERE / 'joint_mask04_12a_row0_boolean.py')
    report = dict(experiment='revised Boolean phase gates on 20 observed row-0 states',
                  fixture=dict(development_cases=len(cases),
                               development_decisions=sum(len(c['expected_dibits']) - 1
                                                         for c in cases),
                               feature=SELECTED,
                               phase_convention=convention,
                               observed_states=len(potentials),
                               possible_states=128),
                  prior_phase_bits=earlier['phase_bits'],
                  phase_bits=[dict(bit=bit, product_terms=optimized[bit][0],
                                   literals=optimized[bit][1],
                                   cubes=[''.join('*' if x < 0 else str(x) for x in cube)
                                          for cube in covers[bit]])
                              for bit in (0, 1)],
                  state_phase={f'{key:02X}': value
                               for key, value in sorted(potentials.items())},
                  limitations=[
                      'The low-level failures are now development data; success on them does not validate the revised gates.',
                      'Unobserved states receive gate outputs by extrapolation, not by identified Nokia hardware.',
                      'ADC range, row latch, phase logic and USART connections remain explicit assumptions.',
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    print('revised gates', report['phase_bits'], flush=True)
    return report


if __name__ == '__main__':
    run()
