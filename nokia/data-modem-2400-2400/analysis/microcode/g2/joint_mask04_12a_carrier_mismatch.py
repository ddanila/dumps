"""Challenge the frozen 12A line with a mismatched reference receiver oscillator."""

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_analog_holdout as holdout
import joint_mask04_12a_buffered_line as line
import joint_mask04_12a_fixed_gain_phase as fixed
import reference_modem
from joint_mask04_tx_12a_delayed_latch import capturing_execute
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
PRIOR = HERE / 'results/joint-mask04-12a-fixed-gain-phase.json'
HOLDOUT = HERE / 'results/joint-mask04-12a-analog-holdout.json'
OFFSETS_HZ = (-14, -7, 0, 7, 14)


def run(out=HERE / 'results/joint-mask04-12a-carrier-mismatch.json'):
    frozen = json.loads(PRIOR.read_text())
    hold = json.loads(HOLDOUT.read_text())
    if len(holdout.BUSES) != 6 or reference_modem.CARRIER_HZ != 1800:
        raise ValueError('reference carrier or DAC bus fixture changed')
    mapping = line.candidate(line.mapping_with_upper_source(0, '17.6'),
                             line.mapped(line.MAPPINGS['q3']), 4)
    _, base = line.fixture()
    execute = capturing_execute()
    cases = []
    for selector, delay in (('40', 5), ('60', 18)):
        saved_selector = next(c for c in frozen['cases']
                              if c['selector'] == selector)
        for payload_index, payload in enumerate(holdout.PAYLOADS):
            offered = line_octets(payload, delay)
            result, raw, expected = line.transmitter(
                execute, mapping, base, offered)
            old = next(c for c in hold['cases']
                       if c['selector'] == selector and
                       c['payload_index'] == payload_index)
            if (result['trace_digest'] != old['tx_trace_digest'] or
                    hashlib.sha256(bytes(raw)).hexdigest() !=
                    old['y12a_sha256']):
                raise ValueError(('saved transmitter changed', selector,
                                  payload_index))
            bus_cases = []
            for bus_index, bus in enumerate(holdout.BUSES):
                saved_bus = next(b for b in saved_selector['bus_cases']
                                 if b['bus_index'] == bus_index)
                gain = saved_bus['gain']
                wave = fixed.line_wave(raw, bus)
                pcm = fixed.pcm_at(fixed.window_at(wave, 6), gain)
                scores = []
                for offset in OFFSETS_HZ:
                    with patch.object(reference_modem, 'CARRIER_HZ',
                                      1800 + offset):
                        decoded = reference_modem.receive(pcm)
                    wrong = [i for i, (actual, want) in enumerate(
                        zip(decoded, expected[1:])) if actual != want]
                    scores.append(dict(receiver_offset_hz=offset,
                                       wrong=len(wrong),
                                       wrong_indices=wrong))
                if next(s for s in scores if s['receiver_offset_hz'] == 0)[
                        'wrong'] != 0:
                    raise ValueError(('nominal fixed-gain result changed',
                                      selector, payload_index, bus_index))
                bus_cases.append(dict(bus_index=bus_index, gain=gain,
                                      pcm_sha256=hashlib.sha256(bytes(
                                          value + 127 for value in pcm)).hexdigest(),
                                      scores=scores))
            cases.append(dict(selector=selector, payload_index=payload_index,
                              offered_line_bytes=[f'{value:02X}' for value in offered],
                              tx_trace_digest=result['trace_digest'],
                              bus_cases=bus_cases))
    report = dict(experiment='12A fixed-line reference receiver oscillator mismatch',
                  fixture=dict(transmit_line='Q=0.5, center 1950 Hz, +6 samples; zero-run-calibrated gain',
                               receiver_nominal_hz=1800,
                               receiver_offsets_hz=OFFSETS_HZ,
                               selectors=['40', '60'],
                               payloads_per_selector=2,
                               dac_buses=6),
                  cases=cases,
                  limitations=[
                      'Only the external reference receiver oscillator changes; the DSC transmitter and its assumed line clock stay fixed.',
                      'A receiver-oscillator mismatch is not a direct transmitter frequency-offset or DSC carrier-tracking test.',
                      'The DAC bus, latch, filter, ADC and USART routes remain untraced assumptions.'
                  ],
                  source_sha256={str(p.relative_to(HERE.parents[4])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (Path(__file__), PRIOR, HOLDOUT,
                                           HERE / 'joint_mask04_12a_fixed_gain_phase.py',
                                           HERE / 'reference_modem.py',
                                           HERE.parent / 'assumed/execute.py')})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    report = run()
    for offset in OFFSETS_HZ:
        wrong = [s['wrong'] for c in report['cases']
                 for b in c['bus_cases'] for s in b['scores']
                 if s['receiver_offset_hz'] == offset]
        print(offset, sum(wrong), sum(n == 0 for n in wrong), '/', len(wrong))
