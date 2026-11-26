"""Fit a compact phase gate rule to the now-observed row-0 state graph."""

import hashlib
import itertools
import json
from pathlib import Path

from joint_mask04_12a_multivisit_phase_screen import HERE, INPUTS, SELECTED, solve

FRESH = (HERE / 'results/joint-mask04-12a-row0-fresh-0.json',
         HERE / 'results/joint-mask04-12a-row0-fresh-64.json')


def matches(cube, value):
    return all(bit < 0 or bit == ((value >> position) & 1)
               for position, bit in enumerate(cube))


def minimize(phases, bit):
    on = sorted(value for value, phase in phases.items() if (phase >> bit) & 1)
    off = [value for value in phases if value not in on]
    candidates = []
    for cube in itertools.product((-1, 0, 1), repeat=7):
        if any(matches(cube, value) for value in off):
            continue
        mask = sum(1 << index for index, value in enumerate(on)
                   if matches(cube, value))
        if mask:
            candidates.append((cube, mask))
    full = (1 << len(on)) - 1
    best = {0: (0, 0, ())}
    for _ in on:
        next_best = dict(best)
        for covered, prior in best.items():
            for cube, mask in candidates:
                updated = covered | mask
                proposed = (prior[0] + 1,
                            prior[1] + sum(value >= 0 for value in cube),
                            prior[2] + (cube,))
                if updated not in next_best or proposed < next_best[updated]:
                    next_best[updated] = proposed
        best = next_best
        if full in best:
            break
    if full not in best:
        raise ValueError('no Boolean cover for observed phase bit')
    return best[full]


def phase(value, covers):
    return sum((int(any(matches(cube, value) for cube in cover)) << bit)
               for bit, cover in enumerate(covers))


def run(out=HERE / 'results/joint-mask04-12a-row0-boolean.json'):
    cases = [case for path in (*INPUTS, *FRESH)
             for case in json.loads(path.read_text())['cases']]
    if len(cases) != 16:
        raise ValueError('phase-logic development case count changed')
    convention = (2, 1, 3, 0)
    potentials, conflicts, components = solve(cases, SELECTED, convention)
    if conflicts or len(components) != 1 or len(potentials) != 14:
        raise ValueError('row-0 phase graph changed')
    optimized = [minimize(potentials, bit) for bit in (0, 1)]
    covers = [row[2] for row in optimized]
    if any(phase(value, covers) != expected
           for value, expected in potentials.items()):
        raise ValueError('Boolean cover changes a development phase')
    paths = (Path(__file__), HERE / 'joint_mask04_12a_multivisit_phase_screen.py',
             *INPUTS, *FRESH)
    report = dict(experiment='minimal separate-output Boolean phase gates on 14 row-0 states',
                  fixture=dict(development_cases=len(cases),
                               development_decisions=sum(len(c['expected_dibits']) - 1
                                                         for c in cases),
                               feature=SELECTED,
                               state_bits='first Y5–Y7; second Y7,Y4,Y6; 3ED row0 bit0',
                               phase_convention=convention,
                               observed_states=len(potentials),
                               possible_states=128),
                  phase_bits=[dict(bit=bit, product_terms=optimized[bit][0],
                                   literals=optimized[bit][1],
                                   cubes=[''.join('*' if x < 0 else str(x) for x in cube)
                                          for cube in covers[bit]])
                              for bit in (0, 1)],
                  state_phase={f'{key:02X}': value
                               for key, value in sorted(potentials.items())},
                  limitations=[
                      'The offset-0/64 payload labels are development data for this Boolean cover; they are no longer holdouts.',
                      'Unobserved states receive gate outputs by extrapolation, not by an identified Nokia circuit.',
                      'The row-0 bit and the two Y capture edges are untraced physical hypotheses.',
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    print('phase gates', report['phase_bits'], flush=True)
    return report


if __name__ == '__main__':
    run()
