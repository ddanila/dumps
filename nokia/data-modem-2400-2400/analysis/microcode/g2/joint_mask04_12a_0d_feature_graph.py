"""Test early receive bits against old and new real-PROM phase constraints."""

import hashlib
import json
from collections import defaultdict, deque
from pathlib import Path

from joint_mask04_12a_multivisit_phase_screen import SELECTED, sample_state

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
MODEL = RESULTS / 'joint-mask04-12a-mode-phase-twelve.json'
INPUTS = (
    RESULTS / 'joint-mask04-12a-lowgain133-expanded-visits.json',
    RESULTS / 'joint-mask04-12a-mode1-expanded-1.15.json',
    RESULTS / 'joint-mask04-12a-mode1-expanded-1.25.json',
    RESULTS / 'joint-mask04-12a-visit94-phase-holdout-133.json',
    RESULTS / 'joint-mask04-12a-visit94-phase-holdout-135.json',
    RESULTS / 'joint-mask04-12a-visit94-gain07-challenge-0.7.json',
    RESULTS / 'joint-mask04-12a-visit94-gain07-challenge-0.8.json',
    RESULTS / 'joint-mask04-12a-visit94-mode81-control-expanded.json',
    RESULTS / 'joint-mask04-12a-visit94-old0d-replay.json',
)
FEATURES = {
    'seven_bit': (),
    'first_y4': (('46', 'y3f8', 4),),
    'row0_bit1': (('46', 'row0', 1),),
    'later_y6': (('94', 'y3f8', 6),),
    'first_y4_plus_row0_bit1': (('46', 'y3f8', 4), ('46', 'row0', 1)),
}
OUT = RESULTS / 'joint-mask04-12a-0d-feature-graph.json'


def code(symbol, features):
    value = sample_state(symbol, SELECTED)
    for index, (visit, site, bit) in enumerate(features):
        value |= ((symbol['visits'][visit][site] >> bit) & 1) << (7 + index)
    return value


def solve(cases, features, steps):
    edges = defaultdict(list)
    nodes = set()
    for case in cases:
        states = [code(symbol, features)
                  for symbol in case['multi_visit_symbols']]
        nodes.update(states)
        for index in range(1, len(states)):
            step = steps[case['expected_dibits'][index]]
            edges[states[index - 1]].append((states[index], step))
            edges[states[index]].append((states[index - 1], -step))
    labels = {}
    conflicts = 0
    components = []
    for seed in sorted(nodes):
        if seed in labels:
            continue
        labels[seed] = 0
        queue = deque([seed])
        size = 0
        while queue:
            state = queue.popleft()
            size += 1
            for neighbor, step in edges[state]:
                phase = (labels[state] + step) & 3
                if neighbor in labels:
                    conflicts += labels[neighbor] != phase
                else:
                    labels[neighbor] = phase
                    queue.append(neighbor)
        components.append(size)
    return dict(state_codes=len(nodes), components=sorted(components, reverse=True),
                directed_conflicts=conflicts,
                relative_phase={f'{state:03X}': phase
                                for state, phase in sorted(labels.items())})


def run(out=OUT):
    steps = json.loads(MODEL.read_text())['fixture']['phase_convention']
    cases = [case for path in INPUTS
             for case in json.loads(path.read_text())['cases']]
    if len(cases) != 18 or any(len(case['multi_visit_symbols']) != 65
                                for case in cases):
        raise ValueError('expanded case coverage changed')
    row0_bit1_shift = sum(
        bool((symbol['visits']['46']['row0'] ^
              symbol['visits']['47']['row0']) & 2)
        for case in cases for symbol in case['multi_visit_symbols'])
    if row0_bit1_shift:
        raise ValueError(('row-0 bit 1 shifts across candidate U12 clock',
                          row0_bit1_shift))
    results = {name: solve(cases, features, steps)
               for name, features in FEATURES.items()}
    expected = {'seven_bit': (21, 116), 'first_y4': (24, 0),
                'row0_bit1': (24, 0), 'later_y6': (26, 16),
                'first_y4_plus_row0_bit1': (24, 0)}
    if ({name: (row['state_codes'], row['directed_conflicts'])
         for name, row in results.items()} != expected or
            any(row['components'] != [row['state_codes']]
                for row in results.values())):
        raise ValueError('early-feature phase graph changed')
    paths = (Path(__file__), MODEL, *INPUTS,
             HERE / 'joint_mask04_12a_multivisit_phase_screen.py')
    report = dict(experiment='18-stream early-bit receive phase graph screen',
                  fixture=dict(streams=len(cases), symbols=65 * len(cases),
                               decisions=64 * len(cases),
                               phase_convention=steps,
                               row0_bit1_46_to_47_mismatches=row0_bit1_shift,
                               features={name: [dict(visit=visit, site=site,
                                                     bit=bit)
                                                for visit, site, bit in features]
                                         for name, features in FEATURES.items()}),
                  results=results,
                  limitations=[
                      'The feature screen uses all 18 cases to select a bit; zero conflicts are development evidence, not a fresh holdout.',
                      'The graph labels are relative phases inferred from offered dibits under assumed line and ADC routes.',
                      'A graph fit does not prove a Boolean gate implementation, package wiring, serial route or analog demodulator.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    report = run()
    print({name: (row['state_codes'], row['directed_conflicts'])
           for name, row in report['results'].items()})
