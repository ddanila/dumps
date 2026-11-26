"""Hold out new payloads from the frozen six-bit gain/phase transition rule."""

import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_analog_holdout as holdout
import joint_mask04_12a_buffered_line as line
import joint_mask04_buffered_serial_handoff as handoff
import joint_mask04_tx_rx_loopback as loopback
from joint_mask04_12a_sixth_receive_bit import scan, state
from joint_mask04_tx_12a_delayed_latch import capturing_execute
from photo_dac_bus_permutations import mapped_codes
from photo_joint_line_filter_screen import SILENCE_END, TONE_END, bandpass
from receiver_mask04_offset_visit_phase import project
from reference_modem import receive
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
DEVELOPMENT = HERE / 'results/joint-mask04-12a-fifth-receive-bit.json'
SECOND = HERE / 'results/joint-mask04-12a-frozen-fifth-new-payloads.json'
FIXED = HERE / 'results/joint-mask04-12a-fixed-gain-phase.json'
EXTRAS = (('second', 4), ('second', 6))
PAYLOADS = {'40': (0x0F, 0x72, 0xB5, 0xC8, 0x31, 0xE6, 0x4A, 0x9D),
            '60': (0xA6, 0x19, 0xF0, 0x4D, 0x83, 0x2B, 0xC5, 0x78)}
LEVELS = (0.75, 1.0, 1.25)
PHASE_VISIT = TONE_END * 375 + 1


def run(out=HERE / 'results/joint-mask04-12a-frozen-sixth-new-payloads.json'):
    development = json.loads(DEVELOPMENT.read_text())['cases']
    second = json.loads(SECOND.read_text())['cases']
    fixed = json.loads(FIXED.read_text())
    table, conflicts = scan(development + second, EXTRAS)
    if conflicts or len(table) != 91:
        raise ValueError(('six-bit development rule changed', len(table), conflicts))
    mapping = line.candidate(line.mapping_with_upper_source(0, '17.6'),
                             line.mapped(line.MAPPINGS['q3']), 4)
    _, base = line.fixture()
    cases = []
    with tempfile.TemporaryDirectory() as temp:
        controller, controller_sha = handoff.compiled_controller(temp)
        for selector, delay in (('40', 5), ('60', 18)):
            offered = line_octets(PAYLOADS[selector], delay)
            tx, raw, expected = line.transmitter(
                capturing_execute((PHASE_VISIT, 32)), mapping, base, offered)
            gain = next(b for b in next(c for c in fixed['cases']
                                       if c['selector'] == selector)['bus_cases']
                        if b['bus_index'] == 0)['gain']
            codes = mapped_codes(raw, holdout.BUSES[0])
            gated = codes[:TONE_END] + [128] * (SILENCE_END - TONE_END) + codes[SILENCE_END:]
            wave = bandpass([value - 128 for value in gated], 0.5)
            selected = wave[SILENCE_END + 6:SILENCE_END + 6 + line.RX_SYMBOLS * 8]
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
                rows = project(symbols, 46, 93)
                first = [r['visits']['47']['y3f8'] for r in rows]
                second_y = [r['visits']['94']['y3f8'] for r in rows]
                states = [state(a, b, EXTRAS) for a, b in zip(first, second_y)]
                keys = [(a << 6) | b for a, b in zip(states, states[1:])]
                decoded = [None] + [table.get(key) for key in keys]
                wrong = [i for i, (got, want) in enumerate(zip(
                    decoded[1:], expected[1:]), 1)
                         if got is not None and got != want]
                unknown = [i for i, got in enumerate(decoded[1:], 1)
                           if got is None]
                readout = line.readout_result(decoded, expected, offered,
                                              controller, selector, delay)
                cases.append(dict(selector=selector, level=level,
                                  payload=[f'{v:02X}' for v in PAYLOADS[selector]],
                                  offered_line_bytes=[f'{v:02X}' for v in offered],
                                  tx_trace_digest=tx['trace_digest'],
                                  rx_trace_digest=rx['trace_digest'],
                                  raw_sha256=hashlib.sha256(bytes(raw)).hexdigest(),
                                  pcm_sha256=hashlib.sha256(bytes(v + 127 for v in pcm)).hexdigest(),
                                  adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                                  reference_wrong_indices=reference_wrong,
                                  expected_dibits=expected,
                                  first_y=first,second_y=second_y,
                                  transition_keys=[f'{key:03X}' for key in keys],
                                  new_transition_keys=sorted(f'{key:03X}' for key in set(keys)
                                                             if key not in table),
                                  wrong_indices=wrong, unknown_indices=unknown,
                                  decoded_dibits=decoded,
                                  readout=readout))
                print(selector,level,'wrong',len(wrong),'unknown',len(unknown),
                      'reference',len(reference_wrong),flush=True)
    paths = (Path(__file__), DEVELOPMENT, SECOND, FIXED,
             HERE / 'joint_mask04_12a_sixth_receive_bit.py',
             HERE / 'joint_mask04_12a_buffered_line.py',
             HERE / 'joint_mask04_tx_rx_loopback.py',
             HERE.parent / 'assumed/execute.py')
    report = dict(experiment='frozen six-bit rule on third payloads at combined phase/gain',
                  fixture=dict(payloads={name:[f'{v:02X}' for v in values]
                                         for name,values in PAYLOADS.items()},
                               levels=LEVELS,phase_offset=32,phase_visit=PHASE_VISIT,
                               feature='first Y5–Y7; second Y4,Y6,Y7; transition width 12',
                               trained_keys=len(table),
                               line='Q=0.5, bus 0, +6 samples, zero-run gain',
                               controller_probe_sha256=controller_sha),
                  cases=cases,
                  limitations=['The feature and 91 transition labels were frozen before these payloads.',
                               'The R1 offset, converter buses, analog filter, capture clocks and serial logic remain photo-compatible hypotheses.',
                               'Unseen transition keys remain unknown; no label is fitted on these cases.'],
                  source_sha256={str(p.relative_to(HERE.parents[4])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in paths})
    out.write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    run()
