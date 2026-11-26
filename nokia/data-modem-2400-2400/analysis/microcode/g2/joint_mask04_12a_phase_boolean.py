"""Minimize the observed four-phase state decoder to two Boolean outputs."""

import hashlib
import itertools
import json
from pathlib import Path

from joint_mask04_12a_phase_potential import EXTRAS, HERE, HOLDOUTS
from joint_mask04_12a_sixth_receive_bit import state

SOURCE = HERE / 'results/joint-mask04-12a-phase-potential.json'


def matches(cube, value):
    return all(bit < 0 or bit == ((value >> position) & 1)
               for position, bit in enumerate(cube))


def minimize_bit(phases, bit):
    on = sorted(value for value, phase in phases.items() if (phase >> bit) & 1)
    off = [value for value in phases if value not in on]
    candidates = []
    for cube in itertools.product((-1, 0, 1), repeat=6):
        if any(matches(cube, value) for value in off):
            continue
        mask = sum(1 << index for index, value in enumerate(on)
                   if matches(cube, value))
        if mask:
            candidates.append((cube, mask))
    full = (1 << len(on)) - 1
    best = {0: (0, 0, ())}
    for _ in on:
        newer = dict(best)
        for covered, prior in best.items():
            for cube, mask in candidates:
                updated = covered | mask
                candidate = (prior[0] + 1,
                             prior[1] + sum(value >= 0 for value in cube),
                             prior[2] + (cube,))
                if updated not in newer or candidate < newer[updated]:
                    newer[updated] = candidate
        best = newer
        if full in best:
            break
    if full not in best:
        raise ValueError('no Boolean cover for observed states')
    return best[full]


def phase(value, covers):
    return sum((int(any(matches(cube, value) for cube in cover)) << bit)
               for bit, cover in enumerate(covers))


def challenge(cases, covers, convention):
    inverse = {step: dibit for dibit, step in enumerate(convention)}
    result = []
    for case in cases:
        states = [state(a, b, EXTRAS)
                  for a, b in zip(case['first_y'], case['second_y'])]
        predicted = [None] + [inverse[(phase(after, covers) -
                                       phase(before, covers)) % 4]
                              for before, after in zip(states, states[1:])]
        wrong = [index for index, (got, want) in enumerate(
            zip(predicted[1:], case['expected_dibits'][1:]), 1)
                 if got != want]
        result.append(dict(selector=case['selector'], level=case.get('level'),
                           wrong_indices=wrong,
                           matches_lookup=predicted == case['decoded_dibits'],
                           predicted_dibits=predicted))
    return result


def run(out=HERE / 'results/joint-mask04-12a-phase-boolean.json'):
    source = json.loads(SOURCE.read_text())
    phases = {int(key, 16): value for key, value in source['state_phase'].items()}
    convention = source['fixture']['chosen_convention']
    optimized = [minimize_bit(phases, bit) for bit in (0, 1)]
    covers = [row[2] for row in optimized]
    if any(phase(value, covers) != expected for value, expected in phases.items()):
        raise ValueError('Boolean circuit changes a developed state phase')
    holdouts = {path.stem: challenge(json.loads(path.read_text())['cases'],
                                    covers, convention)
                for path in HOLDOUTS}
    paths = (Path(__file__), SOURCE, *HOLDOUTS,
             HERE / 'joint_mask04_12a_phase_potential.py',
             HERE / 'joint_mask04_12a_sixth_receive_bit.py')
    report = dict(experiment='minimum two-output Boolean cover of observed phase states',
                  fixture=dict(observed_states=len(phases), possible_states=64,
                               phase_convention=convention,
                               six_bit_state='first Y5–Y7; second Y4,Y6,Y7'),
                  phase_bits=[dict(bit=bit, product_terms=optimized[bit][0],
                                   literals=optimized[bit][1],
                                   cubes=[''.join('*' if x < 0 else str(x) for x in cube)
                                          for cube in covers[bit]])
                              for bit in (0, 1)],
                  observed_state_phases_exact=True,
                  holdouts=holdouts,
                  limitations=[
                      'The Boolean covers use labelled development-state phases and do not identify actual Nokia gates.',
                      'Unobserved input states are assigned by minimization, not validated by training or physical traces.',
                      'The later-clock challenge tests a different timing hypothesis; errors there do not overturn the original capture fixture.',
                  ],
                  source_sha256={str(p.relative_to(HERE.parents[4])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    for name, cases in holdouts.items():
        print(name, [(c['selector'], c['level'], len(c['wrong_indices']))
                     for c in cases], flush=True)
    return report


if __name__ == '__main__':
    run()
