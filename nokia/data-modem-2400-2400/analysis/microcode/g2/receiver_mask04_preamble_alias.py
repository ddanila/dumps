"""Test whether preamble phase-47 bytes distinguish 45 from 180 degrees."""

import hashlib
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from receiver_mask04_protocol_preamble import (DATA_SYMBOLS,
                                               PREAMBLE_SYMBOLS, candidate,
                                               capture, fixture, mapped,
                                               mapping_with_upper_source,
                                               MAPPINGS)
from receiver_mask04_preamble_selector import analyze

SEED = 0x72A1
ANGLES = (45, 180)


def preamble_rows(case):
    return [dict(row0=row['row0']['y'], row3=row['row3']['y'],
                 y3f8=row['at_3f8']['y'])
            for row in case['symbols'][:PREAMBLE_SYMBOLS]]


def run(out=HERE / 'results/receiver-mask04-preamble-alias.json'):
    generator = random.Random(SEED)
    middle = [generator.randrange(4) for _ in range(DATA_SYMBOLS)]
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    cases = []
    for degrees in ANGLES:
        raw = capture(mapping, base, degrees, SEED, middle)
        analyzed = analyze(raw)
        cases.append(dict(degrees=degrees, preamble=preamble_rows(raw),
                          nominal_data=analyzed['nominal_data'],
                          diagonal_data=analyzed['diagonal_data'],
                          trace_digest=raw['trace_digest'],
                          adc_stream_sha256=raw['adc_stream_sha256'],
                          selected_y_sha256=raw['edge_captured_sha256']))
        print('captured', degrees, flush=True)
    first, second = cases
    identical = first['preamble'] == second['preamble']
    if not identical:
        raise ValueError('phase-47 preamble alias changed')
    if (first['nominal_data']['errors'] == 0 or
            first['diagonal_data']['errors'] != 0 or
            first['diagonal_data']['unknown'] != 0 or
            second['nominal_data']['errors'] != 0 or
            second['nominal_data']['unknown'] != 0 or
            second['diagonal_data']['unknown'] == 0):
        raise ValueError('contrasting data readouts changed')
    paths = [Path(__file__),
             HERE / 'receiver_mask04_preamble_selector.py',
             HERE / 'receiver_mask04_protocol_preamble.py',
             HERE / 'receiver_mask04_phase47_logic.py',
             HERE / 'receiver_mask04_two_visit_rule.py',
             HERE / 'reference_modem.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(experiment='phase-47 preamble capture alias versus data readout',
                  fixture=dict(seed=SEED, angles=ANGLES,
                               preamble_symbols=PREAMBLE_SYMBOLS,
                               capture_visit=47,
                               bytes=['3ED row0 Y', '3ED row3 Y', '3F8 Y']),
                  cases=cases,
                  preamble_triples_identical=identical,
                  distinct_preamble_triples=sorted({(row['row0'], row['row3'], row['y3f8'])
                                                   for row in first['preamble']}),
                  limitations=[
                      'The impossibility conclusion applies only to these three bytes at fixed ADC visit 47, not other receive visits, raw ADC samples or hidden circuit state.',
                      'Nominal and diagonal readouts are external diagnostics; this comparison does not identify a physical selector or USART route.',
                      'The reference line waveform and complementary ADC path remain assumptions.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    print(run()['distinct_preamble_triples'])
