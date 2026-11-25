"""Test a small sampled-state DPSK readout on the conditional 0/2 path."""

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
from lower_i_d3f8_upper_symbol_screen import CHANNELS, LAGS, SYMBOL_INDEXES, sequences
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_two_row_decision_screen import capture
from reference_modem import receive, transmit

SITES = ('start', 'center', 'end')
PHASE_OFFSETS = (-2, -1, 0, 1, 2)
STATE_CHANNELS = ('Y3F8', 'Y3F9', 'Y3FA', 'Q', 'R10', 'R11', 'R12', 'R13')
CODINGS = ('offset_binary', 'twos_complement')
VALIDATION_SEEDS = (0x2421, 0x2401, 0x26A1, 0x33C3)


def positions(site, offset):
    indexes = []
    visit = 0
    for sample in range(LONG_SAMPLES):
        length = 94 if sample % 4 < 3 else 93
        origin = {'start': visit + 2,
                  'center': visit + length // 2,
                  'end': visit + length - 3}[site]
        indexes.append(origin + offset)
        visit += length
    if visit != 12000 or not all(0 <= n < visit for n in indexes):
        raise ValueError('two-row sample hold schedule changed')
    return indexes


def signal(rows, channel, indexes, coding):
    raw = [rows[visit][CHANNELS.index(channel)] for visit in indexes]
    return ([value - 128 for value in raw] if coding == 'offset_binary' else
            [value if value < 128 else value - 256 for value in raw])


def errors(decisions, stimuli, indexes, lag):
    return sum(decisions[index][symbol - 1] != stimuli[index]['middle'][symbol + lag]
               for index in indexes for symbol in SYMBOL_INDEXES)


def run(out=HERE / 'results/receiver-two-row-sampled-state-dpsk.json'):
    receiver = mapping_with_upper_source(0, '17.6')
    transmitter = mapped(MAPPINGS['q3'])
    mapping = candidate(receiver, transmitter, SELECTED_MASK)
    _, base = fixture()
    stimuli = sequences()
    selected = sorted(set(TRAIN + HOLDOUT))
    streams, digests = {}, {}
    for index in selected:
        streams[index], digests[index] = capture(mapping, base, stimuli[index]['middle'])
        print(f'captured {index}', flush=True)
    if len(set(digests.values())) != len(selected):
        raise ValueError('stimulus traces collapsed')

    reference_errors = {}
    for index in selected:
        dibits = [0] * 8 + stimuli[index]['middle'] + [0] * 8
        pcm = transmit(dibits)[SAMPLE_START:SAMPLE_START + LONG_SAMPLES]
        reference_errors[index] = errors({index: receive(pcm)}, stimuli, [index], 0)
    if any(reference_errors.values()):
        raise ValueError('reference window failed its own stimulus')

    tested = invalid = exact_training = exact_all = 0
    best = None
    for site in SITES:
        for phase in PHASE_OFFSETS:
            indexes = positions(site, phase)
            for channel in STATE_CHANNELS:
                for coding in CODINGS:
                    try:
                        decisions = {index: receive(signal(streams[index], channel,
                                                           indexes, coding))
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
                        row = dict(site=site, phase_offset=phase, channel=channel,
                                   coding=coding, symbol_lag=lag,
                                   training_errors=train, holdout_errors=holdout)
                        if best is None or (train, holdout) < (
                                best['training_errors'], best['holdout_errors']):
                            best = row
    validation = []
    indexes = positions(best['site'], best['phase_offset'])
    for seed in VALIDATION_SEEDS:
        generator = random.Random(seed)
        middle = [generator.randrange(4) for _ in range(16)]
        rows, digest = capture(mapping, base, middle)
        pcm = transmit([0] * 8 + middle + [0] * 8)[
            SAMPLE_START:SAMPLE_START + LONG_SAMPLES]
        try:
            decisions = receive(signal(rows, best['channel'], indexes, best['coding']))
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
        print(f'validated {seed}', flush=True)
    sources = ('receiver_two_row_sampled_state_dpsk.py',
               'receiver_two_row_decision_screen.py', 'reference_modem.py')
    report = dict(experiment='conditional 0/2 sampled-state external DPSK diagnostic',
                  source_sha256={name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
                                 for name in sources},
                  train_indices=TRAIN, holdout_indices=HOLDOUT,
                  symbol_indices=SYMBOL_INDEXES, tested=tested, invalid=invalid,
                  exact_training=exact_training, exact_all=exact_all,
                  reference_errors=reference_errors, best=best, validation=validation,
                  trace_digests=digests)
    save(out, report)
    return report


if __name__ == '__main__':
    print(run()['best'])
