"""Test zero-error data bus orders against the executed A1 tone transition."""

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from photo_127_liveness import ROM
from photo_a1_dynamic_mode_replay import tone_summary
from photo_dac_bus_permutations import SELECTED, mapped_codes
from photo_main_frame_carrier_swap import spectrum

BUS = HERE / 'results/photo-dac-bus-permutations.json'
MODE = HERE / 'results/photo-controller-mode-decode.json'
DYNAMIC = HERE / 'results/photo-a1-dynamic-mode-replay.json'
SAMPLES = 640
VISITS_PER_SAMPLE = 375


def static_raw(rom, step):
    return [((phase := (3 + (1 + sample * VISITS_PER_SAMPLE) * step) & 255)
             - rom[256 + phase]) & 255 for sample in range(SAMPLES)]


def dynamic_raw(rom, case):
    phase = 3
    before = []
    after = []
    switch = case['switch_pc127_visit']
    for visit in range(1, case['pc127_and_pc129_visits'] + 1):
        step = 0xB0 if visit - 1 < switch else 0x88
        phase = (phase + step) & 255
        if (visit - 1) % VISITS_PER_SAMPLE == 0:
            (before if step == 0xB0 else after).append((phase - rom[256 + phase]) & 255)
    if len(before) != case['before']['samples'] or len(after) != case['after']['samples']:
        raise ValueError('dynamic capture schedule changed')
    return before, after


def run(out=HERE / 'results/photo-dac-joint-data-tone.json'):
    bus = json.loads(BUS.read_text())
    mode = json.loads(MODE.read_text())
    dynamic = json.loads(DYNAMIC.read_text())
    rom = ROM.read_bytes()
    zero = bus['zero_error_candidates']
    if len(zero) != 12 or len(dynamic['cases']) != 4:
        raise ValueError('data/tone evidence set changed')
    raw_tone = static_raw(rom, 0x88)
    raw_carrier = static_raw(rom, 0xB0)
    mode_by_name = {case['controller_mode']: case for case in mode['cases']}
    for name, raw in (('state_A1', raw_tone), ('main_00', raw_carrier)):
        expected = mode_by_name[name]['first_16_codes_if_clocked']
        if [f'{value:02X}' for value in mapped_codes(raw, SELECTED)[:16]] != expected:
            raise ValueError(('static recurrence differs from executed mode run', name))
    transitions = {case['selector']: dynamic_raw(rom, case) for case in dynamic['cases']}
    for case in dynamic['cases']:
        before, after = transitions[case['selector']]
        if ([f'{value:02X}' for value in mapped_codes(before, SELECTED)[:8]] !=
                case['first_8_pre_dac_codes'] or
                [f'{value:02X}' for value in mapped_codes(after, SELECTED)[:8]] !=
                case['first_8_post_dac_codes']):
            raise ValueError(('dynamic recurrence differs from executed PROM run',
                              case['selector']))
    candidates = []
    for previous in zero + [bus['selected_prior_order']]:
        permutation = previous['input_bit_to_dac_code_bit']
        steady_tone = mapped_codes(raw_tone, permutation)
        steady_carrier = mapped_codes(raw_carrier, permutation)
        tone = spectrum(steady_tone)['peak_hz']
        carrier = spectrum(steady_carrier)['peak_hz']
        tone_r2 = tone_summary(steady_tone)['r2_2100']
        carrier_r2 = tone_summary(steady_carrier)['r2_1800']
        dynamic_cases = []
        for selector, (raw_before, raw_after) in transitions.items():
            before = tone_summary(mapped_codes(raw_before, permutation))
            after = tone_summary(mapped_codes(raw_after, permutation))
            if before['peak_hz'] != 1800 or after['peak_hz'] != 2100:
                raise ValueError(('dynamic tone peak changed', permutation, selector,
                                  before['peak_hz'], after['peak_hz']))
            dynamic_cases.append(dict(selector=selector,
                                      before_peak_hz=before['peak_hz'],
                                      after_peak_hz=after['peak_hz'],
                                      before_r2_1800=before['r2_1800'],
                                      after_r2_2100=after['r2_2100']))
        if tone != 2100 or carrier != 1800:
            raise ValueError(('static tone peak changed', permutation, tone, carrier))
        candidates.append(dict(input_bit_to_dac_code_bit=permutation,
                               controller_data_errors=previous['total_errors'],
                               steady_carrier_peak_hz=carrier,
                               steady_tone_peak_hz=tone,
                               steady_carrier_r2_1800=carrier_r2,
                               steady_tone_r2_2100=tone_r2,
                               dynamic_a1=dynamic_cases))
    if (len(candidates) != 13 or
            [case['controller_data_errors'] for case in candidates] != [0] * 12 + [1]):
        raise ValueError('joint candidate count changed')
    sources = [Path(__file__), BUS, MODE, DYNAMIC, ROM,
               HERE / 'photo_dac_bus_permutations.py',
               HERE / 'photo_controller_mode_decode.py',
               HERE / 'photo_a1_dynamic_mode_replay.py',
               HERE / 'photo_main_frame_carrier_swap.py']
    report = dict(status='all twelve zero-error candidate DAC buses also project 1800/2100 Hz mode peaks under one fixed bus mapping',
                  fixture=dict(data='104 decisions from four real controller streams under candidate D127 dibit pulses',
                               tone='ROM-executed A1 controller frame bit5 change, decoded B0→88 D127',
                               output='ordered Y→LS273 D; Q4→DAC08 B5 fixed; 12 surviving permutations',
                               sample_hz=9600, sample_gate='one PC129 Y per 375 visits',
                               static_samples=SAMPLES,
                               dynamic_selectors=[case['selector'] for case in dynamic['cases']]),
                  candidates=candidates,
                  zero_error_joint_survivors=12,
                  limitations=['The A1 bit5 mode decode, DAC bus, latch clock, D127 pulse rule and analog route are untraced hypotheses.',
                               'The A1 controller fixture uses synthetic receive events and forced or suppressed timer expiry; the physical 2100 Hz state is not proved.',
                               'Long code sequences for each bus are projected from a PROM-verified phase/ROM/Y recurrence, not independently executed for each bit permutation.',
                               'All twelve perfect-data buses survive, so the tone peak does not identify a unique physical DAC bus or complete C2.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    return report


if __name__ == '__main__':
    report = run()
    print(report['zero_error_joint_survivors'],
          [(case['steady_carrier_r2_1800'], case['steady_tone_r2_2100'])
           for case in report['candidates'][:2]])
