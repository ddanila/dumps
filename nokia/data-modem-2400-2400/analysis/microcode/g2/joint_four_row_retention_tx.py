"""Screen full receive-state retention and TX output in nearby joint maps."""

import copy
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
from joint_upper_source_screen import candidate
from lower_i_d3f8_full_adc import LONG_SAMPLES, SAMPLE_START
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_dac_bus_permutations import mapped_codes
from photo_i0_hold_screen import hold_candidate
from photo_joint_line_filter_screen import bandpass
from photo_joint_tone_training_data import (
    DATA_STEP, SEGMENT_SYMBOLS, SILENCE_SYMBOLS, TONE_STEP,
    TONE_SYMBOLS, TOTAL_SYMBOLS, segment2_from_txd,
)
from photo_main_dibit_dac_decode import decision_result
from photo_main_dibit_pulse import VISITS_PER_SYMBOL, scenario_inputs
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_four_row_condition_screen import PATTERNS, capture, compare, configured
from reference_modem import receive as reference_receive, spectral_peak, transmit as reference_transmit
from split_slice_probe import split_scenario

MASKS = (4, 6, 8, 10, 14)
TXREADY = HERE / 'results/main-loop-usart-txready.json'
BUSES = HERE / 'results/photo-random-dibit-validation.json'
SAMPLE_COUNT = TOTAL_SYMBOLS * 8
TONE_END = TONE_SYMBOLS * 8
SILENCE_END = (TONE_SYMBOLS + SILENCE_SYMBOLS) * 8
SAMPLE_DIVISOR = 375
VALIDATION_SEEDS = (0x2847, 0x3557, 0x3558, 0x8102)


def receiver_case(mapping, base, mask):
    full = capture(mapping, base, PATTERNS[0])
    zero = capture(mapping, base, PATTERNS[1])
    compared = compare(full, zero)
    return dict(mask=mask, same_pc_path=True,
                adc_y_differences=compared['sites']['3F8']['alu.y']['differences'],
                adc_rom_address_differences=compared['sites']['3F9']['rom_address']['differences'],
                wrapper_test_differences=compared['sites']['3EA']['test']['differences'],
                loop_test_differences=compared['sites']['3ED']['test']['differences'],
                after_adc_row=compared['state_differences']['3FA'],
                after_fourth_row=compared['state_differences']['3FE'],
                trace_digests=[case[3]['trace_digest'] for case in (full, zero)])


def nonperiodic_state(mapping, base, middle):
    dibits = [0] * 8 + middle + [0] * 8
    pcm = reference_transmit(dibits)
    if reference_receive(pcm) != dibits[1:]:
        raise ValueError('nonperiodic reference stimulus did not decode')
    samples = [127 - value for value in
               pcm[SAMPLE_START:SAMPLE_START + LONG_SAMPLES]]
    values = [sample for index, sample in enumerate(samples)
              for _ in range(47 if index % 8 < 7 else 46)]
    if len(values) != 6000:
        raise ValueError('nonperiodic four-row hold changed')
    scenario = configured(base, values, 'previous', 'overflow', 1)
    cycles = 32 * len(values) + 47
    ram = scenario['initial']['ram'][:]
    states = []
    pc_digest = hashlib.sha256()
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, cycles, mode='integrated',
                         out=temporary, trace_limit=cycles)
        if (not result['clean'] or result['completed_cycles'] != cycles or
                result['address_counts'].get(0x3F8, 0) != len(values) or
                result['address_counts'].get(0x3FE, 0) != len(values) or
                result['read_sequence_visits'].get(0x3F8, 0) != len(values)):
            raise ValueError('nonperiodic full-row execution did not sustain')
        for line in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(line)
            pc_digest.update(row['pc'].to_bytes(2, 'little'))
            for address, value in row['registers'].items():
                ram[int(address)] = value
            if row['pc'] == 0x3FE:
                states.append(bytes(ram) + bytes((row['q'],)))
    if len(states) != len(values):
        raise ValueError('nonperiodic row-boundary count changed')
    return dict(states=states, pc_digest=pc_digest.hexdigest(),
                trace_digest=result['trace_digest'])


def transmit_case(mapping, base, tx_case, buses):
    selector = tx_case['selector']
    segment2 = segment2_from_txd(tx_case)
    symbols = [3] * SEGMENT_SYMBOLS + segment2
    inputs = ([TONE_STEP] * (TONE_SYMBOLS * VISITS_PER_SYMBOL) +
              [DATA_STEP] * (SILENCE_SYMBOLS * VISITS_PER_SYMBOL) +
              scenario_inputs(symbols))
    if len(inputs) != TOTAL_SYMBOLS * VISITS_PER_SYMBOL + 1:
        raise ValueError('TX controller stimulus changed')
    scenario = split_scenario(hold_candidate(base))
    scenario['name'] += '; alternate joint upper-source mask 04 full TX'
    scenario['inputs']['register_address_bit_overrides']['a_high'] = copy.deepcopy(
        scenario['inputs']['register_address_bit_overrides']['a'])
    for policy in scenario['inputs']['register_address_bit_overrides']['a_high'].values():
        policy['evidence'] += '; untraced high-slice A pin diagnostic level'
    scenario['initial']['q'] = 0
    scenario['io']['read']['pc_sequences'][str(0x127)] = inputs
    scenario['io']['read']['pc_sequences'][str(0x12C)] = [0xEA]
    scenario['io']['read']['address']['bank_by_pc'] = {
        str(0x129): 256, str(0x12E): 256}
    cycles = (TOTAL_SYMBOLS * VISITS_PER_SYMBOL + 64) * 4
    samples = []
    visits = 0
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, cycles, mode='integrated',
                         out=temporary, trace_limit=cycles)
        for line in (Path(temporary) / 'trace.jsonl').open():
            if '"pc": 297' not in line:
                continue
            row = json.loads(line)
            if visits % SAMPLE_DIVISOR == 0 and len(samples) < SAMPLE_COUNT:
                samples.append(row['alu']['y'])
            visits += 1
    base_report = dict(selector=selector, clean=result['clean'],
                       completed_cycles=result['completed_cycles'],
                       pc129_visits=visits, sample_count=len(samples),
                       trace_digest=result['trace_digest'])
    if (not result['clean'] or result['completed_cycles'] != cycles or
            len(samples) != SAMPLE_COUNT):
        return dict(**base_report, complete_candidate_waveform=False)
    bus_cases = []
    for index, bus in enumerate(buses):
        codes = mapped_codes(samples, bus)
        peak = spectral_peak([value - 128 for value in codes[64:TONE_END]],
                             lower=100, upper=3500)
        gated = codes[:TONE_END] + [128] * (SILENCE_END - TONE_END) + codes[SILENCE_END:]
        line = bandpass([value - 128 for value in gated], 1.0)
        score = decision_result([value + 128 for value in line[SILENCE_END:]],
                                symbols, sample_shift=6)
        bus_cases.append(dict(bus_index=index,
                              input_bit_to_dac_code_bit=bus,
                              late_a1_peak_hz=peak['frequency_hz'],
                              filtered_data_errors=score['errors'],
                              data_decisions=score['decisions']))
    return dict(**base_report, complete_candidate_waveform=True,
                raw_y_sample_sha256=hashlib.sha256(bytes(samples)).hexdigest(),
                bus_cases=bus_cases)


def run(out=HERE / 'results/joint-four-row-retention-tx.json'):
    receiver = mapping_with_upper_source(0, '17.6')
    transmitter = mapped(MAPPINGS['q3'])
    _, base = fixture()
    mappings = {mask: candidate(receiver, transmitter, mask) for mask in MASKS}
    receive = []
    for mask in MASKS:
        receive.append(receiver_case(mappings[mask], base, mask))
        print('screened receive mask', mask, flush=True)
    if [row['mask'] for row in receive if
            row['after_fourth_row']['any_byte_differences']] != [4]:
        raise ValueError('full-row receive retention survivor changed')
    control = nonperiodic_state(mappings[4], base, [0] * 16)
    receive_validation = []
    for seed in VALIDATION_SEEDS:
        generator = random.Random(seed)
        middle = [generator.randrange(4) for _ in range(16)]
        case = nonperiodic_state(mappings[4], base, middle)
        if case['pc_digest'] != control['pc_digest']:
            raise ValueError(('nonperiodic receive PC path changed', seed))
        differences = sum(a != b for a, b in zip(control['states'], case['states']))
        receive_validation.append(dict(seed=seed, middle=middle,
                                       visits=len(case['states']),
                                       after_fourth_row_differences=differences,
                                       trace_digest=case['trace_digest']))
        print('validated receive seed', seed, flush=True)
    txready = json.loads(TXREADY.read_text())
    buses = json.loads(BUSES.read_text())['zero_error_survivors']
    if len(buses) != 6:
        raise ValueError('candidate DAC bus family changed')
    tx = []
    for selector in ('40', '60'):
        controller = next(row for row in txready['cases']
                          if row['selector'] == selector)
        tx.append(transmit_case(mappings[4], base, controller, buses))
        print('screened transmit selector', selector, flush=True)
    paths = [Path(__file__), HERE / 'receiver_four_row_condition_screen.py',
             HERE / 'joint_upper_source_screen.py',
             HERE / 'joint_upper_full_tx_replay.py',
             HERE / 'lower_i_d3f8_full_adc.py',
             HERE / 'photo_joint_tone_training_data.py',
             HERE / 'photo_main_dibit_pulse.py',
             HERE / 'photo_joint_line_filter_screen.py',
             HERE / 'photo_main_dibit_dac_decode.py',
             HERE / 'reference_modem.py', HERE.parent / 'assumed/execute.py',
             HERE.parent / 'model.py', MAPPINGS['q3'], TXREADY, BUSES,
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(
        experiment='nearby fixed-map receive retention and controller-driven TX',
        fixture=dict(masks=MASKS, upper_source='joint inverted U17 D5 I0/I7',
                     receive='four-row [0,1,2,3], previous inverted overflow, two 32-sample ADC waveforms',
                     transmit='full controller A1/A2/A3/A4 stimulus, selector 40 and 60, D127 pulse fixture',
                     output='Y129 every 375 visits, six candidate DAC buses and fixed bandpass'),
        receive=receive, receive_validation=receive_validation,
        receive_validation_control_trace_digest=control['trace_digest'],
        transmit_mask04=tx,
        limitations=[
            'The five field maps are local wiring hypotheses, not established board connections.',
            'Receive retention is state sensitivity, not a recovered bit or echo cancellation.',
            'DAC bus, latch, analog response, controller-to-DSC gate and USART paths remain assumed.'],
        source_sha256={str(path.relative_to(HERE.parents[2])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    print([(row['selector'], row['complete_candidate_waveform'],
            [(bus['late_a1_peak_hz'], bus['filtered_data_errors'])
             for bus in row.get('bus_cases', [])])
           for row in result['transmit_mask04']])
