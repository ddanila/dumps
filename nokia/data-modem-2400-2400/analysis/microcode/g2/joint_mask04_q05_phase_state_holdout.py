"""Freeze a four-state 46/93 phase rule, then replay fresh 12A data to 8031."""

import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_analog_holdout as holdout
import joint_mask04_12a_buffered_line as line
import joint_mask04_buffered_serial_handoff as handoff
import joint_mask04_tx_rx_loopback as loopback
from joint_mask04_tx_12a_delayed_latch import capturing_execute
from photo_dac_bus_permutations import mapped_codes
from photo_joint_line_filter_screen import SILENCE_END, TONE_END, bandpass
from receiver_mask04_feature_choice import alternative_states
from receiver_mask04_offset_visit_phase import project
from reference_modem import QUADRANT_TO_DIBIT, receive
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
TRAIN = HERE / 'results/joint-mask04-q05-receive-key-collisions.json'
HOLDOUT = HERE / 'results/joint-mask04-12a-analog-holdout.json'
PHASE = {0x5: 0, 0x8: 1, 0xC: 2, 0xD: 3}


def dibit(before, after):
    if before not in PHASE or after not in PHASE:
        return None
    return QUADRANT_TO_DIBIT[(PHASE[after] - PHASE[before] - 2) & 3]


def run(out=HERE / 'results/joint-mask04-q05-phase-state-holdout.json'):
    training = json.loads(TRAIN.read_text())
    saved = json.loads(HOLDOUT.read_text())
    seen = 0
    for case in training['cases']:
        for row in case['feature_rows']:
            if row['pair'] == '46/93' and row['feature'] == 'alternative':
                if dibit(row['key'] >> 4, row['key'] & 15) != row['dibit']:
                    raise ValueError(('frozen four-state rule fails development',
                                      case['selector'], row['data_index']))
                seen += 1
    if seen != 64:
        raise ValueError('development decision count changed')
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
            old = next(c for c in saved['cases']
                       if c['selector'] == selector and c['payload_index'] == 1)
            if (tx['trace_digest'] != old['tx_trace_digest'] or
                    hashlib.sha256(bytes(raw)).hexdigest() !=
                    old['y12a_sha256']):
                raise ValueError(('saved holdout transmitter changed', selector))
            codes = mapped_codes(raw, holdout.BUSES[0])
            gated = (codes[:TONE_END] + [128] * (SILENCE_END - TONE_END) +
                     codes[SILENCE_END:])
            wave = bandpass([value - 128 for value in gated], 0.5)
            selected = wave[SILENCE_END + 6:SILENCE_END + 6 + line.RX_SYMBOLS * 8]
            gain = 110 / max(abs(value) for value in selected)
            pcm = [max(-127, min(127, round(value * gain)))
                   for value in selected]
            pcm_hash = hashlib.sha256(bytes(value + 127 for value in pcm)).hexdigest()
            saved_score = next(s for s in old['bus_cases'][0]['scores']
                               if s['q'] == 0.5)
            if (pcm_hash != saved_score['pcm_sha256'] or
                    receive(pcm) != expected[1:]):
                raise ValueError(('saved holdout line changed', selector))
            with patch.object(loopback, 'DATA', handoff.PIPELINE_SYMBOLS + handoff.DATA_SYMBOLS), \
                    patch.object(loopback, 'SYMBOLS', line.RX_SYMBOLS), \
                    patch.object(loopback, 'ADC_VISITS', handoff.ADC_VISITS), \
                    patch.object(loopback, 'CYCLES', handoff.RX_CYCLES):
                rx, adc, symbols = loopback.capture(mapping, base, pcm, expected)
            projected = project(symbols, 46, 93)
            states = alternative_states(projected)
            decoded = [None] + [dibit(before, after)
                                for before, after in zip(states, states[1:])]
            data_offset = handoff.PREAMBLE + handoff.PIPELINE_SYMBOLS
            data_wrong = [i for i, (actual, want) in enumerate(
                zip(decoded[data_offset:], expected[data_offset:]))
                if actual is not None and actual != want]
            data_unknown = [i for i, actual in
                            enumerate(decoded[data_offset:]) if actual is None]
            result = line.readout_result(decoded, expected, offered,
                                         controller, selector, delay)
            if (result['data_wrong_indices'] != data_wrong or
                    result['data_unknown_indices'] != data_unknown):
                raise ValueError('controller readout score changed')
            cases.append(dict(selector=selector,
                              payload=[f'{value:02X}' for value in payload],
                              offered_line_bytes=[f'{value:02X}' for value in offered],
                              tx_trace_digest=tx['trace_digest'],
                              rx_trace_digest=rx['trace_digest'],
                              pcm_sha256=pcm_hash,
                              adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                              states=[f'{value:X}' for value in states],
                              expected_dibits=expected,
                              decoded_dibits=decoded,
                              preamble_wrong=sum(got is not None and got != want
                                                 for got, want in zip(
                                                     decoded[1:data_offset],
                                                     expected[1:data_offset])),
                              preamble_unknown=sum(got is None
                                                   for got in decoded[1:data_offset]),
                              readout=result))
    report = dict(experiment='frozen four-state 46/93 Q=0.5 receive holdout',
                  rule=dict(phase={f'{key:X}': value for key, value in PHASE.items()},
                            state='Y5..Y7 at visit 46, Y7 at visit 93',
                            dibit='QUADRANT_TO_DIBIT[(phase_after-phase_before-2) mod 4]',
                            carrier_advance='two quadrants per symbol',
                            development_decisions=seen),
                  fixture=dict(mapping='q3 mask04',
                               payload='second nonzero eight-byte payload per selector',
                               line='ROM-sensitive 12A, Q=0.5, +6 samples, bus 0',
                               controller_probe_sha256=controller_sha),
                  cases=cases,
                  limitations=[
                      'The four-state phase map is inferred from 64 labelled development decisions, not an identified board circuit.',
                      'The capture clock, ADC, DAC, analog line, serial logic and USART/SYNDET wiring are assumed.',
                      'A complete modeled controller handoff is conditional and does not by itself pass physical C3.'
                  ],
                  source_sha256={str(p.relative_to(HERE.parents[4])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (Path(__file__), TRAIN, HOLDOUT,
                                           HERE / 'joint_mask04_12a_q05_receiver.py',
                                           HERE / 'joint_mask04_tx_rx_loopback.py',
                                           HERE.parent / 'assumed/execute.py')})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    report = run()
    for case in report['cases']:
        result = case['readout']
        print(case['selector'], 'data wrong/unknown',
              len(result['data_wrong_indices']),
              len(result['data_unknown_indices']),
              'bytes match', result['recovered_matches_offered'])
