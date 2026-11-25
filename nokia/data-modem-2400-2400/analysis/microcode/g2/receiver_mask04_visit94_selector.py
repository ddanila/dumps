"""Challenge a frozen visit-94 3F8 Y7 preamble phase-class selector."""

import hashlib
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from receiver_mask04_multivisit_capture import capture
from receiver_mask04_protocol_preamble import (DATA_SYMBOLS,
                                               PREAMBLE_SYMBOLS, candidate,
                                               fixture, mapped,
                                               mapping_with_upper_source,
                                               MAPPINGS, phase_quadrant, RULE,
                                               score)

PRIOR = HERE / 'results/receiver-mask04-preamble-class-lookup.json'
VISIT_SCREEN = HERE / 'results/receiver-mask04-preamble-visit-screen.json'
SEED = 0x72A1
TRAINING_DEGREES = (45, 180)
HOLDOUT_DEGREES = (0, 90, 135, 225, 270, 315)
SELECT_SYMBOL = 16


def analyze(case):
    snapshots = [symbol['visits'] for symbol in case['symbols']]
    pairs = [(snap['47']['row0'], snap['47']['row3']) for snap in snapshots]
    nominal = [phase_quadrant(*pair) for pair in pairs]
    diagonal = [((snap['47']['y3f8'] >> 7) & 1
                 if pair == (0xF3, 0xF2) else RULE.get(pair))
                for pair, snap in zip(pairs, snapshots)]
    dibits = [3] * PREAMBLE_SYMBOLS + [s['dibit'] for s in case['symbols'][PREAMBLE_SYMBOLS:]]
    data = range(PREAMBLE_SYMBOLS, PREAMBLE_SYMBOLS + DATA_SYMBOLS)
    selector_values = [(snapshots[symbol]['94']['y3f8'] >> 7) & 1
                       for symbol in range(8, 28)]
    bit = selector_values[SELECT_SYMBOL - 8]
    selected = 'nominal' if bit else 'diagonal'
    states = nominal if bit else diagonal
    return dict(degrees=case['degrees'], selector_byte=f"{snapshots[SELECT_SYMBOL]['94']['y3f8']:02X}",
                selector_y7=bit, steady_selector_one_count=sum(selector_values),
                selected_readout=selected,
                selected_data=score(states, dibits, data),
                nominal_data=score(nominal, dibits, data),
                diagonal_data=score(diagonal, dibits, data),
                trace_digest=case['trace_digest'],
                adc_stream_sha256=case['adc_stream_sha256'])


def run(out=HERE / 'results/receiver-mask04-visit94-selector.json'):
    visit_screen = json.loads(VISIT_SCREEN.read_text())
    at94 = next(row for row in visit_screen['stable_candidates']
                if row['site'] == '3F8' and row['visit'] == 94)
    if (at94['value45'] >> 7, at94['value180'] >> 7) != (0, 1):
        raise ValueError('training selector bit changed')
    prior = json.loads(PRIOR.read_text())
    prior_rows = {row['degrees']: row for row in prior['training'] + prior['holdout']}
    generator = random.Random(SEED)
    middle = [generator.randrange(4) for _ in range(DATA_SYMBOLS)]
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    holdout = []
    for degrees in HOLDOUT_DEGREES:
        case = capture(mapping, base, degrees, middle)
        row = analyze(case)
        if row['trace_digest'] != prior_rows[degrees]['trace_digest']:
            raise ValueError(('capture differs from earlier angle run', degrees))
        holdout.append(row)
        print(degrees, row['selector_byte'], row['selected_readout'],
              row['selected_data']['errors'], row['selected_data']['unknown'],
              flush=True)
    paths = [Path(__file__), PRIOR, VISIT_SCREEN,
             HERE / 'receiver_mask04_multivisit_capture.py',
             HERE / 'receiver_mask04_protocol_preamble.py',
             HERE / 'receiver_mask04_phase47_logic.py',
             HERE / 'receiver_mask04_two_visit_rule.py',
             HERE / 'reference_modem.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(experiment='frozen visit94 3F8 Y7 selector on other grid angles',
                  fixture=dict(training_degrees=TRAINING_DEGREES,
                               holdout_degrees=HOLDOUT_DEGREES,
                               seed=SEED, preamble_selector_symbol=SELECT_SYMBOL,
                               selector_visit=94, decoder_visit=47,
                               steady_preamble_symbols=list(range(8, 28))),
                  training_bit_values={'45': 0, '180': 1},
                  rule='visit94 3F8 Y7 one selects nominal; zero selects diagonal',
                  holdout=holdout,
                  limitations=[
                      'The selector, two 3F8/3ED captures, phase logic and USART path are external hypotheses.',
                      'The carrier grid does not cover intermediate angles, frequency error, arbitrary gain or noise.',
                      'The reference input and complementary ADC route are assumed, not measured Nokia line input.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
