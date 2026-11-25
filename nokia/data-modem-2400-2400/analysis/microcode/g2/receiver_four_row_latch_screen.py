"""Test whether four-row ADC-window output pins expose a dibit decision."""

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
VISITS_PER_SYMBOL = 375
SITES = (0x3F8, 0x3F9, 0x3FA)
FIELDS = ('y', 'sign', 'zero', 'carry', 'overflow')
CHANNELS = tuple((pc, field, bit) for pc in SITES for field in FIELDS
                 for bit in (range(8) if field == 'y' else (0,)))
OPERATIONS = ('direct', 'xor_previous')


def capture(mapping, base, middle):
    dibits = [0] * 8 + middle + [0] * 8
    pcm = transmit(dibits)
    if receive(pcm) != dibits[1:]:
        raise ValueError('reference receiver did not recover stimulus')
    samples = [127 - value for value in
               pcm[SAMPLE_START:SAMPLE_START + LONG_SAMPLES]]
    values = [value for index, value in enumerate(samples)
              for _ in range(47 if index % 8 < 7 else 46)]
    if len(values) != ADC_VISITS:
        raise ValueError('four-row symbol hold changed')
    scenario = configured(base, values, 'previous', 'overflow', 1)
    rows = []
    latest = {}
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, CYCLES, mode='integrated',
                         out=temporary, trace_limit=CYCLES)
        if (not result['clean'] or result['completed_cycles'] != CYCLES or
                result['address_counts'].get(0x3F8, 0) != ADC_VISITS or
                result['read_sequence_visits'].get(0x3F8, 0) != ADC_VISITS or
                [result['address_counts'].get(pc, 0)
                 for pc in (0x3EF, 0x3F3, 0x3F7, 0x3FB)] !=
                [ADC_VISITS + 1, ADC_VISITS, ADC_VISITS, ADC_VISITS]):
            raise ValueError('four-row symbol execution did not sustain')
        for line in (Path(temporary) / 'trace.jsonl').open():
            record = json.loads(line)
            pc = record['pc']
            if pc not in SITES:
                continue
            if pc == 0x3F8:
                read = record['external_read']
                if (not read.get('selected_by_alu') or
                        read['value'] != values[len(rows)] or
                        record['instruction_i_high'] != 0xD5):
                    raise ValueError('four-row ADC byte or instruction changed')
            latest[pc] = record['alu']
            if pc == 0x3FA:
                if len(latest) != len(SITES):
                    raise ValueError('incomplete ADC-window row')
                rows.append(bytes((latest[site][field] >> bit) & 1
                                  for site, field, bit in CHANNELS))
                latest.clear()
    if len(rows) != ADC_VISITS:
        raise ValueError('four-row latch candidate count changed')
    return rows, result['trace_digest']


def errors(streams, stimuli, indexes, channel, operation, phase,
           lag, target_bit, inverted):
    total = 0
    for index in indexes:
        stream = streams[index]
        middle = stimuli[index]['middle']
        for symbol in SYMBOL_INDEXES:
            visit = symbol * VISITS_PER_SYMBOL + phase
            current = stream[visit][channel]
            previous = stream[visit - VISITS_PER_SYMBOL][channel]
            value = current if operation == 'direct' else current ^ previous
            total += ((value ^ inverted) !=
                      ((middle[symbol + lag] >> target_bit) & 1))
    return total


def screen(streams, stimuli, operation, target_bit):
    checks = len(TRAIN) * len(SYMBOL_INDEXES)
    exact_train = exact_both = 0
    best = None
    for channel, (pc, field, bit) in enumerate(CHANNELS):
        for phase in range(VISITS_PER_SYMBOL):
            for lag in LAGS:
                raw = errors(streams, stimuli, TRAIN, channel, operation,
                             phase, lag, target_bit, 0)
                inverted = int(raw > checks // 2)
                train = min(raw, checks - raw)
                exact_train += train == 0
                holdout = errors(streams, stimuli, HOLDOUT, channel, operation,
                                 phase, lag, target_bit, inverted)
                exact_both += train == holdout == 0
                row = dict(pc=f'{pc:03X}', field=field, bit=bit,
                           phase_visit=phase, symbol_lag=lag,
                           inverted=bool(inverted), training_errors=train,
                           holdout_errors=holdout)
                rank = lambda item: (
                    item['training_errors'] + item['holdout_errors'],
                    item['holdout_errors'], item['training_errors'],
                    item['phase_visit'])
                if best is None or rank(row) < rank(best):
                    best = row
    return dict(operation=operation, target_bit=target_bit,
                exact_training_candidates=exact_train,
                exact_training_and_holdout_candidates=exact_both,
                best=best)


def run(out=HERE / 'results/receiver-four-row-latch-screen.json'):
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
        raise ValueError('four-row stimulus traces collapsed')
    results = [screen(streams, stimuli, operation, bit)
               for operation in OPERATIONS for bit in (0, 1)]
    paths = [Path(__file__), HERE / 'receiver_four_row_condition_screen.py',
             HERE / 'receiver_3eb_adc_route_screen.py',
             HERE / 'joint_upper_source_screen.py',
             HERE / 'lower_i_d3f8_upper_d_route.py',
             HERE / 'lower_i_d3f8_full_adc.py',
             HERE / 'lower_i_d3f8_upper_symbol_screen.py',
             HERE / 'reference_modem.py',
             HERE.parent / 'assumed/execute.py', HERE.parent / 'model.py',
             MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(
        experiment='fixed-phase output-pin decision screen in full four-row ADC path',
        fixture=dict(mapping='joint upper-source mask 08',
                     dispatch='scenario [0,1,2,3]',
                     condition='inverted previous overflow at select 0',
                     adc='complementary 127-PCM, 47/46 visits per sample',
                     channels=[f'{pc:03X}.{field}.{bit}'
                               for pc, field, bit in CHANNELS],
                     visits_per_symbol=VISITS_PER_SYMBOL,
                     symbol_indexes=list(SYMBOL_INDEXES), lags=list(LAGS),
                     train_indexes=list(TRAIN), holdout_indexes=list(HOLDOUT),
                     polarities='both'),
        stimuli=[dict(index=index, **stimuli[index], trace_digest=digests[index])
                 for index in selected],
        results=results,
        limitations=[
            'Only one Y-bit or ALU flag at a fixed phase, optionally compared to the previous symbol, is tested.',
            'The four-row dispatch, TEST source, ADC bus, sample clock and output latch are untraced hypotheses.',
            'A statistical bit fit would not by itself establish a physical USART RxD route.'],
        source_sha256={str(path.relative_to(HERE.parents[2])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    for row in run()['results']:
        print(row['operation'], row['target_bit'], row['exact_training_candidates'],
              row['exact_training_and_holdout_candidates'], row['best'])
