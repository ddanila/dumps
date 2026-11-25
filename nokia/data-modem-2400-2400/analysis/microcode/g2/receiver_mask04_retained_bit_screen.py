"""Screen retained R1, R12 and Q bits on the joint mask-04 receive path."""

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
from joint_upper_source_screen import candidate
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
CHANNELS = ('R1', 'R12', 'Q')
OPERATIONS = ('direct', 'xor_previous')
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
        raise ValueError('four-row sample hold changed')
    scenario = configured(base, values, 'previous', 'overflow', 1)
    ram = scenario['initial']['ram'][:]
    rows = []
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, CYCLES, mode='integrated',
                         out=temporary, trace_limit=CYCLES)
        if (not result['clean'] or result['completed_cycles'] != CYCLES or
                result['address_counts'].get(0x3FE, 0) != ADC_VISITS or
                result['read_sequence_visits'].get(0x3F8, 0) != ADC_VISITS):
            raise ValueError('mask-04 receive stream did not sustain')
        for line in (Path(temporary) / 'trace.jsonl').open():
            record = json.loads(line)
            for address, value in record['registers'].items():
                ram[int(address)] = value
            if record['pc'] == 0x3FE:
                rows.append(bytes((ram[1], ram[12], record['q'])))
    if len(rows) != ADC_VISITS:
        raise ValueError('retained state count changed')
    return rows, result['trace_digest']


def errors(streams, stimuli, indexes, channel, bit, operation, phase,
           lag, target_bit, inverted):
    total = 0
    for index in indexes:
        rows = streams[index]
        middle = stimuli[index]['middle']
        for symbol in SYMBOL_INDEXES:
            visit = symbol * VISITS_PER_SYMBOL + phase
            current = (rows[visit][channel] >> bit) & 1
            previous = (rows[visit - VISITS_PER_SYMBOL][channel] >> bit) & 1
            value = current if operation == 'direct' else current ^ previous
            total += ((value ^ inverted) !=
                      ((middle[symbol + lag] >> target_bit) & 1))
    return total


def screen(streams, stimuli, operation, target_bit):
    checks = len(TRAIN) * len(SYMBOL_INDEXES)
    exact_training = exact_all = 0
    best = None
    for channel, name in enumerate(CHANNELS):
        for bit in range(8):
            for phase in range(VISITS_PER_SYMBOL):
                for lag in LAGS:
                    raw = errors(streams, stimuli, TRAIN, channel, bit,
                                 operation, phase, lag, target_bit, 0)
                    inverted = int(raw > checks // 2)
                    train = min(raw, checks - raw)
                    exact_training += train == 0
                    holdout = errors(streams, stimuli, HOLDOUT, channel, bit,
                                     operation, phase, lag, target_bit, inverted)
                    exact_all += train == holdout == 0
                    row = dict(channel=name, bit=bit, operation=operation,
                               target_bit=target_bit, phase_visit=phase,
                               symbol_lag=lag, inverted=bool(inverted),
                               training_errors=train, holdout_errors=holdout)
                    if best is None or (train, holdout) < (
                            best['training_errors'], best['holdout_errors']):
                        best = row
    return dict(operation=operation, target_bit=target_bit,
                exact_training=exact_training, exact_training_and_holdout=exact_all,
                best=best)


def run(out=HERE / 'results/receiver-mask04-retained-bit-screen.json'):
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
        raise ValueError('mask-04 receive stimuli collapsed')
    results = [screen(streams, stimuli, operation, bit)
               for operation in OPERATIONS for bit in (0, 1)]
    best = min((row['best'] for row in results),
               key=lambda row: (row['training_errors'], row['holdout_errors']))
    validation = []
    for seed in VALIDATION_SEEDS:
        generator = random.Random(seed)
        middle = [generator.randrange(4) for _ in range(16)]
        rows, digest = capture(mapping, base, middle)
        channel = CHANNELS.index(best['channel'])
        fresh = {0: rows}
        trial = {0: dict(middle=middle)}
        count = errors(fresh, trial, [0], channel, best['bit'],
                       best['operation'], best['phase_visit'],
                       best['symbol_lag'], best['target_bit'],
                       int(best['inverted']))
        validation.append(dict(seed=seed, errors=count,
                               checks=len(SYMBOL_INDEXES), trace_digest=digest))
        print('validated seed', seed, flush=True)
    paths = [Path(__file__), HERE / 'joint_four_row_retention_tx.py',
             HERE / 'receiver_four_row_condition_screen.py',
             HERE / 'joint_upper_source_screen.py',
             HERE / 'reference_modem.py', HERE.parent / 'assumed/execute.py',
             HERE.parent / 'model.py', MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(
        experiment='retained state bit screen on joint mask-04 full-row receiver',
        fixture=dict(mapping='joint upper-source mask 04',
                     dispatch='scenario [0,1,2,3]',
                     condition='inverted previous overflow at select 0',
                     adc='complementary reference PCM, 47/46 visits per sample',
                     channels=CHANNELS, operations=OPERATIONS,
                     visits_per_symbol=VISITS_PER_SYMBOL,
                     symbol_indexes=SYMBOL_INDEXES, lags=LAGS,
                     train_indexes=TRAIN, holdout_indexes=HOLDOUT),
        results=results, selected_best=best, validation=validation,
        trace_digests=digests,
        limitations=[
            'Only direct or previous-symbol XOR of one R1/R12/Q bit is tested.',
            'A statistical bit fit alone would not establish a physical USART RxD wire.',
            'Dispatch, TEST, ADC bus, sample clock and output latch are hypotheses.'],
        source_sha256={str(path.relative_to(HERE.parents[2])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    print(result['results'], result['validation'])
