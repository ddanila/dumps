"""Screen symbol-to-symbol XOR/subtraction state bits for reference dibits."""

import argparse
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from lower_i_d3f8_adc_cross_symbols import PATTERNS
from lower_i_d3f8_symbol_bit_screen import (
    CHANNELS, HOLDOUT, LAGS, SYMBOL_INDEXES, TRAIN,
    VISITS_PER_SYMBOL, capture,
)
from lower_i_prom_data_route import mapping_for
from photo_controller_path import fixture

OPERATIONS = ('xor', 'subtract')


def delta(current, previous, operation):
    return current ^ previous if operation == 'xor' else (current - previous) & 255


def run(out=HERE / 'results/lower-i-d3f8-symbol-delta-screen.json'):
    mapping = mapping_for('!10.6', '11.2')
    _, base = fixture()
    rows = []
    digests = []
    for pattern in PATTERNS:
        visits, digest = capture(mapping, base, pattern)
        rows.append(visits)
        digests.append(digest)
    if len(set(digests)) != len(digests):
        raise ValueError('pattern traces are not distinct')
    checks = len(TRAIN) * len(SYMBOL_INDEXES)
    results = []
    for operation in OPERATIONS:
        for target_bit in (0, 1):
            min_train = checks
            perfect_train = 0
            perfect_both = 0
            best = None
            for channel in range(len(CHANNELS)):
                for bit in range(8):
                    for lag in LAGS:
                        for phase in range(VISITS_PER_SYMBOL):
                            errors = 0
                            for pattern_index in TRAIN:
                                pattern = PATTERNS[pattern_index]
                                visits = rows[pattern_index]
                                for symbol in SYMBOL_INDEXES:
                                    current = visits[symbol * VISITS_PER_SYMBOL + phase][channel]
                                    previous = visits[(symbol - 1) * VISITS_PER_SYMBOL + phase][channel]
                                    observed = (delta(current, previous, operation) >> bit) & 1
                                    expected = (pattern[(symbol + lag) % 4] >> target_bit) & 1
                                    errors += observed != expected
                            inverted = errors > checks // 2
                            train_errors = min(errors, checks - errors)
                            min_train = min(min_train, train_errors)
                            if train_errors == 0:
                                perfect_train += 1
                            if train_errors > 4:
                                continue
                            holdout_errors = 0
                            for pattern_index in HOLDOUT:
                                pattern = PATTERNS[pattern_index]
                                visits = rows[pattern_index]
                                for symbol in SYMBOL_INDEXES:
                                    current = visits[symbol * VISITS_PER_SYMBOL + phase][channel]
                                    previous = visits[(symbol - 1) * VISITS_PER_SYMBOL + phase][channel]
                                    observed = ((delta(current, previous, operation) >> bit) & 1) ^ inverted
                                    expected = (pattern[(symbol + lag) % 4] >> target_bit) & 1
                                    holdout_errors += observed != expected
                            if train_errors == 0 and holdout_errors == 0:
                                perfect_both += 1
                            candidate = dict(channel=CHANNELS[channel], bit=bit,
                                             phase_visit=phase, symbol_lag=lag,
                                             inverted=inverted,
                                             training_errors=train_errors,
                                             holdout_errors=holdout_errors)
                            if best is None or (train_errors + holdout_errors,
                                                holdout_errors, train_errors) < (
                                                    best['training_errors'] + best['holdout_errors'],
                                                    best['holdout_errors'], best['training_errors']):
                                best = candidate
            results.append(dict(operation=operation, dibit_bit=target_bit,
                                checks_per_set=checks,
                                minimum_training_errors=min_train,
                                perfect_training_candidates=perfect_train,
                                perfect_train_and_holdout_candidates=perfect_both,
                                best_low_training_error_candidate=best))
    paths = [Path(__file__), HERE / 'lower_i_d3f8_symbol_bit_screen.py',
             HERE / 'lower_i_d3f8_sign_adc.py',
             HERE / 'lower_i_d3f8_adc_cross_symbols.py',
             HERE / 'lower_i_d3f8_adc_decoder_screen.py',
             HERE / 'lower_i_prom_data_route.py', HERE / 'photo_controller_path.py',
             HERE / 'split_slice_probe.py', HERE / 'reference_modem.py',
             HERE.parent / 'assumed/execute.py', HERE.parent / 'model.py',
             HERE.parents[2] / 'am27s31dc-prom/nokia-modem-am27s31dc.bin']
    report = dict(status='symbol-to-symbol XOR and subtraction bit screen of sustained D3F8 state',
                  fixture=dict(mapping='I7/A0=!10.6, I0/A1=11.2, lower I6=11.0',
                               condition_select_0='inverted previous sign',
                               input='complementary ADC bit0 to held D3F8 03/05',
                               patterns=[list(pattern) for pattern in PATTERNS],
                               sample_window=[64, 192],
                               visits_per_symbol=VISITS_PER_SYMBOL,
                               symbol_indexes=list(SYMBOL_INDEXES),
                               training_pattern_indexes=list(TRAIN),
                               holdout_pattern_indexes=list(HOLDOUT),
                               tested_symbol_lags=list(LAGS),
                               channels=list(CHANNELS),
                               delta='current symbol state versus previous symbol at same visit phase'),
                  trace_digests=digests,
                  delta_bit_results=results,
                  limitations=[
                      'The ADC decoder, condition source, clock and output route are assumed.',
                      'Only same-channel XOR/subtraction bits at one fixed phase per symbol are tested; a different coding, phase relation or output site could carry a decision.',
                      'Six periodic symbol streams and one Q/RAM seed are used; any candidate requires independent sequence validation.',
                      'An internal bit fit does not prove a physical USART-01 RxD decision.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path,
                        default=HERE / 'results/lower-i-d3f8-symbol-delta-screen.json')
    args = parser.parse_args()
    report = run(args.out)
    print([(row['operation'], row['dibit_bit'], row['minimum_training_errors'],
            row['perfect_train_and_holdout_candidates'])
           for row in report['delta_bit_results']])
