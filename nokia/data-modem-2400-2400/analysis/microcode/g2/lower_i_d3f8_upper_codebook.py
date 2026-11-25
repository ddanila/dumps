"""Search small fixed-phase four-way codes in the upper-sensitive ADC loop."""

import hashlib
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from lower_i_d3f8_upper_symbol_screen import (
    CHANNELS, SYMBOL_INDEXES, VISITS_PER_SYMBOL, capture, sequences,
)
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture

TRAIN = (0, 1, 4, 6)
HOLDOUT = (2, 3, 5, 7, 8, 9)
LAGS = (-2, -1, 0, 1, 2)
OPERATIONS = ('direct', 'xor_previous', 'subtract_previous')
MAX_CODES = (4, 8, 16)


def code(rows, symbol, phase, channel, operation):
    visit = symbol * VISITS_PER_SYMBOL + phase
    current = rows[visit][channel]
    if operation == 'direct':
        return current
    previous = rows[visit - VISITS_PER_SYMBOL][channel]
    return current ^ previous if operation == 'xor_previous' else (current - previous) & 255


def score(codes, stimuli, lag, limit):
    counts = defaultdict(Counter)
    for index in TRAIN:
        for symbol, value in zip(SYMBOL_INDEXES, codes[index]):
            counts[value][stimuli[index]['middle'][symbol + lag]] += 1
    if len(counts) > limit:
        return None
    lookup = {value: min((-count, label) for label, count in labels.items())[1]
              for value, labels in counts.items()}
    train_errors = sum(
        lookup[value] != stimuli[index]['middle'][symbol + lag]
        for index in TRAIN for symbol, value in zip(SYMBOL_INDEXES, codes[index]))
    known_errors = unknown = 0
    for index in HOLDOUT:
        for symbol, value in zip(SYMBOL_INDEXES, codes[index]):
            if value not in lookup:
                unknown += 1
            else:
                known_errors += lookup[value] != stimuli[index]['middle'][symbol + lag]
    return dict(train_errors=train_errors, holdout_errors=known_errors + unknown,
                holdout_unknown=unknown, holdout_known_errors=known_errors,
                code_values=len(lookup),
                lookup={f'{value:02X}': label for value, label in sorted(lookup.items())})


def run(out=HERE / 'results/lower-i-d3f8-upper-codebook.json'):
    _, base = fixture()
    mapping = mapping_with_upper_source(0, '17.6')
    stimuli = sequences()
    rows, digests = [], []
    for stimulus in stimuli:
        captured, digest = capture(mapping, base, stimulus['middle'])
        rows.append(captured)
        digests.append(digest)
    if len(rows) != 10 or len(set(digests)) != 10:
        raise ValueError('independent waveform set changed')

    results = []
    for operation in OPERATIONS:
        best = {limit: None for limit in MAX_CODES}
        tested = {limit: 0 for limit in MAX_CODES}
        exact_train = {limit: 0 for limit in MAX_CODES}
        exact_all = {limit: 0 for limit in MAX_CODES}
        for channel in range(len(CHANNELS)):
            for phase in range(VISITS_PER_SYMBOL):
                codes = [[code(stream, symbol, phase, channel, operation)
                          for symbol in SYMBOL_INDEXES] for stream in rows]
                for lag in LAGS:
                    for limit in MAX_CODES:
                        result = score(codes, stimuli, lag, limit)
                        if result is None:
                            continue
                        tested[limit] += 1
                        exact_train[limit] += result['train_errors'] == 0
                        exact_all[limit] += (result['train_errors'] == 0 and
                                             result['holdout_errors'] == 0)
                        candidate = dict(channel=CHANNELS[channel], phase_visit=phase,
                                         symbol_lag=lag, **result)
                        previous = best[limit]
                        rank = lambda item: (item['train_errors'] + item['holdout_errors'],
                                             item['holdout_errors'], item['holdout_unknown'],
                                             item['code_values'], item['phase_visit'])
                        if previous is None or rank(candidate) < rank(previous):
                            best[limit] = candidate
        results.append(dict(operation=operation,
                            limits=[dict(max_code_values=limit,
                                         candidates_tested=tested[limit],
                                         exact_training=exact_train[limit],
                                         exact_train_and_holdout=exact_all[limit],
                                         best=best[limit]) for limit in MAX_CODES]))

    paths = [Path(__file__),
             HERE / 'lower_i_d3f8_upper_symbol_screen.py',
             HERE / 'lower_i_d3f8_upper_d_route.py',
             HERE / 'lower_i_d3f8_full_adc.py',
             HERE / 'reference_modem.py',
             HERE / 'photo_controller_path.py',
             HERE.parent / 'assumed/execute.py',
             HERE.parents[2] / 'am27s31dc-prom/nokia-modem-am27s31dc.bin']
    report = dict(status='small-codebook receiver decision search in upper-sensitive D3F8 fixture',
                  fixture=dict(mapping=mapping['name'],
                               condition_select_0='inverted previous sign',
                               adc='127 minus reference PCM held at D3F8',
                               symbol_indexes=list(SYMBOL_INDEXES),
                               phases_per_symbol=VISITS_PER_SYMBOL,
                               lags=list(LAGS), channels=list(CHANNELS),
                               operations=list(OPERATIONS),
                               training=list(TRAIN), holdout=list(HOLDOUT),
                               holdout_unknown_counts_as_error=True),
                  stimuli=stimuli, trace_digests=digests, results=results,
                  limitations=['A codebook is trained from controller-independent reference waveforms; fitting a code does not identify hardware decoder logic.',
                               'Only one state byte at one fixed visit phase, optionally compared with the preceding symbol, is tested.',
                               'The ADC ingress, instruction field, condition mux, sample rate and USART-01 RxD route are untraced.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    for row in result['results']:
        print(row['operation'], [(entry['max_code_values'],
                                  entry['candidates_tested'],
                                  None if entry['best'] is None else
                                  (entry['best']['train_errors'],
                                   entry['best']['holdout_errors']))
                                 for entry in row['limits']])
