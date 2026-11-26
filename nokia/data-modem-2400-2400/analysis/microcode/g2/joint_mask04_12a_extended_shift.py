"""Extend only the 12A transmitter tail to test later line alignments."""

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_buffered_line as line
from joint_mask04_12a_buffered_line import (BUSES, MAPPINGS, candidate,
                                           fixture, mapped,
                                           mapping_with_upper_source,
                                           pcm_at_shift)
from joint_mask04_tx_12a_delayed_latch import capturing_execute
from reference_modem import receive
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
PRIOR = HERE / 'results/joint-mask04-12a-buffered-line.json'
EXTRA_SAMPLES = 6
SAMPLES = line.SAMPLES + EXTRA_SAMPLES
TX_CYCLES = line.TX_CYCLES + EXTRA_SAMPLES * 375 * 4
SHIFTS = tuple(range(4, 13))


def run(out=HERE / 'results/joint-mask04-12a-extended-shift.json'):
    saved = json.loads(PRIOR.read_text())
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    buses = json.loads(BUSES.read_text())['zero_error_survivors']
    if len(buses) != 6:
        raise ValueError('photo-compatible DAC bus family changed')
    tx = capturing_execute()
    cases = []
    for selector, delay in (('40', 5), ('60', 18)):
        offered = line_octets([0] * 8, delay)
        with patch.object(line, 'SAMPLES', SAMPLES), \
                patch.object(line, 'TX_CYCLES', TX_CYCLES):
            result, raw, expected = line.transmitter(tx, mapping, base, offered)
        old = next(c for c in saved['cases'] if c['selector'] == selector)
        if (len(raw) != SAMPLES or
                hashlib.sha256(bytes(raw[:line.SAMPLES])).hexdigest() !=
                old['y12a_sha256']):
            raise ValueError('original 846 transmitter samples changed')
        bus_cases = []
        for bus_index, bus in enumerate(buses):
            scores = []
            for shift in SHIFTS:
                pcm = pcm_at_shift(raw, bus, shift)
                if len(pcm) != line.RX_SYMBOLS * 8:
                    raise ValueError(('extended PCM window changed', shift))
                predictions = receive(pcm)
                wrong = [index for index, (actual, wanted) in
                         enumerate(zip(predictions, expected[1:]))
                         if actual != wanted]
                item = dict(shift=shift, wrong=len(wrong),
                            wrong_indices=wrong,
                            pcm_sha256=hashlib.sha256(bytes(value + 127
                                                            for value in pcm)).hexdigest())
                if shift <= 6:
                    old_score = next(s for s in old['bus_cases'][bus_index]['scores']
                                     if s['shift'] == shift)
                    if (item['wrong'] != old_score['wrong'] or
                            item['wrong_indices'] != old_score['first_wrong'] or
                            item['pcm_sha256'] != old_score['pcm_sha256']):
                        raise ValueError(('original alignment score changed',
                                          selector, bus_index, shift))
                scores.append(item)
            bus_cases.append(dict(bus_index=bus_index, scores=scores,
                                  best=min(scores, key=lambda s: (s['wrong'],
                                                                   abs(s['shift'] - 6)))))
        cases.append(dict(selector=selector, tx_trace_digest=result['trace_digest'],
                          original_samples_sha256=old['y12a_sha256'],
                          extended_samples_sha256=hashlib.sha256(bytes(raw)).hexdigest(),
                          bus_cases=bus_cases))
    report = dict(experiment='extended ROM-sensitive 12A line alignment',
                  fixture=dict(original_samples=line.SAMPLES,
                               extra_held_end_samples=EXTRA_SAMPLES,
                               extended_samples=SAMPLES,
                               tx_cycles=TX_CYCLES,
                               shifts=SHIFTS,
                               analog='same DAC bus, A2 mid-code gate and causal bandpass as saved fixture'),
                  cases=cases,
                  source_sha256={str(p.relative_to(HERE.parents[4])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (Path(__file__), PRIOR,
                                           HERE / 'joint_mask04_12a_buffered_line.py',
                                           HERE / 'photo_joint_line_filter_screen.py',
                                           HERE.parent / 'assumed/execute.py')},
                  limitations=[
                      'The extra tail is a held-data extension, not additional controller bytes.',
                      'DAC bus, latch clock, A2 gate, analog filter and physical line are assumed.',
                      'A known-carrier reference decoder score does not establish a DSC receiver or USART route.'
                  ])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    for case in result['cases']:
        print(case['selector'], [(b['bus_index'], b['best']['shift'],
                                  b['best']['wrong']) for b in case['bus_cases']])
