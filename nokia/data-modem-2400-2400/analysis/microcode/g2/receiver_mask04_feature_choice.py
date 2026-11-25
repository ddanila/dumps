"""Compare the two minimum four-bit receive features on fresh PROM streams."""

import hashlib
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from receiver_mask04_cubic_transition import fit, forced_prediction
from receiver_mask04_four_bit_transition import score, states_from_symbols
from receiver_mask04_multivisit_capture import (DATA_SYMBOLS, MAPPINGS,
                                                candidate, capture, fixture,
                                                mapped,
                                                mapping_with_upper_source)

INTERMEDIATE = HERE / 'results/receiver-mask04-multivisit-capture.json'
GRID = HERE / 'results/receiver-mask04-three-bit-two-visit.json'
PRIMARY = HERE / 'results/receiver-mask04-four-bit-transition.json'
SEED = 0xD2A9
DEGREES = (0, 45, 75, 165)


def alternative_state(first, second):
    return ((first >> 5) & 7) | (((second >> 7) & 1) << 3)


def alternative_states(symbols):
    return [alternative_state(symbol['visits']['47']['y3f8'],
                              symbol['visits']['94']['y3f8'])
            for symbol in symbols]


def add_case(table, states, expected):
    for before, after, value in zip(states, states[1:], expected[1:]):
        key = (before << 4) | after
        if key in table and table[key] != value:
            raise ValueError(('alternative-state label collision', key))
        table[key] = value


def development_table():
    table = {}
    intermediate = json.loads(INTERMEDIATE.read_text())['cases']
    grid = json.loads(GRID.read_text())['fresh_cases']
    for case in intermediate:
        symbols = case['symbols']
        add_case(table, alternative_states(symbols),
                 [symbol['dibit'] for symbol in symbols])
    for case in grid:
        states = [alternative_state(a, b) for a, b in
                  zip(case['first_visit_y'], case['second_visit_y'])]
        add_case(table, states, case['expected_dibits'])
    return table


def metrics(result):
    return {name: result[name] for name in
            ('checks', 'errors', 'unknown', 'data_errors', 'data_unknown')}


def run(out=HERE / 'results/receiver-mask04-feature-choice.json'):
    alternative = development_table()
    primary_source = json.loads(PRIMARY.read_text())
    primary = {int(key, 16): value for key, value in
               primary_source['rule']['table'].items()}
    if len(alternative) != 91 or len(primary) != 86:
        raise ValueError('development tables changed')
    alt_terms, alt_basis, alt_conflicts = fit(alternative, 3)
    terms, basis, conflicts = fit(primary, 3)
    if not alt_conflicts or conflicts:
        raise ValueError('expected only primary cubic fit')
    primary_forced = {**primary, **{key: value for key in range(256)
                                    if key not in primary and
                                    (value := forced_prediction(key, terms, basis))
                                    is not None}}
    generator = random.Random(SEED)
    data = [generator.randrange(4) for _ in range(DATA_SYMBOLS)]
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    cases = []
    for degrees in DEGREES:
        case = capture(mapping, base, degrees, data)
        symbols = case['symbols']
        expected = [symbol['dibit'] for symbol in symbols]
        primary_states = states_from_symbols(symbols)
        alternative_capture = alternative_states(symbols)
        row = dict(degrees=degrees, trace_digest=case['trace_digest'],
                   adc_stream_sha256=case['adc_stream_sha256'],
                   primary_cubic=metrics(score(primary_forced, primary_states, expected)),
                   alternative_lookup=metrics(score(alternative, alternative_capture,
                                                    expected)))
        cases.append(row)
        print(degrees, row['primary_cubic'], row['alternative_lookup'], flush=True)
    aggregate = {name: dict(checks=sum(row[name]['checks'] for row in cases),
                            errors=sum(row[name]['errors'] for row in cases),
                            unknown=sum(row[name]['unknown'] for row in cases),
                            data_errors=sum(row[name]['data_errors'] for row in cases),
                            data_unknown=sum(row[name]['data_unknown'] for row in cases))
                 for name in ('primary_cubic', 'alternative_lookup')}
    paths = [Path(__file__), INTERMEDIATE, GRID, PRIMARY,
             HERE / 'receiver_mask04_cubic_transition.py',
             HERE / 'receiver_mask04_four_bit_transition.py',
             HERE / 'receiver_mask04_multivisit_capture.py',
             HERE / 'receiver_mask04_protocol_preamble.py',
             MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(experiment='fresh real-PROM comparison of two four-bit two-visit receive features',
                  fixture=dict(seed=SEED, degrees=DEGREES, data_dibits=data,
                               mapping='joint upper-source mask 04',
                               adc='complementary PCM, 47/46 visits per sample'),
                  development=dict(primary_keys=len(primary),
                                   alternative_keys=len(alternative),
                                   primary_cubic_rank=len(basis),
                                   alternative_cubic_rank=len(alt_basis),
                                   alternative_cubic_contradictions=len(alt_conflicts),
                                   primary_terms=len(terms),
                                   alternative_terms=len(alt_terms)),
                  cases=cases, aggregate=aggregate,
                  limitations=[
                      'The alternative feature was one of two minimum collision-free subsets found in the earlier development audit; this comparison is a new seed, not a physical circuit identification.',
                      'Unknown transition keys remain unknown; no held-out reference labels are added to either development table.',
                      'The two capture visits, symbol memory, clock and USART route are board hypotheses.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    print(run()['aggregate'])
