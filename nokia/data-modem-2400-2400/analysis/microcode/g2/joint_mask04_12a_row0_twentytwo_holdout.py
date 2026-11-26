"""Fresh real-PROM Tx-to-Rx holdout for frozen 22-state gates and +5 line shift."""

import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_analog_holdout as holdout
import joint_mask04_12a_buffered_line as line
import joint_mask04_12a_frozen_sixth_new_payloads as frozen
import joint_mask04_buffered_serial_handoff as handoff
import joint_mask04_tx_rx_loopback as loopback
from joint_mask04_12a_multivisit_phase_screen import HERE, SELECTED, sample_state
from joint_mask04_12a_row0_boolean import phase
from joint_mask04_tx_12a_delayed_latch import capturing_execute
from photo_dac_bus_permutations import mapped_codes
from photo_joint_line_filter_screen import SILENCE_END, TONE_END, bandpass
from reference_modem import receive
from zero_run_detector import line_octets

MODEL = HERE / 'results/joint-mask04-12a-row0-boolean-twentytwo.json'
FIXED = HERE / 'results/joint-mask04-12a-fixed-gain-phase.json'
SCREEN = HERE / 'results/joint-mask04-12a-phase112-line-shift.json'
OUT = HERE / 'results/joint-mask04-12a-row0-twentytwo-holdout.json'
PAYLOADS = {'40': (0x84, 0x2F, 0xD1, 0x6B, 0x09, 0xF5, 0x38, 0xC2),
            '60': (0x47, 0xBA, 0x03, 0xE9, 0x5C, 0x16, 0xD0, 0x7F)}
OFFSET = 112
SHIFT = 5


def run(out=OUT):
    model = json.loads(MODEL.read_text())
    fixed = json.loads(FIXED.read_text())
    screen = json.loads(SCREEN.read_text())
    if any(case['shifts'][str(SHIFT)]['wrong_indices_zero_based']
           for case in screen['cases']):
        raise ValueError('frozen line shift not exact on development pair')
    covers = [tuple(tuple(-1 if char == '*' else int(char) for char in cube)
                    for cube in bit['cubes']) for bit in model['phase_bits']]
    inverse = {step: dibit for dibit, step in enumerate(
        model['fixture']['phase_convention'])}
    known = set(model['state_phase'])
    mapping = line.candidate(line.mapping_with_upper_source(0, '17.6'),
                             line.mapped(line.MAPPINGS['q3']), 4)
    _, base = line.fixture()
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        controller, controller_sha = handoff.compiled_controller(temporary)
        for selector, delay in (('40', 5), ('60', 18)):
            offered = line_octets(PAYLOADS[selector], delay)
            tx, raw, expected = line.transmitter(
                capturing_execute((frozen.PHASE_VISIT, OFFSET)),
                mapping, base, offered)
            gain = next(bus for bus in next(c for c in fixed['cases']
                           if c['selector'] == selector)['bus_cases']
                        if bus['bus_index'] == 0)['gain']
            codes = mapped_codes(raw, holdout.BUSES[0])
            gated = codes[:TONE_END] + [128] * (SILENCE_END - TONE_END) + codes[SILENCE_END:]
            wave = bandpass([value - 128 for value in gated], 0.5)
            selected = wave[SILENCE_END + SHIFT:
                            SILENCE_END + SHIFT + line.RX_SYMBOLS * 8]
            pcm = [max(-127, min(127, round(value * gain))) for value in selected]
            reference_wrong = [index for index, (got, want) in enumerate(
                zip(receive(pcm), expected[1:])) if got != want]
            with patch.object(loopback, 'DATA', handoff.PIPELINE_SYMBOLS + handoff.DATA_SYMBOLS), \
                    patch.object(loopback, 'SYMBOLS', line.RX_SYMBOLS), \
                    patch.object(loopback, 'ADC_VISITS', handoff.ADC_VISITS), \
                    patch.object(loopback, 'CYCLES', handoff.RX_CYCLES):
                rx, adc, symbols = loopback.capture(mapping, base, pcm, expected)
            states = [sample_state(symbol, SELECTED) for symbol in symbols]
            phases = [phase(value, covers) for value in states]
            decoded = [None] + [inverse[(b - a) & 3]
                                for a, b in zip(phases, phases[1:])]
            wrong = [index for index, (got, want) in enumerate(
                zip(decoded[1:], expected[1:]), 1) if got != want]
            readout = line.readout_result(decoded, expected, offered,
                                          controller, selector, delay)
            cases.append(dict(selector=selector,
                              payload=[f'{value:02X}' for value in PAYLOADS[selector]],
                              offered_line_bytes=[f'{value:02X}' for value in offered],
                              tx_trace_digest=tx['trace_digest'],
                              rx_trace_digest=rx['trace_digest'],
                              raw_sha256=hashlib.sha256(bytes(raw)).hexdigest(),
                              pcm_sha256=hashlib.sha256(bytes(value + 127 for value in pcm)).hexdigest(),
                              adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                              expected_dibits=expected,
                              reference_wrong_indices_zero_based=reference_wrong,
                              states=[f'{value:02X}' for value in states],
                              unseen_states=sorted(f'{value:02X}' for value in set(states)
                                                   if f'{value:02X}' not in known),
                              decoded_dibits=decoded,
                              wrong_indices_one_based=wrong,
                              readout=readout))
            print('22-state holdout', selector, 'reference', len(reference_wrong),
                  'gate', len(wrong), 'unseen', cases[-1]['unseen_states'],
                  'line', readout['recovered_matches_offered'], flush=True)
    paths = (Path(__file__), MODEL, FIXED, SCREEN,
             HERE / 'joint_mask04_12a_buffered_line.py',
             HERE / 'joint_mask04_tx_rx_loopback.py',
             HERE / 'joint_mask04_12a_multivisit_phase_screen.py',
             HERE / 'joint_mask04_12a_row0_boolean.py',
             HERE.parent / 'assumed/execute.py', line.MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='frozen 22-state gates and +5 reference line on fresh phase-112 payloads',
                  fixture=dict(R1_offset=OFFSET, level=1.0, line_shift=SHIFT,
                               Q=0.5, candidate_DAC_bus=0,
                               controller_probe_sha256=controller_sha,
                               feature=SELECTED),
                  cases=cases,
                  limitations=[
                      'The 22-state gates and line shift were frozen before these two payloads.',
                      'A correct external phase gate and modeled 8251/8031 handoff do not identify Nokia receiver hardware.',
                      'DAC, ADC, latch, clock, phase logic and serial nets remain untraced assumptions.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
