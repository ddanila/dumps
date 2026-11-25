"""Validate a frozen three-bit, two-visit receive phase decoder."""

import hashlib
import json
import random
from pathlib import Path

from receiver_mask04_multivisit_capture import (HERE, DATA_SYMBOLS,
                                                MAPPINGS, candidate, capture,
                                                fixture, mapped,
                                                mapping_with_upper_source)
from reference_modem import QUADRANT_TO_DIBIT
from common import save

DEVELOPMENT = HERE / 'results/receiver-mask04-multivisit-capture.json'
SEED = 0xE217
DEGREES = (0, 15, 30, 45, 60, 75, 90, 105, 120, 135, 150, 165, 180)


def phase(symbol):
    first = symbol['visits']['47']['y3f8']
    second = symbol['visits']['94']['y3f8']
    a = (first >> 6) & 1
    b = (first >> 7) & 1
    c = (second >> 7) & 1
    return 2 * c + int(a == b == c)


def score(symbols):
    phases = [phase(symbol) for symbol in symbols]
    dibits = [None] + [QUADRANT_TO_DIBIT[(after - before - 2) & 3]
                       for before, after in zip(phases, phases[1:])]
    expected = [symbol['dibit'] for symbol in symbols]
    return dict(checks=len(symbols) - 1,
                errors=sum(actual != want for actual, want in
                           zip(dibits[1:], expected[1:])),
                preamble_errors=sum(dibits[index] != 3
                                    for index in range(1, 32)),
                data_errors=sum(dibits[index] != expected[index]
                                for index in range(32, len(symbols))),
                phases=phases, dibits=dibits)


def run(out=HERE / 'results/receiver-mask04-three-bit-two-visit.json'):
    development = json.loads(DEVELOPMENT.read_text())['cases']
    development_rows = []
    for case in development:
        result = score(case['symbols'])
        if result['errors']:
            raise ValueError(('frozen decoder lost development case',
                              case['degrees']))
        development_rows.append(dict(degrees=case['degrees'],
                                     trace_digest=case['trace_digest'],
                                     score=result))
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    generator = random.Random(SEED)
    middle = [generator.randrange(4) for _ in range(DATA_SYMBOLS)]
    fresh = []
    for degrees in DEGREES:
        case = capture(mapping, base, degrees, middle)
        result = score(case['symbols'])
        fresh.append(dict(degrees=degrees, seed=SEED,
                          trace_digest=case['trace_digest'],
                          adc_stream_sha256=case['adc_stream_sha256'],
                          gate_edges=case['gate_edges'],
                          first_visit_y=[symbol['visits']['47']['y3f8']
                                         for symbol in case['symbols']],
                          second_visit_y=[symbol['visits']['94']['y3f8']
                                          for symbol in case['symbols']],
                          expected_dibits=[symbol['dibit']
                                           for symbol in case['symbols']],
                          score=result))
        print('captured', degrees, 'errors', result['errors'],
              'preamble', result['preamble_errors'],
              'data', result['data_errors'], flush=True)
    paths = [Path(__file__), DEVELOPMENT,
             HERE / 'receiver_mask04_multivisit_capture.py',
             HERE / 'receiver_mask04_protocol_preamble.py',
             HERE / 'reference_modem.py', MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(experiment='frozen three-bit two-visit phase readout on continuous receive streams',
                  rule=dict(inputs=['3F8 Y6 at visit 47', '3F8 Y7 at visit 47',
                                    '3F8 Y7 at visit 94'],
                            phase_high='visit94.Y7',
                            phase_low='1 iff all three input bits agree',
                            differential='(phase[current] - phase[previous] - 2) mod 4'),
                  fixture=dict(mapping='joint upper-source mask 04',
                               adc='complementary PCM, 47/46 visits per sample',
                               preamble_symbols=32, data_symbols=DATA_SYMBOLS,
                               fresh_seed=SEED, degrees=DEGREES),
                  development_cases=development_rows,
                  fresh_cases=fresh,
                  fresh_aggregate=dict(checks=sum(row['score']['checks'] for row in fresh),
                                       errors=sum(row['score']['errors'] for row in fresh),
                                       preamble_errors=sum(row['score']['preamble_errors'] for row in fresh),
                                       data_errors=sum(row['score']['data_errors'] for row in fresh)),
                  limitations=['The three-bit rule was derived from inspected intermediate-angle traces; only the new seed is independent validation.',
                               'Two symbol-relative capture visits, two-bit phase storage, differential arithmetic, bit serialization and USART RxD are external circuit hypotheses.',
                               'The ADC path and symbol timing are assumed; noise, gain change and arbitrary continuous carrier phase are not established by this angle grid.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
