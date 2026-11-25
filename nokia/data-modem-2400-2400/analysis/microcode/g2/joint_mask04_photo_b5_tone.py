"""Check the photo-suggested DAC08 B5 bit on the fixed joint PROM mapping."""

import copy
import hashlib
import json
import math
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from joint_four_row_retention_tx import (candidate, fixture, hold_candidate,
                                         mapped, mapping_with_upper_source,
                                         MAPPINGS, split_scenario)
from photo_dac_bus_permutations import mapped_codes
from photo_joint_line_filter_screen import BUSES
from photo_joint_tone_training_data import DATA_STEP, TONE_STEP, TONE_SYMBOLS
from photo_main_dibit_pulse import VISITS_PER_SYMBOL
from photo_tx_divided_prom_clock import capture
from reference_modem import spectral_peak

SAMPLE_COUNT = TONE_SYMBOLS * 8
LATE_START = 64
SAMPLE_HZ = 9600
SOURCE_BIT = 4
DAC_B5_CODE_BIT = 3


def dft_power(values, frequency_hz):
    count = len(values)
    angle = 2 * math.pi * frequency_hz / SAMPLE_HZ
    real = sum(value * math.cos(angle * index)
               for index, value in enumerate(values))
    imag = sum(value * math.sin(angle * index)
               for index, value in enumerate(values))
    return real * real + imag * imag


def replay(mapping, base, name, step, buses):
    scenario = split_scenario(hold_candidate(base))
    scenario['name'] += '; joint-map photo B5 ' + name
    scenario['inputs']['register_address_bit_overrides']['a_high'] = copy.deepcopy(
        scenario['inputs']['register_address_bit_overrides']['a'])
    for policy in scenario['inputs']['register_address_bit_overrides']['a_high'].values():
        policy['evidence'] += '; untraced high-slice A pin diagnostic level'
    scenario['initial']['q'] = 0
    scenario['io']['read']['pc_sequences'][str(0x127)] = [step] * (
        TONE_SYMBOLS * VISITS_PER_SYMBOL + 1)
    scenario['io']['read']['pc_sequences'][str(0x12C)] = [0xEA]
    scenario['io']['read']['address']['bank_by_pc'] = {
        str(0x129): 256, str(0x12E): 256}
    cycles = (TONE_SYMBOLS * VISITS_PER_SYMBOL + 64) * 4
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, cycles, mode='integrated',
                         out=temporary, trace_limit=cycles)
        samples = capture(Path(temporary) / 'trace.jsonl', SAMPLE_COUNT)
    if (not result['clean'] or result['completed_cycles'] != cycles or
            samples['captured_samples'] != SAMPLE_COUNT):
        raise ValueError(('joint-map B5 PROM run failed', name, result['stop']))
    phases = []
    for phase in ('pre_rising', 'post_rom'):
        raw = samples[phase]
        bits = [(value >> SOURCE_BIT) & 1 for value in raw]
        if any(bus[SOURCE_BIT] != DAC_B5_CODE_BIT for bus in buses):
            raise ValueError('photo B5 assignment changed')
        waveform = [2 * bit - 1 for bit in bits[LATE_START:]]
        peak = spectral_peak(waveform, lower=1000, upper=2600)
        expected_hz = 2100 if name == 'A1_2100_tone' else 1800
        full_peaks = sorted({spectral_peak(
            [value - 128 for value in mapped_codes(raw, bus)[LATE_START:]],
            lower=1000, upper=2600)['frequency_hz'] for bus in buses})
        phases.append(dict(phase=phase,
                           b5_bit_sha256=hashlib.sha256(bytes(bits)).hexdigest(),
                           b5_transitions=sum(a != b for a, b in zip(bits, bits[1:])),
                           b5_late_peak_hz=peak['frequency_hz'],
                           b5_late_peak_power=round(peak['power'], 3),
                           b5_expected_hz=expected_hz,
                           b5_expected_power=round(dft_power(waveform, expected_hz), 3),
                           b5_expected_to_peak_power=round(
                               dft_power(waveform, expected_hz) / peak['power'], 6),
                           full_code_peak_hz_across_six_buses=full_peaks,
                           b5_late_one_count=sum(bits[LATE_START:]),
                           raw_y_sha256=hashlib.sha256(bytes(raw)).hexdigest()))
    return dict(stimulus=name, input_d127=f'{step:02X}', cycles=cycles,
                trace_digest=result['trace_digest'],
                raw_rising_edges=samples['raw_rising_edges'],
                samples=SAMPLE_COUNT, phases=phases)


def run(out=HERE / 'results/joint-mask04-photo-b5-tone.json'):
    buses = json.loads(BUSES.read_text())['zero_error_survivors']
    if len(buses) != 6 or any(bus[SOURCE_BIT] != DAC_B5_CODE_BIT for bus in buses):
        raise ValueError('photo-compatible DAC bus family changed')
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    cases = [replay(mapping, base, name, step, buses)
             for name, step in (('A1_2100_tone', TONE_STEP),
                                ('unmodulated_1800_carrier', DATA_STEP))]
    for case, expected_full_hz, expected_b5_hz in zip(
            cases, (2100, 1800), (2400, 2600)):
        for phase in case['phases']:
            if (phase['full_code_peak_hz_across_six_buses'] != [expected_full_hz] or
                    phase['b5_late_peak_hz'] != expected_b5_hz):
                raise ValueError(('photo B5 versus full-code spectrum changed',
                                  case['stimulus'], phase))
    report = dict(
        status='A photo-suggested DAC08 B5 bit is tested on the fixed mask-04 real-PROM stream under tone and unmodulated-carrier inputs.',
        fixture=dict(mapping='joint upper-source lower mask 04',
                     input='D127 held at A1 tone step 88 or unmodulated step B0',
                     latch='candidate U10 D2 rising/falling phase, divided by 375',
                     photo_route='DAC08 B5 pin 9 appears to lead toward 74LS273 Q4 pin 9',
                     assumed_source='Am2901 Y bit 4 to 74LS273 D4; Q4 to DAC08 B5',
                     sample_hz=SAMPLE_HZ,
                     spectral_window='samples 64 through 255, 192 samples, 50 Hz DFT bins'),
        cases=cases,
        limitations=[
            'Only the Q4-to-B5 segment is suggested by the existing photograph; Y4-to-D4, latch clock, full DAC bus and analog route are untraced.',
            'A one-bit DAC input spectrum is not the analog line spectrum and cannot pass C2 alone.',
            'The held D127 stimuli are reconstructed controller-mode hypotheses, not a live controller/DSC co-simulation.'],
        source_sha256={str(path.relative_to(HERE.parents[2])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in [Path(__file__), BUSES,
                                    HERE / 'joint_four_row_retention_tx.py',
                                    HERE / 'photo_tx_divided_prom_clock.py',
                                    HERE.parent / 'assumed/execute.py', MAPPINGS['q3'],
                                    *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]})
    save(out, report)
    return report


if __name__ == '__main__':
    for case in run()['cases']:
        print(case['stimulus'],
              [(row['phase'], row['b5_late_peak_hz'], row['b5_transitions'])
               for row in case['phases']])
