"""Test one-time R1 phase offsets after the 12A transmitter reaches data."""

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
SEED = HERE / 'results/joint-mask04-12a-phase-seed.json'
FIXED = HERE / 'results/joint-mask04-12a-fixed-gain-phase.json'
VISIT = SILENCE_END * 375 + 1
OFFSETS = (32, 64)


def run(out=HERE / 'results/joint-mask04-12a-running-phase.json'):
    seed = json.loads(SEED.read_text())
    fixed = json.loads(FIXED.read_text())
    mapping = line.candidate(line.mapping_with_upper_source(0, '17.6'),
                             line.mapped(line.MAPPINGS['q3']), 4)
    _, base = line.fixture()
    cases = []
    for selector, delay in (('40', 5), ('60', 18)):
        payload = fresh.PAYLOADS[selector]
        offered = line_octets(payload, delay)
        baseline = next(c for c in seed['cases'] if c['selector'] == selector)['seeds'][0]
        fixed_case = next(c for c in fixed['cases'] if c['selector'] == selector)
        gain = next(b for b in fixed_case['bus_cases']
                    if b['bus_index'] == 0)['gain']
        for offset in OFFSETS:
            tx, raw, expected = line.transmitter(
                capturing_execute((VISIT, offset)), mapping, base, offered)
            raw_hash = hashlib.sha256(bytes(raw)).hexdigest()
            codes = mapped_codes(raw, holdout.BUSES[0])
            gated = (codes[:TONE_END] + [128] * (SILENCE_END - TONE_END) +
                     codes[SILENCE_END:])
            wave = bandpass([value - 128 for value in gated], 0.5)
            selected = wave[SILENCE_END + 6:SILENCE_END + 6 + line.RX_SYMBOLS * 8]
            pcm = [max(-127, min(127, round(value * gain)))
                   for value in selected]
            wrong = [i for i, (got, want) in enumerate(
                zip(receive(pcm), expected[1:])) if got != want]
            row = dict(selector=selector, offset=offset,
                       phase_poke_127_visit=VISIT,
                       tx_trace_digest=tx['trace_digest'],
                       raw_sha256=raw_hash,
                       baseline_raw_sha256=baseline['raw_sha256'],
                       raw_changed=raw_hash != baseline['raw_sha256'],
                       pcm_sha256=hashlib.sha256(bytes(v + 127 for v in pcm)).hexdigest(),
                       reference_wrong_indices=wrong,
                       expected_dibits=expected,
                       pcm=pcm)
            cases.append(row)
            print(selector, offset, 'raw changed', row['raw_changed'],
                  'reference wrong', len(wrong), flush=True)
    report = dict(experiment='one-time running R1 phase perturbation',
                  fixture=dict(visit=VISIT, offsets=OFFSETS,
                               line='Q=0.5, bus 0, +6 samples, zero-run fixed gain',
                               data='two fresh nonzero payloads'),
                  cases=cases,
                  limitations=['The R1 intervention is a diagnostic, not a photographed board command.',
                               'The DAC, analog, ADC and serial routes remain assumed.'],
                  source_sha256={str(p.relative_to(HERE.parents[4])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (Path(__file__), SEED, FIXED,
                                           HERE / 'joint_mask04_tx_12a_delayed_latch.py',
                                           HERE.parent / 'assumed/execute.py')})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
