"""Validate a frozen four-input receive phase readout on fresh PROM runs."""

import hashlib
import json
import random
from pathlib import Path

from receiver_mask04_protocol_preamble import (HERE, candidate, capture,
                                               fixture, mapped,
                                               mapping_with_upper_source,
                                               MAPPINGS)
from receiver_mask04_rotated_codebook import expected_states
from reference_modem import QUADRANT_TO_DIBIT
from common import save

DEVELOPMENT = HERE / 'results/receiver-mask04-3f8-phase-bit.json'
SEEDS = (0x8D31, 0x2B71)
DEGREES = (0, 45, 90, 135, 180)
DATA_SYMBOLS = 16
PREAMBLE_SYMBOLS = 32
VISITS_PER_SYMBOL = 375
PHASE_VISIT = 47

# Input order: row-0 Y bits 0, 1, 3; transient 3F8 Y bit 7.
# Frozen after screening the ten development cases; unlisted inputs are unknown.
PHASE_BY_INPUT = {0b0001: 1, 0b0010: 0, 0b0011: 2,
                  0b1001: 0, 0b1010: 2, 0b1011: 3, 0b1101: 3}
DEVELOPMENT_OFFSETS = {0: 0, 45: 2, 90: 1, 135: 3, 180: 2}


def input_code(row0, y3f8):
    return ((row0 & 1) | (row0 & 2) |
            (((row0 >> 3) & 1) << 2) | (y3f8 & 0x80) >> 4)


def phases(pairs, y3f8):
    return [PHASE_BY_INPUT.get(input_code(pair[0], y))
            for pair, y in zip(pairs, y3f8)]


def score(states, expected):
    dibits = [None]
    for before, after in zip(states, states[1:]):
        dibits.append(None if before is None or after is None else
                      QUADRANT_TO_DIBIT[(after - before - 2) & 3])
    return dict(checks=len(expected) - 1,
                errors=sum(got is not None and got != want
                           for got, want in zip(dibits[1:], expected[1:])),
                unknown=sum(got is None for got in dibits[1:]),
                unrecognized_symbols=sum(state is None for state in states),
                dibits=dibits)


def run(out=HERE / 'results/receiver-mask04-four-bit-phase.json'):
    development = json.loads(DEVELOPMENT.read_text())['fresh']
    if len(development) != 10:
        raise ValueError('development case count changed')
    development_rows = []
    for case in development:
        states = phases(case['pairs'], case['y3f8'])
        labels = expected_states(case['middle'])
        offset = DEVELOPMENT_OFFSETS[case['degrees']]
        if any(state != ((label + offset) & 3)
               for state, label in zip(states, labels)):
            raise ValueError(('frozen rule disagrees with development',
                              case['degrees'], case['seed']))
        check = score(states, case['middle'])
        if check['errors'] or check['unknown']:
            raise ValueError('development differential readout changed')
        development_rows.append(dict(degrees=case['degrees'], seed=case['seed'],
                                     trace_digest=case['trace_digest'],
                                     score=check))
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    fresh = []
    for degrees in DEGREES:
        for seed in SEEDS:
            generator = random.Random(seed)
            middle = [generator.randrange(4) for _ in range(DATA_SYMBOLS)]
            case = capture(mapping, base, degrees, seed, middle)
            pairs = [(row['row0']['y'], row['row3']['y'])
                     for row in case['symbols']]
            y3f8 = [row['at_3f8']['y'] for row in case['symbols']]
            states = phases(pairs, y3f8)
            expected = [row['dibit'] for row in case['symbols']]
            result = score(states, expected)
            fresh.append(dict(degrees=degrees, seed=seed,
                              trace_digest=case['trace_digest'],
                              capture_edge_count=case['gate_edges'],
                              expected_dibits=expected,
                              input_codes=[input_code(pair[0], y)
                                           for pair, y in zip(pairs, y3f8)],
                              phases=states, score=result,
                              nominal_readout=case['nominal']['all_data'],
                              diagonal_readout=case['diagonal']['all_data']))
            print('captured', degrees, hex(seed), result['errors'],
                  result['unknown'], result['unrecognized_symbols'], flush=True)
    paths = [Path(__file__), DEVELOPMENT,
             HERE / 'receiver_mask04_protocol_preamble.py',
             HERE / 'receiver_mask04_rotated_codebook.py',
             HERE / 'reference_modem.py', MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(experiment='four-bit frozen phase readout across carrier rotations',
                  rule=dict(inputs='row0 Y0, Y1, Y3 and 3F8 Y7 at ADC visit 47',
                            phase_by_input={f'{key:04b}': value
                                            for key, value in PHASE_BY_INPUT.items()},
                            absent_inputs='unknown',
                            differential='(phase[current] - phase[previous] - 2) mod 4'),
                  fixture=dict(mapping='joint upper-source mask 04',
                               adc='complementary PCM, 47/46 visits per sample',
                               degrees=DEGREES, fresh_seeds=SEEDS,
                               preamble_symbols=PREAMBLE_SYMBOLS,
                               data_symbols=DATA_SYMBOLS,
                               capture_visit=PHASE_VISIT,
                               development_label_offsets=DEVELOPMENT_OFFSETS),
                  development_cases=development_rows, fresh_cases=fresh,
                  fresh_aggregate=dict(checks=sum(row['score']['checks'] for row in fresh),
                                       errors=sum(row['score']['errors'] for row in fresh),
                                       unknown=sum(row['score']['unknown'] for row in fresh)),
                  limitations=['The four-input table was fitted to existing executed traces using reference phase labels and rotation-specific development offsets.',
                               'The input latches, four-input logic, symbol clock, phase register, serial output and USART RxD route are external hypotheses.',
                               'Only the declared carrier rotations and reference amplitude are tested; this is not proof of a physical receive circuit.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
