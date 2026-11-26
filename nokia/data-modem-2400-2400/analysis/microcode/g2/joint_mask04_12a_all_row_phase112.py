"""Rerun a changed carrier phase and test U24-style row qualification."""

import hashlib
import json
from pathlib import Path

import joint_mask04_12a_all_row_latch as original
import joint_mask04_12a_analog_holdout as holdout
import joint_mask04_12a_buffered_line as line
import joint_mask04_12a_frozen_sixth_new_payloads as frozen
import joint_mask04_buffered_serial_handoff as handoff
from joint_mask04_12a_row0_serial_timing import covers_from_model
from joint_mask04_tx_12a_delayed_latch import capturing_execute
from photo_dac_bus_permutations import mapped_codes
from photo_joint_line_filter_screen import SILENCE_END, TONE_END, bandpass
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'results/joint-mask04-12a-row0-boolean-phase112.json'
LOGIC = HERE / 'results/joint-mask04-12a-row0-boolean-twentytwo.json'
FIXED = HERE / 'results/joint-mask04-12a-fixed-gain-phase.json'
OUT = HERE / 'results/joint-mask04-12a-all-row-phase112.json'


def run(out=OUT):
    source = json.loads(SOURCE.read_text())
    fixed = json.loads(FIXED.read_text())
    model = json.loads(LOGIC.read_text())
    covers = covers_from_model(model)
    inverse = {step: dibit for dibit, step in
               enumerate(model['fixture']['phase_convention'])}
    mapping = line.candidate(line.mapping_with_upper_source(0, '17.6'),
                             line.mapped(line.MAPPINGS['q3']), 4)
    _, base = line.fixture()
    cases = []
    for old in source['cases']:
        selector = old['selector']
        delay = 5 if selector == '40' else 18
        payload = tuple(int(value, 16) for value in old['payload'])
        offered = line_octets(payload, delay)
        tx, raw, expected = line.transmitter(
            capturing_execute((frozen.PHASE_VISIT, 112)), mapping, base, offered)
        if (tx['trace_digest'] != old['tx_trace_digest'] or
                hashlib.sha256(bytes(raw)).hexdigest() != old['raw_sha256'] or
                expected != old['expected_dibits']):
            raise ValueError(('transmitter changed', selector))
        gain = next(bus for bus in next(case for case in fixed['cases']
                        if case['selector'] == selector)['bus_cases']
                    if bus['bus_index'] == 0)['gain']
        codes = mapped_codes(raw, holdout.BUSES[0])
        gated = codes[:TONE_END] + [128] * (SILENCE_END - TONE_END) + codes[SILENCE_END:]
        wave = bandpass([value - 128 for value in gated], 0.5)
        selected = wave[SILENCE_END + 6:SILENCE_END + 6 + line.RX_SYMBOLS * 8]
        pcm = [max(-127, min(127, round(value * gain))) for value in selected]
        if hashlib.sha256(bytes(value + 127 for value in pcm)).hexdigest() != old['pcm_sha256']:
            raise ValueError(('line PCM changed', selector))
        rx, adc, rows = original.capture_rows(mapping, base, pcm)
        if (rx['trace_digest'] != old['rx_trace_digest'] or
                hashlib.sha256(bytes(adc)).hexdigest() != old['adc_sha256']):
            raise ValueError(('real-PROM receiver changed', selector))
        if any(rows[(symbol, visit)]['row0'] !=
               old['multi_visit_symbols'][symbol]['visits'][str(visit)]['row0'] or
               rows[(symbol, visit)]['row3'] !=
               old['multi_visit_symbols'][symbol]['visits'][str(visit)]['row3']
               for symbol in range(handoff.RX_SYMBOLS) for visit in original.VISITS):
            raise ValueError(('captured old rows changed', selector))
        row_cases = []
        for row in range(4):
            got = original.decisions(rows, row, covers, inverse)
            wrong = [index for index, (actual, want) in enumerate(
                zip(got, expected[1:]), 1) if actual != want]
            row_cases.append(dict(row=row, decision_errors=len(wrong),
                                  wrong_indices=wrong))
        if row_cases[0]['decision_errors'] or not all(
                item['decision_errors'] for item in row_cases[1:]):
            raise ValueError(('row discrimination changed', selector))
        if any(rows[(symbol, visit)]['row1'] or rows[(symbol, visit)]['row2']
               for symbol in range(handoff.RX_SYMBOLS) for visit in original.VISITS):
            raise ValueError(('intermediate row outputs changed', selector))
        cases.append(dict(selector=selector, payload=old['payload'],
                          rx_trace_digest=rx['trace_digest'],
                          row_cases=row_cases,
                          u24_qualified_preincrement_00_errors=row_cases[0]['decision_errors'],
                          u24_unqualified_every_row_errors=row_cases[3]['decision_errors'],
                          sample_rows=[dict(symbol=symbol, visit=visit,
                                            **rows[(symbol, visit)])
                                       for symbol in range(handoff.RX_SYMBOLS)
                                       for visit in original.VISITS]))
        print('phase112 all-row', selector,
              [item['decision_errors'] for item in row_cases], flush=True)
    paths = (Path(__file__), SOURCE, LOGIC, FIXED,
             HERE / 'joint_mask04_12a_all_row_latch.py',
             HERE / 'joint_mask04_12a_row0_serial_timing.py')
    report = dict(experiment='all-row real-PROM capture and U24-style qualifier at changed carrier phase',
                  fixture=dict(phase_offset=112, line_shift=6, level=1.0,
                               capture_visits=original.VISITS,
                               phase_gates='frozen 22-state model',
                               assumed_counter='U24 modulo-four, 00 before row-0 increment'),
                  cases=cases,
                  limitations=[
                      'The row counter, qualifier gate and latch clock are photo-compatible assumptions, not traced nets.',
                      'The DAC, analog line and ADC route remain assumed; Tx and Rx executions use the actual PROM dumps.',
                      'Only the two phase-112 payloads and one line level are tested.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
