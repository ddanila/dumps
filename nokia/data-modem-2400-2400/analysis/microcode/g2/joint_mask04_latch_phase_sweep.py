"""Sweep a candidate free-running latch across the executed Y7 loop phase."""

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from photo_a1_dynamic_mode_replay import tone_summary
from photo_joint_line_filter_screen import SILENCE_END, TONE_END, bandpass
from photo_joint_tone_training_data import (
    DATA_STEP, SEGMENT_SYMBOLS, SILENCE_SYMBOLS, TONE_STEP, TONE_SYMBOLS,
    TOTAL_SYMBOLS, segment2_from_txd,
)
from photo_main_dibit_dac_decode import decision_result
from photo_main_dibit_pulse import VISITS_PER_SAMPLE, VISITS_PER_SYMBOL, scenario_inputs

TXREADY = HERE / 'results/main-loop-usart-txready.json'
PROM_SAMPLES = HERE / 'results/joint-mask04-msb-data-phase.json'
PHASE_CHECK = HERE / 'results/joint-mask04-tx-phase-accumulator.json'
SAMPLES = TOTAL_SYMBOLS * 8
PERIOD = VISITS_PER_SAMPLE


def unpack(hex_string):
    return [(byte >> bit) & 1 for byte in bytes.fromhex(hex_string)
            for bit in range(8)]


def run(out=HERE / 'results/joint-mask04-latch-phase-sweep.json'):
    txready = json.loads(TXREADY.read_text())
    prom = json.loads(PROM_SAMPLES.read_text())
    phase_check = json.loads(PHASE_CHECK.read_text())
    cases = []
    for selector in ('40', '60'):
        tx = next(row for row in txready['cases'] if row['selector'] == selector)
        executed = next(row for row in prom['cases'] if row['selector'] == selector)
        checked = next(row for row in phase_check['cases']
                       if row['selector'] == selector)
        symbols = [3] * SEGMENT_SYMBOLS + segment2_from_txd(tx)
        inputs = ([TONE_STEP] * (TONE_SYMBOLS * VISITS_PER_SYMBOL) +
                  [DATA_STEP] * (SILENCE_SYMBOLS * VISITS_PER_SYMBOL) +
                  scenario_inputs(symbols))
        if len(inputs) < SAMPLES * PERIOD:
            raise ValueError(('D127 fixture too short', selector))
        phase = checked['initial_phase_before_first_input']
        y7 = []
        for value in inputs[:SAMPLES * PERIOD]:
            phase = (phase + value) & 255
            y7.append(phase >> 7)
        anchored = unpack(executed['sites'][0]['packed_msb_lsb_first_hex'])
        phase_zero = y7[::PERIOD]
        if (len(phase_zero) != SAMPLES or phase_zero != anchored or
                any(unpack(site['packed_msb_lsb_first_hex']) != anchored
                    for site in executed['sites'])):
            raise ValueError(('phase-zero recurrence differs from full PROM',
                              selector))
        rows = []
        for offset in range(PERIOD):
            bits = y7[offset::PERIOD]
            codes = [8 * bit for bit in bits]
            gated = (codes[:TONE_END] + [4] * (SILENCE_END - TONE_END) +
                     codes[SILENCE_END:])
            line = bandpass([value - 4 for value in gated], 1.0)
            tone = tone_summary(line[64:TONE_END])
            decision = decision_result(
                [value + 128 for value in line[SILENCE_END:]],
                symbols, sample_shift=6)
            rows.append(dict(offset_visits=offset,
                             tone_peak_hz=tone['peak_hz'],
                             data_decisions=decision['decisions'],
                             data_errors=decision['errors'],
                             error_indices=decision['error_indices']))
        failures = [row for row in rows if row['data_errors']]
        cases.append(dict(selector=selector,
                          phase_zero_y7_sha256=hashlib.sha256(
                              bytes(phase_zero)).hexdigest(),
                          executed_trace_digest=executed['trace_digest'],
                          offsets_tested=len(rows),
                          zero_error_offsets=len(rows) - len(failures),
                          tone_peaks_hz=sorted({row['tone_peak_hz'] for row in rows}),
                          failure_offsets=[row['offset_visits'] for row in failures],
                          failure_symbol_indices=sorted({index for row in failures
                                                         for index in row['error_indices']}),
                          rows=rows))
        print(selector, 'zero-error', len(rows) - len(failures),
              'of', len(rows), 'tone', cases[-1]['tone_peaks_hz'], flush=True)
    paths = (Path(__file__), TXREADY, PROM_SAMPLES, PHASE_CHECK,
             HERE / 'photo_joint_tone_training_data.py',
             HERE / 'photo_main_dibit_pulse.py',
             HERE / 'photo_joint_line_filter_screen.py',
             HERE / 'photo_main_dibit_dac_decode.py',
             HERE / 'photo_a1_dynamic_mode_replay.py')
    report = dict(experiment='free-running LS273 latch phase sensitivity of candidate Y7-to-B5 route',
                  fixture=dict(period_visits=PERIOD, samples=SAMPLES,
                               assumed_sample_rate_hz=9600,
                               assumed_dac_b5_weight=8,
                               assumed_a2_mid_code_gate=4,
                               analog='1950 Hz Q=1 bandpass',
                               receiver_sample_shift=6),
                  cases=cases,
                  limitations=[
                      'Only offset zero is directly anchored to all 832 Y7 samples in each full real-PROM run; other offsets project the R1 recurrence verified on the first 18 A4 dibits.',
                      'The D127 pulse source, 9600 Hz clock and latch phase, Y7-to-D4 route, DAC mapping, A2 gate and analog path remain assumptions.',
                      'A fixed external receive sample shift can make one late decision fail at some latch phases; this is not a physical receiver measurement.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
