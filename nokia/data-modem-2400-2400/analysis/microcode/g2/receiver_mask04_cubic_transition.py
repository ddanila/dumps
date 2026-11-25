"""Extend the frozen two-visit transition table only where cubic algebra forces it."""

import hashlib
import itertools
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from receiver_mask04_four_bit_transition import score, states_from_symbols
from receiver_mask04_multivisit_capture import (DATA_SYMBOLS, MAPPINGS,
                                                candidate, capture, fixture,
                                                mapped,
                                                mapping_with_upper_source)

SOURCE = HERE / 'results/receiver-mask04-four-bit-transition.json'
NEW_SEED = 0xC4E1
NEW_ANGLES = (0, 75, 165)


def monomials(degree):
    return [sum(1 << bit for bit in subset)
            for size in range(degree + 1)
            for subset in itertools.combinations(range(8), size)]


def features(key, terms):
    return sum(1 << index for index, mask in enumerate(terms)
               if key & mask == mask)


def reduce(row, basis):
    for pivot in sorted(basis, reverse=True):
        if row & (1 << pivot):
            row ^= basis[pivot]
    return row


def fit(table, degree):
    terms = monomials(degree)
    width = len(terms)
    feature_mask = (1 << width) - 1
    basis = {}
    contradictions = []
    for key, dibit in sorted(table.items()):
        row = reduce(features(key, terms) | (dibit << width), basis)
        coefficients = row & feature_mask
        if not coefficients:
            if row >> width:
                contradictions.append(key)
        else:
            basis[coefficients.bit_length() - 1] = row
    return terms, basis, contradictions


def forced_prediction(key, terms, basis):
    row = reduce(features(key, terms), basis)
    return (row >> len(terms)) & 3 if row & ((1 << len(terms)) - 1) == 0 else None


def run(out=HERE / 'results/receiver-mask04-cubic-transition.json'):
    source = json.loads(SOURCE.read_text())
    table = {int(key, 16): value for key, value in source['rule']['table'].items()}
    if len(table) != 86 or source['fresh_aggregate'] != dict(
            checks=611, errors=0, unknown=5, data_errors=0, data_unknown=5):
        raise ValueError('frozen four-bit development or validation changed')
    quadratic_terms, quadratic_basis, quadratic_conflicts = fit(table, 2)
    cubic_terms, cubic_basis, cubic_conflicts = fit(table, 3)
    if not quadratic_conflicts or cubic_conflicts:
        raise ValueError('expected quadratic contradiction and cubic fit')
    extension = {key: forced_prediction(key, cubic_terms, cubic_basis)
                 for key in range(256) if key not in table}
    forced = {**table, **{key: value for key, value in extension.items()
                          if value is not None}}
    cases = []
    newly_seen = {}
    for case in source['fresh_cases']:
        states = case['states']
        expected = case['expected_dibits']
        baseline = case['score']
        result = score(forced, states, expected)
        if baseline['errors'] or result['errors'] or result['unknown'] > baseline['unknown']:
            raise ValueError(('cubic extension regression', case['degrees']))
        for index in range(1, len(states)):
            key = (states[index - 1] << 4) | states[index]
            if key not in table and key not in newly_seen:
                newly_seen[key] = dict(prediction=extension[key],
                                       observed=expected[index])
        cases.append(dict(degrees=case['degrees'], trace_digest=case['trace_digest'],
                          baseline=dict(checks=baseline['checks'],
                                        errors=baseline['errors'], unknown=baseline['unknown'],
                                        data_errors=baseline['data_errors'],
                                        data_unknown=baseline['data_unknown']),
                          cubic=dict(checks=result['checks'],
                                     errors=result['errors'], unknown=result['unknown'],
                                     data_errors=result['data_errors'],
                                     data_unknown=result['data_unknown'])))
    aggregate = dict(checks=sum(c['cubic']['checks'] for c in cases),
                     errors=sum(c['cubic']['errors'] for c in cases),
                     unknown=sum(c['cubic']['unknown'] for c in cases),
                     data_errors=sum(c['cubic']['data_errors'] for c in cases),
                     data_unknown=sum(c['cubic']['data_unknown'] for c in cases))
    generator = random.Random(NEW_SEED)
    middle = [generator.randrange(4) for _ in range(DATA_SYMBOLS)]
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    new_cases = []
    for degrees in NEW_ANGLES:
        capture_case = capture(mapping, base, degrees, middle)
        states = states_from_symbols(capture_case['symbols'])
        expected = [symbol['dibit'] for symbol in capture_case['symbols']]
        baseline = score(table, states, expected)
        result = score(forced, states, expected)
        row = dict(degrees=degrees, trace_digest=capture_case['trace_digest'],
                   adc_stream_sha256=capture_case['adc_stream_sha256'],
                   baseline=dict(checks=baseline['checks'], errors=baseline['errors'],
                                 unknown=baseline['unknown'],
                                 data_errors=baseline['data_errors'],
                                 data_unknown=baseline['data_unknown']),
                   cubic=dict(checks=result['checks'], errors=result['errors'],
                              unknown=result['unknown'],
                              data_errors=result['data_errors'],
                              data_unknown=result['data_unknown']))
        new_cases.append(row)
        print('new', degrees, row['baseline'], row['cubic'], flush=True)
    paths = [Path(__file__), SOURCE,
             HERE / 'receiver_mask04_four_bit_transition.py',
             HERE / 'receiver_mask04_multivisit_capture.py',
             HERE / 'receiver_mask04_protocol_preamble.py',
             MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(experiment='cubic Boolean implication of two-visit real-PROM transition keys',
                  fixture=dict(development_keys=len(table),
                               independent_cases=len(cases),
                               independent_seed=source['fixture']['fresh_seed'],
                               angles=source['fixture']['degrees']),
                  quadratic=dict(terms=len(quadratic_terms), rank=len(quadratic_basis),
                                 contradictory_keys=[f'{key:02X}' for key in quadratic_conflicts]),
                  cubic=dict(terms=len(cubic_terms), rank=len(cubic_basis),
                             contradictory_keys=cubic_conflicts,
                             forced_unseen_keys=sum(value is not None for value in extension.values()),
                             unconstrained_unseen_keys=sum(value is None for value in extension.values())),
                  independent_new_keys={f'{key:02X}': value
                                        for key, value in sorted(newly_seen.items())},
                  independent_cases=cases, independent_aggregate=aggregate,
                  new_seed=dict(seed=NEW_SEED, angles=NEW_ANGLES,
                                data_dibits=middle, cases=new_cases,
                                aggregate=dict(checks=sum(c['cubic']['checks'] for c in new_cases),
                                               errors=sum(c['cubic']['errors'] for c in new_cases),
                                               unknown=sum(c['cubic']['unknown'] for c in new_cases),
                                               data_errors=sum(c['cubic']['data_errors'] for c in new_cases),
                                               data_unknown=sum(c['cubic']['data_unknown'] for c in new_cases))),
                  limitations=[
                      'Degree three is a constraint on the observed four-bit transition table, not a recovered Nokia logic network.',
                      'Only predictions identical across every fitting cubic rule are emitted; other transitions remain unknown.',
                      'The two capture visits, symbol memory, serial clock and USART connection remain board hypotheses.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    print(run()['independent_aggregate'])
