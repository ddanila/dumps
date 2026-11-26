"""Rebuild the phase-131 line once and audit gain/clipping before RX sweeps."""

import hashlib
import json
from pathlib import Path

import joint_mask04_12a_analog_holdout as holdout
import joint_mask04_12a_buffered_line as line
import joint_mask04_12a_frozen_sixth_new_payloads as frozen
from joint_mask04_12a_mode_phase131_gain_challenge import OFFSET, PAYLOADS
from joint_mask04_tx_12a_delayed_latch import capturing_execute
from photo_dac_bus_permutations import mapped_codes
from photo_joint_line_filter_screen import SILENCE_END, TONE_END, bandpass
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
FIXED = HERE / 'results/joint-mask04-12a-fixed-gain-phase.json'
BASELINE = HERE / 'results/joint-mask04-12a-mode-phase131-baseline-control.json'
BOOSTED = HERE / 'results/joint-mask04-12a-mode-phase131-gain-challenge.json'
OUT = HERE / 'results/joint-mask04-12a-mode-phase131-adc-range.json'
FACTORS = (1.0, 1.125, 1.25)


def pcm_for(selected, calibrated_gain, factor):
    return [max(-127, min(127, round(value * calibrated_gain * factor)))
            for value in selected]


def run(out=OUT):
    fixed = json.loads(FIXED.read_text())
    baseline = {case['selector']: case for case in
                json.loads(BASELINE.read_text())['cases']}
    boosted = {case['selector']: case for case in
               json.loads(BOOSTED.read_text())['cases']}
    mapping = line.candidate(line.mapping_with_upper_source(0, '17.6'),
                             line.mapped(line.MAPPINGS['q3']), 4)
    _, base = line.fixture()
    cases = []
    for selector, delay in (('40', 5), ('60', 18)):
        payload = PAYLOADS[selector]
        offered = line_octets(payload, delay)
        tx, raw, _ = line.transmitter(
            capturing_execute((frozen.PHASE_VISIT, OFFSET)),
            mapping, base, offered)
        calibration = next(bus['gain'] for bus in next(
            case for case in fixed['cases'] if case['selector'] == selector
        )['bus_cases'] if bus['bus_index'] == 0)
        codes = mapped_codes(raw, holdout.BUSES[0])
        gated = (codes[:TONE_END] + [128] * (SILENCE_END - TONE_END)
                 + codes[SILENCE_END:])
        wave = bandpass([value - 128 for value in gated], 0.5)
        selected = wave[SILENCE_END + 5:
                        SILENCE_END + 5 + line.RX_SYMBOLS * 8]
        if len(selected) != line.RX_SYMBOLS * 8:
            raise ValueError('line sample count changed')
        factors = []
        for factor in FACTORS:
            unbounded = [round(value * calibration * factor)
                         for value in selected]
            pcm = pcm_for(selected, calibration, factor)
            digest = hashlib.sha256(bytes(value + 127 for value in pcm)).hexdigest()
            if factor == 1.0 and digest != baseline[selector]['pcm_sha256']:
                raise ValueError(('baseline PCM changed', selector))
            if factor == 1.25 and digest != boosted[selector]['pcm_sha256']:
                raise ValueError(('boosted PCM changed', selector))
            factors.append(dict(factor=factor, pcm_sha256=digest,
                                min_unbounded=min(unbounded),
                                max_unbounded=max(unbounded),
                                clipped_samples=sum(abs(value) > 127
                                                    for value in unbounded),
                                near_rail_samples=sum(abs(value) >= 120
                                                      for value in pcm)))
        if tx['trace_digest'] != baseline[selector]['tx_trace_digest']:
            raise ValueError(('phase-131 TX changed', selector))
        cases.append(dict(selector=selector, payload=[f'{x:02X}' for x in payload],
                          tx_trace_digest=tx['trace_digest'],
                          raw_sha256=hashlib.sha256(bytes(raw)).hexdigest(),
                          selected_wave=selected,
                          calibrated_gain=calibration,
                          factors=factors))
        print(selector, [(x['factor'], x['clipped_samples'],
                          x['near_rail_samples']) for x in factors], flush=True)
    paths = (Path(__file__), FIXED, BASELINE, BOOSTED,
             HERE / 'joint_mask04_12a_mode_phase131_gain_challenge.py')
    report = dict(experiment='phase-131 candidate ADC range under gain change',
                  cases=cases,
                  limitations=[
                      'The DAC bus, analog filter, gain and ADC encoding are circuit assumptions; clipping is measured only in the modeled PCM fixture.',
                      'This check does not execute the receiver at intermediate gains.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
