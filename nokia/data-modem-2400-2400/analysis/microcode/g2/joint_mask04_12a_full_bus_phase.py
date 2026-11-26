"""Measure tone, reversal and dibit phases in executed 12A DAC candidates."""

import cmath
import hashlib
import json
import math
from pathlib import Path

import joint_mask04_12a_buffered_line as line
import joint_mask04_buffered_serial_handoff as handoff
from joint_mask04_tx_12a_delayed_latch import capturing_execute
from photo_dac_bus_permutations import mapped_codes
from photo_joint_line_filter_screen import SILENCE_END, TONE_END, bandpass
from photo_joint_tone_training_data import SILENCE_SYMBOLS, TONE_SYMBOLS
from reference_modem import PHASE_STEPS, raised_cosine, spectral_peak
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
PRIOR = HERE / 'results/joint-mask04-12a-buffered-line.json'
OUT = HERE / 'results/joint-mask04-12a-full-bus-phase.json'
SAMPLES_PER_SYMBOL = 8
SAMPLE_RATE = 9600
TONE_HZ = 2100
CARRIER_HZ = 1800
SEGMENT_SYMBOLS = 32
DATA_START = TONE_SYMBOLS + SILENCE_SYMBOLS + handoff.PREAMBLE + handoff.PIPELINE_SYMBOLS


def phasors(codes, start, count, frequency, offset=0):
    result = []
    for symbol in range(start, start + count):
        sample = symbol * SAMPLES_PER_SYMBOL + offset
        result.append(sum((codes[sample + index] - 128) * cmath.exp(
            -2j * math.pi * frequency * (sample + index) / SAMPLE_RATE)
            for index in range(SAMPLES_PER_SYMBOL)))
    if min(abs(value) for value in result) < 1:
        raise ValueError('candidate full-byte carrier phasor vanished')
    return result


def adjacent(phasor):
    return [math.degrees(cmath.phase(current * previous.conjugate()))
            for previous, current in zip(phasor, phasor[1:])]


def angular_error(actual, expected):
    return abs((actual - expected + 180) % 360 - 180)


def matched_phasors(pcm):
    estimates = []
    for symbol in range(len(pcm) // SAMPLES_PER_SYMBOL):
        acc = sum(pcm[index] * cmath.exp(
            -2j * math.pi * CARRIER_HZ * index / SAMPLE_RATE) *
            raised_cosine((index - SAMPLES_PER_SYMBOL * symbol) /
                          SAMPLES_PER_SYMBOL)
            for index in range(max(0, SAMPLES_PER_SYMBOL * symbol - 32),
                               min(len(pcm), SAMPLES_PER_SYMBOL * symbol + 33)))
        estimates.append(acc)
    return estimates


def run(out=OUT):
    prior = json.loads(PRIOR.read_text())
    buses = json.loads(line.BUSES.read_text())['zero_error_survivors']
    if len(buses) != 6:
        raise ValueError('photo-compatible DAC bus family changed')
    mapping = line.candidate(line.mapping_with_upper_source(0, '17.6'),
                             line.mapped(line.MAPPINGS['q3']), 4)
    _, base = line.fixture()
    cases = []
    for selector, delay in (('40', 5), ('60', 18)):
        offered = line_octets([0] * 8, delay)
        result, raw, expected = line.transmitter(
            capturing_execute(), mapping, base, offered)
        old = next(c for c in prior['cases'] if c['selector'] == selector)
        if (result['trace_digest'] != old['tx_trace_digest'] or
                hashlib.sha256(bytes(raw)).hexdigest() != old['y12a_sha256'] or
                len(expected) != handoff.RX_SYMBOLS or
                len(raw) != line.SAMPLES):
            raise ValueError('full-byte PROM transmitter differs from prior run')
        bus_cases = []
        for index, bus in enumerate(buses):
            codes = mapped_codes(raw, bus)
            gated = codes[:TONE_END] + [128] * (SILENCE_END - TONE_END) + codes[SILENCE_END:]
            filtered = [value + 128 for value in bandpass(
                [value - 128 for value in gated], 0.5)]
            tone_angles = adjacent(phasors(codes, 0, SEGMENT_SYMBOLS, TONE_HZ))
            reversal_angles = adjacent(phasors(
                codes, TONE_SYMBOLS + SILENCE_SYMBOLS, SEGMENT_SYMBOLS, CARRIER_HZ))
            # Include the preceding pipeline symbol so all 32 payload dibits
            # have a previous phase. The controller bits set the expected steps.
            data_angles = adjacent(phasors(codes, DATA_START - 1,
                                            handoff.DATA_SYMBOLS + 1, CARRIER_HZ))
            dibits = expected[handoff.PREAMBLE + handoff.PIPELINE_SYMBOLS:]
            if len(data_angles) != len(dibits) or len(dibits) != 32:
                raise ValueError('payload phasor count changed')
            target = [PHASE_STEPS[dibit] * 22.5 for dibit in dibits]
            direct = [angular_error(actual, wanted)
                      for actual, wanted in zip(data_angles, target)]
            conjugated = [angular_error(actual, -wanted)
                          for actual, wanted in zip(data_angles, target)]
            filtered_reversal = adjacent(phasors(
                filtered, TONE_SYMBOLS + SILENCE_SYMBOLS,
                SEGMENT_SYMBOLS, CARRIER_HZ, 6))
            filtered_data = adjacent(phasors(
                filtered, DATA_START - 1, handoff.DATA_SYMBOLS + 1,
                CARRIER_HZ, 6))
            filtered_errors = [angular_error(actual, wanted)
                               for actual, wanted in zip(filtered_data, target)]
            window = filtered[SILENCE_END + 6:SILENCE_END + 6 +
                              handoff.RX_SYMBOLS * SAMPLES_PER_SYMBOL]
            matched_data = adjacent(matched_phasors(
                [value - 128 for value in window]))[
                    handoff.PREAMBLE + handoff.PIPELINE_SYMBOLS - 1:]
            if len(matched_data) != len(target):
                raise ValueError('matched data phase count changed')
            matched_errors = [angular_error(actual, wanted)
                              for actual, wanted in zip(matched_data, target)]
            tone_peak = spectral_peak([value - 128 for value in
                                       codes[:TONE_SYMBOLS * SAMPLES_PER_SYMBOL]])
            if (tone_peak['frequency_hz'] != TONE_HZ or
                    max(abs(abs(value) - 180) for value in reversal_angles) > 1e-6 or
                    max(matched_errors) >= 45):
                raise ValueError(('full-bus tone/reversal/data signature changed',
                                  selector, index))
            bus_cases.append(dict(bus_index=index, input_bit_to_dac_code_bit=bus,
                                  code_sha256=hashlib.sha256(bytes(codes)).hexdigest(),
                                  tone_peak_hz=tone_peak['frequency_hz'],
                                  tone_adjacent_phase_degrees=tone_angles,
                                  tone_max_phase_error_degrees=max(map(abs, tone_angles)),
                                  reversal_adjacent_phase_degrees=reversal_angles,
                                  reversal_max_half_turn_error_degrees=max(
                                      abs(abs(value) - 180) for value in reversal_angles),
                                  data_adjacent_phase_degrees=data_angles,
                                  data_phase_error_degrees=direct,
                                  data_phase_error_if_conjugated_degrees=conjugated,
                                  data_max_phase_error_degrees=max(direct),
                                  data_max_phase_error_if_conjugated_degrees=max(conjugated),
                                  filtered_reversal_max_half_turn_error_degrees=max(
                                      abs(abs(value) - 180) for value in filtered_reversal),
                                  filtered_data_adjacent_phase_degrees=filtered_data,
                                  filtered_data_phase_error_degrees=filtered_errors,
                                  filtered_data_max_phase_error_degrees=max(filtered_errors),
                                  matched_data_adjacent_phase_degrees=matched_data,
                                  matched_data_phase_error_degrees=matched_errors,
                                  matched_data_max_phase_error_degrees=max(matched_errors)))
        cases.append(dict(selector=selector, offered_line_bytes=[f'{x:02X}' for x in offered],
                          tx_trace_digest=result['trace_digest'],
                          raw_sha256=hashlib.sha256(bytes(raw)).hexdigest(),
                          expected_data_dibits=expected[handoff.PREAMBLE +
                                                        handoff.PIPELINE_SYMBOLS:],
                          bus_cases=bus_cases))
        print('full-bus phase', selector,
              [(b['bus_index'], round(b['tone_max_phase_error_degrees'], 2),
                round(b['reversal_max_half_turn_error_degrees'], 2),
                round(b['data_max_phase_error_degrees'], 2),
                round(b['matched_data_max_phase_error_degrees'], 2))
               for b in bus_cases], flush=True)
    paths = (Path(__file__), PRIOR, line.BUSES,
             HERE / 'joint_mask04_12a_buffered_line.py',
             HERE / 'joint_mask04_tx_12a_delayed_latch.py',
             HERE / 'photo_dac_bus_permutations.py',
             HERE / 'photo_joint_line_filter_screen.py',
             HERE / 'reference_modem.py',
             HERE.parent / 'assumed/execute.py', line.MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='direct full-byte 12A phase signatures in executed controller-fed PROM streams',
                  fixture=dict(selectors=['40', '60'], sample_rate_hz=SAMPLE_RATE,
                               tone_hz=TONE_HZ, carrier_hz=CARRIER_HZ,
                               sample_site='every 375th 12A Y; early raw-PROM gate/Y ordering',
                               filtered_phase='Q=0.5 candidate bandpass and fixed +6-sample alignment',
                               input='actual 8031-derived zero-run line bytes in 32-symbol preamble and 32-symbol data window',
                               six_buses='photo-compatible B5/Q4 bus orders'),
                  cases=cases,
                  limitations=[
                      'The Y-to-74LS273 data path, divided latch clock, DAC08 bus, analog output and line filter remain assumed.',
                      'A digital DAC-code phasor is not a measurement of Nokia analog current or an identified line-output sample stream.',
                      'The controller D127 pulse and sample alignment are declared fixture hypotheses.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
