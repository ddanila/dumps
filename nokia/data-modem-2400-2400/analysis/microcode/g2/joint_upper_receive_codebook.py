"""Screen compact fixed-phase dibit codes on the joint TX/ADC field map."""

import hashlib
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from joint_upper_receive_bit_screen import (
    HOLDOUT, TRAIN, capture,
)
from joint_upper_source_screen import SELECTED_MASK, candidate
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from lower_i_d3f8_upper_symbol_screen import (
    CHANNELS, LAGS, SYMBOL_INDEXES, VISITS_PER_SYMBOL, sequences,
)
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

OPERATIONS = ('direct', 'xor_previous', 'subtract_previous')
MAX_CODES = (4, 8, 16)


def code(rows, symbol, phase, channel, operation):
    visit = symbol * VISITS_PER_SYMBOL + phase
    current = rows[visit][channel]
    if operation == 'direct':
        return current
    previous = rows[visit - VISITS_PER_SYMBOL][channel]
    return current ^ previous if operation == 'xor_previous' else (current - previous) & 255


def evaluate(codes, stimuli, lag):
    counts = defaultdict(Counter)
    for index in TRAIN:
        for symbol, value in zip(SYMBOL_INDEXES, codes[index]):
            counts[value][stimuli[index]['middle'][symbol + lag]] += 1
    if len(counts) > max(MAX_CODES):
        return None
    lookup = {value: min((-count, label) for label, count in labels.items())[1]
              for value, labels in counts.items()}
    train_errors = sum(
        lookup[value] != stimuli[index]['middle'][symbol + lag]
        for index in TRAIN for symbol, value in zip(SYMBOL_INDEXES, codes[index]))
    holdout_known_errors = holdout_unknown = 0
    if train_errors <= 4:
        for index in HOLDOUT:
            for symbol, value in zip(SYMBOL_INDEXES, codes[index]):
                if value not in lookup:
                    holdout_unknown += 1
                else:
                    holdout_known_errors += lookup[value] != stimuli[index]['middle'][symbol + lag]
    return dict(code_values=len(lookup), train_errors=train_errors,
                holdout_errors=(holdout_known_errors + holdout_unknown
                                if train_errors <= 4 else None),
                holdout_unknown=holdout_unknown if train_errors <= 4 else None,
                lookup={f'{value:02X}': label for value, label in sorted(lookup.items())})


def run(out=HERE / 'results/joint-upper-receive-codebook.json'):
    receiver = mapping_with_upper_source(0, '17.6')
    transmitter = mapped(MAPPINGS['q3'])
    mapping = candidate(receiver, transmitter, SELECTED_MASK)
    _, base = fixture()
    stimuli = sequences()
    selected = sorted(set(TRAIN + HOLDOUT))
    streams, digests = {}, {}
    for index in selected:
        streams[index], digests[index] = capture(
            mapping, base, stimuli[index]['middle'])
    if len(set(digests.values())) != len(selected):
        raise ValueError('codebook ADC stimulus digests collapsed')

    results = []
    for operation in OPERATIONS:
        best = {limit: None for limit in MAX_CODES}
        tested = {limit: 0 for limit in MAX_CODES}
        exact_train = {limit: 0 for limit in MAX_CODES}
        exact_all = {limit: 0 for limit in MAX_CODES}
        for channel in range(len(CHANNELS)):
            for phase in range(VISITS_PER_SYMBOL):
                codes = {index: [code(streams[index], symbol, phase,
                                      channel, operation)
                                 for symbol in SYMBOL_INDEXES]
                         for index in selected}
                for lag in LAGS:
                    result = evaluate(codes, stimuli, lag)
                    if result is None:
                        continue
                    for limit in MAX_CODES:
                        if result['code_values'] > limit:
                            continue
                        tested[limit] += 1
                        exact_train[limit] += result['train_errors'] == 0
                        exact_all[limit] += (result['train_errors'] == 0 and
                                             result['holdout_errors'] == 0)
                        if result['holdout_errors'] is None:
                            continue
                        row = dict(channel=CHANNELS[channel],
                                   phase_visit=phase, symbol_lag=lag, **result)
                        old = best[limit]
                        rank = lambda x: (x['train_errors'] + x['holdout_errors'],
                                          x['holdout_errors'], x['holdout_unknown'],
                                          x['code_values'], x['phase_visit'])
                        if old is None or rank(row) < rank(old):
                            best[limit] = row
        results.append(dict(operation=operation,
                            limits=[dict(max_code_values=limit,
                                         candidates_tested=tested[limit],
                                         exact_training=exact_train[limit],
                                         exact_train_and_holdout=exact_all[limit],
                                         best_low_training_error_candidate=best[limit])
                                    for limit in MAX_CODES]))

    paths = [Path(__file__), HERE / 'joint_upper_receive_bit_screen.py',
             HERE / 'joint_upper_source_screen.py',
             HERE / 'lower_i_d3f8_upper_symbol_screen.py',
             HERE / 'photo_controller_path.py',
             HERE / 'split_slice_probe.py',
             HERE.parent / 'assumed/execute.py', HERE.parent / 'model.py',
             MAPPINGS['q3'],
             HERE / 'results/joint-upper-source-mask08-mapping.json',
             HERE.parents[2] / 'am27s31dc-prom/nokia-modem-am27s31dc.bin',
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(status='small fixed-phase receive codebook screen under joint TX/ADC map',
                  fixture=dict(mapping='joint upper-source mask 08',
                               adc='127 minus reference PCM held at D3F8',
                               channels=list(CHANNELS),
                               symbol_indexes=list(SYMBOL_INDEXES),
                               visits_per_symbol=VISITS_PER_SYMBOL,
                               lags=list(LAGS), operations=list(OPERATIONS),
                               max_code_values=list(MAX_CODES),
                               train_indexes=list(TRAIN),
                               holdout_indexes=list(HOLDOUT),
                               unknown_holdout_code_counts_as_error=True),
                  stimuli=[dict(index=index, **stimuli[index], trace_digest=digests[index])
                           for index in selected],
                  results=results,
                  limitations=[
                      'Only one state byte at a fixed symbol phase, optionally compared with the preceding symbol, is tested.',
                      'A fitted lookup is a diagnostic classification, not traced DSC decoder logic or a USART RxD route.',
                      'ADC ingress, sample clock, upper instruction and condition mux remain untraced.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    print([(row['operation'],
            [(item['max_code_values'], item['exact_training'],
              None if item['best_low_training_error_candidate'] is None else
              (item['best_low_training_error_candidate']['train_errors'],
               item['best_low_training_error_candidate']['holdout_errors']))
             for item in row['limits']]) for row in report['results']])
