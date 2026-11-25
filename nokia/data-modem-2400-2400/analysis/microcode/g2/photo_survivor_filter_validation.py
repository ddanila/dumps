"""Test a fixed one-pole analog continuation on the surviving DAC buses."""

import hashlib
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from photo_127_liveness import ROM
from photo_a1_dynamic_mode_replay import tone_summary
from photo_dac_bus_permutations import SELECTED, mapped_codes, raw_y_codes
from photo_joint_tone_training_data import (DATA_STEP, SEGMENT_SYMBOLS,
                                            SILENCE_SYMBOLS, TONE_STEP,
                                            TONE_SYMBOLS, raw_codes,
                                            segment2_from_txd)
from photo_joint_waveform_shape_screen import best_fit, reference_templates
from photo_main_dibit_dac_decode import decision_result
from photo_main_dibit_pulse import VISITS_PER_SYMBOL, scenario_inputs

RANDOM = HERE / 'results/photo-random-dibit-validation.json'
JOINED = HERE / 'results/photo-joint-tone-training-data.json'
SHAPE = HERE / 'results/photo-joint-waveform-shape-screen.json'
TXREADY = HERE / 'results/main-loop-usart-txready.json'
ALPHA = 0.75


def one_pole(values):
    state = float(values[0])
    result = []
    for value in values:
        state = ALPHA * value + (1 - ALPHA) * state
        result.append(state)
    return result


def fit_cases(rom, survivors):
    random_report = json.loads(RANDOM.read_text())
    joined = {case['selector']: case for case in json.loads(JOINED.read_text())['cases']}
    shape = {case['selector']: case for case in json.loads(SHAPE.read_text())['cases']}
    txready = json.loads(TXREADY.read_text())
    prior_buses = [row['input_bit_to_dac_code_bit'] for row in
                   json.loads((HERE / 'results/photo-dac-bus-permutations.json').read_text())['zero_error_candidates']]
    rows = []
    for selector in ('40', '60'):
        clock_case = next(case for case in txready['cases']
                          if case['selector'] == selector)
        dibits = [3] * SEGMENT_SYMBOLS + segment2_from_txd(clock_case)
        inputs = ([TONE_STEP] * (TONE_SYMBOLS * VISITS_PER_SYMBOL) +
                  [DATA_STEP] * (SILENCE_SYMBOLS * VISITS_PER_SYMBOL) +
                  scenario_inputs(dibits))
        full, _ = raw_codes(rom, inputs)
        digest = hashlib.sha256(bytes(mapped_codes(full, SELECTED))).hexdigest()
        assert digest == joined[selector]['selected_bus_sample_sha256']
        raw = full[(TONE_SYMBOLS + SILENCE_SYMBOLS) * 8:]
        assert raw == raw_y_codes(rom, dibits)
        templates = reference_templates(dibits)
        for bus_index, bus in enumerate(survivors):
            codes = mapped_codes(raw, bus)
            original, _ = best_fit(codes, templates)
            previous_index = prior_buses.index(bus)
            saved = next(row['pulse_shaped_reference_r2'] for row in
                         shape[selector]['fits'] if row['pc'] == '129' and
                         row['bus_index'] == previous_index)
            assert original == saved
            filtered, _ = best_fit(one_pole(codes), templates)
            raw_decision = decision_result(codes, dibits)
            filtered_decision = decision_result(one_pole(codes), dibits)
            assert raw_decision['errors'] == filtered_decision['errors'] == 0
            rows.append(dict(kind='standard', source=selector,
                             bus_index=bus_index, raw_r2=original,
                             filtered_r2=filtered,
                             decisions=raw_decision['decisions'],
                             filtered_errors=filtered_decision['errors']))
    for seed in (row['seed'] for row in random_report['projected_cases']):
        generator = random.Random(seed)
        dibits = [generator.randrange(4) for _ in range(64)]
        raw = raw_y_codes(rom, dibits)
        templates = reference_templates(dibits)
        for bus_index, bus in enumerate(survivors):
            codes = mapped_codes(raw, bus)
            original, _ = best_fit(codes, templates)
            filtered, _ = best_fit(one_pole(codes), templates)
            raw_decision = decision_result(codes, dibits)
            filtered_decision = decision_result(one_pole(codes), dibits)
            assert raw_decision['errors'] == filtered_decision['errors'] == 0
            rows.append(dict(kind='synthetic', source=seed,
                             bus_index=bus_index, raw_r2=original,
                             filtered_r2=filtered,
                             decisions=raw_decision['decisions'],
                             filtered_errors=filtered_decision['errors']))
    return rows


def run(out=HERE / 'results/photo-survivor-filter-validation.json'):
    rom = ROM.read_bytes()
    survivors = json.loads(RANDOM.read_text())['zero_error_survivors']
    assert len(survivors) == 6
    rows = fit_cases(rom, survivors)
    assert len(rows) == 36 and all(row['filtered_r2'] > row['raw_r2'] for row in rows)
    tone_raw, _ = raw_codes(rom, [TONE_STEP] * (TONE_SYMBOLS * VISITS_PER_SYMBOL))
    tone = []
    for bus_index, bus in enumerate(survivors):
        codes = mapped_codes(tone_raw, bus)
        raw_peak = tone_summary(codes)['peak_hz']
        filtered_peak = tone_summary(one_pole(codes))['peak_hz']
        assert raw_peak == filtered_peak == 2100
        tone.append(dict(bus_index=bus_index, raw_peak_hz=raw_peak,
                         filtered_peak_hz=filtered_peak))
    paths = [Path(__file__), RANDOM, JOINED, SHAPE, TXREADY, ROM,
             HERE / 'photo_dac_bus_permutations.py',
             HERE / 'photo_joint_tone_training_data.py',
             HERE / 'photo_joint_waveform_shape_screen.py',
             HERE / 'photo_main_dibit_dac_decode.py',
             HERE / 'photo_main_dibit_pulse.py',
             HERE / 'reference_modem.py']
    report = dict(status='conditional single-pole analog continuation improves candidate waveform shape',
                  fixture=dict(alpha=ALPHA,
                               filter='y[n]=0.75*x[n]+0.25*y[n-1], initialized at first sample',
                               sample_rate_hz=9600, bus_orders=len(survivors),
                               standard_sequences=2, synthetic_sequences=4,
                               sequence_symbols=64),
                  rows=rows, tone=tone,
                  raw_r2_range=[min(row['raw_r2'] for row in rows),
                                max(row['raw_r2'] for row in rows)],
                  filtered_r2_range=[min(row['filtered_r2'] for row in rows),
                                     max(row['filtered_r2'] for row in rows)],
                  limitations=['The one-pole filter is a fixed diagnostic model, not a traced or measured Nokia analog circuit.',
                               'The DAC byte route, 9600 Hz latch clock, D127 decoder and analog line connection remain hypotheses.',
                               'The random streams use a ROM recurrence checked on two 32-symbol full-PROM prefixes; they are not real 8031 traffic.',
                               'Zero errors from an external reference receiver do not establish DSC receive or echo-canceller behavior.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    print(report['raw_r2_range'], report['filtered_r2_range'],
          len(report['rows']))
