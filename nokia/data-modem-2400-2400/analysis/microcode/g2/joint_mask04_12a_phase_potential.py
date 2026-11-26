"""Test whether the six-bit Y states admit a DPSK phase-difference rule."""

import hashlib
import itertools
import json
from collections import defaultdict, deque
from pathlib import Path

from joint_mask04_12a_sixth_receive_bit import state

HERE = Path(__file__).resolve().parent
DEVELOPMENT = (
    HERE / 'results/joint-mask04-12a-fifth-receive-bit.json',
    HERE / 'results/joint-mask04-12a-frozen-fifth-new-payloads.json',
)
HOLDOUTS = (
    HERE / 'results/joint-mask04-12a-frozen-sixth-new-payloads.json',
    HERE / 'results/joint-mask04-12a-frozen-sixth-phase96.json',
    HERE / 'results/joint-mask04-12a-sixth-late-capture.json',
)
EXTRAS = (('second', 4), ('second', 6))


def edges(cases):
    for case in cases:
        states = [state(a, b, EXTRAS)
                  for a, b in zip(case['first_y'], case['second_y'])]
        for index, (before, after) in enumerate(zip(states, states[1:]), 1):
            yield before, after, case['expected_dibits'][index]


def phase_potential(training, convention):
    graph = defaultdict(list)
    for before, after, dibit in edges(training):
        step = convention[dibit]
        graph[before].append((after, step))
        graph[after].append((before, -step))
    potentials = {}
    conflicts = 0
    components = 0
    for seed in graph:
        if seed in potentials:
            continue
        components += 1
        potentials[seed] = 0
        queue = deque([seed])
        while queue:
            before = queue.popleft()
            for after, step in graph[before]:
                value = (potentials[before] + step) % 4
                if after in potentials:
                    conflicts += potentials[after] != value
                else:
                    potentials[after] = value
                    queue.append(after)
    return potentials, conflicts, components


def challenge(cases, potentials, convention):
    inverse = {step: dibit for dibit, step in enumerate(convention)}
    result = []
    for case in cases:
        states = [state(a, b, EXTRAS)
                  for a, b in zip(case['first_y'], case['second_y'])]
        predicted = [None]
        for before, after in zip(states, states[1:]):
            predicted.append(None if before not in potentials or after not in potentials
                             else inverse[(potentials[after] - potentials[before]) % 4])
        wrong = [i for i, (got, want) in enumerate(
            zip(predicted[1:], case['expected_dibits'][1:]), 1)
                 if got is not None and got != want]
        unknown = [i for i, got in enumerate(predicted[1:], 1) if got is None]
        result.append(dict(selector=case['selector'], level=case.get('level'),
                           observed_states=sorted(f'{value:02X}' for value in set(states)),
                           new_states=sorted(f'{value:02X}' for value in set(states)
                                             if value not in potentials),
                           wrong_indices=wrong, unknown_indices=unknown,
                           predicted_dibits=predicted))
    return result


def run(out=HERE / 'results/joint-mask04-12a-phase-potential.json'):
    training = [case for path in DEVELOPMENT
                for case in json.loads(path.read_text())['cases']]
    if len(training) != 14:
        raise ValueError('development case count changed')
    solutions = []
    for convention in itertools.permutations(range(4)):
        potentials, conflicts, components = phase_potential(training, convention)
        if not conflicts:
            solutions.append((convention, potentials, components))
    if len(solutions) != 2 or any(components != 1 or len(potentials) != 18
                                  for _, potentials, components in solutions):
        raise ValueError('development phase solutions changed')
    convention, potentials, _ = solutions[0]
    holdouts = {}
    for path in HOLDOUTS:
        holdouts[path.stem] = challenge(json.loads(path.read_text())['cases'],
                                       potentials, convention)
    paths = (Path(__file__), HERE / 'joint_mask04_12a_sixth_receive_bit.py',
             *DEVELOPMENT, *HOLDOUTS)
    report = dict(experiment='four-phase potential for six-bit Y states',
                  fixture=dict(development_cases=14,
                               development_transitions=sum(len(c['expected_dibits']) - 1
                                                           for c in training),
                               state_bits='first Y5–Y7; second Y4,Y6,Y7',
                               capture_visits=[46, 93],
                               conventions_tested=24,
                               solution_conventions=[list(c) for c, _, _ in solutions],
                               chosen_convention=list(convention),
                               observed_states=len(potentials),
                               connected_components=1),
                  state_phase={f'{key:02X}': value
                               for key, value in sorted(potentials.items())},
                  holdouts=holdouts,
                  limitations=[
                      'The state phases and dibit convention are inferred from 14 labelled development cases, not from identified hardware.',
                      'Only 18 of 64 possible states are observed in development; an unseen state remains undecoded.',
                      'Holdouts reuse saved real-PROM captures; they are independent of the phase fit but not new physical measurements.',
                      'The one-visit-late capture is a deliberately changed clock hypothesis, not the established 46/93 fixture.',
                  ],
                  source_sha256={str(p.relative_to(HERE.parents[4])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    for name, cases in holdouts.items():
        print(name, [(c['selector'], c['level'], len(c['wrong_indices']),
                      len(c['unknown_indices'])) for c in cases], flush=True)
    return report


if __name__ == '__main__':
    run()
