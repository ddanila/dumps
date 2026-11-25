"""Screen photo-compatible DAC buses against full controller dibit decisions."""

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from photo_127_liveness import ROM
from photo_a1_dynamic_mode_replay import tone_summary
from photo_dac08_bus_order_screen import q_to_dac, swap_bits
from photo_main_dibit_pulse import (BASE, PULSE_VISITS, VISITS_PER_SAMPLE,
                                    VISITS_PER_SYMBOL, dibit_rule)
from reference_modem import receive, transmit

PULSE_REPORT = HERE / 'results/photo-main-dibit-pulse.json'
CONTROLLER = HERE / 'results/main-loop-serial.json'
INPUT_ORDERS = ('ordered_y_to_d', 'swap_y7_y4_to_d')
OUTPUT_ORDERS = ('reverse', 'rotate_q_to_next_b', 'swap_q4_q5')
FIXED_SAMPLE_SHIFT = 4


def candidate_codes(rom, dibits, input_order, output_order, pulsed=True):
    phase = 3
    codes = []
    ends = []
    for dibit in dibits:
        pulse_step = dibit_rule(dibit & 1, dibit >> 1)
        for visit in range(VISITS_PER_SYMBOL):
            step = pulse_step if pulsed and visit < PULSE_VISITS else BASE
            phase = (phase + step) & 255
            if visit % VISITS_PER_SAMPLE == 0:
                y = (phase - rom[256 + phase]) & 255
                if input_order == 'swap_y7_y4_to_d':
                    y = swap_bits(y, 7, 4)
                elif input_order != 'ordered_y_to_d':
                    raise ValueError(input_order)
                codes.append(q_to_dac(y, output_order))
        ends.append(phase)
    return codes, ends


def correlation(first, second):
    if len(first) != len(second):
        raise ValueError('unaligned waveform lengths')
    a_mean = sum(first) / len(first)
    b_mean = sum(second) / len(second)
    a = [value - a_mean for value in first]
    b = [value - b_mean for value in second]
    denominator = math.sqrt(sum(v * v for v in a) *
                            sum(v * v for v in b))
    return (sum(x * y for x, y in zip(a, b)) / denominator
            if denominator else 0.0)


def decision_result(codes, dibits, sample_shift=FIXED_SAMPLE_SHIFT):
    aligned = [value - 128 for value in codes[sample_shift:]]
    aligned = aligned[:len(aligned) // 8 * 8]
    decisions = receive(aligned)
    expected = dibits[1:len(decisions) + 1]
    errors = [i for i, (actual, target) in
              enumerate(zip(decisions, expected)) if actual != target]
    return dict(decisions=len(decisions), errors=len(errors),
                error_indices=errors, first_8_decisions=decisions[:8],
                first_8_expected=expected[:8],
                decision_counts={str(value): decisions.count(value)
                                 for value in range(4)})


def run(out=HERE / 'results/photo-main-dibit-dac-decode.json'):
    pulse = json.loads(PULSE_REPORT.read_text())
    controller = json.loads(CONTROLLER.read_text())
    if pulse['source_sha256'][str(CONTROLLER.relative_to(HERE.parents[2]))] != hashlib.sha256(CONTROLLER.read_bytes()).hexdigest():
        raise ValueError('pulse run uses a different controller stream')
    if len(pulse['cases']) != 4:
        raise ValueError('expected four full-stream pulse cases')
    rom = ROM.read_bytes()
    case_by_selector = {case['selector']: case for case in pulse['cases']}
    controller_by_selector = {row['selector']: row for row in controller['rows']
                              if row['selector'] in case_by_selector}
    if set(case_by_selector) != set(controller_by_selector):
        raise ValueError('controller class coverage changed')
    for order in OUTPUT_ORDERS:
        if q_to_dac(0x10, order) != 0x08:
            raise ValueError('candidate Q4→DAC B5 changed')
    mappings = []
    for input_order in INPUT_ORDERS:
        for output_order in OUTPUT_ORDERS:
            rows = []
            for selector in sorted(case_by_selector):
                case = case_by_selector[selector]
                dibits = case['all_dibits']
                codes, ends = candidate_codes(rom, dibits, input_order,
                                              output_order)
                if input_order == 'ordered_y_to_d' and output_order == 'swap_q4_q5':
                    if ([f'{value:02X}' for value in codes[:16]] !=
                            [row['dac_code'] for row in case['first_16_dac_samples']] or
                            hashlib.sha256(bytes(codes)).hexdigest() !=
                            case['dac_sample_sha256'] or
                            tone_summary(codes) != case['full_stream_tone_fit']):
                        raise AssertionError(('executed DAC recurrence mismatch',
                                              selector))
                    for symbol, (phase, recorded) in enumerate(zip(ends,
                                                                    case['symbol_ends'])):
                        baseline = (3 + (symbol + 1) *
                                    VISITS_PER_SYMBOL * BASE) & 255
                        if (recorded['phase'] != f'{phase:02X}' or
                                recorded['cumulative_offset'] !=
                                f'{(phase - baseline) & 255:02X}'):
                            raise AssertionError(('executed phase mismatch',
                                                  selector, symbol))
                reference = transmit(dibits)
                score = abs(correlation(codes[FIXED_SAMPLE_SHIFT:],
                                        reference[:-FIXED_SAMPLE_SHIFT]))
                decision = decision_result(codes, dibits)
                rows.append(dict(selector=selector,
                                 dibits=len(dibits),
                                 projected_dac_peak_hz=tone_summary(codes)['peak_hz'],
                                 reference_peak_hz=tone_summary(reference)['peak_hz'],
                                 abs_reference_correlation=round(score, 6),
                                 **decision))
            mappings.append(dict(y_to_ls273=input_order,
                                 ls273_q_to_dac=output_order,
                                 total_decisions=sum(row['decisions'] for row in rows),
                                 total_errors=sum(row['errors'] for row in rows),
                                 mean_abs_reference_correlation=round(
                                     sum(row['abs_reference_correlation'] for row in rows)
                                     / len(rows), 6),
                                 cases=rows))
    selected = next(row for row in mappings if
                    row['y_to_ls273'] == 'ordered_y_to_d' and
                    row['ls273_q_to_dac'] == 'swap_q4_q5')
    if (selected['total_decisions'] != 104 or selected['total_errors'] != 1 or
            [row['errors'] for row in selected['cases']] != [1, 0, 0, 0] or
            min(row['total_errors'] for row in mappings if row is not selected) < 30):
        raise AssertionError('candidate DAC decision discriminator changed')
    selected_on_00 = min(mappings, key=lambda mapping: mapping['cases'][0]['errors'])
    if selected_on_00 is not selected:
        raise AssertionError('first controller class did not select same bus')
    selection_check = dict(training_selector='00',
                           training_errors=selected['cases'][0]['errors'],
                           held_out_selectors=['20', '40', '60'],
                           held_out_decisions=sum(row['decisions'] for row in
                                                  selected['cases'][1:]),
                           held_out_errors=sum(row['errors'] for row in
                                               selected['cases'][1:]))
    timing_sweep = []
    for sample_shift in range(8):
        cases = []
        for selector in sorted(case_by_selector):
            dibits = case_by_selector[selector]['all_dibits']
            codes, _ = candidate_codes(rom, dibits, 'ordered_y_to_d',
                                       'swap_q4_q5')
            cases.append(dict(selector=selector,
                              **decision_result(codes, dibits, sample_shift)))
        timing_sweep.append(dict(sample_shift=sample_shift,
                                 total_decisions=sum(row['decisions'] for row in cases),
                                 total_errors=sum(row['errors'] for row in cases),
                                 cases=cases))
    if ([row['total_errors'] for row in timing_sweep] !=
            [60, 42, 13, 3, 1, 3, 7, 24]):
        raise AssertionError('candidate sample timing screen changed')
    controls = []
    for selector in sorted(case_by_selector):
        dibits = case_by_selector[selector]['all_dibits']
        codes, _ = candidate_codes(rom, dibits, 'ordered_y_to_d',
                                   'swap_q4_q5', pulsed=False)
        controls.append(dict(selector=selector,
                             **decision_result(codes, dibits)))
    if (sum(row['errors'] for row in controls) != 74 or
            any(row['decision_counts']['0'] != row['decisions']
                for row in controls)):
        raise AssertionError('unmodulated control changed')
    paths = [Path(__file__), PULSE_REPORT, CONTROLLER, ROM,
             HERE / 'photo_main_dibit_pulse.py',
             HERE / 'photo_dac08_bus_order_screen.py',
             HERE / 'photo_a1_dynamic_mode_replay.py',
             HERE / 'reference_modem.py',
             HERE.parent / 'board/inventory.json',
             HERE.parents[2] / 'photos/PXL_20261123_114854803.jpg']
    report = dict(
        status='one photo-compatible candidate DAC bus lets an independent reference receiver recover 103 of 104 controller dibits',
        fixture=dict(input='four full controller USART streams through the previously executed parity/counter pulse and PC129 phase walk',
                     output='PC129 Am2901 Y sampled once per 375 visits; six simple LS273/DAC08 bus orders preserving the photo-suggested Q4→B5 segment',
                     receiver='independent V.26-class known-carrier raised-cosine reference decoder, not DSC2847 receiver microcode',
                     fixed_sample_shift=FIXED_SAMPLE_SHIFT,
                     ac_center=128),
        mappings=mappings,
        selection_check=selection_check,
        selected_bus_timing_sweep=timing_sweep,
        no_pulse_control=dict(cases=controls,
                              total_errors=sum(row['errors'] for row in controls),
                              total_decisions=sum(row['decisions'] for row in controls)),
        limitations=['The output bus, sample clock and analog line route are hypotheses; one photographed Q4→B5 segment does not establish the other seven bits.',
                     'The four-visit USART dibit pulse and its parity/counter wiring are assumed, not traced.',
                     'The reference receiver has known carrier and fixed chosen timing; it is not the Nokia DSC receiver and does not satisfy C3.',
                     'The candidate code stream has abrupt phase changes and no demonstrated pulse shaping, segment-1 reversals or physical DAC output.'],
        source_sha256={str(path.relative_to(HERE.parents[2])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path,
                        default=HERE / 'results/photo-main-dibit-dac-decode.json')
    args = parser.parse_args()
    for row in run(args.out)['mappings']:
        print(row['y_to_ls273'], row['ls273_q_to_dac'],
              row['total_errors'], '/', row['total_decisions'],
              row['mean_abs_reference_correlation'])
