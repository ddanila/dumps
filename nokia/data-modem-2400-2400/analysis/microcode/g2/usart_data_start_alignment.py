"""Screen first-data-byte bit alignment for the paced USART-to-DSC candidate."""

import argparse
import hashlib
import json
from pathlib import Path

from controller_segment2_pattern import standard_bits
from photo_127_liveness import ROM
from photo_controller_path import fixture
from photo_dac_bus_permutations import (matched_filter_basis, raw_y_codes,
                                        score)
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from photo_segment1_to_segment2_continuous import replay

HERE = Path(__file__).resolve().parent
PACED = HERE / 'results/main-loop-usart-txready.json'
BUS = HERE / 'results/photo-dac-bus-permutations.json'
PRIOR = HERE / 'results/photo-segment1-to-segment2-continuous.json'
CONTROL_RUNS = {('40', 0), ('60', 2)}


def serial_bits(values):
    return [(value >> bit) & 1 for value in values for bit in range(8)]


def dibits(bits):
    return [(bits[index] << 1) | bits[index + 1]
            for index in range(0, len(bits), 2)]


def run(out=HERE / 'results/usart-data-start-alignment.json'):
    paced = json.loads(PACED.read_text())
    buses = [row['input_bit_to_dac_code_bit'] for row in
             json.loads(BUS.read_text())['zero_error_candidates']]
    prior = json.loads(PRIOR.read_text())
    if len(buses) != 12 or len(paced['cases']) != 16:
        raise ValueError('input coverage changed')
    rom = ROM.read_bytes()
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    cases = []
    for selector, polynomial in (('40', 'GPC'), ('60', 'GPA')):
        phases = [row for row in paced['cases'] if row['selector'] == selector]
        if len(phases) != 8 or len({tuple(row['first_nine_transmitted_bytes'])
                                    for row in phases}) != 1:
            raise ValueError(('TxD bytes differ by clock phase', selector))
        baseline = next(row for row in phases if row['tx_clock_phase_ticks'] == 0)
        if baseline['sync_fill_bits_since_a3_entry'] < 64:
            raise ValueError(('phase-zero fill window too short', selector))
        data = serial_bits([int(value, 16) for value in
                            baseline['first_nine_transmitted_bytes']])
        expected = [3] * 32 + dibits(standard_bits(polynomial))
        for skip in range(9):
            offered = [3] * 32 + dibits(data[skip:skip + 64])
            if len(offered) != 64:
                raise ValueError(('short data window', selector, skip))
            raw = raw_y_codes(rom, offered)
            basis = matched_filter_basis(raw)
            scores = [score(basis, expected, bus) for bus in buses]
            if any(decisions != 62 for _, decisions in scores):
                raise ValueError(('aligned decision count changed', selector, skip))
            row = dict(selector=selector, polynomial=polynomial,
                       first_data_bit_skipped=skip,
                       a3_fill_symbols=32,
                       input_symbol_mismatches=sum(a != b for a, b in
                                                   zip(offered, expected)),
                       errors_by_12_candidate_buses=[errors for errors, _ in scores])
            if skip == 1:
                previous = next(item for item in prior['cases']
                                if item['selector'] == selector and
                                item['a3_idle_rule'] == 'repeated_11_idle')
                if (offered != previous['a3_symbols'] +
                        previous['actual_a4_segment2_symbols'] or
                        previous['errors_by_12_candidate_buses'] !=
                        row['errors_by_12_candidate_buses']):
                    raise ValueError(('skip-one input differs from prior PROM run', selector))
                row['real_prom_trace_digest'] = previous['trace_digest']
                row['real_prom_microinstructions'] = previous['microinstructions']
                row['real_prom_selected_bus_sample_sha256'] = previous['selected_bus_sample_sha256']
            if (selector, skip) in CONTROL_RUNS:
                execution, checked_raw = replay(offered, f'TxD skip {skip} control',
                                                rom, base, mapping)
                if raw != checked_raw:
                    raise ValueError(('control PROM sample reconstruction changed',
                                      selector, skip))
                row['real_prom_trace_digest'] = execution['trace_digest']
                row['real_prom_microinstructions'] = execution['microinstructions']
                row['real_prom_selected_bus_sample_sha256'] = execution['selected_bus_sample_sha256']
                row['real_prom_pc129_visits'] = execution['pc129_visits']
            cases.append(row)
    for selector in ('40', '60'):
        zero = [row['first_data_bit_skipped'] for row in cases
                if row['selector'] == selector and
                set(row['errors_by_12_candidate_buses']) == {0}]
        if zero != [1]:
            raise ValueError(('unique alignment changed', selector, zero))
    paths = [Path(__file__), PACED, BUS, PRIOR, ROM,
             HERE / 'photo_segment1_to_segment2_continuous.py',
             HERE / 'photo_dac_bus_permutations.py',
             HERE / 'photo_controller_path.py',
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             HERE / 'controller_segment2_pattern.py', MAPPINGS['q3']]
    report = dict(
        status='only skipping the first data bit yields zero standard segment-2 decisions for both controller selectors in the paced-8251 candidate; adjacent alignments are verified real-PROM controls',
        fixture=dict(tx_clock_phase_ticks=0,
                     source='last 64 FF-fill bits after A3 entry, then first nine actually shifted 8251A TxD data bytes',
                     alignment='try skip 0 through 8 data bits before grouping the next 64 left-digit-first into 32 dibits',
                     dsc='q3 upper-bank four-visit D127 parity/counter pulse and 375-visit Y129 DAC capture',
                     real_prom_controls=[dict(selector=selector, skip=skip)
                                         for selector, skip in sorted(CONTROL_RUNS)]),
        cases=cases,
        limitations=['The connection from USART TxD and a first-byte timing cue to D127 remains a labelled circuit hypothesis.',
                     'Only the two neighboring control alignments and the previously checked skip-one inputs have full real-PROM traces; other scores use the independently verified ROM/Y recurrence.',
                     'The 64 FF bits are selected as a window inside the phase-zero fill interval; the physical segment-1 start is not measured.',
                     'The DAC bus, sample clock, analog line path, DSC receiver and echo canceller remain unverified.'],
        source_sha256={str(path.relative_to(HERE.parents[2])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path,
                        default=HERE / 'results/usart-data-start-alignment.json')
    args = parser.parse_args()
    report = run(args.out)
    for case in report['cases']:
        print(case['selector'], case['first_data_bit_skipped'],
              set(case['errors_by_12_candidate_buses']))
