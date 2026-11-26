"""Screen bounded analog hypotheses on the ROM-sensitive 12A line fixture."""

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_buffered_line as line
import photo_joint_line_filter_screen as filt
from joint_mask04_12a_extended_shift import (EXTRA_SAMPLES, SAMPLES,
                                              TX_CYCLES)
from joint_mask04_tx_12a_delayed_latch import capturing_execute
from photo_dac_bus_permutations import mapped_codes
from reference_modem import receive
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
PRIOR = HERE / 'results/joint-mask04-12a-buffered-line.json'
CENTERS = (1650, 1950, 2250)
QS = (0.5, 1.0, 2.0, 3.0)
PEAKS = (80, 110, 127)
SHIFTS = (6, 7)


def run(out=HERE / 'results/joint-mask04-12a-analog-screen.json'):
    saved = json.loads(PRIOR.read_text())
    mapping = line.candidate(line.mapping_with_upper_source(0, '17.6'),
                             line.mapped(line.MAPPINGS['q3']), 4)
    _, base = line.fixture()
    buses = json.loads(line.BUSES.read_text())['zero_error_survivors']
    if len(buses) != 6:
        raise ValueError('DAC bus fixture changed')
    execute = capturing_execute()
    cases = []
    for selector, delay in (('40', 5), ('60', 18)):
        offered = line_octets([0] * 8, delay)
        with patch.object(line, 'SAMPLES', SAMPLES), \
                patch.object(line, 'TX_CYCLES', TX_CYCLES):
            result, raw, expected = line.transmitter(
                execute, mapping, base, offered)
        old = next(c for c in saved['cases'] if c['selector'] == selector)
        if (len(raw) != SAMPLES or
                hashlib.sha256(bytes(raw[:line.SAMPLES])).hexdigest() !=
                old['y12a_sha256']):
            raise ValueError('saved transmitter prefix changed')
        bus_cases = []
        for bus_index, bus in enumerate(buses):
            codes = mapped_codes(raw, bus)
            gated = (codes[:filt.TONE_END] +
                     [128] * (filt.SILENCE_END - filt.TONE_END) +
                     codes[filt.SILENCE_END:])
            source = [value - 128 for value in gated]
            scores = []
            for center in CENTERS:
                with patch.object(filt, 'CENTER_HZ', center):
                    for q in QS:
                        waveform = filt.bandpass(source, q)
                        for shift in SHIFTS:
                            selected = waveform[
                                filt.SILENCE_END + shift:
                                filt.SILENCE_END + shift + line.RX_SYMBOLS * 8]
                            if len(selected) != line.RX_SYMBOLS * 8:
                                raise ValueError('PCM window is short')
                            scale = max(abs(value) for value in selected)
                            for peak in PEAKS:
                                pcm = [max(-127, min(127, round(value * peak / scale)))
                                       for value in selected]
                                wrong = [i for i, (got, want) in enumerate(
                                    zip(receive(pcm), expected[1:])) if got != want]
                                scores.append(dict(center_hz=center, q=q,
                                                   peak=peak, shift=shift,
                                                   wrong=len(wrong),
                                                   wrong_indices=wrong))
            baseline = next(s for s in scores if s['center_hz'] == 1950
                            and s['q'] == 1 and s['peak'] == 110
                            and s['shift'] == 6)
            old_baseline = next(s for s in old['bus_cases'][bus_index]['scores']
                                if s['shift'] == 6)
            if (baseline['wrong'] != old_baseline['wrong'] or
                    baseline['wrong_indices'] != old_baseline['first_wrong']):
                raise ValueError(('baseline decisions changed', selector,
                                  bus_index))
            bus_cases.append(dict(bus_index=bus_index, scores=scores))
        cases.append(dict(selector=selector,
                          tx_trace_digest=result['trace_digest'],
                          y12a_prefix_sha256=old['y12a_sha256'],
                          bus_cases=bus_cases))
    joint = []
    for bus_index in range(len(buses)):
        left = cases[0]['bus_cases'][bus_index]['scores']
        right = cases[1]['bus_cases'][bus_index]['scores']
        for a, b in zip(left, right):
            if any(a[key] != b[key] for key in
                   ('center_hz', 'q', 'peak', 'shift')):
                raise ValueError('candidate order mismatch')
            joint.append(dict(bus_index=bus_index,
                              center_hz=a['center_hz'], q=a['q'],
                              peak=a['peak'], shift=a['shift'],
                              call_wrong=a['wrong'],
                              answer_wrong=b['wrong']))
    report = dict(experiment='12A bounded analog parameter screen',
                  fixture=dict(centers_hz=CENTERS, qs=QS, peaks=PEAKS,
                               shifts=SHIFTS, dac_buses=len(buses),
                               samples=SAMPLES,
                               extra_held_end_samples=EXTRA_SAMPLES),
                  cases=cases, joint=joint,
                  limitations=[
                      'Center, Q, gain and DAC bus are candidate analog settings, not traced hardware.',
                      'The reference decoder knows the carrier; this is not a DSC receiver or USART result.',
                      'The controller data are a zero-run fixture; any selected setting needs independent data.'
                  ],
                  source_sha256={str(p.relative_to(HERE.parents[4])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (Path(__file__), PRIOR,
                                           HERE / 'joint_mask04_12a_buffered_line.py',
                                           HERE / 'photo_joint_line_filter_screen.py',
                                           HERE.parent / 'assumed/execute.py')})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    report = run()
    print('joint zero-error cases:', sum(row['call_wrong'] == row['answer_wrong'] == 0
                                         for row in report['joint']))
    print('minimum combined errors:', min(row['call_wrong'] + row['answer_wrong']
                                           for row in report['joint']))
