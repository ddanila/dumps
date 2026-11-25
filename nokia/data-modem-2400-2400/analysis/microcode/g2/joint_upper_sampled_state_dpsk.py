"""Try a small five-phase sampled-state DPSK readout on the joint map."""

import hashlib
import math
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from joint_upper_receive_bit_screen import HOLDOUT, TRAIN, capture
from joint_upper_source_screen import SELECTED_MASK, candidate
from lower_i_d3f8_full_adc import LONG_SAMPLES, SAMPLE_START
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from lower_i_d3f8_upper_symbol_screen import (
    CHANNELS, LAGS, SYMBOL_INDEXES, sequences,
)
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from reference_modem import receive, transmit

SITES = ('start', 'center', 'end')
PHASE_OFFSETS = (-2, -1, 0, 1, 2)
STATE_CHANNELS = ('Y3F8', 'Y3F9', 'Y3FA', 'Q', 'R10', 'R11', 'R12', 'R13')
CODINGS = ('offset_binary', 'twos_complement')
VALIDATION_SEEDS = (0x2421, 0x2401, 0x26A1, 0x33C3)


def positions(site, offset):
    starts = []
    next_visit = 0
    for index in range(LONG_SAMPLES):
        length = 188 if index % 2 == 0 else 187
        starts.append(next_visit)
        next_visit += length
    if next_visit != 24000:
        raise ValueError('ADC hold schedule changed')
    indexes = []
    for sample, start in enumerate(starts):
        length = 188 if sample % 2 == 0 else 187
        origin = {'start': start + 2,
                  'center': start + length // 2,
                  'end': start + length - 3}[site]
        indexes.append(origin + offset)
    if any(index < 0 or index >= 24000 for index in indexes):
        raise ValueError('sample phase outside ADC hold')
    return indexes


def signal(rows, channel, indexes, coding):
    raw = [rows[visit][CHANNELS.index(channel)] for visit in indexes]
    return ([value - 128 for value in raw] if coding == 'offset_binary' else
            [value if value < 128 else value - 256 for value in raw])


def errors(decisions, stimuli, indexes, lag):
    return sum(decisions[index][symbol - 1] != stimuli[index]['middle'][symbol + lag]
               for index in indexes for symbol in SYMBOL_INDEXES)


def correlation(left, right):
    a_mean = sum(left) / len(left)
    b_mean = sum(right) / len(right)
    a = [value - a_mean for value in left]
    b = [value - b_mean for value in right]
    return sum(x * y for x, y in zip(a, b)) / math.sqrt(
        sum(x * x for x in a) * sum(y * y for y in b))


def run(out=HERE / 'results/joint-upper-sampled-state-dpsk.json'):
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
        raise ValueError('sampled-state stimulus digests collapsed')

    reference_errors = {}
    for index in selected:
        dibits = [0] * 8 + stimuli[index]['middle'] + [0] * 8
        pcm = transmit(dibits)[SAMPLE_START:SAMPLE_START + LONG_SAMPLES]
        reference_errors[index] = errors({index: receive(pcm)}, stimuli,
                                         [index], 0)
    if any(reference_errors.values()):
        raise ValueError('reference window/alignment does not recover dibits')

    tested = invalid = exact_training = exact_all = 0
    best = None
    for site in SITES:
        for phase in PHASE_OFFSETS:
            sample_indexes = positions(site, phase)
            for channel in STATE_CHANNELS:
                for coding in CODINGS:
                    try:
                        decisions = {index: receive(signal(streams[index], channel,
                                                            sample_indexes, coding))
                                     for index in selected}
                    except ValueError as err:
                        if 'no carrier' not in str(err):
                            raise
                        invalid += 1
                        continue
                    for lag in LAGS:
                        tested += 1
                        train_errors = errors(decisions, stimuli, TRAIN, lag)
                        exact_training += train_errors == 0
                        if train_errors > 4:
                            continue
                        holdout_errors = errors(decisions, stimuli, HOLDOUT, lag)
                        exact_all += train_errors == holdout_errors == 0
                        row = dict(site=site, phase_offset=phase,
                                   channel=channel, coding=coding,
                                   symbol_lag=lag,
                                   training_errors=train_errors,
                                   holdout_errors=holdout_errors)
                        if best is None or (
                                train_errors + holdout_errors,
                                holdout_errors, train_errors) < (
                                best['training_errors'] + best['holdout_errors'],
                                best['holdout_errors'], best['training_errors']):
                            best = row

    if (best is None or
            (best['site'], best['phase_offset'], best['channel'],
             best['coding'], best['symbol_lag']) !=
            ('center', 0, 'Y3F8', 'offset_binary', 0)):
        raise ValueError('selected sampled-state readout changed')
    validation = []
    center = positions(best['site'], best['phase_offset'])
    for seed in VALIDATION_SEEDS:
        generator = random.Random(seed)
        middle = [generator.randrange(4) for _ in range(16)]
        rows, digest = capture(mapping, base, middle)
        dibits = [0] * 8 + middle + [0] * 8
        pcm = transmit(dibits)[SAMPLE_START:SAMPLE_START + LONG_SAMPLES]
        output = signal(rows, best['channel'], center, best['coding'])
        decoded = receive(output)
        direct_adc = [127 - sample - 128 for sample in pcm]
        adc_decoded = receive(direct_adc)
        validation.append(dict(seed=seed, dibits=middle,
                               candidate_errors=sum(decoded[symbol - 1] !=
                                                    middle[symbol]
                                                    for symbol in SYMBOL_INDEXES),
                               direct_adc_errors=sum(adc_decoded[symbol - 1] !=
                                                     middle[symbol]
                                                     for symbol in SYMBOL_INDEXES),
                               candidate_to_pcm_correlation=round(
                                   correlation(output, pcm), 6),
                               trace_digest=digest))
    if any(row['direct_adc_errors'] for row in validation):
        raise ValueError('direct ADC reference control changed')

    paths = [Path(__file__), HERE / 'joint_upper_receive_bit_screen.py',
             HERE / 'joint_upper_source_screen.py',
             HERE / 'lower_i_d3f8_upper_symbol_screen.py',
             HERE / 'lower_i_d3f8_full_adc.py',
             HERE / 'reference_modem.py',
             HERE / 'photo_controller_path.py',
             HERE / 'split_slice_probe.py',
             HERE.parent / 'assumed/execute.py', HERE.parent / 'model.py',
             MAPPINGS['q3'],
             HERE / 'results/joint-upper-source-mask08-mapping.json',
             HERE.parents[2] / 'am27s31dc-prom/nokia-modem-am27s31dc.bin',
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(status='five-phase sampled state streams passed through an independent DPSK diagnostic',
                  fixture=dict(mapping='joint upper-source mask 08',
                               adc='127 minus reference PCM held 188/187 visits per sample',
                               sites=list(SITES),
                               phase_offsets=list(PHASE_OFFSETS),
                               channels=list(STATE_CHANNELS),
                               codings=list(CODINGS),
                               sample_rate_hz=9600,
                               known_carrier_hz=1800,
                               symbol_indexes=list(SYMBOL_INDEXES),
                               symbol_lags=list(LAGS),
                               train_indexes=list(TRAIN),
                               holdout_indexes=list(HOLDOUT),
                               reference_window_errors=reference_errors),
                  stimuli=[dict(index=index, **stimuli[index], trace_digest=digests[index])
                           for index in selected],
                  candidates_tested=tested, invalid_no_carrier=invalid,
                  exact_training_candidates=exact_training,
                  exact_train_and_holdout_candidates=exact_all,
                  best_low_training_error_candidate=best,
                  fresh_validation=validation,
                  limitations=[
                      'The known-carrier filter is an external diagnostic, not recovered DSC code or a proven USART output route.',
                      'Only single state channels sampled at five visit phases near sample start, center or end with two byte codings are tested.',
                      'ADC input, sample/latch clock, high instruction and DAC/USART routes remain untraced.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    print(result['candidates_tested'], result['invalid_no_carrier'],
          result['exact_training_candidates'], result['best_low_training_error_candidate'],
          [row['candidate_errors'] for row in result['fresh_validation']])
