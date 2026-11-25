"""Run a conditional A3 idle pattern into real A4 segment-2 bits without resetting DSC."""

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
from controller_segment2_pattern import standard_bits
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

CONTROLLER = HERE / 'results/main-loop-timer1-segment2.json'
BUSES = HERE / 'results/photo-dac-bus-permutations.json'
PREVIOUS = HERE / 'results/photo-segment2-standard-calibration.json'
SYMBOLS_PER_SEGMENT = 32


def controller_segment2(case):
    values = [int(value, 16) for value in
              case['a4_port01_bytes'] + [case['first_a5_port01_byte']]]
    bits = [(value >> bit) & 1 for value in values for bit in range(8)][1:65]
    if len(bits) != 64 or bits != standard_bits(case['polynomial']):
        raise ValueError(('timer-paced controller bits changed', case['selector']))
    return [(bits[index] << 1) | bits[index + 1] for index in range(0, 64, 2)]


def replay(dibits, label, rom, base, mapping):
    inputs = scenario_inputs(dibits)
    scenario = hold_candidate(base)
    scenario['name'] += f'; A3 {label} then A4 actual segment-2 bits'
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
        raise ValueError(('continuous DSC replay stopped', label))
    raw = raw_y_codes(rom, dibits)
    if hashlib.sha256(bytes(mapped_codes(raw, SELECTED))).hexdigest() != trace['sample_sha256']:
        raise ValueError(('candidate sample reconstruction changed', label))
    offsets = [(phase - (3 + (index + 1) * VISITS_PER_SYMBOL * BASE)) & 255
               for index, phase in enumerate(trace['symbol_end_phases'])]
    reference_offsets = [(-16 * phase) & 255 for phase in phase_positions(dibits)]
    if offsets != reference_offsets:
        raise ValueError(('continuous phase checkpoints differ', label))
    return dict(microinstructions=cycles, pc129_visits=trace['pc129_visits'],
                trace_digest=result['trace_digest'],
                selected_bus_sample_sha256=trace['sample_sha256'],
                boundary_selected_bus_codes=[f'{value:02X}' for value in
                                             trace['samples'][248:264]],
                symbol_phase_offsets=offsets), raw


def run(out=HERE / 'results/photo-segment1-to-segment2-continuous.json'):
    controller = json.loads(CONTROLLER.read_text())
    buses = [row['input_bit_to_dac_code_bit'] for row in
             json.loads(BUSES.read_text())['zero_error_candidates']]
    previous = json.loads(PREVIOUS.read_text())
    if len(buses) != 12 or len(controller['cases']) != 2 or len(previous['cases']) != 4:
        raise ValueError('controller or DAC candidate coverage changed')
    rom = ROM.read_bytes()
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    cases = []
    for controller_case in controller['cases']:
        selector = controller_case['selector']
        segment2 = controller_segment2(controller_case)
        if segment2[0] != 0:
            raise ValueError(('segment-2 first dibit changed', selector))
        for name, idle in (('repeated_11_idle', [3] * SYMBOLS_PER_SEGMENT),
                           ('unmodulated_00_control', [0] * SYMBOLS_PER_SEGMENT)):
            offered = idle + segment2
            execution, raw = replay(offered, name, rom, base, mapping)
            basis = matched_filter_basis(raw)
            scores = [score(basis, [3] * SYMBOLS_PER_SEGMENT + segment2, bus)
                      for bus in buses]
            if any(decisions != 62 for _, decisions in scores):
                raise ValueError(('64-symbol decision coverage changed', selector, name))
            expected_errors = 0 if name == 'repeated_11_idle' else 31
            if {errors for errors, _ in scores} != {expected_errors}:
                raise ValueError(('continuous sequence decode changed', selector, name,
                                  scores))
            first = execution['symbol_phase_offsets'][:SYMBOLS_PER_SEGMENT]
            if name == 'repeated_11_idle' and first != [128, 0] * 16:
                raise ValueError(('segment-1 idle phase changed', selector))
            if name == 'unmodulated_00_control' and first != [0] * 32:
                raise ValueError(('unmodulated control phase changed', selector))
            if execution['symbol_phase_offsets'][31:33] != [0, 0]:
                raise ValueError(('segment boundary phase is discontinuous', selector))
            cases.append(dict(selector=selector, polynomial=controller_case['polynomial'],
                              a3_idle_rule=name,
                              a3_symbols=idle,
                              actual_a4_segment2_symbols=segment2,
                              standard_target_decisions=62,
                              errors_by_12_candidate_buses=[errors for errors, _ in scores],
                              phase_at_last_a3_and_first_a4_symbols=[0, 0],
                              **execution))
    paths = [Path(__file__), CONTROLLER, BUSES, PREVIOUS, ROM,
             HERE / 'controller_segment2_pattern.py',
             HERE / 'photo_dac_bus_permutations.py',
             HERE / 'photo_frame_toggle_edge_pulse.py',
             HERE / 'photo_main_dibit_pulse.py',
             HERE / 'photo_controller_path.py',
             HERE / 'photo_i0_hold_screen.py',
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             HERE / 'reference_modem.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3']]
    report = dict(
        status='one continuous real-PROM phase path can carry hypothetical A3 segment 1 then actual controller A4 segment 2 under a fixed swapped-lane input and DAC bus family',
        fixture=dict(controller='interrupt-paced A3 no-port01 interval followed by exact A4/A5 GPC/GPA 64-bit stream',
                     a3_idle='assume an untraced idle source emits dibit 11 every symbol for 32 symbols, or control 00',
                     input='four-visit D127 parity/counter pulse with first serial bit assigned to pulse lane 1',
                     sample='candidate Y129 capture every 375 PC129 visits, 12 photo-B5-compatible DAC bus orders'),
        cases=cases,
        limitations=['The A3 idle-11 source, its exact 32-symbol duration, parity/counter pulse and controller-to-D127 route are not established by a board trace.',
                     'The DAC sample clock, full DAC bus and analog line path remain candidate projections; no physical output waveform is measured.',
                     'The 62 aligned matched-filter decisions omit the first and last symbols as independent decisions; they are not DSC receiver output.',
                     'No receive or echo-canceller behavior is demonstrated, so C2/C3/C4 remain open.'],
        source_sha256={str(path.relative_to(HERE.parents[2])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path,
                        default=HERE / 'results/photo-segment1-to-segment2-continuous.json')
    args = parser.parse_args()
    report = run(args.out)
    for case in report['cases']:
        print(case['selector'], case['a3_idle_rule'], case['pc129_visits'],
              set(case['errors_by_12_candidate_buses']))
