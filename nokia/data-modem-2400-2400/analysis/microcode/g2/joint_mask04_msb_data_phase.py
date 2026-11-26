"""Read controller A4 dibit phase changes from executed raw DAC MSB samples."""

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from joint_four_row_retention_tx import (MAPPINGS, candidate, fixture, mapped,
                                         mapping_with_upper_source)
from joint_mask04_free_clock_msb import (BUSES, EDGE, PRIOR, TXREADY, replay)
from joint_mask04_msb_segment1_phase import (CARRIER_HZ, successive_angles,
                                             symbol_phasors)
from photo_dac_bus_permutations import SELECTED, mapped_codes
from photo_joint_tone_training_data import (SEGMENT_SYMBOLS, SILENCE_SYMBOLS,
                                            TONE_SYMBOLS, segment2_from_txd)
from photo_main_dibit_pulse import BASE, PULSE_VISITS, dibit_rule


def circular_error(observed, expected):
    return abs((observed - expected + 180) % 360 - 180)


def phase_target(dibit, sign):
    step = dibit_rule(dibit & 1, dibit >> 1)
    offset = (PULSE_VISITS * (step - BASE)) & 255
    return sign * offset * 360 / 256


def score(codes, dibits, sign):
    start = TONE_SYMBOLS + SILENCE_SYMBOLS
    training = symbol_phasors(codes, start, CARRIER_HZ)
    data = symbol_phasors(codes, start + SEGMENT_SYMBOLS, CARRIER_HZ)
    angles = successive_angles([training[-1], *data])
    expected = [phase_target(dibit, sign) for dibit in dibits]
    errors = [circular_error(observed, target)
              for observed, target in zip(angles, expected)]
    if len(errors) != 32:
        raise ValueError('A4 dibit count changed')
    return dict(observed_phase_degrees=angles,
                expected_phase_degrees=expected,
                absolute_phase_errors_degrees=errors,
                max_error_degrees=max(errors),
                mean_error_degrees=sum(errors) / len(errors),
                wrong_quadrants=sum(error >= 45 for error in errors))


def packed_msb(codes):
    if len(codes) % 8:
        raise ValueError('sample count is not byte aligned')
    return bytes(sum(((codes[offset + bit] >> 7) & 1) << bit
                     for bit in range(8))
                 for offset in range(0, len(codes), 8))


def run(out=HERE / 'results/joint-mask04-msb-data-phase.json'):
    txready = json.loads(TXREADY.read_text())
    prior = json.loads(PRIOR.read_text())
    edge = json.loads(EDGE.read_text())
    buses = json.loads(BUSES.read_text())['zero_error_survivors']
    previous = json.loads((HERE / 'results/joint-mask04-msb-segment1-phase.json').read_text())
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
        previous_case = next(row for row in previous['cases']
                             if row['selector'] == selector)
        execution, streams = replay(mapping, base, tx_case, prior_case,
                                    edge_case, buses, return_streams=True)
        if execution['trace_digest'] != previous_case['trace_digest']:
            raise ValueError(('PROM trace changed', selector))
        dibits = segment2_from_txd(tx_case)
        sites = []
        for site, old in zip(execution['sites'], previous_case['sites']):
            if site['pc'] != old['pc']:
                raise ValueError(('capture site changed', selector))
            codes = mapped_codes(streams[int(site['pc'], 16)], SELECTED)
            if hashlib.sha256(bytes(codes)).hexdigest() != old['sample_sha256']:
                raise ValueError(('executed sample bytes changed', selector,
                                  site['pc']))
            primary = score(codes, dibits, sign=-1)
            opposite = score(codes, dibits, sign=1)
            sites.append(dict(pc=site['pc'], primary=primary,
                              opposite_sign=opposite,
                              packed_msb_lsb_first_hex=packed_msb(codes).hex(),
                              msb_sample_sha256=old['msb_sha256']))
        if (any(item['primary']['wrong_quadrants'] or
                item['primary']['max_error_degrees'] >= 45
                for item in sites) or
                len({item['packed_msb_lsb_first_hex'] for item in sites}) != 1 or
                not any(item['opposite_sign']['wrong_quadrants'] for item in sites)):
            raise ValueError(('direct A4 phase check failed', selector,
                              [(site['pc'], site['primary']['max_error_degrees'],
                                site['primary']['wrong_quadrants'],
                                site['opposite_sign']['wrong_quadrants'])
                               for site in sites]))
        cases.append(dict(selector=selector, dibits=dibits,
                          dsc_microinstructions=execution['cycles'],
                          trace_digest=execution['trace_digest'], sites=sites))
        print(selector, [(site['pc'],
                          round(site['primary']['max_error_degrees'], 2),
                          site['opposite_sign']['wrong_quadrants'])
                         for site in sites], flush=True)
    paths = [Path(__file__), TXREADY, PRIOR, EDGE, BUSES,
             HERE / 'results/joint-mask04-msb-segment1-phase.json',
             HERE / 'results/joint-mask04-free-clock-msb.json',
             HERE / 'joint_mask04_msb_segment1_phase.py',
             HERE / 'joint_mask04_free_clock_msb.py',
             HERE / 'joint_mask04_dac_msb_data.py',
             HERE / 'joint_four_row_retention_tx.py',
             HERE / 'photo_joint_tone_training_data.py',
             HERE / 'photo_main_dibit_pulse.py',
             HERE / 'photo_dac_bus_permutations.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(experiment='direct A4 phase steps from executed candidate DAC MSB samples',
                  fixture=dict(mapping='joint upper-source lower mask 04',
                               source='controller-derived call/answer A3-A4 stream',
                               capture='free-running sample each 1500 microinstructions at PCs 127-12A',
                               candidate='Y7-to-DAC08 B1 through assumed latch',
                               sample_rate_hz=9600,
                               phasor='8 raw MSB samples per symbol at 1800 Hz',
                               primary_phase_sign='negative from four-visit D127 phase rule',
                               control_phase_sign='positive'),
                  cases=cases,
                  limitations=[
                      'The raw candidate DAC MSB is an executed digital output under a field map and board scenario, not a verified Nokia line signal.',
                      'The sample clock, Y7-to-latch-to-DAC08 B1 route, DAC current conversion and analog output are untraced.',
                      'The controller TxD sequence is executed but projected onto the DSC schedule; the phase expectation uses the proposed D127 four-visit input rule.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
