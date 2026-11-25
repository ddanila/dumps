"""Test whether retained mask-04 register pairs encode DPSK quadrature."""

import hashlib
import math
import random
import sys
from itertools import combinations, product
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from joint_upper_receive_bit_screen import HOLDOUT, TRAIN
from joint_upper_source_screen import candidate
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from lower_i_d3f8_upper_symbol_screen import LAGS, SYMBOL_INDEXES, sequences
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_mask04_retained_bit_screen import capture, CHANNELS, VISITS_PER_SYMBOL
from reference_modem import QUADRANT_TO_DIBIT

CODINGS = ('offset_binary', 'twos_complement')
PAIRS = tuple(combinations(range(len(CHANNELS)), 2))
VALIDATION_SEEDS = (0x2421, 0x2401, 0x26A1, 0x33C3)


def value(byte, coding):
    return byte - 128 if coding == 'offset_binary' else (
        byte if byte < 128 else byte - 256)


def decision(rows, symbol, phase, pair, codings, conjugate, halfturn):
    def sample(index):
        row = rows[index * VISITS_PER_SYMBOL + phase]
        i = value(row[pair[0]], codings[0])
        q = value(row[pair[1]], codings[1])
        return complex(i, -q if conjugate else q)
    previous = sample(symbol - 1)
    current = sample(symbol)
    delta = current * previous.conjugate()
    if halfturn:
        delta = -delta
    if abs(delta) < 1e-12:
        return None
    quadrant = round(math.atan2(delta.imag, delta.real) / (math.pi / 2)) % 4
    return QUADRANT_TO_DIBIT[quadrant]


def errors(streams, stimuli, indexes, pair, codings, conjugate,
           halfturn, phase, lag):
    count = 0
    invalid = 0
    for index in indexes:
        rows = streams[index]
        middle = stimuli[index]['middle']
        for symbol in SYMBOL_INDEXES:
            observed = decision(rows, symbol, phase, pair, codings,
                                conjugate, halfturn)
            invalid += observed is None
            count += observed != middle[symbol + lag]
    return count, invalid


def run(out=HERE / 'results/receiver-mask04-quadrature-decision.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    stimuli = sequences()
    selected = sorted(set(TRAIN + HOLDOUT))
    streams, digests = {}, {}
    for index in selected:
        streams[index], digests[index] = capture(mapping, base,
                                                 stimuli[index]['middle'])
        print('captured stream', index, flush=True)
    if len(set(digests.values())) != len(selected):
        raise ValueError('quadrature stimulus traces collapsed')
    tested = exact_training = exact_all = 0
    best = None
    for pair in PAIRS:
        for codings in product(CODINGS, repeat=2):
            for conjugate in (False, True):
                for halfturn in (False, True):
                    for phase in range(VISITS_PER_SYMBOL):
                        for lag in LAGS:
                            train, invalid_train = errors(
                                streams, stimuli, TRAIN, pair, codings,
                                conjugate, halfturn, phase, lag)
                            holdout, invalid_holdout = errors(
                                streams, stimuli, HOLDOUT, pair, codings,
                                conjugate, halfturn, phase, lag)
                            tested += 1
                            exact_training += train == 0 and invalid_train == 0
                            exact_all += (train == holdout == 0 and
                                          invalid_train == invalid_holdout == 0)
                            row = dict(channels=[CHANNELS[pair[0]], CHANNELS[pair[1]]],
                                       codings=codings, conjugate=conjugate,
                                       carrier_halfturn=halfturn,
                                       phase_visit=phase, symbol_lag=lag,
                                       training_errors=train, holdout_errors=holdout,
                                       invalid_training=invalid_train,
                                       invalid_holdout=invalid_holdout)
                            if best is None or (train, invalid_train) < (
                                    best['training_errors'], best['invalid_training']):
                                best = row
    validation = []
    pair = tuple(CHANNELS.index(name) for name in best['channels'])
    for seed in VALIDATION_SEEDS:
        generator = random.Random(seed)
        middle = [generator.randrange(4) for _ in range(16)]
        rows, digest = capture(mapping, base, middle)
        count, invalid = errors({0: rows}, {0: dict(middle=middle)}, [0],
                                pair, best['codings'], best['conjugate'],
                                best['carrier_halfturn'], best['phase_visit'],
                                best['symbol_lag'])
        validation.append(dict(seed=seed, errors=count, invalid=invalid,
                               checks=len(SYMBOL_INDEXES), trace_digest=digest))
        print('validated seed', seed, flush=True)
    paths = [Path(__file__), HERE / 'receiver_mask04_retained_bit_screen.py',
             HERE / 'joint_four_row_retention_tx.py',
             HERE / 'reference_modem.py', HERE.parent / 'assumed/execute.py',
             HERE.parent / 'model.py', MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(
        experiment='fixed symbol-phase quadrature decision from mask-04 retained bytes',
        fixture=dict(mapping='joint upper-source mask 04',
                     dispatch='scenario [0,1,2,3]',
                     condition='inverted previous overflow at select 0',
                     adc='complementary reference PCM, 47/46 visits per sample',
                     channels=CHANNELS, pairs=[[CHANNELS[i], CHANNELS[j]]
                                              for i, j in PAIRS],
                     codings=CODINGS, conjugate='both',
                     carrier_halfturn='both',
                     visits_per_symbol=VISITS_PER_SYMBOL,
                     symbol_indexes=SYMBOL_INDEXES, lags=LAGS,
                     train_indexes=TRAIN, holdout_indexes=HOLDOUT),
        tested=tested, exact_training=exact_training,
        exact_training_and_holdout=exact_all, best=best,
        validation=validation, trace_digests=digests,
        limitations=[
            'The I/Q interpretation and differential decision are external diagnostics, not DSC-executed code.',
            'Only two raw retained bytes at a fixed symbol phase are tested; no filter or adaptive phase recovery is modeled.',
            'ADC, register-latch, sample clock, TEST and USART RxD routes remain hypotheses.'],
        source_sha256={str(path.relative_to(HERE.parents[2])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    print(result['tested'], result['exact_training'], result['best'],
          result['validation'])
