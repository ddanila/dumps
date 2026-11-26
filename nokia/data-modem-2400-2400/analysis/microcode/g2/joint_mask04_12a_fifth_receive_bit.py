"""Screen one extra DSC Y bit against gain/phase transition collisions."""

import hashlib
import json
from collections import defaultdict
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_analog_holdout as holdout
import joint_mask04_12a_buffered_line as line
import joint_mask04_buffered_serial_handoff as handoff
import joint_mask04_q05_fresh_payload_levels as fresh
import joint_mask04_tx_rx_loopback as loopback
from joint_mask04_tx_12a_delayed_latch import capturing_execute
from photo_dac_bus_permutations import mapped_codes
from photo_joint_line_filter_screen import SILENCE_END, TONE_END, bandpass
from receiver_mask04_controller_zero_handoff import dibits_from_bytes
from receiver_mask04_offset_visit_phase import project
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
FIXED = HERE / 'results/joint-mask04-12a-fixed-gain-phase.json'
HALF = HERE / 'results/joint-mask04-12a-phase-timing.json'
CONTROLLER = HERE / 'results/joint-mask04-12a-controller-continuation.json'
LEVELS = (0.75, 1.0, 1.25)


def capture(mapping, base, pcm, expected):
    with patch.object(loopback, 'DATA', handoff.PIPELINE_SYMBOLS + handoff.DATA_SYMBOLS), \
            patch.object(loopback, 'SYMBOLS', line.RX_SYMBOLS), \
            patch.object(loopback, 'ADC_VISITS', handoff.ADC_VISITS), \
            patch.object(loopback, 'CYCLES', handoff.RX_CYCLES):
        rx, adc, symbols = loopback.capture(mapping, base, pcm, expected)
    rows = project(symbols, 46, 93)
    first = [row['visits']['47']['y3f8'] for row in rows]
    second = [row['visits']['94']['y3f8'] for row in rows]
    return rx['trace_digest'], hashlib.sha256(bytes(adc)).hexdigest(), first, second


def feature(first, second, source, bit):
    base = ((first >> 5) & 7) | (((second >> 7) & 1) << 3)
    extra = ((first if source == 'first' else second) >> bit) & 1
    return base | (extra << 4)


def conflicts(cases, source=None, bit=None):
    labels = defaultdict(lambda: defaultdict(list))
    for case in cases:
        if source is None:
            states = [feature(a, b, 'second', 7) & 15
                      for a, b in zip(case['first_y'], case['second_y'])]
        else:
            states = [feature(a, b, source, bit)
                      for a, b in zip(case['first_y'], case['second_y'])]
        for index, (before, after) in enumerate(zip(states, states[1:]), 1):
            key = f'{before:02X}{after:02X}'
            labels[key][case['expected_dibits'][index]].append(
                f"{case['fixture']}:{case['selector']}:{index}")
    return dict(keys=len(labels),
                conflicts={key: {str(value): examples[:4]
                                 for value, examples in values.items()}
                           for key, values in labels.items() if len(values) > 1})


def run(out=HERE / 'results/joint-mask04-12a-fifth-receive-bit.json'):
    fixed = json.loads(FIXED.read_text())
    half = json.loads(HALF.read_text())
    controller = json.loads(CONTROLLER.read_text())
    mapping = line.candidate(line.mapping_with_upper_source(0, '17.6'),
                             line.mapped(line.MAPPINGS['q3']), 4)
    _, base = line.fixture()
    execute = capturing_execute()
    cases = []
    for selector, delay in (('40', 5), ('60', 18)):
        offered = line_octets(fresh.PAYLOADS[selector], delay)
        tx, raw, expected = line.transmitter(execute, mapping, base, offered)
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
            digest, adc_hash, first, second = capture(mapping, base, pcm, expected)
            cases.append(dict(fixture=f'level{level}', selector=selector,
                              tx_trace_digest=tx['trace_digest'],
                              rx_trace_digest=digest, adc_sha256=adc_hash,
                              expected_dibits=expected,
                              first_y=first, second_y=second))
            print(selector, level, 'captured', flush=True)
        source = next(c for c in half['cases'] if c['selector'] == selector
                      and c['timing'] == 'silence_start')
        digest, adc_hash, first, second = capture(
            mapping, base, source['pcm'], source['expected_dibits'])
        cases.append(dict(fixture='half_fresh', selector=selector,
                          rx_trace_digest=digest, adc_sha256=adc_hash,
                          expected_dibits=source['expected_dibits'],
                          first_y=first, second_y=second))
        joined = next(c for c in controller['cases'] if c['selector'] == selector)
        # The prior joined report records states, not its PCM. It remains a
        # separate holdout to challenge any feature found here.
        if joined['training_exact_maps'] != 1:
            raise ValueError(('joined controller phase map changed', selector))
    baseline = conflicts(cases)
    candidates = []
    for source in ('first', 'second'):
        for bit in range(8):
            if (source == 'first' and bit in (5, 6, 7)) or \
                    (source == 'second' and bit == 7):
                continue
            score = conflicts(cases, source, bit)
            candidates.append(dict(source=source, bit=bit,
                                   transition_keys=score['keys'],
                                   conflicts=score['conflicts']))
    report = dict(experiment='fifth sampled Y bit for gain/phase receive collisions',
                  fixture=dict(levels=LEVELS, half_phase='offset 32 at silence start',
                               visits=[46,93], base_feature='first Y bits 5,6,7 plus second Y bit 7'),
                  cases=cases,
                  baseline=baseline,
                  candidates=candidates,
                  limitations=['Feature selection uses labeled development data; no physical latch wiring is identified.',
                               'The joined controller A4/A5 stream is not among these raw-Y captures and remains a holdout.',
                               'The ADC, capture clocks and serial output remain assumed.'],
                  source_sha256={str(p.relative_to(HERE.parents[4])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (Path(__file__), FIXED, HALF, CONTROLLER,
                                           HERE / 'joint_mask04_12a_buffered_line.py',
                                           HERE / 'joint_mask04_tx_rx_loopback.py',
                                           HERE.parent / 'assumed/execute.py')})
    out.write_text(json.dumps(report, indent=2) + '\n')
    print('baseline conflicts',len(baseline['conflicts']),
          'zero-conflict fifth bits',[(c['source'],c['bit']) for c in candidates
                                       if not c['conflicts']],flush=True)
    return report


if __name__ == '__main__':
    run()
