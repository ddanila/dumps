"""Hold out nonperiodic dibits against the conditional q3 transmitter path."""

import hashlib
import json
import random
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from photo_127_liveness import ROM
from photo_controller_path import fixture
from photo_dac_bus_permutations import (SELECTED, mapped_codes,
                                        matched_filter_basis, raw_y_codes, score)
from photo_i0_hold_screen import hold_candidate
from photo_main_dibit_pulse import (VISITS_PER_SYMBOL, inspect_trace,
                                    scenario_inputs)
from photo_main_dibit_dac_decode import decision_result
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

BUSES = HERE / 'results/photo-dac-bus-permutations.json'
SEEDS = (0x2847, 0x3558, 0x8102, 0x001F)
PROJECTED_SYMBOLS = 256
EXECUTED_SYMBOLS = 32


def dibits_for(seed, count):
    generator = random.Random(seed)
    return [generator.randrange(4) for _ in range(count)]


def full_prom_witness(mapping, base, rom, seed):
    dibits = dibits_for(seed, EXECUTED_SYMBOLS)
    inputs = scenario_inputs(dibits)
    scenario = hold_candidate(base)
    scenario['name'] += '; seeded nonperiodic D127 parity pulse'
    scenario['initial']['q'] = 0
    scenario['io']['read']['pc_sequences'][str(0x127)] = inputs
    scenario['io']['read']['pc_sequences'][str(0x12C)] = [0x7A]
    scenario['io']['read']['address']['bank_by_pc'] = {
        str(0x129): 256, str(0x12E): 256}
    cycles = (EXECUTED_SYMBOLS * VISITS_PER_SYMBOL + 64) * 4
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, cycles, mode='integrated',
                         out=temporary, trace_limit=cycles)
        trace = inspect_trace(Path(temporary) / 'trace.jsonl', rom,
                              inputs, dibits)
    if (not result['clean'] or result['completed_cycles'] != cycles or
            result['address_counts'].get(0x129) != trace['pc129_visits'] or
            result['address_counts'].get(0x12E, 0) or
            trace['dac_samples'] != EXECUTED_SYMBOLS * 8):
        raise ValueError(('random full-PROM witness incomplete', seed))
    return dict(seed=seed, dibits=dibits, cycles=cycles,
                pc129_visits=trace['pc129_visits'],
                dac_samples=trace['dac_samples'],
                selected_bus_sample_sha256=trace['dac_sample_sha256'],
                trace_digest=result['trace_digest'])


def run(out=HERE / 'results/photo-random-dibit-validation.json'):
    rom = ROM.read_bytes()
    buses = [row['input_bit_to_dac_code_bit'] for row in
             json.loads(BUSES.read_text())['zero_error_candidates']]
    assert len(buses) == 12
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    executed = [full_prom_witness(mapping, base, rom, seed)
                for seed in SEEDS[:2]]
    for witness in executed:
        raw = raw_y_codes(rom, witness['dibits'])
        expected_hash = hashlib.sha256(bytes(mapped_codes(raw, SELECTED))).hexdigest()
        assert witness['selected_bus_sample_sha256'] == expected_hash
    rows = []
    for seed in SEEDS:
        dibits = dibits_for(seed, PROJECTED_SYMBOLS)
        raw = raw_y_codes(rom, dibits)
        basis = matched_filter_basis(raw)
        errors = [score(basis, dibits, bus)[0] for bus in buses]
        for bus, expected in zip(buses, errors):
            direct = decision_result(mapped_codes(raw, bus), dibits)
            assert (direct['errors'], direct['decisions']) == (
                expected, PROJECTED_SYMBOLS - 2)
        carrier_only = matched_filter_basis(raw_y_codes(rom, [0] * PROJECTED_SYMBOLS))
        no_pulse_errors = score(carrier_only, dibits, buses[0])[0]
        rows.append(dict(seed=seed, symbols=PROJECTED_SYMBOLS,
                         decisions=PROJECTED_SYMBOLS - 2,
                         errors_by_bus=errors,
                         no_pulse_errors=no_pulse_errors,
                         dibit_sha256=hashlib.sha256(bytes(dibits)).hexdigest()))
    total_errors = [sum(row['errors_by_bus'][i] for row in rows)
                    for i in range(len(buses))]
    survivors = [bus for bus, errors in zip(buses, total_errors) if errors == 0]
    if len(survivors) != 6 or any(row['no_pulse_errors'] < 100 for row in rows):
        raise ValueError('random transmitter validation changed')
    fixed_destinations = {str(bit): next(iter(destinations))
                          for bit in range(8)
                          if len(destinations := {bus[bit] for bus in survivors}) == 1}
    if fixed_destinations != {'0': 4, '2': 5, '4': 3, '6': 6, '7': 7}:
        raise ValueError('surviving DAC bit positions changed')
    paths = [Path(__file__), BUSES, ROM,
             HERE / 'photo_main_dibit_pulse.py',
             HERE / 'photo_dac_bus_permutations.py',
             HERE / 'photo_main_dibit_dac_decode.py',
             HERE / 'reference_modem.py',
             HERE / 'photo_controller_path.py',
             HERE / 'photo_i0_hold_screen.py',
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3'],
             HERE.parents[2] / 'photos/PXL_20261123_114854803.jpg']
    report = dict(status='conditional q3 transmitter phase path generalizes to nonperiodic synthetic dibits',
                  fixture=dict(d127='assumed four-visit parity/counter dibit pulse',
                               dac_clock='one capture per 375 PC129 visits',
                               receiver='independent fixed-phase reference matched filter',
                               prior_candidates=12,
                               executed_symbols_per_seed=EXECUTED_SYMBOLS,
                               projected_symbols_per_seed=PROJECTED_SYMBOLS),
                  full_prom_witnesses=executed,
                  projected_cases=rows,
                  total_errors_by_bus=total_errors,
                  zero_error_survivors=survivors,
                  fixed_source_bit_to_dac_code_bit=fixed_destinations,
                  decoder_validation='All 48 bus/stream scores agree with direct reference receiver results.',
                  limitations=['Only two 32-symbol prefixes were executed with full real-PROM traces; all 256-symbol scores use the recurrence whose PC129 address, ROM byte, Y and selected-bus DAC hash those traces check.',
                               'The seeded dibits are synthetic holdouts, not bytes from the 8031; the D127 decoder, DAC bus and clock remain untraced.',
                               'An independent reference receiver decoding the candidate output does not establish a DSC receive or echo-canceller path.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    print(report['total_errors_by_bus'], len(report['zero_error_survivors']))
