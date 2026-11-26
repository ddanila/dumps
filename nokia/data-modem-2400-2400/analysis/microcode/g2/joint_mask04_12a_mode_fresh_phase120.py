"""Challenge frozen mode-aware gates with fresh data and carrier start."""

import hashlib
import json
import tempfile
from pathlib import Path

import joint_mask04_12a_analog_holdout as holdout
import joint_mask04_12a_buffered_line as line
import joint_mask04_12a_frozen_sixth_new_payloads as frozen
import joint_mask04_buffered_serial_handoff as handoff
from joint_mask04_12a_multivisit_phase_screen import SELECTED, sample_state
from joint_mask04_12a_row0_serial_timing import VARIANTS, covers_from_model, replay
from joint_mask04_12a_row_mode_edge import EDGE, MODE_READS, execute_case
from joint_mask04_tx_12a_delayed_latch import capturing_execute
from photo_dac_bus_permutations import mapped_codes
from photo_joint_line_filter_screen import SILENCE_END, TONE_END, bandpass
from reference_modem import receive
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
MODEL = HERE / 'results/joint-mask04-12a-mode-phase-holdout.json'
OLD = HERE / 'results/joint-mask04-12a-row0-boolean-twentytwo.json'
FIXED = HERE / 'results/joint-mask04-12a-fixed-gain-phase.json'
OUT = HERE / 'results/joint-mask04-12a-mode-fresh-phase120.json'
PAYLOADS = {
    '40': (0xA6, 0x13, 0xE8, 0x5D, 0xC2, 0x7B, 0x90, 0x4F),
    '60': (0x35, 0xDC, 0x04, 0xB9, 0x6E, 0x81, 0xF2, 0x47),
}
OFFSET = 120
SHIFT = 5


def run(out=OUT):
    model = json.loads(MODEL.read_text())
    prior = json.loads(OLD.read_text())
    fixed = json.loads(FIXED.read_text())
    covers = covers_from_model(model)
    old_covers = covers_from_model(prior)
    inverse = {step: dibit for dibit, step in
               enumerate(model['fixture']['phase_convention'])}
    known = {int(key, 16) for key in model['trained_state_phase']}
    mapping = line.candidate(line.mapping_with_upper_source(0, '17.6'),
                             line.mapped(line.MAPPINGS['q3']), 4)
    _, base = line.fixture()
    mode_values = [0x81] * EDGE + [0xA1] * (MODE_READS - EDGE)
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        exe, controller_sha = handoff.compiled_controller(temporary)
        for selector, delay in (('40', 5), ('60', 18)):
            payload = PAYLOADS[selector]
            offered = line_octets(payload, delay)
            tx, raw, expected = line.transmitter(
                capturing_execute((frozen.PHASE_VISIT, OFFSET)),
                mapping, base, offered)
            gain = next(bus for bus in next(case for case in fixed['cases']
                            if case['selector'] == selector)['bus_cases']
                        if bus['bus_index'] == 0)['gain']
            codes = mapped_codes(raw, holdout.BUSES[0])
            gated = codes[:TONE_END] + [128] * (SILENCE_END - TONE_END) + codes[SILENCE_END:]
            wave = bandpass([value - 128 for value in gated], 0.5)
            selected = wave[SILENCE_END + SHIFT:
                            SILENCE_END + SHIFT + line.RX_SYMBOLS * 8]
            pcm = [max(-127, min(127, round(value * gain))) for value in selected]
            reference_wrong = [index + 1 for index, (got, want) in enumerate(
                zip(receive(pcm), expected[1:])) if got != want]
            rx, pc_digest, symbols, gate_edges = execute_case(
                mapping, base, pcm, mode_values)
            symbols = [symbols[s] for s in range(handoff.RX_SYMBOLS)]
            states = [sample_state(symbol, SELECTED) for symbol in symbols]
            case = dict(multi_visit_symbols=symbols, expected_dibits=expected,
                        selector=selector, payload=[f'{value:02X}' for value in payload],
                        offered_line_bytes=[f'{value:02X}' for value in offered])
            score = replay(case, VARIANTS['aligned'], covers, inverse, exe)
            old_score = replay(case, VARIANTS['aligned'], old_covers, inverse, exe)
            cases.append(dict(selector=selector, payload=case['payload'],
                              tx_trace_digest=tx['trace_digest'],
                              rx_trace_digest=rx['trace_digest'],
                              pc_digest=pc_digest,
                              raw_sha256=hashlib.sha256(bytes(raw)).hexdigest(),
                              pcm_sha256=hashlib.sha256(bytes(value + 127 for value in pcm)).hexdigest(),
                              gate_edges=gate_edges,
                              reference_wrong_indices=reference_wrong,
                              expected_dibits=expected,
                              observed_states=[f'{value:02X}' for value in states],
                              unseen_states=sorted(f'{value:02X}' for value in
                                                   set(states) - known),
                              frozen_gate_wrong_indices=score['wrong_decision_indices'],
                              old_gate_wrong_indices=old_score['wrong_decision_indices'],
                              recovered_matches_offered=score['recovered_matches_offered'],
                              controller_decoded_bytes=score['controller_decoded_bytes'],
                              controller_errors=score['controller_errors'],
                              controller_overruns=score['controller_overruns'],
                              minimum_setup_cycles=score['minimum_setup_cycles'],
                              multi_visit_symbols=symbols))
            print('fresh mode phase120', selector,
                  'reference', len(reference_wrong),
                  'new gate', len(score['wrong_decision_indices']),
                  'unseen', cases[-1]['unseen_states'], flush=True)
    paths = (Path(__file__), MODEL, OLD, FIXED,
             HERE / 'joint_mask04_12a_row_mode_edge.py',
             HERE / 'joint_mask04_12a_row0_serial_timing.py')
    report = dict(experiment='frozen changed-mode receiver gates on fresh phase-120 payloads',
                  fixture=dict(payloads={key: [f'{value:02X}' for value in values]
                                         for key, values in PAYLOADS.items()},
                               R1_offset=OFFSET, line_shift=SHIFT,
                               filter_Q=0.5, level=1.0,
                               assumed_mode='81-to-A1 at D3EB read 48001',
                               controller_probe_sha256=controller_sha),
                  cases=cases,
                  limitations=[
                      'Both payloads and carrier offset are outside the changed-mode development and answer holdout; the gates are unchanged.',
                      'The frame byte to D3EB, DAC/ADC, latch, logic and USART nets remain explicit assumptions.',
                      'The first reversal dibit and aligned SYNDET edge are supplied by the known preamble fixture.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
