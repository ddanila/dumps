"""Freeze a two-visit, four-bit direct dibit transition readout."""

import hashlib
import json
import random
from pathlib import Path

from receiver_mask04_multivisit_capture import (HERE, DATA_SYMBOLS, MAPPINGS,
                                                candidate, capture, fixture,
                                                mapped,
                                                mapping_with_upper_source)
from common import save

INTERMEDIATE = HERE / 'results/receiver-mask04-multivisit-capture.json'
GRID = HERE / 'results/receiver-mask04-three-bit-two-visit.json'
SEED = 0x6F0D
DEGREES = (0, 15, 30, 45, 60, 75, 90, 105, 120, 135, 150, 165, 180)


def state(first_y, second_y):
    return ((first_y >> 6) & 3) | (((second_y >> 6) & 3) << 2)


def states_from_symbols(symbols):
    return [state(s['visits']['47']['y3f8'], s['visits']['94']['y3f8'])
            for s in symbols]


def transitions(states):
    return [(before << 4) | after
            for before, after in zip(states, states[1:])]


def score(table, states, expected):
    observed = [table.get(key) for key in transitions(states)]
    return dict(checks=len(observed),
                errors=sum(actual is not None and actual != want
                           for actual, want in zip(observed, expected[1:])),
                unknown=sum(actual is None for actual in observed),
                data_errors=sum(actual is not None and actual != want
                                for actual, want in zip(observed[31:], expected[32:])),
                data_unknown=sum(actual is None for actual in observed[31:]),
                dibits=[None] + observed)


def run(out=HERE / 'results/receiver-mask04-four-bit-transition.json'):
    development = json.loads(INTERMEDIATE.read_text())['cases']
    grid = json.loads(GRID.read_text())['fresh_cases']
    table = {}
    for case in development:
        states = states_from_symbols(case['symbols'])
        expected = [s['dibit'] for s in case['symbols']]
        for key, dibit in zip(transitions(states), expected[1:]):
            if key in table and table[key] != dibit:
                raise ValueError(('intermediate transition conflict', key))
            table[key] = dibit
    for case in grid:
        states = [state(a, b) for a, b in
                  zip(case['first_visit_y'], case['second_visit_y'])]
        for key, dibit in zip(transitions(states), case['expected_dibits'][1:]):
            if key in table and table[key] != dibit:
                raise ValueError(('grid transition conflict', key))
            table[key] = dibit
    if len(table) != 86:
        raise ValueError('development transition count changed')
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    generator = random.Random(SEED)
    middle = [generator.randrange(4) for _ in range(DATA_SYMBOLS)]
    fresh = []
    for degrees in DEGREES:
        case = capture(mapping, base, degrees, middle)
        states = states_from_symbols(case['symbols'])
        expected = [s['dibit'] for s in case['symbols']]
        result = score(table, states, expected)
        fresh.append(dict(degrees=degrees, seed=SEED,
                          trace_digest=case['trace_digest'],
                          adc_stream_sha256=case['adc_stream_sha256'],
                          gate_edges=case['gate_edges'],
                          states=states, expected_dibits=expected,
                          score=result))
        print('captured', degrees, 'errors', result['errors'],
              'unknown', result['unknown'],
              'data', result['data_errors'], result['data_unknown'], flush=True)
    paths = [Path(__file__), INTERMEDIATE, GRID,
             HERE / 'receiver_mask04_multivisit_capture.py',
             HERE / 'receiver_mask04_protocol_preamble.py', MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(experiment='frozen four-bit two-visit transition readout on fresh receive streams',
                  rule=dict(state='visit47 Y6/Y7 in bits0/1, visit94 Y6/Y7 in bits2/3',
                            transition='(previous_state << 4) | current_state',
                            observed_development_transitions=len(table),
                            table={f'{key:02X}': value for key, value in sorted(table.items())}),
                  fixture=dict(mapping='joint upper-source mask 04',
                               adc='complementary PCM, 47/46 visits per sample',
                               preamble_symbols=32, data_symbols=DATA_SYMBOLS,
                               development_cases=len(development) + len(grid),
                               fresh_seed=SEED, degrees=DEGREES),
                  fresh_cases=fresh,
                  fresh_aggregate=dict(checks=sum(row['score']['checks'] for row in fresh),
                                       errors=sum(row['score']['errors'] for row in fresh),
                                       unknown=sum(row['score']['unknown'] for row in fresh),
                                       data_errors=sum(row['score']['data_errors'] for row in fresh),
                                       data_unknown=sum(row['score']['data_unknown'] for row in fresh)),
                  limitations=['The 86-entry transition table was fitted to inspected real-PROM traces, including the earlier fresh-seed challenge; only the new seed is independent validation.',
                               'The table, two-visit latches, symbol memory, bit serializer and USART RxD route are external hypotheses, not identified physical logic.',
                               'Unknown transition keys stay unknown rather than receiving fabricated bits.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
