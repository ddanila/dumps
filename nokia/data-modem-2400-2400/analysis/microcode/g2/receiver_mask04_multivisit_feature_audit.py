"""Audit which two-visit 3F8 bits distinguish observed dibit transitions."""

import hashlib
import itertools
import json
from pathlib import Path

from receiver_mask04_multivisit_capture import HERE
from common import save

DEVELOPMENT = HERE / 'results/receiver-mask04-multivisit-capture.json'
GRID = HERE / 'results/receiver-mask04-three-bit-two-visit.json'
TRANSITION = HERE / 'results/receiver-mask04-four-bit-transition.json'


def state(first_y, second_y):
    return ((first_y >> 4) & 15) | (((second_y >> 4) & 15) << 4)


def observations():
    cases = []
    for case in json.loads(DEVELOPMENT.read_text())['cases']:
        xs = [state(symbol['visits']['47']['y3f8'],
                    symbol['visits']['94']['y3f8'])
              for symbol in case['symbols']]
        cases.append((xs, [s['dibit'] for s in case['symbols']]))
    for case in json.loads(GRID.read_text())['fresh_cases']:
        xs = [state(first, second) for first, second in
              zip(case['first_visit_y'], case['second_visit_y'])]
        cases.append((xs, case['expected_dibits']))
    return [(before, after, dibit)
            for xs, dibits in cases
            for before, after, dibit in zip(xs, xs[1:], dibits[1:])]


def transition_labels(rows, mask):
    labels = {}
    for before, after, dibit in rows:
        labels.setdefault((before & mask, after & mask), set()).add(dibit)
    return labels


def run(out=HERE / 'results/receiver-mask04-multivisit-feature-audit.json'):
    rows = observations()
    if len(rows) != 987:
        raise ValueError('development transition count changed')
    minimum = None
    for width in range(1, 9):
        candidates = []
        for selected in itertools.combinations(range(8), width):
            mask = sum(1 << bit for bit in selected)
            labels = transition_labels(rows, mask)
            if all(len(values) == 1 for values in labels.values()):
                candidates.append(dict(bits=[f'visit{47 if bit < 4 else 94}.Y{4 + bit % 4}'
                                             for bit in selected],
                                       transition_states=len(labels)))
        if candidates:
            minimum = dict(bits_per_symbol=width, candidates=candidates)
            break
    if (minimum is None or minimum['bits_per_symbol'] != 4 or
            len(minimum['candidates']) != 2):
        raise ValueError('minimum feature screen changed')
    three_mask = (1 << 2) | (1 << 3) | (1 << 7)
    three_labels = transition_labels(rows, three_mask)
    three_conflicts = {f'{before:02X}->{after:02X}': sorted(values)
                       for (before, after), values in three_labels.items()
                       if len(values) > 1}
    validation = json.loads(TRANSITION.read_text())
    if (len(three_conflicts) != 4 or
            validation['fresh_aggregate'] !=
            dict(checks=611, errors=0, unknown=5,
                 data_errors=0, data_unknown=5)):
        raise ValueError('validation summary changed')
    paths = [Path(__file__), DEVELOPMENT, GRID, TRANSITION]
    report = dict(experiment='two-visit receive transition feature audit',
                  observations=len(rows),
                  three_bit_rule=dict(bits=['visit47.Y6', 'visit47.Y7', 'visit94.Y7'],
                                      conflicting_transitions=three_conflicts),
                  minimum_conflict_free_feature=minimum,
                  frozen_four_bit_validation=validation['fresh_aggregate'],
                  interpretation='Four captured bits per symbol suffice to distinguish every observed dibit transition in 21 inspected traces, but the fitted 86-entry transition table leaves five unseen decisions on a new stream.',
                  limitations=['This is a collision screen on observed traces, not a proof that a four-bit Boolean circuit implements the modem receiver.',
                               'Feature minimization used all 21 inspected development traces; the frozen-table validation is the separate new-seed run.',
                               'Unseen transition keys remain unknown and no physical latch or USART route has been established.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
