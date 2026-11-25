"""Screen every ADC-hold phase of the PROM-decoded 3FA Y latch stream."""

import hashlib
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from joint_upper_receive_bit_screen import HOLDOUT, TRAIN
from joint_upper_source_screen import SELECTED_MASK, candidate
from lower_i_d3f8_full_adc import LONG_SAMPLES, SAMPLE_START
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from lower_i_d3f8_upper_symbol_screen import LAGS, SYMBOL_INDEXES, sequences
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_four_row_sampled_state_dpsk import capture
from reference_modem import receive, transmit

CODINGS = ('offset_binary', 'twos_complement')
PHASES = tuple(range(47))
VALIDATION_SEEDS = (0x2421, 0x2401, 0x26A1, 0x33C3)


def positions(phase):
    indexes = []
    visit = 0
    for sample in range(LONG_SAMPLES):
        length = 47 if sample % 8 < 7 else 46
        indexes.append(visit + min(phase, length - 1))
        visit += length
    if visit != 6000:
        raise ValueError('ADC-hold phase schedule changed')
    return indexes


def signal(rows, phase, coding):
    raw = [rows[index][2] for index in positions(phase)]
    return ([value - 128 for value in raw] if coding == 'offset_binary' else
            [value if value < 128 else value - 256 for value in raw])


def errors(decisions, stimuli, indexes, lag):
    return sum(decisions[index][symbol - 1] != stimuli[index]['middle'][symbol + lag]
               for index in indexes for symbol in SYMBOL_INDEXES)


def run(out=HERE / 'results/receiver-prom-latch-sample-phase.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), SELECTED_MASK)
    _, base = fixture()
    stimuli = sequences()
    selected = sorted(set(TRAIN + HOLDOUT))
    streams, digests = {}, {}
    for index in selected:
        streams[index], digests[index] = capture(mapping, base,
                                                 stimuli[index]['middle'])
        print('captured stream', index, flush=True)
    if len(set(digests.values())) != len(selected):
        raise ValueError('latch-phase stimulus traces collapsed')
    tested = invalid = exact_training = exact_all = 0
    best = None
    for phase in PHASES:
        for coding in CODINGS:
            try:
                decisions = {index: receive(signal(streams[index], phase, coding))
                             for index in selected}
            except ValueError as err:
                if 'no carrier' not in str(err):
                    raise
                invalid += 1
                continue
            for lag in LAGS:
                tested += 1
                train = errors(decisions, stimuli, TRAIN, lag)
                holdout = errors(decisions, stimuli, HOLDOUT, lag)
                exact_training += train == 0
                exact_all += train == holdout == 0
                row = dict(phase_visit=phase, coding=coding, symbol_lag=lag,
                           training_errors=train, holdout_errors=holdout)
                if best is None or (train, holdout) < (
                        best['training_errors'], best['holdout_errors']):
                    best = row
    validation = []
    for seed in VALIDATION_SEEDS:
        generator = random.Random(seed)
        middle = [generator.randrange(4) for _ in range(16)]
        rows, digest = capture(mapping, base, middle)
        pcm = transmit([0] * 8 + middle + [0] * 8)[
            SAMPLE_START:SAMPLE_START + LONG_SAMPLES]
        try:
            decisions = receive(signal(rows, best['phase_visit'], best['coding']))
            count = sum(decisions[symbol - 1] != middle[symbol + best['symbol_lag']]
                        for symbol in SYMBOL_INDEXES)
        except ValueError as err:
            if 'no carrier' not in str(err):
                raise
            count = None
        validation.append(dict(seed=seed, errors=count,
                               reference_errors=sum(receive(pcm)[symbol - 1] !=
                                                    middle[symbol]
                                                    for symbol in SYMBOL_INDEXES),
                               trace_digest=digest))
        print('validated', seed, flush=True)
    paths = [Path(__file__), HERE / 'receiver_prom_row_latch_gate.py',
             HERE / 'receiver_four_row_sampled_state_dpsk.py',
             HERE / 'receiver_four_row_condition_screen.py',
             HERE / 'reference_modem.py', HERE.parent / 'assumed/execute.py',
             HERE.parent / 'model.py', MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(
        experiment='all ADC-hold phases of PROM-decoded 3FA Y latch stream',
        fixture=dict(mapping='joint upper-source mask 08',
                     dispatch='scenario [0,1,2,3]',
                     condition='inverted previous overflow at select 0',
                     adc='complementary reference PCM, 47/46 visits per sample',
                     latch='hypothetical 3FA→3ED NAND rising edge captures prior 3FA Y',
                     phases=PHASES, codings=CODINGS, lags=LAGS,
                     train_indexes=TRAIN, holdout_indexes=HOLDOUT,
                     symbol_indexes=SYMBOL_INDEXES),
        tested=tested, invalid=invalid, exact_training=exact_training,
        exact_training_and_holdout=exact_all, best=best,
        validation=validation, trace_digests=digests,
        limitations=[
            'The differential receiver is an external diagnostic, not executed DSC code.',
            'Only this Y byte, sample-rate divider phase, and fixed reference decoder are tested.',
            'NAND, latch, divider, ADC bus and USART RxD wiring remain hypotheses.'],
        source_sha256={str(path.relative_to(HERE.parents[2])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    print(result['tested'], result['exact_training'], result['best'],
          result['validation'])
