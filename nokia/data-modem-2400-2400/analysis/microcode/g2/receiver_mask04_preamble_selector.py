"""Use an executed preamble latch bit to select a receive phase readout."""

import hashlib
import json
import random
from pathlib import Path

from receiver_mask04_protocol_preamble import (HERE, DATA_SYMBOLS,
                                               PREAMBLE_SYMBOLS, candidate,
                                               capture, fixture, mapped,
                                               mapping_with_upper_source,
                                               MAPPINGS, phase_quadrant,
                                               RULE, score)
from reference_modem import QUADRANT_TO_DIBIT
from common import save

PRIOR = HERE / 'results/receiver-mask04-protocol-preamble.json'
DEGREES = (0, 45, 90, 135)
FRESH_SEED = 0x72A1
SELECT_SYMBOL = 16


def analyze(case):
    symbols = case['symbols']
    pairs = [(row['row0']['y'], row['row3']['y']) for row in symbols]
    nominal = [phase_quadrant(*pair) for pair in pairs]
    diagonal = [((row['at_3f8']['y'] >> 7) & 1
                 if pair == (0xF3, 0xF2) else RULE.get(pair))
                for pair, row in zip(pairs, symbols)]
    dibits = [3] * PREAMBLE_SYMBOLS + case['middle']
    training = range(1, PREAMBLE_SYMBOLS)
    data = range(PREAMBLE_SYMBOLS, PREAMBLE_SYMBOLS + DATA_SYMBOLS)
    preamble_byte = symbols[SELECT_SYMBOL]['row0']['y']
    selected = 'nominal' if preamble_byte & 0x08 else 'diagonal'
    states = nominal if selected == 'nominal' else diagonal
    return dict(degrees=case['degrees'], seed=case['seed'],
                preamble_row0_byte=f'{preamble_byte:02X}',
                preamble_selector_bit3=(preamble_byte >> 3) & 1,
                selected_readout=selected,
                nominal_preamble=score(nominal, dibits, training),
                diagonal_preamble=score(diagonal, dibits, training),
                nominal_data=score(nominal, dibits, data),
                diagonal_data=score(diagonal, dibits, data),
                selected_data=score(states, dibits, data),
                trace_digest=case['trace_digest'],
                adc_stream_sha256=case['adc_stream_sha256'],
                edge_captured_sha256=case['edge_captured_sha256'])


def run(out=HERE / 'results/receiver-mask04-preamble-selector.json'):
    prior = json.loads(PRIOR.read_text())
    development = [analyze(case) for case in prior['cases']]
    if ([(row['degrees'], row['preamble_selector_bit3']) for row in development] !=
            [(0, 1), (0, 1), (45, 0), (45, 0)]):
        raise ValueError('development preamble bit changed')
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    generator = random.Random(FRESH_SEED)
    middle = [generator.randrange(4) for _ in range(DATA_SYMBOLS)]
    fresh = []
    for degrees in DEGREES:
        case = capture(mapping, base, degrees, FRESH_SEED, middle)
        fresh.append(analyze(case))
        print(degrees, fresh[-1]['selected_readout'],
              fresh[-1]['selected_data']['errors'],
              fresh[-1]['selected_data']['unknown'], flush=True)
    paths = [Path(__file__), PRIOR,
             HERE / 'receiver_mask04_protocol_preamble.py',
             HERE / 'receiver_mask04_phase47_logic.py',
             HERE / 'receiver_mask04_two_visit_rule.py',
             HERE / 'reference_modem.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(experiment='preamble row-0 latch bit selects nominal or diagonal readout',
                  rule='row-0 3ED Y bit 3 at preamble symbol 16: one selects nominal; zero selects diagonal',
                  fixture=dict(development='saved continuous 0/45 degree traces',
                               fresh_degrees=DEGREES, fresh_seed=FRESH_SEED,
                               preamble_symbols=PREAMBLE_SYMBOLS,
                               data_symbols=DATA_SYMBOLS,
                               capture_visit=47),
                  development=development, fresh=fresh,
                  limitations=[
                      'The preamble is an assumed reference line waveform; the 3ED latch, selector, phase logic and RxD path remain external hypotheses.',
                      'A single preamble byte can distinguish tested phase classes without proving arbitrary carrier-phase tracking.',
                      'The two decoder rules were developed before this selection test; only the new streams are independent selector validation.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
