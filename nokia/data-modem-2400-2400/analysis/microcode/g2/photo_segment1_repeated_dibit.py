"""Replay the 32-symbol segment-1 signature with an explicit synthetic D127 stimulus."""

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
from photo_127_liveness import ROM
from photo_controller_path import fixture
from photo_dac_bus_permutations import (mapped_codes, matched_filter_basis,
                                        raw_y_codes, score, SELECTED)
from photo_frame_toggle_edge_pulse import inspect
from photo_i0_hold_screen import hold_candidate
from photo_main_dibit_pulse import BASE, VISITS_PER_SYMBOL, scenario_inputs
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from reference_modem import phase_positions

BUSES = HERE / 'results/photo-dac-bus-permutations.json'
SYMBOL_COUNT = 32


def run(out=HERE / 'results/photo-segment1-repeated-dibit.json'):
    dibits = [3] * SYMBOL_COUNT
    inputs = scenario_inputs(dibits)
    _, base = fixture()
    scenario = hold_candidate(base)
    scenario['name'] += '; synthetic segment-1 repeated dibit 11'
    scenario['initial']['q'] = 0
    scenario['io']['read']['pc_sequences'][str(0x127)] = inputs
    scenario['io']['read']['pc_sequences'][str(0x12c)] = [0xEA]
    scenario['io']['read']['address']['bank_by_pc'] = {str(0x129): 256,
                                                       str(0x12e): 256}
    cycles = (SYMBOL_COUNT * VISITS_PER_SYMBOL + 64) * 4
    rom = ROM.read_bytes()
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapped(MAPPINGS['q3']), scenario, cycles,
                         mode='integrated', out=temporary, trace_limit=cycles)
        trace = inspect(Path(temporary) / 'trace.jsonl', rom, inputs, dibits)
    if (not result['clean'] or result['completed_cycles'] != cycles or
            result['address_counts'].get(0x129) != trace['pc129_visits'] or
            result['address_counts'].get(0x12e, 0)):
        raise ValueError('PROM replay did not complete')
    raw = raw_y_codes(rom, dibits)
    if hashlib.sha256(bytes(mapped_codes(raw, SELECTED))).hexdigest() != trace['sample_sha256']:
        raise ValueError('reconstructed sample stream differs from executed PROM')
    offsets = [(phase - (3 + (index + 1) * VISITS_PER_SYMBOL * BASE)) & 255
               for index, phase in enumerate(trace['symbol_end_phases'])]
    target = [128 if index % 2 == 0 else 0 for index in range(SYMBOL_COUNT)]
    if offsets != target or phase_positions(dibits) != [8 if index % 2 == 0 else 0
                                                        for index in range(SYMBOL_COUNT)]:
        raise ValueError(('segment-1 phase trajectory', offsets))
    buses = json.loads(BUSES.read_text())['zero_error_candidates']
    basis = matched_filter_basis(raw)
    rows = []
    for bus in buses:
        permutation = bus['input_bit_to_dac_code_bit']
        errors, decisions = score(basis, dibits, permutation)
        rows.append(dict(input_bit_to_dac_code_bit=permutation,
                         errors=errors, decisions=decisions))
    if len(rows) != 12 or any(row['decisions'] != 30 for row in rows):
        raise ValueError('candidate bus or decision coverage changed')
    paths = [Path(__file__), BUSES, ROM,
             HERE / 'photo_127_liveness.py',
             HERE / 'photo_controller_path.py',
             HERE / 'photo_dac_bus_permutations.py',
             HERE / 'photo_frame_toggle_edge_pulse.py',
             HERE / 'photo_main_dibit_pulse.py',
             HERE / 'photo_i0_hold_screen.py',
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             HERE / 'reference_modem.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3']]
    report = dict(
        status='synthetic repeated-dibit segment-1 signature tested in real PROM execution',
        stimulus=dict(dibits=dibits, d127_first_four_visits='90',
                      d127_remaining_visits='B0', visits_per_symbol=VISITS_PER_SYMBOL,
                      sample_gate='one PC129 Y capture per 375 visits',
                      controller_source='not established'),
        execution=dict(microinstructions=cycles, pc129_visits=trace['pc129_visits'],
                       trace_digest=result['trace_digest'],
                       selected_bus_sample_sha256=trace['sample_sha256'],
                       first_16_selected_bus_samples=[f'{v:02X}' for v in trace['samples'][:16]],
                       symbol_phase_offsets=offsets),
        reference_phase_positions=phase_positions(dibits),
        candidate_bus_decisions=rows,
        limitations=['The repeated dibits and four-visit D127 pulses are imposed, not recovered from the controller segment-1 state.',
                     'The D127 route, sample clock, full DAC bus and line path remain hypotheses.',
                     'The matched-filter check is a candidate waveform projection, not received hardware data.'],
        source_sha256={str(path.relative_to(HERE.parents[2])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path,
                        default=HERE / 'results/photo-segment1-repeated-dibit.json')
    args = parser.parse_args()
    report = run(args.out)
    print('phase offsets', report['execution']['symbol_phase_offsets'])
    print('bus errors', [row['errors'] for row in report['candidate_bus_decisions']])
