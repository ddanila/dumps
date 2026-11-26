"""Challenge the ROM-sensitive 12A DAC route with buffered controller data."""

import copy
import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import joint_mask04_buffered_serial_handoff as handoff
import joint_mask04_tx_rx_loopback as loopback
from joint_mask04_tx_12a_delayed_latch import capturing_execute
from joint_mask04_buffered_serial_handoff import (PREAMBLE, PIPELINE_SYMBOLS,
                                                  RX_SYMBOLS, SAMPLES,
                                                  TX_CYCLES, buffered_inputs)
from joint_four_row_retention_tx import (BUSES, MAPPINGS, candidate, fixture,
                                         hold_candidate, mapped,
                                         mapping_with_upper_source,
                                         split_scenario)
from photo_dac_bus_permutations import mapped_codes
from photo_joint_line_filter_screen import SILENCE_END, TONE_END, bandpass
from photo_joint_tone_training_data import (DATA_STEP, SILENCE_SYMBOLS,
                                            TONE_STEP, TONE_SYMBOLS)
from photo_main_dibit_pulse import BASE, VISITS_PER_SYMBOL
from reference_modem import receive
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
PRIOR = HERE / 'results/joint-mask04-buffered-serial-handoff.json'
GATE = HERE / 'results/joint-mask04-tx-12a-gate.json'
SHIFTS = tuple(range(-7, 7))


def transmitter(execute, mapping, base, offered):
    inputs, dibits, _ = buffered_inputs(offered)
    scenario = split_scenario(hold_candidate(base))
    scenario['name'] += '; buffered serial bit-pairs with PROM 12A DAC gate'
    scenario['inputs']['register_address_bit_overrides']['a_high'] = copy.deepcopy(
        scenario['inputs']['register_address_bit_overrides']['a'])
    for policy in scenario['inputs']['register_address_bit_overrides']['a_high'].values():
        policy['evidence'] += '; untraced high-slice A pin diagnostic level'
    scenario['initial']['q'] = 0
    scenario['io']['read']['pc_sequences'][str(0x127)] = (
        [TONE_STEP] * (TONE_SYMBOLS * VISITS_PER_SYMBOL) +
        [DATA_STEP] * (SILENCE_SYMBOLS * VISITS_PER_SYMBOL) +
        inputs + [BASE] * (6 * 375))
    scenario['io']['read']['pc_sequences'][str(0x12C)] = [0xEA]
    scenario['io']['read']['address']['bank_by_pc'] = {
        str(0x129): 256, str(0x12E): 256}
    result = execute(mapping, scenario, TX_CYCLES, mode='integrated',
                     trace_limit=0)
    y = result['site_y'][0x12A]
    if (not result['clean'] or result['completed_cycles'] != TX_CYCLES or
            len(y) < SAMPLES * 375 or
            result['address_counts'].get(0x12A) != len(y)):
        raise ValueError('buffered 12A transmitter did not sustain')
    raw = [y[n * 375] for n in range(SAMPLES)]
    expected = [3] * (PREAMBLE + PIPELINE_SYMBOLS) + dibits
    return result, raw, expected


def waveform_scores(raw, bus, expected):
    codes = mapped_codes(raw, bus)
    gated = codes[:TONE_END] + [128] * (SILENCE_END - TONE_END) + codes[SILENCE_END:]
    line = bandpass([value - 128 for value in gated], 1.0)
    scores = []
    for shift in SHIFTS:
        selected = line[SILENCE_END + shift:
                        SILENCE_END + shift + RX_SYMBOLS * 8]
        if len(selected) != RX_SYMBOLS * 8:
            raise ValueError(('buffered waveform too short', shift))
        gain = 110 / max(abs(value) for value in selected)
        pcm = [max(-127, min(127, round(value * gain))) for value in selected]
        decisions = receive(pcm)
        if len(decisions) != RX_SYMBOLS - 1:
            raise ValueError('reference decision count changed')
        wrong = [index for index, (actual, want) in
                 enumerate(zip(decisions, expected[1:])) if actual != want]
        scores.append(dict(shift=shift, wrong=len(wrong),
                           data_wrong=sum(index >= PREAMBLE + PIPELINE_SYMBOLS - 1
                                          for index in wrong),
                           first_wrong=wrong[:12],
                           pcm_sha256=hashlib.sha256(
                               bytes(value + 127 for value in pcm)).hexdigest(),
                           gain=round(gain, 6)))
    return dict(code_sha256=hashlib.sha256(bytes(codes)).hexdigest(),
                scores=scores,
                best=min(scores, key=lambda row: (row['wrong'],
                                                  abs(row['shift'] - 6))))


def pcm_at_shift(raw, bus, shift):
    codes = mapped_codes(raw, bus)
    gated = codes[:TONE_END] + [128] * (SILENCE_END - TONE_END) + codes[SILENCE_END:]
    line = bandpass([value - 128 for value in gated], 1.0)
    selected = line[SILENCE_END + shift:SILENCE_END + shift + RX_SYMBOLS * 8]
    gain = 110 / max(abs(value) for value in selected)
    return [max(-127, min(127, round(value * gain))) for value in selected]


def receiver_handoff(mapping, base, pcm, expected, offered, exe, selector, delay):
    with patch.object(loopback, 'DATA', handoff.PIPELINE_SYMBOLS + handoff.DATA_SYMBOLS), \
            patch.object(loopback, 'SYMBOLS', RX_SYMBOLS), \
            patch.object(loopback, 'ADC_VISITS', handoff.ADC_VISITS), \
            patch.object(loopback, 'CYCLES', handoff.RX_CYCLES):
        result, adc, symbols = loopback.capture(mapping, base, pcm, expected)
    primary, alternative = handoff.frozen_tables()
    predictions = {}
    for pair in handoff.PAIRS:
        projected = handoff.project(symbols, *pair)
        first = handoff.decisions(handoff.states_from_symbols(projected), primary)
        second = handoff.decisions(handoff.alternative_states(projected), alternative)
        predictions[pair] = handoff.consensus(first, second)
    selected, selected_pairs = handoff.select(pcm, predictions)
    readouts = {}
    for name, decoded in ((f'fixed_{a}_{b}', predictions[(a, b)])
                          for a, b in handoff.PAIRS):
        readouts[name] = readout_result(decoded, expected, offered, exe,
                                       selector, delay)
    readouts['frozen_margin'] = readout_result(selected, expected, offered,
                                              exe, selector, delay)
    return dict(rx_trace_digest=result['trace_digest'],
                adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                selected_pairs={f'{a}/{b}': selected_pairs.count(f'{a}/{b}')
                                for a, b in handoff.PAIRS},
                readouts=readouts,
                expected_line_bytes=[f'{value:02X}' for value in offered])


def readout_result(decoded, expected, offered, exe, selector, delay):
    data = decoded[PREAMBLE + PIPELINE_SYMBOLS:]
    wrong = [i for i, (value, want) in enumerate(zip(data, expected[
        PREAMBLE + PIPELINE_SYMBOLS:])) if value is not None and value != want]
    unknown = [i for i, value in enumerate(data) if value is None]
    recovered = None
    controller = None
    if not wrong and not unknown:
        recovered = handoff.bytes_lsb_first([
            bit for dibit in data for bit in (dibit & 1, (dibit >> 1) & 1)])
        controller = {str(pulse): handoff.controller(exe, delay,
                      int(selector, 16), pulse, recovered)
                      for pulse in (handoff.DATA_START_BIT - 1,
                                    handoff.DATA_START_BIT,
                                    handoff.DATA_START_BIT + 1)}
    return dict(data_wrong_indices=wrong,
                data_unknown_indices=unknown,
                recovered_line_bytes=([f'{value:02X}' for value in recovered]
                                      if recovered is not None else None),
                recovered_matches_offered=(recovered == offered
                                            if recovered is not None else None),
                controller_handoffs=controller)


def run(out=HERE / 'results/joint-mask04-12a-buffered-line.json'):
    execute = capturing_execute()
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    buses = json.loads(BUSES.read_text())['zero_error_survivors']
    prior = json.loads(PRIOR.read_text())
    gate = json.loads(GATE.read_text())
    if len(buses) != 6 or len(gate['full']) != 2:
        raise ValueError('photo-compatible DAC fixture changed')
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        exe, controller_source_sha256 = handoff.compiled_controller(temporary)
        for selector, delay in (('40', 5), ('60', 18)):
            offered = line_octets([0] * 8, delay)
            result, raw, expected = transmitter(execute, mapping, base, offered)
            baseline = next(case for case in prior['cases']
                            if case['selector'] == selector)
            if result['trace_digest'] != baseline['tx_trace_digest']:
                raise ValueError('buffered controller/PROM stimulus changed')
            bus_cases = [dict(bus_index=index,
                              input_bit_to_dac_code_bit=bus,
                              **waveform_scores(raw, bus, expected))
                         for index, bus in enumerate(buses)]
            pcm = pcm_at_shift(raw, buses[0], 6)
            if (hashlib.sha256(bytes(value + 127 for value in pcm)).hexdigest() !=
                    next(row for row in bus_cases[0]['scores'] if row['shift'] == 6)['pcm_sha256']):
                raise ValueError('receiver PCM differs from line screen')
            rx = receiver_handoff(mapping, base, pcm, expected, offered, exe,
                                  selector, delay)
            cases.append(dict(selector=selector,
                              offered_line_bytes=[f'{value:02X}' for value in offered],
                              tx_trace_digest=result['trace_digest'],
                              y12a_sha256=hashlib.sha256(bytes(raw)).hexdigest(),
                              samples=len(raw),
                              bus_cases=bus_cases,
                              receiver_handoff=rx))
    paths = (Path(__file__), PRIOR, GATE, BUSES,
             HERE / 'joint_mask04_tx_12a_delayed_latch.py',
             HERE / 'joint_mask04_buffered_serial_handoff.py',
             HERE / 'photo_joint_line_filter_screen.py',
             HERE / 'reference_modem.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='ROM-sensitive 12A DAC hypothesis on buffered serial line',
                  fixture=dict(tx_cycles=TX_CYCLES, samples=SAMPLES,
                               selectors=['40', '60'],
                               dac_buses='six photo-compatible survivors',
                               latch='every 375th candidate 12A->127 NAND edge, early gate order',
                               analog='A2 mid-code mute and assumed bandpass; gain to peak 110',
                               alignment_shifts=SHIFTS,
                               receiver='real-PROM mask04 plus frozen 46/93 and margin external readouts',
                               controller_probe_sha256=controller_source_sha256),
                  cases=cases,
                  limitations=[
                      'The PROM gate, divider, latch data/clock pins, DAC bus, analog filter and ADC path are assumptions.',
                      'The frozen receive decision logic and paced USART/8031 interface are external models; no onboard RxD route is traced.',
                      'The buffered bit-pair decoder and controller-to-DSC route remain conditional.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    report = run()
    for case in report['cases']:
        print(case['selector'], [(bus['bus_index'], bus['best']['shift'],
                                 bus['best']['wrong']) for bus in case['bus_cases']])
