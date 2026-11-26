"""Screen executed Y and row bits at five visits for DPSK phase consistency."""

import hashlib
import itertools
import json
from collections import defaultdict, deque
from pathlib import Path

from joint_mask04_12a_sixth_receive_bit import state

HERE = Path(__file__).resolve().parent
INPUTS = (
    HERE / 'results/joint-mask04-12a-third-capture-baseline-32.json',
    HERE / 'results/joint-mask04-12a-third-capture-baseline-96.json',
    HERE / 'results/joint-mask04-12a-third-capture-16.json',
    HERE / 'results/joint-mask04-12a-third-capture-80.json',
    HERE / 'results/joint-mask04-12a-third-capture-low-gain.json',
)
PHASES = ('46', '47', '93', '94', '141')
SITES = ('row0', 'y3f8', 'row3')
CONVENTIONS = tuple(itertools.permutations(range(4)))
SELECTED = ('46', 'row0', 0)


def sample_state(symbol, extra=None):
    visits = symbol['visits']
    value = state(visits['46']['y3f8'], visits['93']['y3f8'],
                  (('second', 4), ('second', 6)))
    if extra is not None:
        phase, site, bit = extra
        value |= ((visits[phase][site] >> bit) & 1) << 6
    return value


def solve(cases, feature, convention):
    graph = defaultdict(list)
    for case in cases:
        values = [sample_state(symbol, feature)
                  for symbol in case['multi_visit_symbols']]
        for index, (before, after) in enumerate(zip(values, values[1:]), 1):
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


def score(cases, feature):
    results = [(convention, *solve(cases, feature, convention))
               for convention in CONVENTIONS]
    minimum = min(row[2] for row in results)
    convention, potentials, _, components = next(
        row for row in results if row[2] == minimum)
    return dict(feature=feature, minimum_conflicts=minimum,
                zero_conventions=[list(row[0]) for row in results
                                  if row[2] == 0],
                best_convention=list(convention),
                observed_states=len(potentials),
                component_sizes=sorted((len(group) for group in components),
                                       reverse=True))


def run(out=HERE / 'results/joint-mask04-12a-multivisit-phase-screen.json'):
    cases = [case for path in INPUTS
             for case in json.loads(path.read_text())['cases']]
    if len(cases) != 12 or any(len(c['multi_visit_symbols']) != 65 for c in cases):
        raise ValueError('multi-visit fixture count changed')
    baseline = score(cases, None)
    features = [(phase, site, bit)
                for phase in PHASES for site in SITES for bit in range(8)]
    screened = [score(cases, feature) for feature in features]
    selected = next(row for row in screened if tuple(row['feature']) == SELECTED)
    potentials, conflicts, components = solve(cases, SELECTED,
                                               tuple(selected['best_convention']))
    if conflicts or len(components) != 1:
        raise ValueError('selected row feature changed')
    symbols = [symbol for case in cases for symbol in case['multi_visit_symbols']]
    selected_bits = [((symbol['visits'][SELECTED[0]][SELECTED[1]] >> SELECTED[2]) & 1)
                     for symbol in symbols]
    comparisons = {}
    for name, phase, bit in (('first_y4', '46', 4),
                             ('second_y5', '93', 5)):
        other = [((symbol['visits'][phase]['y3f8'] >> bit) & 1)
                 for symbol in symbols]
        comparisons[name] = sum(a != b for a, b in zip(selected_bits, other))
    paths = (Path(__file__), HERE / 'joint_mask04_12a_sixth_receive_bit.py',
             *INPUTS)
    report = dict(experiment='five-visit Y/row bit screen for four-phase receive state',
                  fixture=dict(cases=len(cases), decisions=sum(
                      len(c['expected_dibits']) - 1 for c in cases),
                               symbols=len(symbols), captured_visits=PHASES,
                               sites=SITES, bits_per_site=8,
                               conventions_tested=len(CONVENTIONS)),
                  baseline=baseline, screened=screened,
                  zero_conflict_features=sum(row['minimum_conflicts'] == 0
                                             for row in screened),
                  selected=dict(**selected,
                                state_phase={f'{key:02X}': value
                                             for key, value in sorted(potentials.items())},
                                component_states=[[f'{value:02X}' for value
                                                   in sorted(group)]
                                                  for group in components],
                                bit_differences=comparisons),
                  limitations=[
                      'The 12 captured cases are development evidence; selecting a bit on them requires an untouched holdout.',
                      'The row-0 bit is an executed ALU Y at 3ED, not a proven latched board output.',
                      'A zero-conflict phase graph does not identify the physical ADC or USART route.',
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    print('baseline', baseline['minimum_conflicts'],
          'zero features', report['zero_conflict_features'],
          'selected', selected,
          'visit 141 best', min(row['minimum_conflicts'] for row in screened
                                if row['feature'][0] == '141'), flush=True)
    return report


if __name__ == '__main__':
    run()
