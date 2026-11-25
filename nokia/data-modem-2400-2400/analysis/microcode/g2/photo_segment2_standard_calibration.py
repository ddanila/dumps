"""Replay real controller segment-2 bits through both candidate D127 dibit orders."""

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from controller_segment2_pattern import source_windows, standard_bits
from photo_127_liveness import ROM
from photo_controller_path import fixture
from photo_dac_bus_permutations import (SELECTED, mapped_codes,
                                        matched_filter_basis, raw_y_codes, score)
from photo_frame_toggle_edge_pulse import inspect
from photo_i0_hold_screen import hold_candidate
from photo_main_dibit_pulse import BASE, VISITS_PER_SYMBOL, scenario_inputs
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from reference_modem import phase_positions

LONG = HERE / 'results/main-loop-long.json'
BUSES = HERE / 'results/photo-dac-bus-permutations.json'
PATTERN = HERE / 'results/controller-segment2-pattern.json'


def replay(dibits, rom, base, mapping):
    inputs = scenario_inputs(dibits)
    scenario = hold_candidate(base)
    scenario['name'] += '; controller A4 segment-2 dibits'
    scenario['initial']['q'] = 0
    scenario['io']['read']['pc_sequences'][str(0x127)] = inputs
    scenario['io']['read']['pc_sequences'][str(0x12c)] = [0xEA]
    scenario['io']['read']['address']['bank_by_pc'] = {str(0x129): 256,
                                                       str(0x12e): 256}
    cycles = (len(dibits) * VISITS_PER_SYMBOL + 64) * 4
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, cycles, mode='integrated',
                         out=temporary, trace_limit=cycles)
        trace = inspect(Path(temporary) / 'trace.jsonl', rom, inputs, dibits)
    if (not result['clean'] or result['completed_cycles'] != cycles or
            result['address_counts'].get(0x129) != trace['pc129_visits'] or
            result['address_counts'].get(0x12e, 0)):
        raise ValueError('DSC PROM replay did not complete')
    raw = raw_y_codes(rom, dibits)
    if hashlib.sha256(bytes(mapped_codes(raw, SELECTED))).hexdigest() != trace['sample_sha256']:
        raise ValueError('reconstructed DAC stream differs from executed PROM')
    offsets = [(phase - (3 + (index + 1) * VISITS_PER_SYMBOL * BASE)) & 255
               for index, phase in enumerate(trace['symbol_end_phases'])]
    return dict(microinstructions=cycles, pc129_visits=trace['pc129_visits'],
                trace_digest=result['trace_digest'],
                selected_bus_sha256=trace['sample_sha256'],
                first_16_selected_bus_codes=[f'{value:02X}' for value in trace['samples'][:16]],
                symbol_phase_offsets=offsets), raw


def run(out=HERE / 'results/photo-segment2-standard-calibration.json'):
    controller = json.loads(LONG.read_text())
    pattern = json.loads(PATTERN.read_text())
    buses = [row['input_bit_to_dac_code_bit'] for row in
             json.loads(BUSES.read_text())['zero_error_candidates']]
    if len(pattern['exact_64_bit_windows']) != 4 or len(buses) != 12:
        raise ValueError('source pattern or candidate bus count changed')
    rom = ROM.read_bytes()
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    cases = []
    for selector, polynomial in (('40', 'GPC'), ('60', 'GPA')):
        controller_row = next(row for row in controller['runs']
                              if row['selector'] == selector)
        window = source_windows(controller_row)[0]
        bits = window['first_64_bits_from_second_bit']
        if bits != standard_bits(polynomial):
            raise ValueError(('A4 bits differ from standard', selector))
        standard_dibits = [(bits[index] << 1) | bits[index + 1]
                           for index in range(0, 64, 2)]
        direct_dibits = [bits[index] | (bits[index + 1] << 1)
                         for index in range(0, 64, 2)]
        for name, offered in (('first_serial_bit_to_D127_bit0', direct_dibits),
                              ('first_serial_bit_to_D127_bit1', standard_dibits)):
            execution, raw = replay(offered, rom, base, mapping)
            basis = matched_filter_basis(raw)
            decisions = [score(basis, standard_dibits, bus) for bus in buses]
            if any(total != 30 for _, total in decisions):
                raise ValueError(('candidate decision count changed', selector, name))
            if name == 'first_serial_bit_to_D127_bit1':
                target_offsets = [(-16 * phase) & 255
                                  for phase in phase_positions(standard_dibits)]
                if execution['symbol_phase_offsets'] != target_offsets or any(
                        errors for errors, _ in decisions):
                    raise ValueError(('standard segment-2 calibration failed', selector))
            cases.append(dict(selector=selector, polynomial=polynomial,
                              first_a4_iteration=window['first_iteration'],
                              controller_bytes=window['bytes'],
                              input_lane_order=name,
                              standard_dibits=standard_dibits,
                              errors_by_12_candidate_buses=[errors for errors, _ in decisions],
                              aligned_decisions=30, **execution))
    for case in cases:
        if case['input_lane_order'] == 'first_serial_bit_to_D127_bit0':
            expected_errors = 6 if case['selector'] == '40' else 8
            if set(case['errors_by_12_candidate_buses']) != {expected_errors}:
                raise ValueError(('direct-lane control changed', case['selector']))
    paths = [Path(__file__), LONG, BUSES, PATTERN, ROM,
             HERE / 'controller_segment2_pattern.py',
             HERE / 'photo_dac_bus_permutations.py',
             HERE / 'photo_frame_toggle_edge_pulse.py',
             HERE / 'photo_main_dibit_pulse.py',
             HERE / 'photo_i0_hold_screen.py',
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             HERE / 'reference_modem.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3']]
    report = dict(
        status='controller A4 segment-2 bits select the standard phase sequence in the candidate PROM/DAC path only when the two serial-bit lanes are exchanged',
        fixture=dict(controller='unchanged 8031 A4/A5 port-01 bytes, 64 bits starting at bit 1 of A4',
                     d127='four-visit parity/counter dibit pulse; swap or preserve the two serial-bit lanes',
                     sample='candidate Y129 latch every 375 visits, 12 photo-B5-compatible DAC bus orders'),
        cases=cases,
        limitations=['The parity/counter pulse, two-bit lane assignment, DAC capture clock, complete DAC bus and analog line path are untraced hypotheses.',
                     'The standard comparison uses 30 aligned matched-filter decisions out of 32 symbols; the first and last symbols are not independent decisions.',
                     'The first-bit-low convention used by earlier data screens is not the V.26 ter left-digit-first convention; their zero-error counts alone do not prove standard-compliant phase mapping.',
                     'The controller fixture uses forced timer expiry and synthetic serial events, so natural A4 duration is not established.'],
        source_sha256={str(path.relative_to(HERE.parents[2])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path,
                        default=HERE / 'results/photo-segment2-standard-calibration.json')
    args = parser.parse_args()
    report = run(args.out)
    for case in report['cases']:
        print(case['selector'], case['input_lane_order'],
              case['pc129_visits'], set(case['errors_by_12_candidate_buses']))
