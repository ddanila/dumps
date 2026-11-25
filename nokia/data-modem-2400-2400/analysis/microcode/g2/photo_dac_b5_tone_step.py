"""Replay D127 phase-step runs through the photographed DAC08 B5 candidate."""

import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent/'assumed'), str(HERE)]

from common import save
from photo_127_liveness import ROM, run_case
from photo_127_tone_probe import SAMPLE_RATE_HYPOTHESIS, spectrum
from photo_controller_path import fixture
from photo_dac_b5_127 import latch_b5
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

PHOTO = HERE.parents[2]/'photos/PXL_20261123_114854803.jpg'
INCREMENTS = (16, 24, 32, 40, 48, 56, 64, 72, 80)
SAMPLES = 128


def run(out=HERE/'results/photo-dac-b5-tone-step.json'):
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    cases = []
    for increment in INCREMENTS:
        expected_hz = increment*SAMPLE_RATE_HYPOTHESIS//256
        for bank in (0, 256):
            scenario, result, trace = run_case(mapping, base, increment, bank)
            rows = [row for row in trace if row['pc'] == 0x129][:SAMPLES]
            if (not result['clean'] or len(rows) != SAMPLES or
                    any(not row['external_read']['selected_by_alu'] for row in rows) or
                    any(b['cycle']-a['cycle'] != 4 for a, b in zip(rows, rows[1:]))):
                raise ValueError(f'PC129 candidate capture changed for {increment}, {bank}')
            bit_cases = []
            for bit in range(8):
                b5 = latch_b5(rows, bit)
                shape = (spectrum(b5, expected_hz) if len(set(b5)) > 1 else
                         dict(peak_hz=None, expected_hz=expected_hz,
                              sinusoid_r2=0, bin_hz=SAMPLE_RATE_HYPOTHESIS/SAMPLES))
                bit_cases.append(dict(y_bit_to_ls273_d4=bit,
                                      b5_ones=sum(b5),
                                      b5_transitions=sum(a != b for a, b in zip(b5, b5[1:])),
                                      first_32_b5=b5[:32] if bit == 7 else None,
                                      spectrum=shape))
            cases.append(dict(d127_increment=increment, bank=bank,
                              assumed_frequency_hz=expected_hz,
                              pc129_captures=len(rows),
                              first_16_rom_addresses=[row['external_read']['address']
                                                      for row in rows[:16]],
                              bit_cases=bit_cases,
                              trace_digest=result['trace_digest']))

    upper = {case['d127_increment']: case for case in cases if case['bank'] == 256}
    lower = {case['d127_increment']: case for case in cases if case['bank'] == 0}
    if any(upper[inc]['bit_cases'][7]['spectrum']['peak_hz'] !=
           upper[inc]['assumed_frequency_hz'] for inc in INCREMENTS):
        raise ValueError('upper-bank Y7 target-frequency family changed')
    if (lower[48]['bit_cases'][7]['spectrum']['peak_hz'] != 3600 or
            upper[48]['bit_cases'][7]['spectrum']['sinusoid_r2'] != 0.660524 or
            upper[56]['bit_cases'][7]['spectrum']['sinusoid_r2'] != 0.485502 or
            any(upper[inc]['bit_cases'][bit]['spectrum']['peak_hz'] ==
                upper[inc]['assumed_frequency_hz']
                for inc in (48, 56) for bit in range(7))):
        raise ValueError('photo-candidate B5 target/controls changed')

    paths = [Path(__file__), PHOTO, ROM,
             HERE/'photo_127_liveness.py', HERE/'photo_127_tone_probe.py',
             HERE/'photo_dac_b5_127.py', HERE/'photo_controller_path.py',
             HERE/'photo_i0_hold_screen.py', HERE/'photo_mapping_q_sweep.py',
             HERE/'photo_mapping_stream_screen.py',
             HERE.parent/'assumed/execute.py', MAPPINGS['q3']]
    report = dict(status='conditional photo-B5 phase-step screen, not a line waveform',
                  fixture=dict(mapping='q3 photo-swapped', initial_q=0,
                               d127_source='held scenario byte',
                               d127_increments=list(INCREMENTS),
                               bank_at_pc129=[0, 256],
                               assumed_clock='one rising LS273 edge at each PC129',
                               assumed_sample_rate_hz=SAMPLE_RATE_HYPOTHESIS,
                               photo_candidate='DAC08 pin 9 B5 receives LS273 pin 9 Q4',
                               y_to_ls273_d4='all eight Y-bit choices tested',
                               captures_per_case=SAMPLES),
                  cases=cases,
                  result='Upper-bank Y7-to-D4 yields a B5 peak at the selected phase-step frequency for all nine increments; 48 and 56 are not unique.',
                  limitations=[
                      'The B5←Q4 photo segment is not continuity-verified; Y7→D4 and PC129 latch clock are untraced.',
                      'The 9600 samples/s rate, D127 values, bank choice and held-I0 route are scenario assumptions.',
                      'Only one DAC input bit is inspected; no full DAC code, analog output, controller tone command or receive path is identified.',
                      'Any phase step in this tested family produces its corresponding B5 peak, so the 1800/2100 peaks alone do not identify Nokia tone selection.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    for case in report['cases']:
        if case['bank'] == 256:
            print(case['d127_increment'], case['assumed_frequency_hz'],
                  case['bit_cases'][7]['spectrum']['peak_hz'])
