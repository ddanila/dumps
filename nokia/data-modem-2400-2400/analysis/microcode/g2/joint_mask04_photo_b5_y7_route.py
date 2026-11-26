"""Test executed Y7 through the photographed Q4-to-DAC08-B5 candidate."""

import hashlib
import json
import cmath
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from joint_mask04_msb_data_phase import circular_error, phase_target
from joint_mask04_msb_segment1_phase import successive_angles
from photo_a1_dynamic_mode_replay import tone_summary
from photo_joint_line_filter_screen import (SILENCE_END, TONE_END, bandpass)
from photo_joint_tone_training_data import SEGMENT_SYMBOLS, segment2_from_txd
from photo_main_dibit_dac_decode import decision_result
from reference_modem import rms

SOURCE = HERE / 'results/joint-mask04-msb-data-phase.json'
TXREADY = HERE / 'results/main-loop-usart-txready.json'
PRIOR_B5 = HERE / 'results/joint-mask04-photo-b5-tone.json'
PHOTO = HERE.parents[2] / 'photos/PXL_20261123_114854803.jpg'
DAC_B5_WEIGHT = 8
MID_CODE = DAC_B5_WEIGHT // 2
SAMPLE_RATE_HZ = 9600
SAMPLES_PER_SYMBOL = 8


def bits_from_packed(hex_string):
    return [(byte >> bit) & 1 for byte in bytes.fromhex(hex_string)
            for bit in range(8)]


def phasors(codes, start, frequency):
    return [sum((codes[(start + symbol) * SAMPLES_PER_SYMBOL + sample] - MID_CODE) *
                cmath.exp(-2j * math.pi * frequency *
                          ((start + symbol) * SAMPLES_PER_SYMBOL + sample) /
                          SAMPLE_RATE_HZ)
                for sample in range(SAMPLES_PER_SYMBOL))
            for symbol in range(SEGMENT_SYMBOLS)]


def direct_phase(codes, dibits):
    tone = successive_angles(phasors(codes, 0, 2100))
    training_start = TONE_END // SAMPLES_PER_SYMBOL + \
        (SILENCE_END - TONE_END) // SAMPLES_PER_SYMBOL
    training = phasors(codes, training_start, 1800)
    training_steps = successive_angles(training)
    data = phasors(codes, training_start + SEGMENT_SYMBOLS, 1800)
    data_steps = successive_angles([training[-1], *data])
    expected = [phase_target(dibit, -1) for dibit in dibits]
    errors = [circular_error(got, want)
              for got, want in zip(data_steps, expected)]
    return dict(tone_max_abs_phase_degrees=max(abs(value) for value in tone),
                training_max_half_turn_error_degrees=max(
                    abs(180 - abs(value)) for value in training_steps),
                data_wrong_quadrants=sum(value >= 45 for value in errors),
                data_max_phase_error_degrees=max(errors))


def run(out=HERE / 'results/joint-mask04-photo-b5-y7-route.json'):
    source = json.loads(SOURCE.read_text())
    txready = json.loads(TXREADY.read_text())
    prior_b5 = json.loads(PRIOR_B5.read_text())
    tone_control = next(row for row in prior_b5['cases']
                        if row['input_d127'] == '88')
    assert all(phase['b5_expected_power'] == 0 for phase in
               tone_control['phases'])
    cases = []
    for case in source['cases']:
        selector = case['selector']
        packed = {site['packed_msb_lsb_first_hex'] for site in case['sites']}
        if len(packed) != 1:
            raise ValueError(('free-clock Y7 phases disagree', selector))
        bits = bits_from_packed(packed.pop())
        if len(bits) != 832 or any(
                hashlib.sha256(bytes(bit << 7 for bit in bits)).hexdigest() !=
                site['msb_sample_sha256'] for site in case['sites']):
            raise ValueError(('saved real-PROM Y7 sample hash changed', selector))
        tx_case = next(row for row in txready['cases']
                       if row['selector'] == selector)
        symbols = [3] * SEGMENT_SYMBOLS + segment2_from_txd(tx_case)
        codes = [DAC_B5_WEIGHT * bit for bit in bits]
        raw_phase = direct_phase(codes, segment2_from_txd(tx_case))
        gated = (codes[:TONE_END] +
                 [MID_CODE] * (SILENCE_END - TONE_END) +
                 codes[SILENCE_END:])
        line = bandpass([code - MID_CODE for code in gated], 1.0)
        tone = tone_summary(line[64:TONE_END])
        data = decision_result([value + 128 for value in line[SILENCE_END:]],
                               symbols, sample_shift=6)
        # Photo-visible copper near D4 also heads toward the adjacent DAC
        # input region. Bound the effect if it shares B6 with the B5 latch
        # output; this is a route sensitivity, not an established net.
        neighbor_weight = DAC_B5_WEIGHT + 4
        neighbor_mid = neighbor_weight // 2
        neighbor_codes = [neighbor_weight * bit for bit in bits]
        neighbor_gated = (neighbor_codes[:TONE_END] +
                          [neighbor_mid] * (SILENCE_END - TONE_END) +
                          neighbor_codes[SILENCE_END:])
        neighbor_line = bandpass([code - neighbor_mid for code in neighbor_gated],
                                 1.0)
        neighbor_tone = tone_summary(neighbor_line[64:TONE_END])
        neighbor_data = decision_result(
            [value + 128 for value in neighbor_line[SILENCE_END:]],
            symbols, sample_shift=6)
        silence_ratio = rms(line[SILENCE_END - 32:SILENCE_END]) / \
            rms(line[TONE_END - 32:TONE_END])
        cases.append(dict(selector=selector, dsc_microinstructions=case['dsc_microinstructions'],
                          prom_trace_digest=case['trace_digest'],
                          packed_y7_sha256=hashlib.sha256(bytes(bits)).hexdigest(),
                          b5_code_sha256=hashlib.sha256(bytes(codes)).hexdigest(),
                          tone=tone, data=data, raw_phase=raw_phase,
                          possible_b6_shared_input=dict(
                              assumed_combined_dac_weight=neighbor_weight,
                              tone_peak_hz=neighbor_tone['peak_hz'],
                              data_errors=neighbor_data['errors'],
                              data_decisions=neighbor_data['decisions']),
                          late_a2_to_late_a1_rms=silence_ratio,
                          source_sites=[site['pc'] for site in case['sites']]))
        print(selector, tone['peak_hz'], data['errors'],
              raw_phase['data_wrong_quadrants'], silence_ratio, flush=True)
    paths = (Path(__file__), SOURCE, TXREADY, PRIOR_B5, PHOTO,
             HERE / 'joint_mask04_msb_data_phase.py',
             HERE / 'joint_mask04_msb_segment1_phase.py',
             HERE / 'photo_a1_dynamic_mode_replay.py',
             HERE / 'photo_joint_line_filter_screen.py',
             HERE / 'photo_joint_tone_training_data.py',
             HERE / 'photo_main_dibit_dac_decode.py',
             HERE / 'reference_modem.py',
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='executed Y7 through photo-suggested LS273 Q4 to DAC08 B5',
                  candidate_route='Am2901 Y7 -> assumed LS273 D4 clocked at 9600 Hz -> LS273 Q4 pin 9 -> photo-suggested DAC08 B5 pin 9 -> assumed current conversion and Q=1 line bandpass',
                  fixture=dict(dac_bit_weight=DAC_B5_WEIGHT,
                               a2_gate_mid_code=MID_CODE,
                               sample_rate_hz=9600,
                               bandpass_center_hz=1950,
                               bandpass_q=1,
                               data_sample_shift=6,
                               negative_control='earlier Y4-to-D4-to-B5 held-tone replay has zero power at 2100 Hz'),
                  cases=cases,
                  limitations=['Only Q4-to-B5 is photo-suggested; Y7-to-D4, latch clock and analog output route are untraced.',
                               'The possible D4-to-adjacent-DAC-input route is not a traced net; the B5+B6 calculation only tests its gain effect when both bits carry identical Y7 samples.',
                               'This B5-only alternative does not establish the other seven DAC bit connections or coexistence with the earlier Y7-to-B1 bus orders.',
                               'A2 mid-code gate and analog bandpass are external hypotheses, not measured components.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
