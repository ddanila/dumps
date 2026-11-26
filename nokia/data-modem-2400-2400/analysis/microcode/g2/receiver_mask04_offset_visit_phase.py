"""Test adjacent capture-clock phases with frozen receive decision tables."""

import hashlib
import random
import sys
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
import receiver_mask04_multivisit_capture as capture_module
from receiver_mask04_dual_feature_consensus import consensus, decisions, metrics
from receiver_mask04_dual_zero_handoff import frozen_tables
from receiver_mask04_feature_choice import alternative_states
from receiver_mask04_four_bit_transition import states_from_symbols
from receiver_mask04_frequency_offset import offset_transmit

SEED = 0xC41E
OFFSETS_HZ = (-7, 0, 7)
DEGREES = (75, 165)
VISIT_PAIRS = ((46, 93), (47, 94), (48, 95))
CAPTURE_PHASES = tuple(sorted(set(phase for pair in VISIT_PAIRS
                                  for phase in pair)))


def project(symbols, first, second):
    return [dict(dibit=symbol['dibit'], visits={
        '47': symbol['visits'][str(first)],
        '94': symbol['visits'][str(second)]}) for symbol in symbols]


def run(out=HERE / 'results/receiver-mask04-offset-visit-phase.json'):
    generator = random.Random(SEED)
    middle = [generator.randrange(4)
              for _ in range(capture_module.DATA_SYMBOLS)]
    primary, alternative = frozen_tables()
    mapping = capture_module.candidate(
        capture_module.mapping_with_upper_source(0, '17.6'),
        capture_module.mapped(capture_module.MAPPINGS['q3']), 4)
    _, base = capture_module.fixture()
    cases = []
    for offset_hz in OFFSETS_HZ:
        for degrees in DEGREES:
            with patch.object(capture_module, 'PHASES', CAPTURE_PHASES), \
                    patch.object(capture_module, 'rotated_transmit',
                                 lambda values, angle: offset_transmit(
                                     values, angle, offset_hz)):
                trace = capture_module.capture(mapping, base, degrees, middle)
            variants = []
            for first, second in VISIT_PAIRS:
                symbols = project(trace['symbols'], first, second)
                expected = [symbol['dibit'] for symbol in symbols]
                p = decisions(states_from_symbols(symbols), primary)
                a = decisions(alternative_states(symbols), alternative)
                both = consensus(p, a)
                variants.append(dict(visits=[first, second],
                                     primary=metrics(p, expected),
                                     alternative=metrics(a, expected),
                                     consensus=metrics(both, expected),
                                     conflicts=sum(x is not None and
                                                   y is not None and x != y
                                                   for x, y in zip(p[1:], a[1:]))))
            cases.append(dict(offset_hz=offset_hz, degrees=degrees,
                              trace_digest=trace['trace_digest'],
                              adc_stream_sha256=trace['adc_stream_sha256'],
                              variants=variants))
            print(offset_hz, degrees,
                  [(row['visits'], row['consensus']) for row in variants],
                  flush=True)
    summary = {}
    for first, second in VISIT_PAIRS:
        key = f'{first}/{second}'
        summary[key] = {}
        for offset_hz in OFFSETS_HZ:
            rows = [next(v for v in case['variants']
                         if v['visits'] == [first, second])
                    for case in cases if case['offset_hz'] == offset_hz]
            summary[key][str(offset_hz)] = dict(
                checks=sum(row['consensus']['checks'] for row in rows),
                errors=sum(row['consensus']['errors'] for row in rows),
                unknown=sum(row['consensus']['unknown'] for row in rows),
                data_errors=sum(row['consensus']['data_errors'] for row in rows),
                data_unknown=sum(row['consensus']['data_unknown'] for row in rows),
                conflicts=sum(row['conflicts'] for row in rows))
    paths = [Path(__file__),
             HERE / 'receiver_mask04_frequency_offset.py',
             HERE / 'receiver_mask04_multivisit_capture.py',
             HERE / 'receiver_mask04_dual_feature_consensus.py',
             HERE / 'receiver_mask04_dual_zero_handoff.py',
             HERE / 'receiver_mask04_feature_choice.py',
             HERE / 'receiver_mask04_four_bit_transition.py',
             HERE / 'results/receiver-mask04-four-bit-transition.json',
             HERE / 'results/receiver-mask04-feature-choice.json',
             capture_module.MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(experiment='frozen receive readout at adjacent assumed capture phases',
                  fixture=dict(seed=SEED, data_dibits=middle,
                               degrees=DEGREES, offsets_hz=OFFSETS_HZ,
                               visit_pairs=VISIT_PAIRS,
                               mapping='joint upper-source mask 04',
                               adc='complementary PCM, 47/46 visits per sample'),
                  cases=cases, summary=summary,
                  limitations=[
                      'The decision tables are frozen; the adjacent clock phases are exploratory alternatives, not established latch edges.',
                      'Each case uses an explicit ADC and symbol-clock fixture; no physical receive or USART path is established.',
                      'A zero-error variant on this seed does not establish arbitrary carrier-offset tolerance.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    print(run()['summary'])
