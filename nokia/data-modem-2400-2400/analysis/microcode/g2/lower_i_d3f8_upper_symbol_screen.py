"""Test direct and differential symbol bits in an upper-sensitive ADC loop."""

import argparse
import hashlib
import json
import random
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from lower_i_d3f8_adc_cross_symbols import PATTERNS
from lower_i_d3f8_full_adc import (
    LONG_CYCLES, LONG_SAMPLES, LONG_VISITS, RANDOM_SEEDS,
    SAMPLE_START, hold, scenario_for_full_byte,
)
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from reference_modem import receive, transmit

VISITS_PER_SYMBOL = 1500
SYMBOL_INDEXES = tuple(range(2, 14))
LAGS = (-2, -1, 0, 1, 2)
CHANNELS = ('Y3F8', 'Y3F9', 'Y3FA', 'Q') + tuple(f'R{i}' for i in range(16))
TRAIN = (0, 1, 4)
PERIODIC_HOLDOUT = (2, 3, 5)
RANDOM_HOLDOUT = (6, 7, 8, 9)
OPERATIONS = ('direct', 'subtract')


def sequences():
    rows = [dict(kind='periodic', pattern=list(pattern),
                 middle=list(pattern) * 4) for pattern in PATTERNS]
    for seed in RANDOM_SEEDS:
        generator = random.Random(seed)
        rows.append(dict(kind='nonperiodic', seed=seed,
                         middle=[generator.randrange(4) for _ in range(16)]))
    return rows


def capture(mapping, base, middle):
    dibits = [0] * 8 + middle + [0] * 8
    pcm = transmit(dibits)
    if receive(pcm) != dibits[1:]:
        raise ValueError('reference stimulus did not recover its dibits')
    code = [127 - sample for sample in
            pcm[SAMPLE_START:SAMPLE_START + LONG_SAMPLES]]
    values = hold(code)
    if len(values) != LONG_VISITS:
        raise ValueError('held ADC stream length changed')
    scenario = scenario_for_full_byte(base, values, 'complementary')
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, LONG_CYCLES,
                         mode='integrated', out=temporary,
                         trace_limit=LONG_CYCLES)
        if (not result['clean'] or
                result['address_counts'].get(0x3F8, 0) != LONG_VISITS or
                result['read_sequence_visits'].get(0x3F8, 0) != LONG_VISITS):
            raise ValueError('upper-sensitive symbol trace did not sustain')
        ram = scenario['initial']['ram'][:]
        y8 = y9 = None
        rows = []
        for line in (Path(temporary) / 'trace.jsonl').open():
            record = json.loads(line)
            for address, value in record['registers'].items():
                ram[int(address)] = value
            pc = record['pc']
            if pc == 0x3F8:
                read = record['external_read']
                if (not read.get('selected_by_alu') or
                        read['value'] != values[len(rows)] or
                        record['instruction_i_high'] != 0xFD):
                    raise ValueError('upper D3F8 byte/instruction changed')
                y8 = record['alu']['y']
            elif pc == 0x3F9:
                y9 = record['alu']['y']
            elif pc == 0x3FA:
                if y8 is None or y9 is None:
                    raise ValueError('incomplete D3F8/3F9/3FA visit')
                rows.append(bytes((y8, y9, record['alu']['y'], record['q'], *ram)))
                y8 = y9 = None
        if len(rows) != LONG_VISITS:
            raise ValueError(('upper symbol visit count changed', len(rows)))
    return rows, result['trace_digest']


def error_count(rows, truth, indexes, operation, channel, bit, phase, lag,
                target_bit, inverted=False):
    errors = 0
    for index in indexes:
        visits = rows[index]
        expected = truth[(target_bit, lag, index)]
        for symbol, answer in zip(SYMBOL_INDEXES, expected):
            visit = symbol * VISITS_PER_SYMBOL + phase
            current = visits[visit][channel]
            value = (current if operation == 'direct' else
                     (current - visits[visit - VISITS_PER_SYMBOL][channel]) & 255)
            observed = ((value >> bit) & 1) ^ inverted
            errors += observed != answer
    return errors


def run(out=HERE / 'results/lower-i-d3f8-upper-symbol-screen.json'):
    mapping = mapping_with_upper_source(0, '17.6')
    _, base = fixture()
    stimuli = sequences()
    rows = []
    digests = []
    for stimulus in stimuli:
        visits, digest = capture(mapping, base, stimulus['middle'])
        rows.append(visits)
        digests.append(digest)
    if len(stimuli) != 10 or len(set(digests)) != 10:
        raise ValueError('upper symbol stimulus coverage changed')
    truth = {(target_bit, lag, index): tuple(
        (stimulus['middle'][symbol + lag] >> target_bit) & 1
        for symbol in SYMBOL_INDEXES)
        for target_bit in (0, 1) for lag in LAGS
        for index, stimulus in enumerate(stimuli)}
    checks_train = len(TRAIN) * len(SYMBOL_INDEXES)
    results = []
    for operation in OPERATIONS:
        for target_bit in (0, 1):
            minimum_training_errors = checks_train
            perfect_training_candidates = 0
            perfect_all_candidates = 0
            best = None
            for channel in range(len(CHANNELS)):
                for bit in range(8):
                    for lag in LAGS:
                        for phase in range(VISITS_PER_SYMBOL):
                            errors = error_count(rows, truth, TRAIN, operation,
                                                 channel, bit, phase, lag,
                                                 target_bit)
                            inverted = errors > checks_train // 2
                            train_errors = min(errors, checks_train - errors)
                            minimum_training_errors = min(
                                minimum_training_errors, train_errors)
                            if train_errors == 0:
                                perfect_training_candidates += 1
                            if train_errors > 4:
                                continue
                            periodic_errors = error_count(
                                rows, truth, PERIODIC_HOLDOUT, operation,
                                channel, bit, phase, lag, target_bit, inverted)
                            random_errors = error_count(
                                rows, truth, RANDOM_HOLDOUT, operation,
                                channel, bit, phase, lag, target_bit, inverted)
                            if train_errors == periodic_errors == random_errors == 0:
                                perfect_all_candidates += 1
                            candidate = dict(channel=CHANNELS[channel], bit=bit,
                                             phase_visit=phase, symbol_lag=lag,
                                             inverted=inverted,
                                             training_errors=train_errors,
                                             periodic_holdout_errors=periodic_errors,
                                             random_holdout_errors=random_errors)
                            if best is None or (
                                    train_errors + periodic_errors + random_errors,
                                    random_errors, periodic_errors) < (
                                        best['training_errors'] +
                                        best['periodic_holdout_errors'] +
                                        best['random_holdout_errors'],
                                        best['random_holdout_errors'],
                                        best['periodic_holdout_errors']):
                                best = candidate
            results.append(dict(operation=operation, dibit_bit=target_bit,
                                checks_per_training_set=checks_train,
                                checks_per_periodic_holdout_set=(
                                    len(PERIODIC_HOLDOUT) * len(SYMBOL_INDEXES)),
                                checks_per_random_holdout_set=(
                                    len(RANDOM_HOLDOUT) * len(SYMBOL_INDEXES)),
                                minimum_training_errors=minimum_training_errors,
                                perfect_training_candidates=perfect_training_candidates,
                                perfect_all_candidates=perfect_all_candidates,
                                best_low_training_error_candidate=best))
    paths = [Path(__file__), HERE / 'lower_i_d3f8_upper_d_route.py',
             HERE / 'lower_i_d3f8_full_adc.py',
             HERE / 'lower_i_d3f8_adc_cross_symbols.py',
             HERE / 'reference_modem.py', HERE / 'lower_i_prom_data_route.py',
             HERE / 'photo_controller_path.py', HERE / 'split_slice_probe.py',
             HERE.parent / 'assumed/execute.py', HERE.parent / 'model.py',
             HERE.parents[2] / 'am27s31dc-prom/nokia-modem-am27s31dc.bin']
    report = dict(status='upper-sensitive D3F8 symbol bit and subtraction screen',
                  fixture=dict(mapping='lower I7/A0=!10.6, I0/A1=11.2, I6=11.0; upper I0=17.6',
                               condition_select_0='inverted previous sign',
                               input='held complementary ADC code 127-PCM at D3F8',
                               sample_window=[SAMPLE_START,
                                              SAMPLE_START + LONG_SAMPLES],
                               visits_per_symbol=VISITS_PER_SYMBOL,
                               symbol_indexes=list(SYMBOL_INDEXES),
                               tested_lags=list(LAGS),
                               channels=list(CHANNELS),
                               training_indexes=list(TRAIN),
                               periodic_holdout_indexes=list(PERIODIC_HOLDOUT),
                               random_holdout_indexes=list(RANDOM_HOLDOUT)),
                  stimuli=stimuli, trace_digests=digests,
                  bit_results=results,
                  limitations=[
                      'The upper instruction source, ADC bus route/order, sample clock and condition mux are untraced.',
                      'Only direct bits and same-byte symbol-to-symbol subtraction bits at fixed visit phases are screened.',
                      'The training/holdout split limits fitting claims, but one state seed and one field mapping are used.',
                      'An internal bit fit would still need a physical or independently constrained USART-01 RxD route.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path,
                        default=HERE / 'results/lower-i-d3f8-upper-symbol-screen.json')
    args = parser.parse_args()
    report = run(args.out)
    print([(row['operation'], row['dibit_bit'],
            row['minimum_training_errors'], row['perfect_all_candidates'])
           for row in report['bit_results']])
