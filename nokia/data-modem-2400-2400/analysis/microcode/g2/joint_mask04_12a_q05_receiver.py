"""Feed the frozen Q=0.5 12A line candidate through the real-PROM receiver."""

import hashlib
import json
import tempfile
from pathlib import Path

import joint_mask04_12a_analog_holdout as holdout
import joint_mask04_12a_buffered_line as line
import joint_mask04_buffered_serial_handoff as handoff
from joint_mask04_tx_12a_delayed_latch import capturing_execute
from photo_dac_bus_permutations import mapped_codes
from photo_joint_line_filter_screen import SILENCE_END, TONE_END, bandpass
from reference_modem import receive
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
PRIOR = HERE / 'results/joint-mask04-12a-analog-holdout.json'


def run(out=HERE / 'results/joint-mask04-12a-q05-receiver.json'):
    previous = json.loads(PRIOR.read_text())
    if len(holdout.BUSES) != 6:
        raise ValueError('DAC bus fixture changed')
    mapping = line.candidate(line.mapping_with_upper_source(0, '17.6'),
                             line.mapped(line.MAPPINGS['q3']), 4)
    _, base = line.fixture()
    execute = capturing_execute()
    cases = []
    with tempfile.TemporaryDirectory() as temp:
        controller, controller_sha = handoff.compiled_controller(temp)
        for selector, delay in (('40', 5), ('60', 18)):
            payload = holdout.PAYLOADS[0]
            offered = line_octets(payload, delay)
            tx_result, raw, expected = line.transmitter(
                execute, mapping, base, offered)
            prior_case = next(c for c in previous['cases']
                              if c['selector'] == selector and
                              c['payload_index'] == 0)
            if (tx_result['trace_digest'] != prior_case['tx_trace_digest'] or
                    hashlib.sha256(bytes(raw)).hexdigest() !=
                    prior_case['y12a_sha256']):
                raise ValueError(('held-out Tx changed', selector))
            codes = mapped_codes(raw, holdout.BUSES[0])
            gated = (codes[:TONE_END] + [128] * (SILENCE_END - TONE_END) +
                     codes[SILENCE_END:])
            waveform = bandpass([value - 128 for value in gated], 0.5)
            selected = waveform[
                SILENCE_END + 6:SILENCE_END + 6 + line.RX_SYMBOLS * 8]
            peak = max(abs(value) for value in selected)
            pcm = [max(-127, min(127, round(value * 110 / peak)))
                   for value in selected]
            digest = hashlib.sha256(bytes(value + 127 for value in pcm)).hexdigest()
            saved_score = next(s for s in prior_case['bus_cases'][0]['scores']
                               if s['q'] == 0.5)
            if digest != saved_score['pcm_sha256']:
                raise ValueError(('held-out PCM changed', selector))
            reference = receive(pcm)
            if reference != expected[1:]:
                raise ValueError(('reference decoder no longer exact', selector))
            rx = line.receiver_handoff(mapping, base, pcm, expected, offered,
                                       controller, selector, delay)
            cases.append(dict(selector=selector,
                              payload=[f'{value:02X}' for value in payload],
                              offered_line_bytes=[f'{value:02X}' for value in offered],
                              tx_trace_digest=tx_result['trace_digest'],
                              pcm_sha256=digest,
                              reference_wrong=0,
                              receiver_handoff=rx))
    report = dict(experiment='frozen Q=0.5 12A line into executed mask04 receiver',
                  fixture=dict(payload_index=0, bus_index=0, q=0.5,
                               center_hz=1950, peak=110, shift=6,
                               selectors=['40', '60'],
                               controller_probe_sha256=controller_sha),
                  cases=cases,
                  limitations=[
                      'The latch, DAC bus, analog filter, ADC conversion and receiver input route are assumed.',
                      'The tested readouts are frozen external rules; the board USART receive wire is untraced.',
                      'Known-carrier reference correctness is independent of the DSC receiver decisions.'
                  ],
                  source_sha256={str(p.relative_to(HERE.parents[4])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (Path(__file__), PRIOR,
                                           HERE / 'joint_mask04_12a_analog_holdout.py',
                                           HERE / 'joint_mask04_12a_buffered_line.py',
                                           HERE / 'photo_joint_line_filter_screen.py',
                                           HERE.parent / 'assumed/execute.py')})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    report = run()
    for case in report['cases']:
        print(case['selector'],
              {name: (len(value['data_wrong_indices']),
                      len(value['data_unknown_indices']))
               for name, value in case['receiver_handoff']['readouts'].items()})
