"""Challenge a frozen 12A analog setting on nonzero controller payloads."""

import hashlib
import json
from pathlib import Path

import joint_mask04_12a_buffered_line as line
from joint_mask04_tx_12a_delayed_latch import capturing_execute
from photo_dac_bus_permutations import mapped_codes
from photo_joint_line_filter_screen import SILENCE_END, TONE_END, bandpass
from reference_modem import receive
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
BUSES = json.loads(line.BUSES.read_text())['zero_error_survivors']
PAYLOADS = ((0xA5, 0x3C, 0xF0, 0x0F, 0x81, 0x7E, 0x55, 0xCA),
            (0x42, 0xDB, 0x19, 0xE7, 0x24, 0xB6, 0x68, 0x93))
QS = (0.5, 1.0)


def run(out=HERE / 'results/joint-mask04-12a-analog-holdout.json'):
    if len(BUSES) != 6:
        raise ValueError('DAC bus fixture changed')
    mapping = line.candidate(line.mapping_with_upper_source(0, '17.6'),
                             line.mapped(line.MAPPINGS['q3']), 4)
    _, base = line.fixture()
    execute = capturing_execute()
    cases = []
    for selector, delay in (('40', 5), ('60', 18)):
        for payload_index, payload in enumerate(PAYLOADS):
            offered = line_octets(payload, delay)
            result, raw, expected = line.transmitter(
                execute, mapping, base, offered)
            bus_cases = []
            for bus_index, bus in enumerate(BUSES):
                codes = mapped_codes(raw, bus)
                gated = (codes[:TONE_END] + [128] * (SILENCE_END - TONE_END) +
                         codes[SILENCE_END:])
                source = [value - 128 for value in gated]
                scores = []
                for q in QS:
                    waveform = bandpass(source, q)
                    selected = waveform[
                        SILENCE_END + 6:SILENCE_END + 6 + line.RX_SYMBOLS * 8]
                    if len(selected) != line.RX_SYMBOLS * 8:
                        raise ValueError('PCM window short')
                    scale = max(abs(value) for value in selected)
                    pcm = [max(-127, min(127, round(value * 110 / scale)))
                           for value in selected]
                    predictions = receive(pcm)
                    wrong = [i for i, (got, want) in enumerate(
                        zip(predictions, expected[1:])) if got != want]
                    scores.append(dict(q=q, wrong=len(wrong),
                                       wrong_indices=wrong,
                                       pcm_sha256=hashlib.sha256(
                                           bytes(value + 127 for value in pcm)
                                       ).hexdigest()))
                bus_cases.append(dict(bus_index=bus_index, scores=scores))
            cases.append(dict(selector=selector,
                              payload_index=payload_index,
                              payload=[f'{value:02X}' for value in payload],
                              offered_line_bytes=[f'{value:02X}' for value in offered],
                              tx_trace_digest=result['trace_digest'],
                              y12a_sha256=hashlib.sha256(bytes(raw)).hexdigest(),
                              bus_cases=bus_cases))
    report = dict(experiment='frozen 12A Q=0.5 analog holdout',
                  fixture=dict(center_hz=1950, sample_rate_hz=9600,
                               q_values=QS, peak=110, shift=6,
                               dac_buses=len(BUSES),
                               payloads='two nonzero eight-byte payloads per selector'),
                  cases=cases,
                  limitations=[
                      'The held-out data use the same assumed controller-bit/PROM/DAC and analog route.',
                      'A known-carrier decoder is external to the DSC; no receiver/USART readout is established.',
                      'The filter setting is a candidate, not a measured board component value.'
                  ],
                  source_sha256={str(p.relative_to(HERE.parents[4])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (Path(__file__),
                                           HERE / 'joint_mask04_12a_analog_screen.py',
                                           HERE / 'joint_mask04_12a_buffered_line.py',
                                           HERE / 'photo_joint_line_filter_screen.py',
                                           HERE.parent / 'assumed/execute.py')})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    report = run()
    for case in report['cases']:
        print(case['selector'], case['payload_index'],
              [(bus['bus_index'], [s['wrong'] for s in bus['scores']])
               for bus in case['bus_cases']])
