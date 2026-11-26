"""Challenge the frozen seven-state 12A receiver on new controller payloads."""

import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_analog_holdout as holdout
import joint_mask04_12a_buffered_line as line
import joint_mask04_buffered_serial_handoff as handoff
import joint_mask04_q05_phase_level_map as phase_model
import joint_mask04_tx_rx_loopback as loopback
from joint_mask04_tx_12a_delayed_latch import capturing_execute
from photo_dac_bus_permutations import mapped_codes
from photo_joint_line_filter_screen import SILENCE_END, TONE_END, bandpass
from receiver_mask04_feature_choice import alternative_states
from receiver_mask04_offset_visit_phase import project
from reference_modem import receive
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
FIXED = HERE / 'results/joint-mask04-12a-fixed-gain-phase.json'
RULE = HERE / 'results/joint-mask04-q05-phase-level-map.json'
PAYLOADS = {'40': (0xD3, 0x26, 0x91, 0x4E, 0xB8, 0x07, 0x5C, 0xEA),
            '60': (0x6A, 0xD5, 0x02, 0xB9, 0x40, 0xEF, 0x73, 0x1C)}
LEVELS = (0.75, 1.0, 1.25)


def run(out=HERE / 'results/joint-mask04-q05-fresh-payload-levels.json'):
    frozen = json.loads(FIXED.read_text())
    rule = json.loads(RULE.read_text())
    phase = {int(key, 16): value for family in ('base_phase', 'learned_phase')
             for key, value in rule['rule'][family].items()}
    if phase != {5: 0, 8: 1, 12: 2, 13: 3, 6: 0, 9: 1, 11: 2}:
        raise ValueError('frozen phase rule changed')
    mapping = line.candidate(line.mapping_with_upper_source(0, '17.6'),
                             line.mapped(line.MAPPINGS['q3']), 4)
    _, base = line.fixture()
    execute = capturing_execute()
    cases = []
    with tempfile.TemporaryDirectory() as temp:
        controller, controller_sha = handoff.compiled_controller(temp)
        for selector, delay in (('40', 5), ('60', 18)):
            payload = PAYLOADS[selector]
            offered = line_octets(payload, delay)
            tx, raw, expected = line.transmitter(execute, mapping, base, offered)
            fixed_case = next(c for c in frozen['cases']
                              if c['selector'] == selector)
            gain = next(b for b in fixed_case['bus_cases']
                        if b['bus_index'] == 0)['gain']
            codes = mapped_codes(raw, holdout.BUSES[0])
            gated = (codes[:TONE_END] + [128] * (SILENCE_END - TONE_END) +
                     codes[SILENCE_END:])
            wave = bandpass([value - 128 for value in gated], 0.5)
            selected = wave[SILENCE_END + 6:SILENCE_END + 6 + line.RX_SYMBOLS * 8]
            if len(selected) != line.RX_SYMBOLS * 8:
                raise ValueError('fresh line window changed')
            for level in LEVELS:
                pcm = [max(-127, min(127, round(value * gain * level)))
                       for value in selected]
                reference_wrong = [i for i, (got, want) in enumerate(
                    zip(receive(pcm), expected[1:])) if got != want]
                with patch.object(loopback, 'DATA', handoff.PIPELINE_SYMBOLS + handoff.DATA_SYMBOLS), \
                        patch.object(loopback, 'SYMBOLS', line.RX_SYMBOLS), \
                        patch.object(loopback, 'ADC_VISITS', handoff.ADC_VISITS), \
                        patch.object(loopback, 'CYCLES', handoff.RX_CYCLES):
                    rx, adc, symbols = loopback.capture(mapping, base, pcm, expected)
                states = alternative_states(project(symbols, 46, 93))
                decoded = phase_model.decode([f'{value:X}' for value in states],
                                             phase)
                readout = line.readout_result(decoded, expected, offered,
                                              controller, selector, delay)
                pre_end = handoff.PREAMBLE + handoff.PIPELINE_SYMBOLS
                cases.append(dict(selector=selector, level=level,
                                  payload=[f'{value:02X}' for value in payload],
                                  offered_line_bytes=[f'{value:02X}' for value in offered],
                                  tx_trace_digest=tx['trace_digest'],
                                  raw_y12a_sha256=hashlib.sha256(bytes(raw)).hexdigest(),
                                  rx_trace_digest=rx['trace_digest'],
                                  pcm_sha256=hashlib.sha256(bytes(
                                      value + 127 for value in pcm)).hexdigest(),
                                  adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                                  reference_wrong_indices=reference_wrong,
                                  distinct_states=sorted({f'{value:X}'
                                                          for value in states}),
                                  unknown_states=sorted({f'{value:X}'
                                                         for value in states
                                                         if value not in phase}),
                                  states=[f'{value:X}' for value in states],
                                  expected_dibits=expected,
                                  decoded_dibits=decoded,
                                  preamble_wrong=sum(got is not None and got != want
                                                     for got, want in zip(
                                                         decoded[1:pre_end],
                                                         expected[1:pre_end])),
                                  preamble_unknown=sum(got is None
                                                       for got in decoded[1:pre_end]),
                                  readout=readout))
                print(selector, level, 'reference', len(reference_wrong),
                      'DSC', len(readout['data_wrong_indices']),
                      len(readout['data_unknown_indices']), flush=True)
    report = dict(experiment='frozen seven-state 12A receiver on fresh payloads and levels',
                  fixture=dict(payloads={name: [f'{v:02X}' for v in values]
                                         for name, values in PAYLOADS.items()},
                               levels=LEVELS,
                               line='Q=0.5, 1950 Hz, bus 0, shift +6, zero-run-fixed gain',
                               phase_map={f'{key:X}': value for key, value in phase.items()},
                               controller_probe_sha256=controller_sha),
                  cases=cases,
                  limitations=[
                      'These payloads were not used to fit the frozen phase map; each selector has one new eight-byte source.',
                      'The phase mapping and all DAC/ADC/clock/USART/SYNDET routes remain external photo-compatible hypotheses.',
                      'A conditional handoff is not proof of physical C2 or C3.'
                  ],
                  source_sha256={str(p.relative_to(HERE.parents[4])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (Path(__file__), FIXED, RULE,
                                           HERE / 'joint_mask04_q05_phase_level_map.py',
                                           HERE / 'joint_mask04_tx_rx_loopback.py',
                                           HERE.parent / 'assumed/execute.py')})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
