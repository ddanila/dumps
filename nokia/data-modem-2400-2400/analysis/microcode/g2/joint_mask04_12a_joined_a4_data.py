"""Run known A4 segment-2 bits and unseen data in one DSC Tx/Rx session."""

import hashlib
import itertools
import json
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_analog_holdout as holdout
import joint_mask04_12a_buffered_line as line
import joint_mask04_buffered_serial_handoff as handoff
import joint_mask04_tx_rx_loopback as loopback
from controller_segment2_pattern import standard_bits
from joint_mask04_12a_a4_phase_training import pack_lsb
from joint_mask04_12a_phase_timing_map import decode
from joint_mask04_q05_fresh_payload_levels import PAYLOADS
from joint_mask04_tx_12a_delayed_latch import capturing_execute
from photo_dac_bus_permutations import mapped_codes
from photo_joint_line_filter_screen import SILENCE_END, TONE_END, bandpass
from photo_joint_tone_training_data import SILENCE_SYMBOLS, TONE_SYMBOLS
from photo_main_dibit_pulse import BASE, VISITS_PER_SYMBOL, dibit_rule, scenario_inputs
from receiver_mask04_controller_zero_handoff import dibits_from_bytes
from receiver_mask04_feature_choice import alternative_states
from receiver_mask04_offset_visit_phase import project
from receiver_mask04_serial_candidate import bytes_lsb_first
from reference_modem import receive
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
FIXED = HERE / 'results/joint-mask04-12a-fixed-gain-phase.json'
CONTROLLER_A4 = HERE / 'results/controller-segment2-pattern.json'
TRAINING = 32
PAYLOAD = 32
DATA_SYMBOLS = TRAINING + PAYLOAD
RX_SYMBOLS = handoff.PREAMBLE + handoff.PIPELINE_SYMBOLS + DATA_SYMBOLS
SAMPLES = (TONE_SYMBOLS + SILENCE_SYMBOLS + RX_SYMBOLS) * 8 + 6
TX_CYCLES = (SAMPLES * 375 + 64) * 4
ADC_VISITS = RX_SYMBOLS * 375
RX_CYCLES = 32 * ADC_VISITS + 47
VISIT = TONE_END * 375 + 1


def extended_inputs(offered):
    bits = [(byte >> bit) & 1 for byte in offered for bit in range(8)]
    if len(bits) != 128:
        raise ValueError('joined stream must contain 16 bytes')
    prefix = scenario_inputs([3] * handoff.PREAMBLE)[:-1]
    data = [BASE] * ((handoff.PIPELINE_SYMBOLS + DATA_SYMBOLS) * VISITS_PER_SYMBOL)
    data[:4] = [dibit_rule(1, 1)] * 4
    dibits = dibits_from_bytes(offered)
    for symbol, dibit in enumerate(dibits):
        first, second = dibit & 1, (dibit >> 1) & 1
        visit = (symbol + 1) * VISITS_PER_SYMBOL
        data[visit:visit + 4] = [dibit_rule(first, second)] * 4
    return prefix + data + [BASE], dibits, []


def run(out=HERE / 'results/joint-mask04-12a-joined-a4-data.json'):
    fixed = json.loads(FIXED.read_text())
    a4 = json.loads(CONTROLLER_A4.read_text())
    mapping = line.candidate(line.mapping_with_upper_source(0, '17.6'),
                             line.mapped(line.MAPPINGS['q3']), 4)
    _, base = line.fixture()
    cases = []
    for selector, polynomial, delay in (('40', 'GPC', 5), ('60', 'GPA', 18)):
        if not any(row['selector'] == selector and row['polynomial'] == polynomial
                   and row['bit_order'] == 'lsb_first' and row['start_bit'] == 1
                   for row in a4['exact_64_bit_windows']):
            raise ValueError(('A4 controller window changed', selector))
        training = pack_lsb(standard_bits(polynomial))
        payload = line_octets(PAYLOADS[selector], delay)
        offered = training + payload
        with patch.object(line, 'buffered_inputs', extended_inputs), \
                patch.object(line, 'RX_SYMBOLS', RX_SYMBOLS), \
                patch.object(line, 'SAMPLES', SAMPLES), \
                patch.object(line, 'TX_CYCLES', TX_CYCLES):
            tx, raw, expected = line.transmitter(
                capturing_execute((VISIT, 32)), mapping, base, offered)
        gain = next(b for b in next(c for c in fixed['cases']
                                   if c['selector'] == selector)['bus_cases']
                    if b['bus_index'] == 0)['gain']
        codes = mapped_codes(raw, holdout.BUSES[0])
        gated = codes[:TONE_END] + [128] * (SILENCE_END - TONE_END) + codes[SILENCE_END:]
        wave = bandpass([value - 128 for value in gated], 0.5)
        selected = wave[SILENCE_END + 6:SILENCE_END + 6 + RX_SYMBOLS * 8]
        pcm = [max(-127, min(127, round(value * gain))) for value in selected]
        reference_wrong = [i for i, (got, want) in enumerate(
            zip(receive(pcm), expected[1:])) if got != want]
        with patch.object(loopback, 'DATA', handoff.PIPELINE_SYMBOLS + DATA_SYMBOLS), \
                patch.object(loopback, 'SYMBOLS', RX_SYMBOLS), \
                patch.object(loopback, 'ADC_VISITS', ADC_VISITS), \
                patch.object(loopback, 'CYCLES', RX_CYCLES):
            rx, adc, symbols = loopback.capture(mapping, base, pcm, expected)
        states = [f'{value:X}' for value in alternative_states(project(symbols, 46, 93))]
        keys = sorted({int(value, 16) for value in states})
        maps = []
        for labels in itertools.product(range(4), repeat=len(keys) - 1):
            phase = dict(zip(keys, (0, *labels)))
            if decode(states, phase)[33:65] == expected[33:65]:
                maps.append(phase)
        candidates = []
        for phase in maps:
            decoded = decode(states, phase)
            payload_wrong = [i for i, (got, want) in enumerate(
                zip(decoded[65:97], expected[65:97])) if got != want]
            recovered = bytes_lsb_first([
                bit for dibit in decoded[65:97]
                for bit in (dibit & 1, (dibit >> 1) & 1)])
            candidates.append(dict(phase={f'{key:X}': value for key, value in phase.items()},
                                   payload_wrong_indices=payload_wrong,
                                   recovered_payload_line_bytes=[f'{v:02X}' for v in recovered],
                                   payload_line_matches_offered=recovered == payload))
        cases.append(dict(selector=selector, polynomial=polynomial,
                          training_line_bytes=[f'{v:02X}' for v in training],
                          payload_line_bytes=[f'{v:02X}' for v in payload],
                          tx_trace_digest=tx['trace_digest'],
                          rx_trace_digest=rx['trace_digest'],
                          raw_sha256=hashlib.sha256(bytes(raw)).hexdigest(),
                          pcm_sha256=hashlib.sha256(bytes(v + 127 for v in pcm)).hexdigest(),
                          adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                          reference_wrong_indices=reference_wrong,
                          states=states, distinct_states=[f'{value:X}' for value in keys],
                          training_exact_maps=len(maps),
                          tested_maps=4 ** (len(keys) - 1),
                          candidates=candidates))
        print(selector, 'states',cases[-1]['distinct_states'],
              'A4 maps',len(maps), 'payload wrong',
              [len(c['payload_wrong_indices']) for c in candidates],flush=True)
    report = dict(experiment='joined A4 pattern and fresh data in one real-PROM DSC Tx/Rx run',
                  fixture=dict(training_symbols=TRAINING,payload_symbols=PAYLOAD,
                               r1_offset=32,offset_visit=VISIT,
                               line='Q=0.5, bus 0, +6 samples, zero-run gain',
                               serial='A4 standard window then separately generated scrambled payload bytes'),
                  cases=cases,
                  limitations=['The joined line stream concatenates independently generated A4 and payload bytes; the unchanged controller is not run continuously across them.',
                               'Phase logic, converter buses, analog line, clocks and serializer are assumed.'],
                  source_sha256={str(p.relative_to(HERE.parents[4])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (Path(__file__), FIXED, CONTROLLER_A4,
                                           HERE / 'joint_mask04_12a_buffered_line.py',
                                           HERE.parent / 'assumed/execute.py')})
    out.write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__ == '__main__':
    run()
