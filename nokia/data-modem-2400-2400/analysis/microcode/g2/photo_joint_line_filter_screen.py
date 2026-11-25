"""Screen a candidate DAC gate and analog bandpass on the joined PROM stream."""

import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from photo_127_liveness import ROM
from photo_a1_dynamic_mode_replay import tone_summary
from photo_dac_bus_permutations import SELECTED, mapped_codes
from photo_joint_tone_training_data import (
    DATA_STEP, SEGMENT_SYMBOLS, SILENCE_SYMBOLS, TONE_STEP, TONE_SYMBOLS,
    VISITS_PER_SYMBOL, raw_codes, scenario_inputs, segment2_from_txd,
)
from photo_main_dibit_dac_decode import decision_result
from reference_modem import rms

TXREADY = HERE / 'results/main-loop-usart-txready.json'
JOINT = HERE / 'results/photo-joint-tone-training-data.json'
BUSES = HERE / 'results/photo-random-dibit-validation.json'
SAMPLE_RATE = 9600
CENTER_HZ = 1950
QS = (0.5, 1.0, 2.0, 3.0)
SHIFTS = tuple(range(8))
TONE_END = TONE_SYMBOLS * 8
SILENCE_END = (TONE_SYMBOLS + SILENCE_SYMBOLS) * 8


def bandpass(samples, q):
    """RBJ constant-skirt-gain biquad, zero initial delay state."""
    omega = 2 * math.pi * CENTER_HZ / SAMPLE_RATE
    alpha = math.sin(omega) / (2 * q)
    b0 = alpha / (1 + alpha)
    b2 = -b0
    a1 = -2 * math.cos(omega) / (1 + alpha)
    a2 = (1 - alpha) / (1 + alpha)
    x1 = x2 = y1 = y2 = 0.0
    output = []
    for value in samples:
        y = b0 * value + b2 * x2 - a1 * y1 - a2 * y2
        output.append(y)
        x2, x1 = x1, value
        y2, y1 = y1, y
    return output


def joined_codes(rom, tx_case, joint_case):
    segment2 = segment2_from_txd(tx_case)
    symbols = [3] * SEGMENT_SYMBOLS + segment2
    inputs = ([TONE_STEP] * (TONE_SYMBOLS * VISITS_PER_SYMBOL) +
              [DATA_STEP] * (SILENCE_SYMBOLS * VISITS_PER_SYMBOL) +
              scenario_inputs(symbols))
    raw, _ = raw_codes(rom, inputs)
    selected = mapped_codes(raw, SELECTED)
    if hashlib.sha256(bytes(selected)).hexdigest() != joint_case[
            'selected_bus_sample_sha256']:
        raise ValueError(('joined PROM sample hash changed', tx_case['selector']))
    return raw, symbols


def run(out=HERE / 'results/photo-joint-line-filter-screen.json'):
    txready = json.loads(TXREADY.read_text())
    joint = json.loads(JOINT.read_text())
    buses = json.loads(BUSES.read_text())['zero_error_survivors']
    if len(buses) != 6:
        raise ValueError('DAC bus survivor family changed')
    rom = ROM.read_bytes()
    cases = []
    for selector in ('40', '60'):
        tx_case = next(row for row in txready['cases']
                       if row['selector'] == selector)
        joint_case = next(row for row in joint['cases']
                          if row['selector'] == selector)
        raw, symbols = joined_codes(rom, tx_case, joint_case)
        for index, bus in enumerate(buses):
            codes = mapped_codes(raw, bus)
            # The CD4094-derived capture gate is false in A2; model its
            # analog output as zero about the DAC's mid-code, with the
            # phase accumulator continuing internally.
            gated = codes[:TONE_END] + [128] * (SILENCE_END - TONE_END) + codes[SILENCE_END:]
            source = [value - 128 for value in gated]
            for q in QS:
                line = bandpass(source, q)
                tone = tone_summary(line[64:TONE_END])
                errors = [decision_result([value + 128 for value in line[SILENCE_END:]],
                                          symbols, sample_shift=shift)['errors']
                          for shift in SHIFTS]
                cases.append(dict(selector=selector, bus_index=index, q=q,
                                  tone_peak_hz=tone['peak_hz'],
                                  tone_r2_2100=tone['r2_2100'],
                                  tone_rms=rms(line[64:TONE_END]),
                                  last_32_a2_rms=rms(line[SILENCE_END - 32:SILENCE_END]),
                                  errors_by_sample_shift=errors))
    selected = [row for row in cases if row['q'] == 1.0]
    if (len(selected) != 12 or
            any(row['tone_peak_hz'] != 2100 or
                not 0.7 < row['tone_r2_2100'] < 0.75 or
                row['last_32_a2_rms'] / row['tone_rms'] >= 0.001 or
                row['errors_by_sample_shift'][6] != 0
                for row in selected)):
        raise ValueError('shared line-filter fixture changed')
    sources = (Path(__file__), TXREADY, JOINT, BUSES, ROM,
               HERE / 'photo_joint_tone_training_data.py',
               HERE / 'photo_main_dibit_dac_decode.py',
               HERE / 'reference_modem.py')
    report = dict(experiment='conditional DAC mid-code gate and second-order line bandpass',
                  fixture=dict(controller_selectors=('40', '60'),
                               bus_family='six zero-error random-holdout survivors',
                               sample_rate_hz=SAMPLE_RATE,
                               filter_center_hz=CENTER_HZ,
                               q_values=QS, sample_shifts=SHIFTS,
                               a2_output_gate='assumed mid-code 128; phase continues',
                               tone_window='A1 samples 64..255',
                               silence_window='last 32 A2 samples'),
                  cases=cases,
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    rows = [row for row in result['cases'] if row['q'] == 1.0]
    print(len(rows), min(row['tone_r2_2100'] for row in rows),
          max(row['tone_r2_2100'] for row in rows))
