"""Test byte-wide sampled-state DPSK readouts on the four-row ADC path."""

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
from joint_upper_receive_bit_screen import HOLDOUT, TRAIN
from joint_upper_source_screen import SELECTED_MASK, candidate
from lower_i_d3f8_full_adc import LONG_SAMPLES, SAMPLE_START
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from lower_i_d3f8_upper_symbol_screen import LAGS, SYMBOL_INDEXES, sequences
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_four_row_condition_screen import configured
from reference_modem import receive, transmit

ADC_VISITS = 6000
CYCLES = 32 * ADC_VISITS + 47
SITES = ('start', 'center', 'end')
PHASE_OFFSETS = (-2, -1, 0, 1, 2)
CHANNELS = ('Y3F8', 'Y3F9', 'Y3FA', 'Q', 'R10', 'R11', 'R12', 'R13')
CODINGS = ('offset_binary', 'twos_complement')
VALIDATION_SEEDS = (0x2421, 0x2401, 0x26A1, 0x33C3)


def capture(mapping, base, middle):
    dibits = [0] * 8 + middle + [0] * 8
    pcm = transmit(dibits)
    if receive(pcm) != dibits[1:]:
        raise ValueError('reference receiver did not recover stimulus')
    samples = [127 - value for value in
               pcm[SAMPLE_START:SAMPLE_START + LONG_SAMPLES]]
    values = [sample for index, sample in enumerate(samples)
              for _ in range(47 if index % 8 < 7 else 46)]
    if len(values) != ADC_VISITS:
        raise ValueError('four-row sample schedule changed')
    scenario = configured(base, values, 'previous', 'overflow', 1)
    ram = scenario['initial']['ram'][:]
    rows = []
    y8 = y9 = None
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, CYCLES, mode='integrated',
                         out=temporary, trace_limit=CYCLES)
        if (not result['clean'] or result['completed_cycles'] != CYCLES or
                result['address_counts'].get(0x3F8, 0) != ADC_VISITS or
                result['read_sequence_visits'].get(0x3F8, 0) != ADC_VISITS or
                [result['address_counts'].get(pc, 0)
                 for pc in (0x3EF, 0x3F3, 0x3F7, 0x3FB)] !=
                [ADC_VISITS + 1, ADC_VISITS, ADC_VISITS, ADC_VISITS]):
            raise ValueError('four-row ADC execution did not sustain')
        for line in (Path(temporary) / 'trace.jsonl').open():
            record = json.loads(line)
            for address, value in record['registers'].items():
                ram[int(address)] = value
            pc = record['pc']
            if pc == 0x3F8:
                read = record['external_read']
                if (not read.get('selected_by_alu') or
                        read['value'] != values[len(rows)] or
                        record['instruction_i_high'] != 0xD5):
                    raise ValueError('four-row ADC byte or instruction changed')
                y8 = record['alu']['y']
            elif pc == 0x3F9:
                y9 = record['alu']['y']
            elif pc == 0x3FA:
                if y8 is None or y9 is None:
                    raise ValueError('incomplete ADC-sensitive row')
                rows.append(bytes((y8, y9, record['alu']['y'], record['q'],
                                   *ram[10:14])))
                y8 = y9 = None
    if len(rows) != ADC_VISITS:
        raise ValueError('ADC-window row count changed')
    return rows, result['trace_digest']


def positions(site, offset):
    indexes = []
    visit = 0
    for sample in range(LONG_SAMPLES):
        length = 47 if sample % 8 < 7 else 46
        origin = {'start': visit + 2,
                  'center': visit + length // 2,
                  'end': visit + length - 3}[site]
        indexes.append(origin + offset)
        visit += length
    if visit != ADC_VISITS or not all(0 <= index < visit for index in indexes):
        raise ValueError('sample positions changed')
    return indexes


def signal(rows, channel, indexes, coding):
    raw = [rows[visit][CHANNELS.index(channel)] for visit in indexes]
    return ([value - 128 for value in raw] if coding == 'offset_binary' else
            [value if value < 128 else value - 256 for value in raw])


def errors(decisions, stimuli, indexes, lag):
    return sum(decisions[index][symbol - 1] != stimuli[index]['middle'][symbol + lag]
               for index in indexes for symbol in SYMBOL_INDEXES)


def run(out=HERE / 'results/receiver-four-row-sampled-state-dpsk.json'):
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
        raise ValueError('stimulus traces collapsed')

    tested = invalid = exact_training = exact_all = 0
    best = None
    for site in SITES:
        for phase in PHASE_OFFSETS:
            indexes = positions(site, phase)
            for channel in CHANNELS:
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
            decisions = receive(signal(rows, best['channel'], indexes,
                                       best['coding']))
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
    paths = [Path(__file__), HERE / 'receiver_four_row_condition_screen.py',
             HERE / 'receiver_two_row_sampled_state_dpsk.py',
             HERE / 'reference_modem.py', HERE.parent / 'assumed/execute.py',
             HERE.parent / 'model.py', MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(
        experiment='byte-wide sampled-state external DPSK diagnostic on full four-row path',
        fixture=dict(mapping='joint upper-source mask 08',
                     dispatch='scenario [0,1,2,3]',
                     condition='inverted previous overflow at select 0',
                     adc='complementary 127-PCM, 47/46 visits per sample',
                     channels=CHANNELS, sites=SITES, phase_offsets=PHASE_OFFSETS,
                     codings=CODINGS, symbol_indexes=SYMBOL_INDEXES,
                     lags=LAGS, train_indexes=TRAIN, holdout_indexes=HOLDOUT),
        tested=tested, invalid=invalid, exact_training=exact_training,
        exact_training_and_holdout=exact_all, best=best,
        validation=validation, trace_digests=digests,
        limitations=[
            'The fixed reference receiver is an external diagnostic, not executed DSC decision code.',
            'Only byte-wide Y, Q and four RAM readouts at three phases and small offsets are tested.',
            'The four-row dispatch, TEST, ADC bus, sample clock, output latch and USART route are untraced.'],
        source_sha256={str(path.relative_to(HERE.parents[2])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    print(result['best'], result['validation'])
