"""Measure how much the six surviving DAC orders differ on joined PROM output."""

import hashlib
import itertools
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from photo_127_liveness import ROM
from photo_dac_bus_permutations import mapped_codes
from photo_joint_line_filter_screen import BUSES, JOINT, TXREADY, joined_codes


def run(out=HERE / 'results/photo-dac-survivor-equivalence.json'):
    buses = json.loads(BUSES.read_text())['zero_error_survivors']
    if len(buses) != 6 or len({tuple(bus) for bus in buses}) != 6:
        raise ValueError('expected six distinct DAC orders')
    common = {source: buses[0][source] for source in (0, 2, 4, 6, 7)}
    if any(any(bus[source] != bit for source, bit in common.items()) or
           set(bus[source] for source in (1, 3, 5)) != {0, 1, 2}
           for bus in buses):
        raise ValueError('surviving bus family changed')

    txready = json.loads(TXREADY.read_text())
    joint = json.loads(JOINT.read_text())
    cases = []
    for selector in ('40', '60'):
        tx_case = next(row for row in txready['cases']
                       if row['selector'] == selector)
        joint_case = next(row for row in joint['cases']
                          if row['selector'] == selector)
        raw, _ = joined_codes(ROM.read_bytes(), tx_case, joint_case)
        codes = [mapped_codes(raw, bus) for bus in buses]
        if any(any((a >> 3) != (b >> 3) for a, b in zip(codes[0], other))
               for other in codes[1:]):
            raise ValueError('upper five DAC bits diverge')
        pairs = []
        for a, b in itertools.combinations(range(6), 2):
            difference = [x - y for x, y in zip(codes[a], codes[b])]
            pairs.append(dict(bus_a=a, bus_b=b,
                              max_abs_code_difference=max(map(abs, difference)),
                              rms_code_difference=round(math.sqrt(sum(d * d for d in difference)
                                                                  / len(difference)), 6),
                              different_samples=sum(d != 0 for d in difference)))
        cases.append(dict(selector=selector, joined_samples=len(raw),
                          ordered_y_sha256=hashlib.sha256(bytes(raw)).hexdigest(),
                          upper_five_bit_sha256=hashlib.sha256(
                              bytes(value >> 3 for value in codes[0])).hexdigest(),
                          max_difference_any_pair=max(row['max_abs_code_difference']
                                                      for row in pairs),
                          pairwise_differences=pairs))

    sources = (Path(__file__), BUSES, JOINT, TXREADY, ROM,
               HERE / 'photo_dac_bus_permutations.py',
               HERE / 'photo_joint_line_filter_screen.py',
               HERE / 'photo_joint_tone_training_data.py')
    report = dict(experiment='equivalence of six photo-compatible DAC bus orders on PROM-verified joined transmitter samples',
                  fixture=dict(input='actual GPC/GPA controller A1-A4 stream',
                               dac_bus='ordered Y to LS273 D is assumed; Q4 to DAC B5 is photo-suggested',
                               shared_source_to_code_bits=common,
                               permuted_source_bits=[1, 3, 5],
                               permuted_dac_code_bits=[0, 1, 2],
                               code_full_scale=255),
                  cases=cases,
                  limitations=['Only the previously verified Y129 candidate sample recurrence is tested; no DAC or line capture is measured.',
                               'A shared five-bit code does not prove those five physical wires.',
                               'Distinguishing the remaining six orders requires low-bit wiring or sufficiently precise independent analog data.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    save(out, report)
    return report


if __name__ == '__main__':
    for case in run()['cases']:
        print(case['selector'], case['joined_samples'], case['max_difference_any_pair'])
