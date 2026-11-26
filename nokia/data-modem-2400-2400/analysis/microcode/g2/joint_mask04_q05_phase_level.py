"""Challenge the frozen four-state 12A receive rule at fixed-gain levels."""

import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_analog_holdout as holdout
import joint_mask04_12a_buffered_line as line
import joint_mask04_buffered_serial_handoff as handoff
import joint_mask04_tx_rx_loopback as loopback
import joint_mask04_q05_phase_state_holdout as phase_rule
from joint_mask04_tx_12a_delayed_latch import capturing_execute
from photo_dac_bus_permutations import mapped_codes
from photo_joint_line_filter_screen import SILENCE_END, TONE_END, bandpass
from receiver_mask04_feature_choice import alternative_states
from receiver_mask04_offset_visit_phase import project
from reference_modem import receive
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
FIXED = HERE / 'results/joint-mask04-12a-fixed-gain-phase.json'
PRIOR = HERE / 'results/joint-mask04-q05-phase-state-holdout.json'
LEVELS = (0.75, 1.0, 1.25)


def run(out=HERE / 'results/joint-mask04-q05-phase-level.json'):
    frozen = json.loads(FIXED.read_text())
    previous = json.loads(PRIOR.read_text())
    mapping = line.candidate(line.mapping_with_upper_source(0, '17.6'),
                             line.mapped(line.MAPPINGS['q3']), 4)
    _, base = line.fixture()
    execute = capturing_execute()
    cases = []
    with tempfile.TemporaryDirectory() as temp:
        controller, controller_sha = handoff.compiled_controller(temp)
        for selector, delay in (('40', 5), ('60', 18)):
            payload = holdout.PAYLOADS[1]
            offered = line_octets(payload, delay)
            tx, raw, expected = line.transmitter(execute, mapping, base, offered)
            old = next(c for c in previous['cases']
                       if c['selector'] == selector)
            if tx['trace_digest'] != old['tx_trace_digest']:
                raise ValueError(('held-out transmitter changed', selector))
            fixed_case = next(c for c in frozen['cases']
                              if c['selector'] == selector)
            gain = next(b for b in fixed_case['bus_cases']
                        if b['bus_index'] == 0)['gain']
            codes = mapped_codes(raw, holdout.BUSES[0])
            gated = codes[:TONE_END] + [128] * (SILENCE_END - TONE_END) + codes[SILENCE_END:]
            wave = bandpass([value - 128 for value in gated], 0.5)
            selected = wave[SILENCE_END + 6:SILENCE_END + 6 + line.RX_SYMBOLS * 8]
            if len(selected) != line.RX_SYMBOLS * 8:
                raise ValueError('line window changed')
            for level in LEVELS:
                pcm = [max(-127, min(127, round(value * gain * level)))
                       for value in selected]
                reference_wrong = [i for i, (got, want) in enumerate(
                    zip(receive(pcm), expected[1:])) if got != want]
                if reference_wrong:
                    raise ValueError(('fixed-gain reference line changed',
                                      selector, level, reference_wrong))
                with patch.object(loopback, 'DATA', handoff.PIPELINE_SYMBOLS + handoff.DATA_SYMBOLS), \
                        patch.object(loopback, 'SYMBOLS', line.RX_SYMBOLS), \
                        patch.object(loopback, 'ADC_VISITS', handoff.ADC_VISITS), \
                        patch.object(loopback, 'CYCLES', handoff.RX_CYCLES):
                    rx, adc, symbols = loopback.capture(mapping, base, pcm, expected)
                states = alternative_states(project(symbols, 46, 93))
                decoded = [None] + [phase_rule.dibit(a, b)
                                    for a, b in zip(states, states[1:])]
                readout = line.readout_result(decoded, expected, offered,
                                              controller, selector, delay)
                cases.append(dict(selector=selector, level=level,
                                  fixed_zero_run_gain=gain,
                                  tx_trace_digest=tx['trace_digest'],
                                  rx_trace_digest=rx['trace_digest'],
                                  pcm_sha256=hashlib.sha256(bytes(
                                      value + 127 for value in pcm)).hexdigest(),
                                  adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                                  states=[f'{value:X}' for value in states],
                                  capture_y=[dict(first=s['visits']['46']['y3f8'],
                                                  second=s['visits']['93']['y3f8'])
                                             for s in symbols],
                                  expected_dibits=expected,
                                  decoded_dibits=decoded,
                                  distinct_states=sorted({f'{value:X}'
                                                          for value in states}),
                                  unexpected_states=sorted({f'{value:X}'
                                                            for value in states
                                                            if value not in phase_rule.PHASE}),
                                  reference_wrong=0,
                                  preamble_wrong=sum(got is not None and got != want
                                                     for got, want in zip(
                                                         decoded[1:handoff.PREAMBLE +
                                                                 handoff.PIPELINE_SYMBOLS],
                                                         expected[1:handoff.PREAMBLE +
                                                                  handoff.PIPELINE_SYMBOLS])),
                                  preamble_unknown=sum(got is None
                                                       for got in decoded[1:handoff.PREAMBLE +
                                                                          handoff.PIPELINE_SYMBOLS]),
                                  readout=readout))
                print(selector, level,
                      len(readout['data_wrong_indices']),
                      len(readout['data_unknown_indices']), flush=True)
    report = dict(experiment='frozen 46/93 four-state receive rule under line-level changes',
                  fixture=dict(payload='second nonzero holdout per selector',
                               line='12A Q=0.5, bus 0, +6 sample phase',
                               gain='fixed from zero-run per selector/bus',
                               level_multipliers=LEVELS,
                               controller_probe_sha256=controller_sha),
                  cases=cases,
                  limitations=[
                      'The same payloads used in the phase-rule holdout are reused at altered line levels.',
                      'The four-state rule is external and the ADC/DAC/clock/USART/SYNDET routes are assumed.',
                      'A passing level challenge is conditional and does not prove physical C2 or C3.'
                  ],
                  source_sha256={str(p.relative_to(HERE.parents[4])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (Path(__file__), FIXED, PRIOR,
                                           HERE / 'joint_mask04_q05_phase_state_holdout.py',
                                           HERE / 'joint_mask04_tx_rx_loopback.py',
                                           HERE.parent / 'assumed/execute.py')})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
