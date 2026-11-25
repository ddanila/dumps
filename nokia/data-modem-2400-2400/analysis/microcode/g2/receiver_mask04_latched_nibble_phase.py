"""Test whether the mask-04 3ED latched nibble is a differential phase code."""

import hashlib
import random
import sys
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
from receiver_mask04_3ed_prom_latch import capture, VISITS_PER_SYMBOL, VALIDATION_SEEDS
from reference_modem import QUADRANT_TO_DIBIT

DIRECTIONS = (1, -1)
CARRIER_OFFSETS = tuple(range(16))


def decision(data, symbol, phase, direction, carrier_offset):
    visit = symbol * VISITS_PER_SYMBOL + phase
    current = data[visit] & 15
    previous = data[visit - VISITS_PER_SYMBOL] & 15
    differential = (direction * (current - previous) - carrier_offset) & 15
    quadrant = ((differential + 2) // 4) & 3
    return QUADRANT_TO_DIBIT[quadrant]


def errors(streams, stimuli, indexes, phase, direction, carrier_offset, lag):
    return sum(decision(streams[index], symbol, phase, direction,
                        carrier_offset) != stimuli[index]['middle'][symbol + lag]
               for index in indexes for symbol in SYMBOL_INDEXES)


def screen(streams, stimuli):
    tested = exact_training = exact_train_holdout = 0
    best = None
    for direction in DIRECTIONS:
        for carrier_offset in CARRIER_OFFSETS:
            for phase in range(VISITS_PER_SYMBOL):
                for lag in LAGS:
                    training = errors(streams, stimuli, TRAIN, phase,
                                      direction, carrier_offset, lag)
                    holdout = errors(streams, stimuli, HOLDOUT, phase,
                                     direction, carrier_offset, lag)
                    tested += 1
                    exact_training += training == 0
                    exact_train_holdout += training == holdout == 0
                    if best is None or training < best['training_errors']:
                        best = dict(direction=direction,
                                    carrier_offset=carrier_offset,
                                    phase_visit=phase, symbol_lag=lag,
                                    training_errors=training,
                                    holdout_errors=holdout)
    return dict(tested=tested, exact_training=exact_training,
                exact_training_and_holdout=exact_train_holdout, best=best)


def run(out=HERE / 'results/receiver-mask04-latched-nibble-phase.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    stimuli = sequences()
    selected = sorted(set(TRAIN + HOLDOUT))
    streams, cases = {}, {}
    for index in selected:
        streams[index], cases[index], _ = capture(
            mapping, base, stimuli[index]['middle'])
        print('captured stream', index, flush=True)
    if (len({case['trace_digest'] for case in cases.values()}) != len(selected)
            or len({case['captured_sha256'] for case in cases.values()}) !=
            len(selected)):
        raise ValueError('independent receive stimuli collapsed')
    scores = screen(streams, stimuli)
    best = scores['best']
    validation = []
    for seed in VALIDATION_SEEDS:
        generator = random.Random(seed)
        middle = [generator.randrange(4) for _ in range(16)]
        data, case, _ = capture(mapping, base, middle)
        count = errors({0: data}, {0: dict(middle=middle)}, [0],
                       best['phase_visit'], best['direction'],
                       best['carrier_offset'], best['symbol_lag'])
        validation.append(dict(seed=seed, errors=count,
                               checks=len(SYMBOL_INDEXES), **case))
        print('validated seed', seed, flush=True)
    paths = [Path(__file__), HERE / 'receiver_mask04_3ed_prom_latch.py',
             HERE / 'joint_mask04_adc_rom_wrapper_rule.py',
             HERE / 'receiver_four_row_condition_screen.py',
             HERE / 'reference_modem.py', HERE.parent / 'assumed/execute.py',
             HERE.parent / 'model.py', MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(
        experiment='fixed-phase differential nibble decision on mask-04 3ED Y',
        fixture=dict(mapping='joint upper-source mask 04',
                     latch='hypothetical U19 NAND rising edge on 3ED to 3EA',
                     dispatch='scenario [0,1,2,3]',
                     condition='inverted previous overflow at select 0',
                     adc='complementary reference PCM, 47/46 visits per sample',
                     phase_code='Y[3:0] at each 3ED NAND edge',
                     decision='nearest reference quadrant of current-minus-previous nibble',
                     directions=DIRECTIONS,
                     carrier_offsets=CARRIER_OFFSETS,
                     visits_per_symbol=VISITS_PER_SYMBOL,
                     symbol_indexes=SYMBOL_INDEXES, lags=LAGS,
                     train_indexes=TRAIN, holdout_indexes=HOLDOUT),
        cases=cases, scores=scores, validation=validation,
        limitations=[
            'The differential phase calculation is external diagnostic code, not DSC execution.',
            'The fixed-phase readout does not include filtering or adaptive carrier tracking.',
            'PROM-latch wiring, ADC route, TEST/dispatch and USART RxD remain hypotheses.'],
        source_sha256={str(path.relative_to(HERE.parents[2])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    print(result['scores'], result['validation'])
