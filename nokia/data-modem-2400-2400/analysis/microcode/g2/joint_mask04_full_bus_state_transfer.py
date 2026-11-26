"""Fit two fixed receive-state tables at zero offset; score shifted cases."""

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from receiver_mask04_long_pair_union import classify

SOURCE = HERE / 'results/joint-mask04-full-bus-receive-states.json'
PAIRS = ((46, 93), (47, 94))


def state(symbol, pair):
    first, second = pair
    a = symbol['visits'][str(first)]['y3f8']
    b = symbol['visits'][str(second)]['y3f8']
    return ((a >> 6) & 3) | (((b >> 6) & 3) << 2)


def transition_keys(symbols, pair):
    states = [state(symbol, pair) for symbol in symbols]
    return [None] + [(before << 4) | after
                    for before, after in zip(states, states[1:])]


def fit(cases, pair):
    table = {}
    conflicts = []
    for case in cases:
        expected = [symbol['dibit'] for symbol in case['symbols']]
        for index, key in enumerate(transition_keys(case['symbols'], pair)[1:], 1):
            if key in table and table[key] != expected[index]:
                conflicts.append(dict(selector=case['selector'],
                                      symbol=index, key=f'{key:02X}',
                                      earlier=table[key], current=expected[index]))
            else:
                table[key] = expected[index]
    return table, conflicts


def run(out=HERE / 'results/joint-mask04-full-bus-state-transfer.json'):
    source = json.loads(SOURCE.read_text())
    cases = source['cases']
    development = [case for case in cases if case['offset_hz'] == 0]
    evaluation = [case for case in cases if case['offset_hz'] != 0]
    if (len(development) != 2 or len(evaluation) != 4 or
            any(len(case['symbols']) != 65 for case in cases)):
        raise ValueError('state source changed')
    report = dict(
        experiment='zero-offset direct transition lookup transfer to shifted full-byte DSC streams',
        fixture=dict(source=SOURCE.name,
                     development='call and answer at zero carrier offset',
                     evaluation='same two payloads at ±7 Hz; not used for table fitting',
                     state='two high Y bits at each of two fixed 3F8 visits',
                     pairs=PAIRS,
                     decision='previous 4-bit state concatenated with current state'),
        pairs=[],
        limitations=[
            'The offset fixtures and pair family were already inspected in earlier work; this is an explicit transfer screen, not a blind holdout.',
            'Only two zero-offset payloads train each table, so sparse recognition is expected.',
            'The lookup, capture clocks and USART path are external hypotheses, not identified DSC instructions or photographed nets.',
            'The assumed DAC/ADC, AGC and analog line routes remain unresolved.'],
        source_sha256={str(path.relative_to(HERE.parents[4])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in (Path(__file__), SOURCE)})
    for pair in PAIRS:
        table, conflicts = fit(development, pair)
        if conflicts:
            raise ValueError(('zero-offset development label collision', pair, conflicts))
        rows = []
        for case in cases:
            expected = [symbol['dibit'] for symbol in case['symbols']]
            predictions = [table.get(key) if key is not None else None
                           for key in transition_keys(case['symbols'], pair)]
            line_data = dict(
                checks=len(expected[33:]),
                errors=sum(got is not None and got != want
                           for got, want in zip(predictions[33:], expected[33:])),
                unknown=sum(got is None for got in predictions[33:]))
            rows.append(dict(selector=case['selector'], offset_hz=case['offset_hz'],
                             rx_trace_digest=case['rx_trace_digest'],
                             adc_sha256=case['adc_sha256'],
                             score=classify(predictions, expected),
                             line_data_score=line_data))
        report['pairs'].append(dict(
            pair=pair, table_size=len(table),
            table={f'{key:02X}': value for key, value in sorted(table.items())},
            development_conflicts=conflicts, cases=rows))
        print(pair, 'keys', len(table),
              'shifted data errors/unknown',
              [(row['selector'], row['offset_hz'],
                row['line_data_score']['errors'],
                row['line_data_score']['unknown'])
               for row in rows if row['offset_hz'] != 0], flush=True)
    save(out, report)
    return report


if __name__ == '__main__':
    run()
