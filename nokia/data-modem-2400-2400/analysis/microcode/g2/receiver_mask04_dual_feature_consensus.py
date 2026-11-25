"""Test two frozen four-bit readouts together on held-out real-PROM traces."""

import hashlib
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from receiver_mask04_cubic_transition import fit, forced_prediction
from receiver_mask04_feature_choice import alternative_states, development_table
from receiver_mask04_four_bit_transition import states_from_symbols
from receiver_mask04_multivisit_capture import (DATA_SYMBOLS, MAPPINGS,
                                                candidate, capture, fixture,
                                                mapped,
                                                mapping_with_upper_source)

PRIMARY = HERE / 'results/receiver-mask04-four-bit-transition.json'
ALTERNATIVE = HERE / 'results/receiver-mask04-feature-choice.json'


def decisions(states, table):
    return [None] + [table.get((before << 4) | after)
                    for before, after in zip(states, states[1:])]


def metrics(values, expected):
    return dict(checks=len(values) - 1,
                errors=sum(got is not None and got != want
                           for got, want in zip(values[1:], expected[1:])),
                unknown=sum(got is None for got in values[1:]),
                data_errors=sum(got is not None and got != want
                                for got, want in zip(values[32:], expected[32:])),
                data_unknown=sum(got is None for got in values[32:]))


def consensus(left, right):
    return [a if b is None or a == b else b if a is None else None
            for a, b in zip(left, right)]


def run(out=HERE / 'results/receiver-mask04-dual-feature-consensus.json'):
    source = json.loads(PRIMARY.read_text())
    alternative_report = json.loads(ALTERNATIVE.read_text())
    if (source['fixture']['fresh_seed'] != 0x6F0D or
            alternative_report['development']['alternative_keys'] != 91):
        raise ValueError('frozen receiver inputs changed')
    primary = {int(key, 16): value for key, value in
               source['rule']['table'].items()}
    terms, basis, contradictions = fit(primary, 3)
    if contradictions:
        raise ValueError('primary cubic fit changed')
    primary.update({key: value for key in range(256) if key not in primary
                    and (value := forced_prediction(key, terms, basis)) is not None})
    alternative = development_table()
    generator = random.Random(source['fixture']['fresh_seed'])
    data = [generator.randrange(4) for _ in range(DATA_SYMBOLS)]
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    cases = []
    rescued = {}
    for prior in source['fresh_cases']:
        case = capture(mapping, base, prior['degrees'], data)
        if (case['trace_digest'] != prior['trace_digest'] or
                case['adc_stream_sha256'] != prior['adc_stream_sha256']):
            raise ValueError(('held-out PROM trace changed', prior['degrees']))
        symbols = case['symbols']
        expected = [symbol['dibit'] for symbol in symbols]
        if expected != prior['expected_dibits']:
            raise ValueError('held-out dibits changed')
        p_states = states_from_symbols(symbols)
        a_states = alternative_states(symbols)
        p = decisions(p_states, primary)
        a = decisions(a_states, alternative)
        both = consensus(p, a)
        conflicts = sum(x is not None and y is not None and x != y
                        for x, y in zip(p[1:], a[1:]))
        for index in range(1, len(p)):
            if p[index] is None and a[index] is not None:
                p_key = (p_states[index - 1] << 4) | p_states[index]
                a_key = (a_states[index - 1] << 4) | a_states[index]
                rescued.setdefault(f'{p_key:02X}', []).append(
                    dict(degrees=prior['degrees'], symbol=index,
                         alternative_key=f'{a_key:02X}',
                         predicted=a[index], observed=expected[index]))
        row = dict(degrees=prior['degrees'], trace_digest=case['trace_digest'],
                   adc_stream_sha256=case['adc_stream_sha256'],
                   primary_cubic=metrics(p, expected),
                   alternative_lookup=metrics(a, expected),
                   consensus=metrics(both, expected), conflicts=conflicts)
        cases.append(row)
        print(row['degrees'], row['primary_cubic'], row['alternative_lookup'],
              row['consensus'], conflicts, flush=True)
    aggregate = {name: dict(checks=sum(row[name]['checks'] for row in cases),
                            errors=sum(row[name]['errors'] for row in cases),
                            unknown=sum(row[name]['unknown'] for row in cases),
                            data_errors=sum(row[name]['data_errors'] for row in cases),
                            data_unknown=sum(row[name]['data_unknown'] for row in cases))
                 for name in ('primary_cubic', 'alternative_lookup', 'consensus')}
    paths = [Path(__file__), PRIMARY, ALTERNATIVE,
             HERE / 'receiver_mask04_cubic_transition.py',
             HERE / 'receiver_mask04_feature_choice.py',
             HERE / 'receiver_mask04_four_bit_transition.py',
             HERE / 'receiver_mask04_multivisit_capture.py',
             HERE / 'receiver_mask04_protocol_preamble.py',
             MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(experiment='consensus of two frozen two-visit receiver readouts on 13 held-out real-PROM streams',
                  fixture=dict(seed=source['fixture']['fresh_seed'],
                               degrees=source['fixture']['degrees'],
                               data_dibits=data,
                               mapping='joint upper-source mask 04',
                               adc='complementary PCM, 47/46 visits per sample'),
                  rule='Use the shared label if both readouts know and agree; use the sole known label if only one knows; otherwise emit unknown.',
                  cases=cases, aggregate=aggregate,
                  rescued_primary_keys=rescued,
                  conflicts=sum(case['conflicts'] for case in cases),
                  limitations=[
                      'Both readouts are external hypotheses fitted to earlier real-PROM traces; the validation stream is held out from both tables.',
                      'These 13 rotations share one data sequence, so their decisions are not independent data streams.',
                      'Capture timing, combinational logic, symbol memory, serialization and USART RxD/RxC/SYNDET are not identified board connections.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    print(run()['aggregate'])
