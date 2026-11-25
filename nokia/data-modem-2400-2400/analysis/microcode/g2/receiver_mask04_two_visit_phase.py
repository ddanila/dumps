"""Screen a second executed 3ED visit for 45-degree phase ambiguity."""

import hashlib
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from joint_upper_source_screen import candidate
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_mask04_carrier_phase_screen import capture_rotated
from receiver_mask04_rotated_codebook import expected_states
from receiver_mask04_rowpair_phase_code import row_pairs
from reference_modem import QUADRANT_TO_DIBIT

DEGREES = 45
SEEDS = (0x5A17, 0x76A5, 0x33C3, 0x7B23)
DELTAS = (-47, -46, -24, -8, -1, 0, 1, 8, 24, 46, 47, 48, 94)
PHASE = 47
VISITS_PER_SYMBOL = 375
SYMBOLS = range(2, 14)


def key(case, symbol, delta):
    base = case['windows'][symbol]
    return tuple(base['base'] + base[str(delta)])


def fit(case, delta):
    labels = defaultdict(set)
    for symbol, state in enumerate(case['expected_states']):
        labels[key(case, symbol, delta)].add(state)
    return labels


def score(labels, case, delta):
    states = []
    for symbol in range(16):
        values = labels.get(key(case, symbol, delta), set())
        states.append(next(iter(values)) if len(values) == 1 else None)
    errors = unknown = 0
    for symbol in SYMBOLS:
        a, b = states[symbol - 1:symbol + 1]
        if a is None or b is None:
            unknown += 1
        else:
            decoded = QUADRANT_TO_DIBIT[(b - a - 2) & 3]
            errors += decoded != case['middle'][symbol]
    return dict(errors=errors, unknown=unknown,
                known=len(SYMBOLS) - unknown, checks=len(SYMBOLS))


def run(out=HERE / 'results/receiver-mask04-two-visit-phase.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    cases = []
    for seed in SEEDS:
        generator = random.Random(seed)
        middle = [generator.randrange(4) for _ in range(16)]
        captured, trace = capture_rotated(mapping, base, middle, DEGREES)
        rows = row_pairs(captured)
        windows = []
        for symbol in range(16):
            start = symbol * VISITS_PER_SYMBOL + PHASE
            windows.append(dict(base=list(rows[start]),
                                **{str(delta): list(rows[start + delta])
                                   for delta in DELTAS}))
        cases.append(dict(seed=seed, middle=middle, windows=windows,
                          expected_states=expected_states(middle), **trace))
        print('captured', hex(seed), flush=True)
    prior = json.loads((HERE / 'results/receiver-mask04-rotated-codebook.json').read_text())
    for case in cases[:2]:
        old = next(item for item in prior['cases'] if
                   item['degrees'] == DEGREES and item['seed'] == case['seed'])
        if (case['trace_digest'] != old['trace_digest'] or
                [window['base'] for window in case['windows']] != old['pairs']):
            raise ValueError('two-visit trace differs from prior carrier fixture')
    screens = []
    for delta in DELTAS:
        labels = fit(cases[0], delta)
        all_labels = defaultdict(set)
        for case in cases:
            for symbol, state in enumerate(case['expected_states']):
                all_labels[key(case, symbol, delta)].add(state)
        screens.append(dict(delta=delta, training_states=len(labels),
            training_conflicts=sum(len(values) > 1 for values in labels.values()),
            all_case_states=len(all_labels),
            all_case_conflicts=sum(len(values) > 1 for values in all_labels.values()),
            training=score(labels, cases[0], delta),
            selection=score(labels, cases[1], delta),
            fresh=[score(labels, case, delta) for case in cases[2:]]))
    # This ranking uses only the training and selection streams. The two
    # fresh streams below never influence which offset is selected.
    selected = min(screens, key=lambda row: (row['training_conflicts'],
                   row['selection']['unknown'], row['selection']['errors'],
                   row['training_states'], abs(row['delta'])))['delta']
    paths = (Path(__file__), HERE / 'receiver_mask04_rotated_codebook.py',
             HERE / 'receiver_mask04_carrier_phase_screen.py',
             HERE / 'reference_modem.py', HERE.parent / 'assumed/execute.py',
             MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='second 3ED row-pair visit near phase 47 at 45-degree carrier rotation',
                  fixture=dict(degrees=DEGREES, seeds=SEEDS,
                               base_capture_visit=PHASE, deltas=DELTAS,
                               selection='fewest training conflicts, then selection unknowns/errors/states and absolute offset'),
                  selected_delta=selected, cases=cases, screens=screens,
                  limitations=['Reference phase labels and the lookup are external diagnostics.',
                               'Two visits need a separate storage and timing hypothesis; no such board route or USART RxD path is traced.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
