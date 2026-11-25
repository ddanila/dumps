"""Sweep all 375 PC129 sampling phases for the joined transmitter fixture."""

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from photo_127_liveness import ROM
from photo_a1_dynamic_mode_replay import tone_summary
from photo_dac_bus_permutations import (SELECTED, mapped_codes,
                                        matched_filter_basis, score)
from photo_joint_tone_training_data import (DATA_STEP, SEGMENT_SYMBOLS,
                                            SILENCE_SYMBOLS, TONE_STEP,
                                            TONE_SYMBOLS, TOTAL_SYMBOLS,
                                            segment2_from_txd)
from photo_main_dibit_pulse import VISITS_PER_SAMPLE, VISITS_PER_SYMBOL, scenario_inputs

JOINT = HERE / 'results/photo-joint-tone-training-data.json'
TXREADY = HERE / 'results/main-loop-usart-txready.json'
BUSES = HERE / 'results/photo-dac-bus-permutations.json'


def code_at_each_visit(rom, inputs):
    phase = 3
    codes = bytearray()
    for step in inputs[:TOTAL_SYMBOLS * VISITS_PER_SYMBOL]:
        phase = (phase + step) & 255
        codes.append((phase - rom[256 + phase]) & 255)
    return codes


def screen_case(selector, segment2, validated, rom, buses):
    target = [3] * SEGMENT_SYMBOLS + segment2
    inputs = ([TONE_STEP] * (TONE_SYMBOLS * VISITS_PER_SYMBOL) +
              [DATA_STEP] * (SILENCE_SYMBOLS * VISITS_PER_SYMBOL) +
              scenario_inputs(target))
    codes = code_at_each_visit(rom, inputs)
    rows = []
    for phase in range(VISITS_PER_SAMPLE):
        raw = codes[phase::VISITS_PER_SAMPLE]
        if len(raw) != TOTAL_SYMBOLS * 8:
            raise ValueError(('sample count changed', selector, phase))
        if phase == 0:
            digest = hashlib.sha256(bytes(mapped_codes(raw, SELECTED))).hexdigest()
            if digest != validated['selected_bus_sample_sha256']:
                raise ValueError(('PROM-validated sample digest changed', selector))
        tone = tone_summary(mapped_codes(raw[:TONE_SYMBOLS * 8], SELECTED))
        basis = matched_filter_basis(raw[(TONE_SYMBOLS + SILENCE_SYMBOLS) * 8:])
        decisions = [score(basis, target, bus) for bus in buses]
        if {count for _, count in decisions} != {62}:
            raise ValueError(('decision count changed', selector, phase))
        rows.append(dict(offset=phase, peak_hz=tone['peak_hz'],
                         r2_1800=tone['r2_1800'], r2_2100=tone['r2_2100'],
                         errors_by_bus=[errors for errors, _ in decisions]))
    zero_by_bus = [sum(row['errors_by_bus'][bus] == 0 for row in rows)
                   for bus in range(len(buses))]
    both = [row['offset'] for row in rows if row['peak_hz'] == 2100 and
            all(errors == 0 for errors in row['errors_by_bus'])]
    return dict(selector=selector, offsets_checked=len(rows),
                tone_peak_counts=dict(sorted(Counter(row['peak_hz'] for row in rows).items())),
                zero_error_offsets_by_bus=zero_by_bus,
                all_buses_zero_error_offsets=sum(all(errors == 0 for errors in row['errors_by_bus'])
                                                 for row in rows),
                joint_tone_and_all_bus_zero_error_offsets=both,
                selected_offsets=[rows[index] for index in
                                  (0, 1, 2, 3, 4, 16, 64, 128, 256, 374)],
                worst_errors_by_bus=[max(row['errors_by_bus'][bus] for row in rows)
                                     for bus in range(len(buses))],
                r2_2100_range=[min(row['r2_2100'] for row in rows),
                               max(row['r2_2100'] for row in rows)])


def run(out=HERE / 'results/photo-joint-output-clock-phase.json'):
    joint = json.loads(JOINT.read_text())
    txready = json.loads(TXREADY.read_text())
    buses = [row['input_bit_to_dac_code_bit'] for row in
             json.loads(BUSES.read_text())['zero_error_candidates']]
    if len(buses) != 12 or len(joint['cases']) != 2:
        raise ValueError('joined fixture or bus coverage changed')
    rom = ROM.read_bytes()
    cases = []
    for validated in joint['cases']:
        selector = validated['selector']
        clock_case = next(case for case in txready['cases']
                          if case['selector'] == selector)
        cases.append(screen_case(selector, segment2_from_txd(clock_case),
                                 validated, rom, buses))
    common_offsets = sorted(set(cases[0]['joint_tone_and_all_bus_zero_error_offsets']) &
                            set(cases[1]['joint_tone_and_all_bus_zero_error_offsets']))
    paths = [Path(__file__), JOINT, TXREADY, BUSES, ROM,
             HERE / 'photo_joint_tone_training_data.py',
             HERE / 'photo_dac_bus_permutations.py',
             HERE / 'photo_a1_dynamic_mode_replay.py',
             HERE / 'photo_main_dibit_pulse.py']
    report = dict(status='all distinct PC129 sample offsets screened against the recurrence checked by the joined real-PROM trace',
                  fixture=dict(sample_rule='one hypothetical DAC capture per 375 PC129 visits; offset 0..374',
                               oscillator_hz=14400000, assumed_microinstruction_clock_hz=14400000,
                               four_word_loop_hz=3600000, sample_hz=9600,
                               visits_per_sample=VISITS_PER_SAMPLE,
                               symbol_visits=VISITS_PER_SYMBOL,
                               tone_step_hex=f'{TONE_STEP:02X}',
                               data_step_hex=f'{DATA_STEP:02X}',
                               tone_phase_advance_per_sample=(TONE_STEP * VISITS_PER_SAMPLE) & 255,
                               data_phase_advance_per_sample=(DATA_STEP * VISITS_PER_SAMPLE) & 255,
                               tone_and_data_dac_bus=SELECTED,
                               data_decoding_buses=12,
                               effective_symbol_rate_by_microinstruction_divisor={
                                   str(divisor): 14400000 // (4 * VISITS_PER_SYMBOL * divisor)
                                   for divisor in range(1, 5)}),
                  cases=cases,
                  common_zero_error_offsets_across_both_selectors=common_offsets,
                  common_zero_error_offset_count=len(common_offsets),
                  limitations=['Only offset 0 was captured and checked against the complete real-PROM trace; other offsets project the same verified PC129 recurrence.',
                               'The 375:1 sample divider, absolute sequencer clock, latch data source and DAC route are hypotheses, not traced board connections.',
                               'Matched-filter decisions are from an external reference receiver, not the DSC receive path.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path,
                        default=HERE / 'results/photo-joint-output-clock-phase.json')
    args = parser.parse_args()
    for case in run(args.out)['cases']:
        print(case['selector'], case['tone_peak_counts'],
              case['all_buses_zero_error_offsets'],
              len(case['joint_tone_and_all_bus_zero_error_offsets']))
