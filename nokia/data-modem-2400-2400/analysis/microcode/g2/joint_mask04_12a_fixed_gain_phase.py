"""Freeze Q=0.5 gain on zero-run data, then challenge new payload phases."""

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_analog_holdout as holdout
import joint_mask04_12a_buffered_line as line
from joint_mask04_12a_extended_shift import SAMPLES, TX_CYCLES
from joint_mask04_tx_12a_delayed_latch import capturing_execute
from photo_dac_bus_permutations import mapped_codes
from photo_joint_line_filter_screen import SILENCE_END, TONE_END, bandpass
from reference_modem import receive
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
ZERO = HERE / 'results/joint-mask04-12a-analog-screen.json'
HOLDOUT = HERE / 'results/joint-mask04-12a-analog-holdout.json'
SHIFTS = tuple(range(-7, 13))
LEVELS = (0.75, 1.0, 1.25)
WINDOW = line.RX_SYMBOLS * 8


def line_wave(raw, bus):
    codes = mapped_codes(raw, bus)
    gated = codes[:TONE_END] + [128] * (SILENCE_END - TONE_END) + codes[SILENCE_END:]
    return bandpass([value - 128 for value in gated], 0.5)


def window_at(wave, shift):
    selected = wave[SILENCE_END + shift:SILENCE_END + shift + WINDOW]
    if len(selected) != WINDOW:
        raise ValueError(('PCM window short', shift, len(selected)))
    return selected


def pcm_at(selected, gain):
    return [max(-127, min(127, round(value * gain))) for value in selected]


def run(out=HERE / 'results/joint-mask04-12a-fixed-gain-phase.json'):
    zero = json.loads(ZERO.read_text())
    hold = json.loads(HOLDOUT.read_text())
    if len(holdout.BUSES) != 6:
        raise ValueError('DAC bus fixture changed')
    mapping = line.candidate(line.mapping_with_upper_source(0, '17.6'),
                             line.mapped(line.MAPPINGS['q3']), 4)
    _, base = line.fixture()
    execute = capturing_execute()
    cases = []
    for selector, delay in (('40', 5), ('60', 18)):
        streams = []
        for payload_index, payload in [(-1, (0,) * 8),
                                       *enumerate(holdout.PAYLOADS)]:
            offered = line_octets(payload, delay)
            with patch.object(line, 'SAMPLES', SAMPLES), \
                    patch.object(line, 'TX_CYCLES', TX_CYCLES):
                result, raw, expected = line.transmitter(
                    execute, mapping, base, offered)
            if len(raw) != SAMPLES:
                raise ValueError('extended raw length changed')
            saved = (next(c for c in zero['cases']
                          if c['selector'] == selector)
                     if payload_index == -1 else
                     next(c for c in hold['cases']
                          if c['selector'] == selector and
                          c['payload_index'] == payload_index))
            saved_hash = (saved['y12a_prefix_sha256'] if payload_index == -1
                          else saved['y12a_sha256'])
            if hashlib.sha256(bytes(raw[:line.SAMPLES])).hexdigest() != saved_hash:
                raise ValueError(('saved Tx prefix changed', selector,
                                  payload_index))
            streams.append(dict(payload_index=payload_index,
                                payload=[f'{value:02X}' for value in payload],
                                trace_digest=result['trace_digest'],
                                raw_prefix_sha256=saved_hash,
                                raw=raw, expected=expected))
        calibration = streams[0]
        bus_cases = []
        for bus_index, bus in enumerate(holdout.BUSES):
            calib_wave = line_wave(calibration['raw'], bus)
            calib_selected = window_at(calib_wave, 6)
            gain = 110 / max(abs(value) for value in calib_selected)
            if receive(pcm_at(calib_selected, gain)) != calibration['expected'][1:]:
                raise ValueError(('zero-run calibration failed', selector,
                                  bus_index))
            payload_cases = []
            for stream in streams[1:]:
                wave = line_wave(stream['raw'], bus)
                scores = []
                for shift in SHIFTS:
                    selected = window_at(wave, shift)
                    for level in LEVELS:
                        pcm = pcm_at(selected, gain * level)
                        wrong = [i for i, (actual, want) in enumerate(
                            zip(receive(pcm), stream['expected'][1:]))
                            if actual != want]
                        scores.append(dict(shift=shift, level=level,
                                           wrong=len(wrong),
                                           wrong_indices=wrong))
                payload_cases.append(dict(payload_index=stream['payload_index'],
                                          tx_trace_digest=stream['trace_digest'],
                                          raw_prefix_sha256=stream['raw_prefix_sha256'],
                                          scores=scores))
            bus_cases.append(dict(bus_index=bus_index, gain=round(gain, 9),
                                  payload_cases=payload_cases))
        cases.append(dict(selector=selector,
                          calibration_trace_digest=calibration['trace_digest'],
                          calibration_raw_prefix_sha256=
                              calibration['raw_prefix_sha256'],
                          bus_cases=bus_cases))
    report = dict(experiment='frozen zero-run gain and phase screen on new 12A data',
                  fixture=dict(q=0.5, center_hz=1950, base_peak=110,
                               gain_calibration='one zero-run per selector and DAC bus, shift +6',
                               level_multipliers=LEVELS, shifts=SHIFTS,
                               extended_samples=SAMPLES,
                               payloads='two independent nonzero eight-byte values per selector'),
                  cases=cases,
                  limitations=[
                      'The gain is fixed across payloads within each selector/bus, but calibrated separately for those assumed routes.',
                      'DAC bus, latch, line filter and sample phase are hypothetical physical connections.',
                      'The known-carrier reference decoder is external to the DSC and does not establish a receive/USART route.'
                  ],
                  source_sha256={str(p.relative_to(HERE.parents[4])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (Path(__file__), ZERO, HOLDOUT,
                                           HERE / 'joint_mask04_12a_buffered_line.py',
                                           HERE / 'photo_joint_line_filter_screen.py',
                                           HERE.parent / 'assumed/execute.py')})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    report = run()
    for case in report['cases']:
        print(case['selector'],
              [(bus['bus_index'],
                [next(s['wrong'] for s in payload['scores']
                      if s['shift'] == 6 and s['level'] == 1.0)
                 for payload in bus['payload_cases']])
               for bus in case['bus_cases']])
