"""Run the joined transmit program under candidate 14.4 MHz cycle divisors."""

import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from photo_controller_path import fixture
from photo_dac_bus_permutations import mapped_codes
from photo_i0_hold_screen import hold_candidate
from photo_joint_line_filter_screen import bandpass
from photo_joint_tone_training_data import (DATA_STEP, SEGMENT_SYMBOLS,
                                            SILENCE_SYMBOLS, TONE_STEP,
                                            TONE_SYMBOLS, TOTAL_SYMBOLS,
                                            segment2_from_txd)
from photo_main_dibit_dac_decode import decision_result
from photo_main_dibit_pulse import (BASE, VISITS_PER_SYMBOL, dibit_rule,
                                    scenario_inputs)
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from reference_modem import spectral_peak

TXREADY = HERE / 'results/main-loop-usart-txready.json'
FREE = HERE / 'results/photo-joint-free-clock-sites.json'
BUSES = HERE / 'results/photo-random-dibit-validation.json'
START_CYCLE = 40
SAMPLE_COUNT = TOTAL_SYMBOLS * 8
TONE_END = TONE_SYMBOLS * 8
SILENCE_END = (TONE_SYMBOLS + SILENCE_SYMBOLS) * 8


def inputs_for_divisor(symbols, k):
    visits_per_symbol = VISITS_PER_SYMBOL // k
    if VISITS_PER_SYMBOL % k or visits_per_symbol < 4:
        raise ValueError('invalid cycle divisor for this fixture')
    values = ([TONE_STEP] * (TONE_SYMBOLS * visits_per_symbol) +
              [DATA_STEP] * (SILENCE_SYMBOLS * visits_per_symbol))
    for dibit in symbols:
        offered = dibit_rule(dibit & 1, dibit >> 1)
        values.extend([offered] * 4)
        values.extend([BASE] * (visits_per_symbol - 4))
    values.append(BASE)
    if k == 1 and values != (
            [TONE_STEP] * (TONE_SYMBOLS * VISITS_PER_SYMBOL) +
            [DATA_STEP] * (SILENCE_SYMBOLS * VISITS_PER_SYMBOL) +
            scenario_inputs(symbols)):
        raise ValueError('k=1 controller stimulus changed')
    return values


def target_edge(sample, k):
    # Nearest falling PROM edge to a 9,600-Hz ideal clock at 14.4 MHz/k.
    return (sample * 375 + k // 2) // k


def capture(path, k):
    target = [target_edge(n, k) for n in range(SAMPLE_COUNT)]
    if len(set(target)) != SAMPLE_COUNT:
        raise ValueError('sample targets collide')
    values = []
    edge_count = 0
    last_129 = None
    first_127 = None
    next_sample = 0
    with path.open() as source:
        for line in source:
            if all(f'"pc": {pc}' not in line for pc in (0x127, 0x129, 0x12A)):
                continue
            row = json.loads(line)
            pc = row['pc']
            if pc == 0x127 and first_127 is None:
                first_127 = row['cycle']
            if first_127 is None or row['cycle'] < START_CYCLE:
                continue
            level = (row['raw'][0] >> 2) & 1
            if pc == 0x127 and level != 0:
                raise ValueError('U10.D2 high at loop start')
            if pc == 0x129:
                if level != 1:
                    raise ValueError('U10.D2 missing 129 rising level')
                last_129 = row
            if pc == 0x12A:
                if (level != 0 or last_129 is None or
                        last_129['cycle'] + 1 != row['cycle']):
                    raise ValueError('U10.D2 falling edge timing changed')
                if (next_sample < SAMPLE_COUNT and
                        edge_count == target[next_sample]):
                    values.append(last_129['alu']['y'])
                    next_sample += 1
                edge_count += 1
    if first_127 != START_CYCLE or next_sample != SAMPLE_COUNT:
        raise ValueError(('divisor capture incomplete', k, first_127,
                          next_sample, edge_count))
    gaps = [b - a for a, b in zip(target, target[1:])]
    return dict(values=values, raw_falling_edges=edge_count,
                sample_edge_gaps=sorted(set(gaps)),
                first_edge_index=target[0], last_edge_index=target[-1])


def replay(k, tx_case, free_case, buses, base):
    segment2 = segment2_from_txd(tx_case)
    symbols = [3] * SEGMENT_SYMBOLS + segment2
    inputs = inputs_for_divisor(symbols, k)
    scenario = hold_candidate(base)
    scenario['name'] += '; free-clock four ALU sites'
    scenario['initial']['q'] = 0
    scenario['io']['read']['pc_sequences'][str(0x127)] = inputs
    scenario['io']['read']['pc_sequences'][str(0x12C)] = [0xEA]
    scenario['io']['read']['address']['bank_by_pc'] = {
        str(0x129): 256, str(0x12E): 256}
    cycles = (TOTAL_SYMBOLS * (VISITS_PER_SYMBOL // k) + 64) * 4
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapped(MAPPINGS['q3']), scenario, cycles,
                         mode='integrated', out=temporary, trace_limit=cycles)
        captured = capture(Path(temporary) / 'trace.jsonl', k)
    if (not result['clean'] or result['completed_cycles'] != cycles or
            captured['raw_falling_edges'] != result['address_counts'].get(0x129, 0)):
        raise ValueError(('PROM divisor replay changed', k))
    if k == 1:
        expected = next(site for site in free_case['sites'] if site['pc'] == '129')
        from photo_dac_bus_permutations import SELECTED
        digest = hashlib.sha256(bytes(mapped_codes(captured['values'], SELECTED))).hexdigest()
        if result['trace_digest'] != free_case['trace_digest'] or digest != expected['sample_sha256']:
            raise ValueError('k=1 full-PROM baseline changed')
    bus_rows = []
    for index, bus in enumerate(buses):
        codes = mapped_codes(captured['values'], bus)
        tone = spectral_peak([v - 128 for v in codes[64:TONE_END]],
                             lower=100, upper=3500)
        base_carrier = spectral_peak([v - 128 for v in codes[TONE_END:SILENCE_END]],
                                     lower=100, upper=3500)
        gated = codes[:TONE_END] + [128] * (SILENCE_END - TONE_END) + codes[SILENCE_END:]
        line = bandpass([value - 128 for value in gated], 1.0)
        filtered_errors = decision_result(
            [value + 128 for value in line[SILENCE_END:]], symbols,
            sample_shift=6)['errors']
        raw_errors = decision_result(codes[SILENCE_END:], symbols,
                                     sample_shift=6)['errors']
        bus_rows.append(dict(bus_index=index,
                             input_bit_to_dac_code_bit=bus,
                             tone_peak_hz=tone['frequency_hz'],
                             tone_bin_hz=tone['bin_width_hz'],
                             ungated_a2_carrier_peak_hz=base_carrier['frequency_hz'],
                             raw_data_errors=raw_errors,
                             filtered_data_errors=filtered_errors))
    return dict(divisor=k, assumed_microinstruction_hz=14400000 // k,
                visits_per_symbol=VISITS_PER_SYMBOL // k,
                cycles=cycles, trace_digest=result['trace_digest'],
                raw_falling_edges=captured['raw_falling_edges'],
                sample_edge_gaps=captured['sample_edge_gaps'],
                captured_samples=len(captured['values']),
                selected_bus_sha256=hashlib.sha256(bytes(mapped_codes(
                    captured['values'], buses[0]))).hexdigest(),
                bus_cases=bus_rows)


def run(out=HERE / 'results/photo-tx-cycle-divisor-screen.json'):
    txready = json.loads(TXREADY.read_text())
    free = json.loads(FREE.read_text())
    buses = json.loads(BUSES.read_text())['zero_error_survivors']
    if len(buses) != 6:
        raise ValueError('DAC bus survivor family changed')
    tx_case = next(row for row in txready['cases'] if row['selector'] == '40')
    free_case = next(row for row in free['cases'] if row['selector'] == '40')
    _, base = fixture()
    cases = []
    for k in (1, 2, 3, 4):
        cases.append(replay(k, tx_case, free_case, buses, base))
        print('captured divisor', k, flush=True)
    paths = [Path(__file__), TXREADY, FREE, BUSES,
             HERE / 'photo_joint_tone_training_data.py',
             HERE / 'photo_main_dibit_pulse.py',
             HERE / 'photo_main_dibit_dac_decode.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(
        experiment='real-PROM cycle-divisor screen for counter-qualified DAC clock',
        fixture=dict(controller_selector='40',
                     microinstruction_hz='14.4 MHz / k, k=1..4',
                     sample_hz=9600, symbol_hz=1200,
                     edge='U10.D2 falling at 12A; capture preceding 129 Y',
                     pulse_width_visits=4,
                     candidate_buses='six nonperiodic-data survivors',
                     clock_wiring_and_divider='hypotheses'),
        cases=cases,
        limitations=[
            'Only one controller selector and this D127 phase-step/pulse fixture are screened.',
            'The sequencer clock divisor, edge timing, DAC bus and line route are not measured.',
            'Reference spectral/decoder scores are conditional, not physical DAC measurements.'],
        source_sha256={str(path.relative_to(HERE.parents[2])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    for case in run()['cases']:
        print(case['divisor'], case['sample_edge_gaps'],
              [(row['tone_peak_hz'], row['filtered_data_errors'])
               for row in case['bus_cases']])
