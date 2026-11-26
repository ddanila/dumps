"""Audit executed receive feature collisions on the improved 12A line."""

import hashlib
import json
from collections import defaultdict
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_analog_holdout as holdout
import joint_mask04_12a_buffered_line as line
import joint_mask04_tx_rx_loopback as loopback
import joint_mask04_buffered_serial_handoff as handoff
from joint_mask04_tx_12a_delayed_latch import capturing_execute
from photo_dac_bus_permutations import mapped_codes
from photo_joint_line_filter_screen import SILENCE_END, TONE_END, bandpass
from receiver_mask04_feature_choice import alternative_states
from receiver_mask04_four_bit_transition import states_from_symbols
from receiver_mask04_offset_visit_phase import project
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
PRIOR = HERE / 'results/joint-mask04-12a-q05-receiver.json'
PAIR_NAMES = ((46, 93), (47, 94), (94, 141))


def collisions(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row['key']].append(row)
    conflicting = {f'{key:02X}': values for key, values in groups.items()
                   if len({row['dibit'] for row in values}) > 1}
    return dict(keys=len(groups), conflicting_keys=len(conflicting),
                affected_positions=sum(len(values)
                                       for values in conflicting.values()),
                examples=dict(list(sorted(conflicting.items()))[:12]))


def run(out=HERE / 'results/joint-mask04-q05-receive-key-collisions.json'):
    saved = json.loads(PRIOR.read_text())
    mapping = line.candidate(line.mapping_with_upper_source(0, '17.6'),
                             line.mapped(line.MAPPINGS['q3']), 4)
    _, base = line.fixture()
    execute = capturing_execute()
    all_rows = defaultdict(list)
    cases = []
    for selector, delay in (('40', 5), ('60', 18)):
        payload = holdout.PAYLOADS[0]
        offered = line_octets(payload, delay)
        tx, raw, expected = line.transmitter(execute, mapping, base, offered)
        bus = holdout.BUSES[0]
        codes = mapped_codes(raw, bus)
        gated = codes[:TONE_END] + [128] * (SILENCE_END - TONE_END) + codes[SILENCE_END:]
        wave = bandpass([value - 128 for value in gated], 0.5)
        selected = wave[SILENCE_END + 6:SILENCE_END + 6 + line.RX_SYMBOLS * 8]
        gain = 110 / max(abs(value) for value in selected)
        pcm = [max(-127, min(127, round(value * gain))) for value in selected]
        pcm_hash = hashlib.sha256(bytes(value + 127 for value in pcm)).hexdigest()
        old = next(c for c in saved['cases'] if c['selector'] == selector)
        if (tx['trace_digest'] != old['tx_trace_digest'] or
                pcm_hash != old['pcm_sha256']):
            raise ValueError(('saved Q=0.5 line changed', selector))
        with patch.object(loopback, 'DATA', handoff.PIPELINE_SYMBOLS + handoff.DATA_SYMBOLS), \
                patch.object(loopback, 'SYMBOLS', line.RX_SYMBOLS), \
                patch.object(loopback, 'ADC_VISITS', handoff.ADC_VISITS), \
                patch.object(loopback, 'CYCLES', handoff.RX_CYCLES):
            rx, adc, symbols = loopback.capture(mapping, base, pcm, expected)
        if (rx['trace_digest'] != old['receiver_handoff']['rx_trace_digest'] or
                hashlib.sha256(bytes(adc)).hexdigest() !=
                old['receiver_handoff']['adc_sha256']):
            raise ValueError(('saved DSC receiver changed', selector))
        case_rows = []
        for first, second in PAIR_NAMES:
            projected = project(symbols, first, second)
            for feature, states in (('primary', states_from_symbols(projected)),
                                    ('alternative', alternative_states(projected))):
                for symbol_index in range(handoff.PREAMBLE +
                                          handoff.PIPELINE_SYMBOLS,
                                          len(symbols)):
                    key = (states[symbol_index - 1] << 4) | states[symbol_index]
                    row = dict(selector=selector,
                               data_index=symbol_index - handoff.PREAMBLE -
                               handoff.PIPELINE_SYMBOLS,
                               dibit=expected[symbol_index], key=key)
                    all_rows[(first, second, feature)].append(row)
                    case_rows.append(dict(pair=f'{first}/{second}',
                                          feature=feature, **row))
        cases.append(dict(selector=selector, payload=[f'{v:02X}' for v in payload],
                          tx_trace_digest=tx['trace_digest'],
                          rx_trace_digest=rx['trace_digest'],
                          pcm_sha256=pcm_hash,
                          adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                          feature_rows=case_rows))
    summary = {f'{first}/{second}/{feature}': collisions(rows)
               for (first, second, feature), rows in all_rows.items()}
    report = dict(experiment='executed 12A Q=0.5 receiver feature collisions',
                  fixture=dict(selectors=['40', '60'],
                               payload='first nonzero eight-byte holdout per selector',
                               capture_pairs=PAIR_NAMES,
                               features=['primary Y6/Y7 at both visits',
                                         'alternative Y5..Y7 first, Y7 second'],
                               data_dibits_per_selector=32),
                  cases=cases, summary=summary,
                  limitations=[
                      'A collision proves only that the named four-bit feature cannot uniquely decide the observed data.',
                      'Absence of a collision on 64 data decisions is not proof of arbitrary-data decoding.',
                      'DAC, filter, ADC, latches, decision logic and USART route are assumed.'
                  ],
                  source_sha256={str(p.relative_to(HERE.parents[4])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (Path(__file__), PRIOR,
                                           HERE / 'joint_mask04_12a_q05_receiver.py',
                                           HERE / 'joint_mask04_tx_rx_loopback.py',
                                           HERE.parent / 'assumed/execute.py')})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print({key: (value['keys'], value['conflicting_keys'],
                 value['affected_positions'])
           for key, value in result['summary'].items()})
