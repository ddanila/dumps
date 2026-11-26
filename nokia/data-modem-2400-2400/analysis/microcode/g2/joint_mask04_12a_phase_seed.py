"""Test whether initial R1 phase offsets rotate the ROM-sensitive 12A line."""

import copy
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
PRIOR = HERE / 'results/joint-mask04-q05-fresh-payload-levels.json'
FIXED = HERE / 'results/joint-mask04-12a-fixed-gain-phase.json'
SEEDS = (0, 32, 64)


def run(out=HERE / 'results/joint-mask04-12a-phase-seed.json'):
    saved = json.loads(PRIOR.read_text())
    fixed = json.loads(FIXED.read_text())
    mapping = line.candidate(line.mapping_with_upper_source(0, '17.6'),
                             line.mapped(line.MAPPINGS['q3']), 4)
    _, base = line.fixture()
    execute = capturing_execute()
    cases = []
    for selector, delay in (('40', 5), ('60', 18)):
        payload = fresh.PAYLOADS[selector]
        offered = line_octets(payload, delay)
        fixed_case = next(c for c in fixed['cases']
                          if c['selector'] == selector)
        gain = next(b for b in fixed_case['bus_cases']
                    if b['bus_index'] == 0)['gain']
        streams = []
        for seed in SEEDS:
            scenario = copy.deepcopy(base)
            scenario['initial']['ram'][1] = seed
            scenario['name'] += f'; candidate initial R1 phase offset {seed}'
            tx, raw, expected = line.transmitter(
                execute, mapping, scenario, offered)
            if seed == 0:
                old = next(c for c in saved['cases']
                           if c['selector'] == selector and c['level'] == 1.0)
                if (tx['trace_digest'] != old['tx_trace_digest'] or
                        hashlib.sha256(bytes(raw)).hexdigest() !=
                        old['raw_y12a_sha256']):
                    raise ValueError(('seed-zero transmitter changed', selector))
            codes = mapped_codes(raw, holdout.BUSES[0])
            gated = (codes[:TONE_END] + [128] * (SILENCE_END - TONE_END) +
                     codes[SILENCE_END:])
            wave = bandpass([value - 128 for value in gated], 0.5)
            selected = wave[SILENCE_END + 6:SILENCE_END + 6 + line.RX_SYMBOLS * 8]
            pcm = [max(-127, min(127, round(value * gain)))
                   for value in selected]
            wrong = [i for i, (got, want) in enumerate(
                zip(receive(pcm), expected[1:])) if got != want]
            streams.append(dict(seed_r1=seed,
                                tx_trace_digest=tx['trace_digest'],
                                raw_sha256=hashlib.sha256(bytes(raw)).hexdigest(),
                                pcm_sha256=hashlib.sha256(bytes(
                                    value + 127 for value in pcm)).hexdigest(),
                                reference_wrong_indices=wrong,
                                raw=raw))
            print(selector, seed, 'reference wrong', len(wrong), flush=True)
        baseline = streams[0]['raw']
        for stream in streams:
            raw = stream.pop('raw')
            stream['changed_raw_samples_vs_seed0'] = sum(
                a != b for a, b in zip(raw, baseline))
            stream['changed_data_samples_vs_seed0'] = sum(
                a != b for a, b in zip(raw[SILENCE_END:],
                                       baseline[SILENCE_END:]))
        cases.append(dict(selector=selector,
                          payload=[f'{value:02X}' for value in payload],
                          offered_line_bytes=[f'{value:02X}' for value in offered],
                          fixed_zero_run_gain=gain,
                          seeds=streams))
    report = dict(experiment='initial R1 phase seed on ROM-sensitive 12A line',
                  fixture=dict(seeds_r1=SEEDS,
                               line='Q=0.5, 1950 Hz, bus 0, shift +6, zero-run fixed gain',
                               selectors=['40', '60'],
                               data='two fresh nonzero eight-byte payloads'),
                  cases=cases,
                  limitations=[
                      'Changing initial R1 is a diagnostic seed perturbation, not an observed board command.',
                      'The line and decoder are photo-compatible/external hypotheses; no physical carrier phase is measured.',
                      'Reference decisions do not establish the executed DSC receiver or USART path.'
                  ],
                  source_sha256={str(p.relative_to(HERE.parents[4])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (Path(__file__), PRIOR, FIXED,
                                           HERE / 'joint_mask04_12a_buffered_line.py',
                                           HERE.parent / 'assumed/execute.py')})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
