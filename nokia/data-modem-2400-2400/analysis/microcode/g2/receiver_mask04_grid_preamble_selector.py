"""Validate a frozen two-visit preamble selector on new receiver streams."""

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

CLASS_LOOKUP = HERE / 'results/receiver-mask04-preamble-class-lookup.json'
BIT_SCREEN = HERE / 'results/receiver-mask04-visit94-selector.json'
DEGREES = (0, 45, 90, 135, 180, 225, 270, 315)
FRESH_SEED = 0xB812
SELECT_SYMBOL = 16


def selected_readout(row0, y94):
    """Frozen after the 0x72A1 grid; no data decisions enter this function."""
    if row0 in (0xFD, 0xF2) or (row0 == 0xF5 and y94 & 0x80):
        return 'nominal'
    if row0 in (0xF5, 0xF3):
        return 'diagonal'
    return None


def analyze(case):
    symbols = case['symbols']
    snapshots = [s['visits'] for s in symbols]
    pairs = [(s['47']['row0'], s['47']['row3']) for s in snapshots]
    nominal = [phase_quadrant(*pair) for pair in pairs]
    diagonal = [((s['47']['y3f8'] >> 7) & 1
                 if pair == (0xF3, 0xF2) else RULE.get(pair))
                for pair, s in zip(pairs, snapshots)]
    row0 = snapshots[SELECT_SYMBOL]['47']['row0']
    y94 = snapshots[SELECT_SYMBOL]['94']['y3f8']
    selected = selected_readout(row0, y94)
    preamble = range(1, PREAMBLE_SYMBOLS)
    data = range(PREAMBLE_SYMBOLS, PREAMBLE_SYMBOLS + DATA_SYMBOLS)
    dibits = [3] * PREAMBLE_SYMBOLS + [s['dibit'] for s in symbols[PREAMBLE_SYMBOLS:]]
    return dict(degrees=case['degrees'], row0_47=f'{row0:02X}',
                y3f8_94=f'{y94:02X}', selected_readout=selected,
                nominal_data=score(nominal, dibits, data),
                diagonal_data=score(diagonal, dibits, data),
                selected_preamble=score(nominal if selected == 'nominal' else diagonal,
                                        dibits, preamble) if selected else None,
                selected_data=score(nominal if selected == 'nominal' else diagonal,
                                    dibits, data) if selected else None,
                trace_digest=case['trace_digest'],
                adc_stream_sha256=case['adc_stream_sha256'])


def run(out=HERE / 'results/receiver-mask04-grid-preamble-selector.json'):
    prior = json.loads(CLASS_LOOKUP.read_text())
    bit = json.loads(BIT_SCREEN.read_text())
    by_degree = {r['degrees']: r for r in prior['training'] + prior['holdout']}
    y94 = {r['degrees']: int(r['selector_byte'], 16) for r in bit['holdout']}
    y94[45] = 0x2F
    y94[180] = 0xBF
    development = []
    for degrees in DEGREES:
        row = by_degree[degrees]
        label = selected_readout(int(row['preamble_row0_byte'], 16), y94[degrees])
        result = row[label + '_data'] if label else None
        development.append(dict(degrees=degrees,
                                row0_47=row['preamble_row0_byte'],
                                y3f8_94=f'{y94[degrees]:02X}',
                                selected_readout=label, selected_data=result))
    if any(row['selected_data'] is None or row['selected_data']['errors'] or
           row['selected_data']['unknown'] for row in development):
        raise ValueError('frozen rule fails its development grid')
    generator = random.Random(FRESH_SEED)
    middle = [generator.randrange(4) for _ in range(DATA_SYMBOLS)]
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    fresh = []
    for degrees in DEGREES:
        case = capture(mapping, base, degrees, middle)
        fresh.append(analyze(case))
        row = fresh[-1]
        print(degrees, row['row0_47'], row['y3f8_94'], row['selected_readout'],
              row['selected_data']['errors'] if row['selected_data'] else None,
              row['selected_data']['unknown'] if row['selected_data'] else None,
              flush=True)
    paths = [Path(__file__), CLASS_LOOKUP, BIT_SCREEN,
             HERE / 'receiver_mask04_multivisit_capture.py',
             HERE / 'receiver_mask04_protocol_preamble.py',
             HERE / 'receiver_mask04_phase47_logic.py',
             HERE / 'receiver_mask04_two_visit_rule.py',
             HERE / 'reference_modem.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(experiment='frozen two-visit preamble selector on fresh data across eight phase-grid angles',
                  rule='row0(47) FD or F2 -> nominal; F5 with 3F8(94).Y7=1 -> nominal; F5 otherwise or F3 -> diagonal; other bytes unknown',
                  fixture=dict(development_seed=0x72A1, fresh_seed=FRESH_SEED,
                               degrees=DEGREES, selector_symbol=SELECT_SYMBOL,
                               preamble_symbols=PREAMBLE_SYMBOLS,
                               data_symbols=DATA_SYMBOLS),
                  development=development, fresh=fresh,
                  aggregate=dict(checks=sum(row['selected_data']['checks']
                                            for row in fresh if row['selected_data']),
                                 errors=sum(row['selected_data']['errors']
                                            for row in fresh if row['selected_data']),
                                 unknown=sum(row['selected_data']['unknown']
                                             for row in fresh if row['selected_data']),
                                 unselected=sum(row['selected_data'] is None for row in fresh),
                                 preamble_checks=sum(row['selected_preamble']['checks']
                                                     for row in fresh if row['selected_preamble']),
                                 preamble_errors=sum(row['selected_preamble']['errors']
                                                     for row in fresh if row['selected_preamble']),
                                 preamble_unknown=sum(row['selected_preamble']['unknown']
                                                      for row in fresh if row['selected_preamble'])),
                  limitations=[
                      'The rule is developed on one eight-angle grid and does not establish arbitrary carrier-phase tracking.',
                      'A symbol counter, two executed captures, selection logic, serial clock and RxD route remain external hypotheses.',
                      'The reference input and complementary ADC path are assumed rather than measured on the Nokia board.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    print(run()['aggregate'])
