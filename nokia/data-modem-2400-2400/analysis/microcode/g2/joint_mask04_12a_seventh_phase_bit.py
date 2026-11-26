"""Screen one extra Y bit for a consistent four-phase receive state."""

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
    HERE / 'results/joint-mask04-12a-phase-logic-fresh-16.json',
    HERE / 'results/joint-mask04-12a-phase-logic-fresh-80.json',
)
HOLDOUTS = (
    HERE / 'results/joint-mask04-12a-frozen-sixth-new-payloads.json',
    HERE / 'results/joint-mask04-12a-frozen-sixth-phase96.json',
    HERE / 'results/joint-mask04-12a-sixth-late-capture.json',
)
BASE = (('second', 4), ('second', 6))
UNUSED = tuple([('first', bit) for bit in range(5)] +
               [('second', bit) for bit in (0, 1, 2, 3, 5)])
CONVENTIONS = tuple(itertools.permutations(range(4)))


def states(case, extra):
    if extra == 'full':
        return [(a << 8) | b for a, b in zip(case['first_y'], case['second_y'])]
    extras = BASE if extra is None else BASE + (extra,)
    return [state(a, b, extras)
            for a, b in zip(case['first_y'], case['second_y'])]


def solve(cases, extra, convention):
    graph = defaultdict(list)
    for case in cases:
        sample_states = states(case, extra)
        for index, (before, after) in enumerate(
                zip(sample_states, sample_states[1:]), 1):
            step = convention[case['expected_dibits'][index]]
            graph[before].append((after, step))
            graph[after].append((before, -step))
    potentials = {}
    conflicts = 0
    components = []
    for seed in graph:
        if seed in potentials:
            continue
        potentials[seed] = 0
        queue = deque([seed])
        component = []
        while queue:
            before = queue.popleft()
            component.append(before)
            for after, step in graph[before]:
                value = (potentials[before] + step) % 4
                if after in potentials:
                    conflicts += potentials[after] != value
                else:
                    potentials[after] = value
                    queue.append(after)
        components.append(component)
    return potentials, conflicts, components


def score(cases, extra):
    results = [(convention, *solve(cases, extra, convention))
               for convention in CONVENTIONS]
    minimum = min(row[2] for row in results)
    winners = [row for row in results if row[2] == minimum]
    convention, potentials, _, components = winners[0]
    return dict(extra=extra, minimum_conflicts=minimum,
                zero_conflict_conventions=[list(row[0]) for row in results
                                           if row[2] == 0],
                best_convention=list(convention),
                observed_states=len(potentials),
                component_sizes=sorted((len(c) for c in components), reverse=True),
                state_phase={f'{key:04X}' if extra == 'full' else f'{key:02X}': value
                             for key, value in sorted(potentials.items())}
                if minimum == 0 else None)


def challenge(cases, extra, phases, components, convention):
    inverse = {step: dibit for dibit, step in enumerate(convention)}
    component_of = {value: number for number, group in enumerate(components)
                    for value in group}
    result = []
    for case in cases:
        sample_states = states(case, extra)
        decoded = [None] + [None if before not in phases or after not in phases
                            or component_of[before] != component_of[after]
                            else inverse[(phases[after] - phases[before]) % 4]
                            for before, after in zip(sample_states, sample_states[1:])]
        wrong = [i for i, (got, want) in enumerate(
            zip(decoded[1:], case['expected_dibits'][1:]), 1)
                 if got is not None and got != want]
        unknown = [i for i, got in enumerate(decoded[1:], 1) if got is None]
        result.append(dict(selector=case['selector'], level=case.get('level'),
                           wrong_indices=wrong, unknown_indices=unknown,
                           cross_component_indices=[i for i, (before, after) in enumerate(
                               zip(sample_states, sample_states[1:]), 1)
                               if before in component_of and after in component_of
                               and component_of[before] != component_of[after]],
                           new_states=sorted(f'{value:02X}' for value in set(sample_states)
                                             if value not in phases)))
    return result


def run(out=HERE / 'results/joint-mask04-12a-seventh-phase-bit.json'):
    development = [case for path in DEVELOPMENT
                   for case in json.loads(path.read_text())['cases']]
    if len(development) != 18:
        raise ValueError('development case count changed')
    baseline = score(development, None)
    singles = [score(development, extra) for extra in UNUSED]
    full = score(development, 'full')
    survivors = []
    for row in singles:
        if row['minimum_conflicts']:
            continue
        extra = tuple(row['extra'])
        phases, _, components = solve(development, extra, tuple(row['best_convention']))
        holdouts = {path.stem: challenge(json.loads(path.read_text())['cases'],
                                        extra, phases, components,
                                        tuple(row['best_convention']))
                    for path in HOLDOUTS}
        survivors.append(dict(extra=extra, observed_states=row['observed_states'],
                              component_sizes=row['component_sizes'],
                              component_states=[[f'{value:02X}' for value in sorted(group)]
                                                for group in components],
                              convention=row['best_convention'],
                              state_phase=row['state_phase'], holdouts=holdouts))
    paths = (Path(__file__), HERE / 'joint_mask04_12a_sixth_receive_bit.py',
             *DEVELOPMENT, *HOLDOUTS)
    report = dict(experiment='seventh Y bit for static four-phase state compatibility',
                  fixture=dict(development_cases=18,
                               transitions=sum(len(c['expected_dibits']) - 1
                                               for c in development),
                               base='first Y5–Y7; second Y4,Y6,Y7',
                               capture_visits=[46, 93],
                               unused_bits=UNUSED,
                               conventions_tested=len(CONVENTIONS)),
                  baseline=baseline, single_bits=singles, full_bytes=full,
                  survivors=survivors,
                  limitations=[
                      'The offset-16/80 failures are now development cases, not held-out evidence for these seventh-bit candidates.',
                      'Disconnected phase components have independent arbitrary rotations; cross-component transitions are unvalidated.',
                      'The Y capture clocks and external phase-decision logic remain photo-compatible assumptions.',
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    print('baseline', baseline['minimum_conflicts'],
          'full', full['minimum_conflicts'], flush=True)
    for row in survivors:
        print(row['extra'], row['observed_states'], row['component_sizes'],
              [(name, [(c['selector'], len(c['wrong_indices']),
                        len(c['unknown_indices'])) for c in cases])
               for name, cases in row['holdouts'].items()], flush=True)
    return report


if __name__ == '__main__':
    run()
