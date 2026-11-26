"""Screen one extra two-visit Y bit for a compact receive transition rule."""

import hashlib
import itertools
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save

DEVELOPMENT = HERE / 'results/receiver-mask04-multivisit-capture.json'
INDEPENDENT = HERE / 'results/receiver-mask04-three-bit-two-visit.json'
EXTRA_BITS = (('visit47_Y4', 0, 4), ('visit47_Y5', 0, 5),
              ('visit94_Y4', 1, 4), ('visit94_Y5', 1, 5))


def streams(report, kind):
    cases = report['cases'] if kind == 'symbols' else report['fresh_cases']
    for case in cases:
        if kind == 'symbols':
            symbols = case['symbols']
            first = [item['visits']['47']['y3f8'] for item in symbols]
            second = [item['visits']['94']['y3f8'] for item in symbols]
            expected = [item['dibit'] for item in symbols]
        else:
            first = case['first_visit_y']
            second = case['second_visit_y']
            expected = case['expected_dibits']
        if len(first) != 48 or len(second) != 48 or len(expected) != 48:
            raise ValueError(('receive trace length changed', case['degrees']))
        yield dict(degrees=case['degrees'], first=first, second=second,
                   expected=expected, trace_digest=case['trace_digest'])


def state(first, second, extra):
    result = ((first >> 6) & 3) | (((second >> 6) & 3) << 2)
    if extra is not None:
        _, visit, bit = extra
        result |= (((first if visit == 0 else second) >> bit) & 1) << 4
    return result


def transitions(case, extra):
    states = [state(first, second, extra)
              for first, second in zip(case['first'], case['second'])]
    bits = 4 if extra is None else 5
    return [((before << bits) | after, expected)
            for before, after, expected in
            zip(states, states[1:], case['expected'][1:])]


def table_from(cases, extra):
    table = {}
    for case in cases:
        for key, dibit in transitions(case, extra):
            if key in table and table[key] != dibit:
                raise ValueError(('same-key decision collision', key))
            table[key] = dibit
    return table


def fit(table, bits, degree):
    terms = [sum(1 << bit for bit in subset)
             for size in range(degree + 1)
             for subset in itertools.combinations(range(bits), size)]
    width = len(terms)
    coefficient_mask = (1 << width) - 1
    basis = {}
    contradictions = []

    def features(key):
        return sum(1 << index for index, mask in enumerate(terms)
                   if key & mask == mask)

    def reduce(row):
        for pivot in sorted(basis, reverse=True):
            if row & (1 << pivot):
                row ^= basis[pivot]
        return row

    for key, dibit in sorted(table.items()):
        row = reduce(features(key) | (dibit << width))
        coefficients = row & coefficient_mask
        if coefficients:
            basis[coefficients.bit_length() - 1] = row
        elif row >> width:
            contradictions.append(key)

    def predict(key):
        if key in table:
            return table[key]
        row = reduce(features(key))
        return (row >> width) & 3 if not row & coefficient_mask else None

    return dict(terms=len(terms), rank=len(basis),
                contradictions=contradictions), predict


def score(cases, extra, predict):
    result = dict(checks=0, wrong=0, unknown=0, data_wrong=0,
                  data_unknown=0)
    for case in cases:
        for index, (key, wanted) in enumerate(transitions(case, extra)):
            got = predict(key)
            result['checks'] += 1
            if got is None:
                result['unknown'] += 1
                result['data_unknown'] += index >= 31
            elif got != wanted:
                result['wrong'] += 1
                result['data_wrong'] += index >= 31
    return result


def run(out=HERE / 'results/receiver-mask04-extra-capture-bit-screen.json'):
    development = json.loads(DEVELOPMENT.read_text())
    independent = json.loads(INDEPENDENT.read_text())
    if (development['fixture']['seed'] != 29292 or
            independent['fixture']['fresh_seed'] != 57879):
        raise ValueError('independent receive seeds changed')
    training = list(streams(development, 'symbols'))
    holdout = list(streams(independent, 'arrays'))
    if any((value & 0x0F) != 0x0F
           for case in [*training, *holdout]
           for value in [*case['first'], *case['second']]):
        raise ValueError('captured Y0-Y3 are no longer constant ones')
    rows = []
    for extra in (None, *EXTRA_BITS):
        name = 'Y6/Y7 at visits 47 and 94' if extra is None else extra[0]
        width = 8 if extra is None else 10
        early = table_from(training, extra)
        cubic, predictor = fit(early, width, 3)
        combined = table_from([*training, *holdout], extra)
        quadratic, _ = fit(combined, width, 2)
        result = score(holdout, extra, predictor)
        if cubic['contradictions'] or result['wrong']:
            raise ValueError(('held-out receive feature changed', name))
        rows.append(dict(feature=name,
                         extra_bit=None if extra is None else
                         dict(visit=47 if extra[1] == 0 else 94,
                              y_bit=extra[2]),
                         training_keys=len(early),
                         training_cubic=cubic,
                         independent=result,
                         combined_keys=len(combined),
                         combined_quadratic=quadratic))
        print(name, 'keys', len(early), 'independent', result,
              'combined quadratic contradictions',
              len(quadratic['contradictions']), flush=True)
    baseline = rows[0]['independent']['unknown']
    if (baseline != 84 or any(row['independent']['unknown'] <= baseline
                              for row in rows[1:])):
        raise ValueError('one-extra-bit coverage conclusion changed')
    sources = [Path(__file__), DEVELOPMENT, INDEPENDENT,
               HERE / 'receiver_mask04_multivisit_capture.py',
               HERE / 'receiver_mask04_three_bit_two_visit.py',
               HERE / 'receiver_mask04_four_bit_transition.py']
    report = dict(experiment='one-extra-bit receiver transition screen on saved real-PROM captures',
                  fixture=dict(training_seed=development['fixture']['seed'],
                               independent_seed=independent['fixture']['fresh_seed'],
                               training_traces=[case['trace_digest'] for case in training],
                               independent_traces=[case['trace_digest'] for case in holdout],
                               state='Y6/Y7 at visits 47 and 94; optional fifth Y bit',
                               transition='previous/current 4- or 5-bit state',
                               independent_checks=611),
                  rows=rows,
                  limitations=[
                      'This reanalysis uses saved executed PROM captures; it does not run new microinstructions.',
                      'The four-bit and five-bit states are external capture hypotheses, not identified Nokia latches or receive decisions.',
                      'The combined quadratic screen includes the independent traces and is only a structural description, not a held-out score.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
