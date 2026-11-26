"""Screen receive sample alignment for the phase-112 development pair."""

import hashlib
import json
from pathlib import Path

import joint_mask04_12a_analog_holdout as holdout
import joint_mask04_12a_buffered_line as line
import joint_mask04_12a_frozen_sixth_new_payloads as frozen
from joint_mask04_tx_12a_delayed_latch import capturing_execute
from photo_dac_bus_permutations import mapped_codes
from photo_joint_line_filter_screen import SILENCE_END, TONE_END, bandpass
from reference_modem import receive
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
PRIOR = HERE / 'results/joint-mask04-12a-row0-boolean-phase112.json'
FIXED = HERE / 'results/joint-mask04-12a-fixed-gain-phase.json'
OUT = HERE / 'results/joint-mask04-12a-phase112-line-shift.json'
SHIFTS = tuple(range(3, 11))


def run(out=OUT):
    prior = json.loads(PRIOR.read_text())
    fixed = json.loads(FIXED.read_text())
    mapping = line.candidate(line.mapping_with_upper_source(0, '17.6'),
                             line.mapped(line.MAPPINGS['q3']), 4)
    _, base = line.fixture()
    cases = []
    for old in prior['cases']:
        selector = old['selector']
        delay = 5 if selector == '40' else 18
        payload = tuple(int(value, 16) for value in old['payload'])
        offered = line_octets(payload, delay)
        tx, raw, expected = line.transmitter(
            capturing_execute((frozen.PHASE_VISIT, 112)), mapping, base, offered)
        if (tx['trace_digest'] != old['tx_trace_digest'] or
                hashlib.sha256(bytes(raw)).hexdigest() != old['raw_sha256'] or
                expected != old['expected_dibits']):
            raise ValueError(('phase-112 transmitter changed', selector))
        gain = next(bus for bus in next(c for c in fixed['cases']
                       if c['selector'] == selector)['bus_cases']
                    if bus['bus_index'] == 0)['gain']
        codes = mapped_codes(raw, holdout.BUSES[0])
        gated = codes[:TONE_END] + [128] * (SILENCE_END - TONE_END) + codes[SILENCE_END:]
        wave = bandpass([value - 128 for value in gated], 0.5)
        shifts = {}
        for shift in SHIFTS:
            selected = wave[SILENCE_END + shift:
                            SILENCE_END + shift + line.RX_SYMBOLS * 8]
            pcm = [max(-127, min(127, round(value * gain))) for value in selected]
            wrong = [index for index, (got, want) in enumerate(
                zip(receive(pcm), expected[1:])) if got != want]
            if shift == 6 and hashlib.sha256(bytes(value + 127 for value in pcm)).hexdigest() != old['pcm_sha256']:
                raise ValueError(('phase-112 reference control changed', selector))
            shifts[str(shift)] = dict(wrong_indices_zero_based=wrong,
                                     pcm_sha256=hashlib.sha256(
                                         bytes(value + 127 for value in pcm)).hexdigest())
        cases.append(dict(selector=selector, gain=gain,
                          tx_trace_digest=tx['trace_digest'], shifts=shifts))
        print('line-shift', selector,
              [(s, len(v['wrong_indices_zero_based'])) for s, v in shifts.items()],
              flush=True)
    paths = (Path(__file__), PRIOR, FIXED,
             HERE / 'joint_mask04_12a_buffered_line.py',
             HERE / 'joint_mask04_tx_12a_delayed_latch.py',
             HERE.parent / 'assumed/execute.py', line.MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='phase-112 reference line shift development screen',
                  fixture=dict(R1_offset=112, levels=[1.0], shifts=SHIFTS,
                               filter_Q=0.5, fixed_gain=True,
                               candidate_DAC_bus=0),
                  cases=cases,
                  limitations=[
                      'The two phase-112 payloads are development data for choosing a line shift.',
                      'Reference-decoder errors do not identify an onboard DSC decision.',
                      'The physical sample clock, DAC bus and analog line remain untraced.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
