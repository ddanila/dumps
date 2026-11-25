"""Screen fixed-phase dibit decisions on the interleaved 0/2 ADC path."""

import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from joint_upper_receive_bit_screen import HOLDOUT, TRAIN
from joint_upper_receive_codebook import evaluate
from joint_upper_source_screen import SELECTED_MASK, candidate
from lower_i_d3f8_full_adc import LONG_CYCLES, LONG_SAMPLES, SAMPLE_START, scenario_for_full_byte
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from lower_i_d3f8_upper_symbol_screen import CHANNELS, LAGS, SYMBOL_INDEXES, sequences
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from reference_modem import receive, transmit

VISITS_PER_SYMBOL = 750
ADC_VISITS = 12000
OPERATIONS = ('direct', 'xor_previous', 'subtract_previous')
MAX_CODE_VALUES = (4, 8, 16)


def capture(mapping, base, middle):
    dibits = [0] * 8 + middle + [0] * 8
    pcm = transmit(dibits)
    if receive(pcm) != dibits[1:]:
        raise ValueError('reference modem failed to recover its stimulus')
    samples = [127 - sample for sample in
               pcm[SAMPLE_START:SAMPLE_START + LONG_SAMPLES]]
    values = [value for index, sample in enumerate(samples)
              for value in [sample] * (94 if index % 4 < 3 else 93)]
    if len(values) != ADC_VISITS:
        raise ValueError('two-row ADC sample hold changed')
    scenario = scenario_for_full_byte(base, values, 'complementary')
    scenario['dispatch']['mode'] = 'sequence'
    scenario['dispatch']['sequence'] = [0, 2]
    ram = scenario['initial']['ram'][:]
    rows = []
    y8 = y9 = None
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, LONG_CYCLES,
                         mode='integrated', out=temporary, trace_limit=LONG_CYCLES)
        if (not result['clean'] or
                result['address_counts'].get(0x3F8, 0) != ADC_VISITS or
                result['read_sequence_visits'].get(0x3F8, 0) != ADC_VISITS or
                result['address_counts'].get(0x3EF, 0) != ADC_VISITS + 1):
            raise ValueError('two-row receive execution did not sustain')
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
                    raise ValueError('two-row ADC byte or instruction changed')
                y8 = record['alu']['y']
            elif pc == 0x3F9:
                y9 = record['alu']['y']
            elif pc == 0x3FA:
                if y8 is None or y9 is None:
                    raise ValueError('incomplete two-row ADC visit')
                rows.append(bytes((y8, y9, record['alu']['y'], record['q'], *ram)))
                y8 = y9 = None
    if len(rows) != ADC_VISITS:
        raise ValueError(('two-row receive row count changed', len(rows)))
    return rows, result['trace_digest']


def observed(rows, symbol, phase, channel, operation):
    visit = symbol * VISITS_PER_SYMBOL + phase
    current = rows[visit][channel]
    if operation == 'direct':
        return current
    previous = rows[visit - VISITS_PER_SYMBOL][channel]
    return (current ^ previous if operation == 'xor_previous' else
            (current - previous) & 255)


def count_errors(streams, stimuli, indexes, operation, channel, bit, phase,
                 lag, target_bit, inverted):
    return sum(
        (((observed(streams[index], symbol, phase, channel, operation)
           >> bit) & 1) ^ inverted) !=
        ((stimuli[index]['middle'][symbol + lag] >> target_bit) & 1)
        for index in indexes for symbol in SYMBOL_INDEXES)


def screen(streams, stimuli, operation, target_bit):
    checks = len(TRAIN) * len(SYMBOL_INDEXES)
    minimum = checks
    exact_train = exact_all = 0
    best = None
    for channel, name in enumerate(CHANNELS):
        for bit in range(8):
            for lag in LAGS:
                for phase in range(VISITS_PER_SYMBOL):
                    raw_errors = count_errors(streams, stimuli, TRAIN, operation,
                                              channel, bit, phase, lag,
                                              target_bit, False)
                    inverted = raw_errors > checks // 2
                    train_errors = min(raw_errors, checks - raw_errors)
                    minimum = min(minimum, train_errors)
                    exact_train += train_errors == 0
                    if train_errors > 3:
                        continue
                    holdout_errors = count_errors(streams, stimuli, HOLDOUT,
                                                  operation, channel, bit,
                                                  phase, lag, target_bit,
                                                  inverted)
                    exact_all += train_errors == holdout_errors == 0
                    row = dict(channel=name, bit=bit, phase_visit=phase,
                               symbol_lag=lag, inverted=inverted,
                               training_errors=train_errors,
                               holdout_errors=holdout_errors)
                    if best is None or (
                            train_errors + holdout_errors,
                            holdout_errors, train_errors, phase) < (
                            best['training_errors'] + best['holdout_errors'],
                            best['holdout_errors'],
                            best['training_errors'], best['phase_visit']):
                        best = row
    return dict(operation=operation, target_bit=target_bit,
                minimum_training_errors=minimum,
                exact_training_candidates=exact_train,
                exact_training_and_holdout_candidates=exact_all,
                best_at_most_three_training_errors=best)


def codebook_screen(streams, stimuli, operation):
    best = {limit: None for limit in MAX_CODE_VALUES}
    tested = {limit: 0 for limit in MAX_CODE_VALUES}
    exact_train = {limit: 0 for limit in MAX_CODE_VALUES}
    exact_all = {limit: 0 for limit in MAX_CODE_VALUES}
    for channel, name in enumerate(CHANNELS):
        for phase in range(VISITS_PER_SYMBOL):
            codes = {index: [observed(streams[index], symbol, phase,
                                      channel, operation)
                             for symbol in SYMBOL_INDEXES]
                     for index in streams}
            for lag in LAGS:
                row = evaluate(codes, stimuli, lag)
                if row is None:
                    continue
                for limit in MAX_CODE_VALUES:
                    if row['code_values'] > limit:
                        continue
                    tested[limit] += 1
                    exact_train[limit] += row['train_errors'] == 0
                    exact_all[limit] += (row['train_errors'] == 0 and
                                         row['holdout_errors'] == 0)
                    if row['holdout_errors'] is None:
                        continue
                    candidate_row = dict(channel=name, phase_visit=phase,
                                         symbol_lag=lag, **row)
                    old = best[limit]
                    rank = lambda item: (item['train_errors'] + item['holdout_errors'],
                                         item['holdout_errors'],
                                         item['holdout_unknown'],
                                         item['code_values'],
                                         item['phase_visit'])
                    if old is None or rank(candidate_row) < rank(old):
                        best[limit] = candidate_row
    return dict(operation=operation,
                limits=[dict(max_code_values=limit,
                             candidates_tested=tested[limit],
                             exact_training=exact_train[limit],
                             exact_training_and_holdout=exact_all[limit],
                             best_at_most_four_training_errors=best[limit])
                        for limit in MAX_CODE_VALUES])


def run(out=HERE / 'results/receiver-two-row-decision-screen.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), SELECTED_MASK)
    _, base = fixture()
    stimuli = sequences()
    selected = sorted(set(TRAIN + HOLDOUT))
    streams = {}
    digests = {}
    for index in selected:
        streams[index], digests[index] = capture(mapping, base,
                                                 stimuli[index]['middle'])
    if len(set(digests.values())) != len(selected):
        raise ValueError('independent two-row ADC traces collapsed')
    results = [screen(streams, stimuli, operation, bit)
               for operation in OPERATIONS for bit in (0, 1)]
    codebooks = [codebook_screen(streams, stimuli, operation)
                 for operation in OPERATIONS]
    paths = [Path(__file__), HERE / 'receiver_dispatch_source_screen.py',
             HERE / 'joint_upper_receive_bit_screen.py',
             HERE / 'joint_upper_receive_codebook.py',
             HERE / 'joint_upper_source_screen.py',
             HERE / 'lower_i_d3f8_full_adc.py',
             HERE / 'lower_i_d3f8_upper_d_route.py',
             HERE / 'lower_i_d3f8_upper_symbol_screen.py',
             HERE / 'photo_controller_path.py', HERE / 'reference_modem.py',
             HERE / 'split_slice_probe.py',
             HERE.parent / 'assumed/execute.py', HERE.parent / 'model.py',
             MAPPINGS['q3'],
             HERE / 'results/joint-upper-source-mask08-mapping.json',
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(
        status='fixed-phase dibit-bit screen on the interleaved 3EF/3F7 ADC path',
        fixture=dict(mapping='joint upper-source mask 08',
                     dispatch='scenario sequence [0,2] at 3EC; counter/buffer route untraced',
                     adc='complementary 127-PCM with 94/94/94/93 visit holds per four samples',
                     upper_instruction_at_d3f8='D5',
                     visits_per_symbol=VISITS_PER_SYMBOL,
                     channels=list(CHANNELS), operations=list(OPERATIONS),
                     codebook_max_values=list(MAX_CODE_VALUES),
                     lags=list(LAGS), symbol_indexes=list(SYMBOL_INDEXES),
                     train_indexes=list(TRAIN), holdout_indexes=list(HOLDOUT),
                     candidate_polarities='both'),
        stimuli=[dict(index=index, **stimuli[index], trace_digest=digests[index])
                 for index in selected],
        results=results,
        codebooks=codebooks,
        limitations=[
            'Only single state-byte bits at one fixed symbol phase, optionally compared to the previous symbol, are tested.',
            'A bit fit is not a DSC-to-USART RxD route, and the two-row dispatch schedule is a scenario hypothesis.',
            'ADC bus, sample clock, upper instruction wiring and condition source remain untraced.'],
        source_sha256={str(path.relative_to(HERE.parents[2])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    for row in report['results']:
        print(row['operation'], row['target_bit'],
              row['minimum_training_errors'],
              row['exact_training_candidates'],
              row['exact_training_and_holdout_candidates'],
              row['best_at_most_three_training_errors'])
    for row in report['codebooks']:
        print('codebook', row['operation'],
              [(item['max_code_values'], item['exact_training'],
                item['exact_training_and_holdout'])
               for item in row['limits']])
