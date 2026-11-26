"""Measure A3 half-turns directly in executed candidate DAC MSB samples."""

import cmath
import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from joint_four_row_retention_tx import (MAPPINGS, candidate, fixture, mapped,
                                         mapping_with_upper_source)
from joint_mask04_free_clock_msb import (BUSES, EDGE, PRIOR, TXREADY, replay)
from photo_dac_bus_permutations import SELECTED, mapped_codes
from photo_joint_tone_training_data import SILENCE_SYMBOLS, TONE_SYMBOLS

SAMPLES_PER_SYMBOL = 8
SEGMENT_SYMBOLS = 32
SAMPLE_RATE_HZ = 9600
TONE_HZ = 2100
CARRIER_HZ = 1800


def symbol_phasors(codes, start, frequency):
    values = [((code & 0x80) - 64) for code in codes]
    output = []
    for symbol in range(SEGMENT_SYMBOLS):
        offset = (start + symbol) * SAMPLES_PER_SYMBOL
        output.append(sum(
            values[offset + index] * cmath.exp(
                -2j * math.pi * frequency * (offset + index) / SAMPLE_RATE_HZ)
            for index in range(SAMPLES_PER_SYMBOL)))
    if min(abs(value) for value in output) < 1:
        raise ValueError('candidate carrier phasor vanished')
    return output


def successive_angles(phasors):
    return [math.degrees(cmath.phase(current * previous.conjugate()))
            for previous, current in zip(phasors, phasors[1:])]


def half_turn_error(angle):
    return abs(180 - abs(angle))


def run(out=HERE / 'results/joint-mask04-msb-segment1-phase.json'):
    txready = json.loads(TXREADY.read_text())
    prior = json.loads(PRIOR.read_text())
    edge = json.loads(EDGE.read_text())
    buses = json.loads(BUSES.read_text())['zero_error_survivors']
    earlier = json.loads((HERE / 'results/joint-mask04-free-clock-msb.json').read_text())
    if len(buses) != 6 or any(bus[7] != 7 for bus in buses):
        raise ValueError('candidate Y7-to-DAC-MSB family changed')
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    cases = []
    for selector in ('40', '60'):
        tx_case = next(row for row in txready['cases']
                       if row['selector'] == selector)
        prior_case = next(row for row in prior['transmit_mask04']
                          if row['selector'] == selector)
        edge_case = next(row for row in edge['cases']
                         if row['selector'] == selector)
        prior_free = next(row for row in earlier['cases']
                          if row['selector'] == selector)
        execution, streams = replay(mapping, base, tx_case, prior_case,
                                    edge_case, buses, return_streams=True)
        if execution != prior_free:
            raise ValueError(('free-clock replay changed', selector))
        sites = []
        for site in execution['sites']:
            pc = int(site['pc'], 16)
            codes = mapped_codes(streams[pc], SELECTED)
            tone = successive_angles(symbol_phasors(codes, 0, TONE_HZ))
            segment = successive_angles(symbol_phasors(
                codes, TONE_SYMBOLS + SILENCE_SYMBOLS, CARRIER_HZ))
            tone_max = max(abs(value) for value in tone)
            segment_error = max(half_turn_error(value) for value in segment)
            if len(tone) != 31 or len(segment) != 31 or tone_max >= 45 or \
                    segment_error >= 5:
                raise ValueError(('MSB phase signature changed', selector,
                                  site['pc'], tone_max, segment_error))
            sites.append(dict(pc=site['pc'],
                              sample_sha256=hashlib.sha256(bytes(codes)).hexdigest(),
                              msb_sha256=hashlib.sha256(
                                  bytes(code & 0x80 for code in codes)).hexdigest(),
                              tone_adjacent_phase_degrees=tone,
                              tone_max_abs_phase_degrees=tone_max,
                              segment1_adjacent_phase_degrees=segment,
                              segment1_max_half_turn_error_degrees=segment_error))
        if len({site['msb_sha256'] for site in sites}) != 1:
            raise ValueError(('MSB changed across free-clock phases', selector))
        cases.append(dict(selector=selector,
                          dsc_microinstructions=execution['cycles'],
                          trace_digest=execution['trace_digest'],
                          sites=sites))
        print(selector, 'sites', [(site['pc'],
                                  round(site['tone_max_abs_phase_degrees'], 2),
                                  round(site['segment1_max_half_turn_error_degrees'], 2))
                                 for site in sites], flush=True)
    paths = [Path(__file__), TXREADY, PRIOR, EDGE, BUSES,
             HERE / 'results/joint-mask04-free-clock-msb.json',
             HERE / 'joint_mask04_free_clock_msb.py',
             HERE / 'joint_mask04_dac_msb_data.py',
             HERE / 'joint_four_row_retention_tx.py',
             HERE / 'photo_joint_tone_training_data.py',
             HERE / 'photo_main_dibit_pulse.py',
             HERE / 'photo_dac_bus_permutations.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(experiment='direct phase of candidate DAC MSB in executed A1/A3 PROM samples',
                  fixture=dict(mapping='joint upper-source lower mask 04',
                               source='controller-derived call/answer A1-A4 stream',
                               capture='free-running sample each 1500 microinstructions at PCs 127-12A',
                               candidate='Y7-to-DAC08 B1 through assumed latch',
                               sample_rate_hz=SAMPLE_RATE_HZ,
                               phasor='8 raw MSB samples per symbol, corrected for 2100 Hz tone or 1800 Hz carrier',
                               output_inversion='immaterial to adjacent phase'),
                  cases=cases,
                  limitations=[
                      'The sample clock, Y7-to-latch-to-DAC08 B1 route, DAC current conversion and physical line route are not traced.',
                      'The real controller frame and TxD bytes determine the input sequence, but their events are projected onto the DSC schedule.',
                      'The phase measurement uses raw candidate DAC codes, not measured Nokia line current or an identified analog output.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
