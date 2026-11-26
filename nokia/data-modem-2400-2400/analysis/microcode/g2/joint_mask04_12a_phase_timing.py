"""Move a 32-count running phase offset into the muted line interval."""

import hashlib
import json
from pathlib import Path

import joint_mask04_12a_analog_holdout as holdout
import joint_mask04_12a_buffered_line as line
import joint_mask04_q05_fresh_payload_levels as fresh
from joint_mask04_tx_12a_delayed_latch import capturing_execute
from photo_dac_bus_permutations import mapped_codes
from photo_joint_line_filter_screen import SILENCE_END, TONE_END, bandpass
from reference_modem import receive
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
FIXED = HERE / 'results/joint-mask04-12a-fixed-gain-phase.json'
PRIOR = HERE / 'results/joint-mask04-12a-running-phase.json'
TIMINGS = {'silence_start': TONE_END * 375 + 1,
           'four_samples_before_data': (SILENCE_END - 4) * 375 + 1}


def run(out=HERE / 'results/joint-mask04-12a-phase-timing.json'):
    fixed = json.loads(FIXED.read_text())
    prior = json.loads(PRIOR.read_text())
    mapping = line.candidate(line.mapping_with_upper_source(0, '17.6'),
                             line.mapped(line.MAPPINGS['q3']), 4)
    _, base = line.fixture()
    cases = []
    for selector, delay in (('40', 5), ('60', 18)):
        offered = line_octets(fresh.PAYLOADS[selector], delay)
        fixed_case = next(c for c in fixed['cases'] if c['selector'] == selector)
        gain = next(b for b in fixed_case['bus_cases']
                    if b['bus_index'] == 0)['gain']
        boundary = next(c for c in prior['cases']
                        if c['selector'] == selector and c['offset'] == 32)
        for name, visit in TIMINGS.items():
            tx, raw, expected = line.transmitter(
                capturing_execute((visit, 32)), mapping, base, offered)
            codes = mapped_codes(raw, holdout.BUSES[0])
            gated = (codes[:TONE_END] + [128] * (SILENCE_END - TONE_END) +
                     codes[SILENCE_END:])
            wave = bandpass([value - 128 for value in gated], 0.5)
            selected = wave[SILENCE_END + 6:SILENCE_END + 6 + line.RX_SYMBOLS * 8]
            pcm = [max(-127, min(127, round(value * gain)))
                   for value in selected]
            wrong = [i for i, (got, want) in enumerate(
                zip(receive(pcm), expected[1:])) if got != want]
            cases.append(dict(selector=selector, timing=name, visit=visit,
                              offset=32, tx_trace_digest=tx['trace_digest'],
                              raw_sha256=hashlib.sha256(bytes(raw)).hexdigest(),
                              pcm_sha256=hashlib.sha256(bytes(v + 127 for v in pcm)).hexdigest(),
                              reference_wrong_indices=wrong,
                              boundary_wrong_indices=boundary['reference_wrong_indices'],
                              expected_dibits=expected, pcm=pcm))
            print(selector, name, 'wrong', wrong, flush=True)
    report = dict(experiment='32-count running phase step timing screen',
                  fixture=dict(timings=TIMINGS, offset=32,
                               mute=f'{TONE_END}:{SILENCE_END}',
                               line='fixed Q=0.5, bus 0, +6 sample, zero-run gain'),
                  cases=cases,
                  limitations=['R1 phase step is an intervention, not a board command.',
                               'DAC/ADC/analog/clock/serial routes remain photo-compatible hypotheses.'],
                  source_sha256={str(p.relative_to(HERE.parents[4])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (Path(__file__), FIXED, PRIOR,
                                           HERE / 'joint_mask04_tx_12a_delayed_latch.py',
                                           HERE.parent / 'assumed/execute.py')})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
