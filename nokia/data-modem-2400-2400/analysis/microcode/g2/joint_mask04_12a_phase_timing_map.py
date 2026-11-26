"""Fit a four-state phase label on call and test the answer holdout."""

import hashlib
import itertools
import json
import tempfile
from pathlib import Path

import joint_mask04_12a_buffered_line as line
import joint_mask04_buffered_serial_handoff as handoff
from joint_mask04_q05_fresh_payload_levels import PAYLOADS
from reference_modem import QUADRANT_TO_DIBIT
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
TX = HERE / 'results/joint-mask04-12a-phase-timing.json'
RX = HERE / 'results/joint-mask04-12a-phase-timing-rx.json'


def decode(states, phase):
    states = [int(value, 16) for value in states]
    return [None] + [QUADRANT_TO_DIBIT[
        (phase[after] - phase[before] - 2) & 3]
        for before, after in zip(states, states[1:])]


def run(out=HERE / 'results/joint-mask04-12a-phase-timing-map.json'):
    tx = json.loads(TX.read_text())
    rx = json.loads(RX.read_text())
    call = next(c for c in rx['cases'] if c['selector'] == '40')
    call_tx = next(c for c in tx['cases'] if c['selector'] == '40'
                   and c['timing'] == 'silence_start')
    states = sorted({int(value, 16) for value in call['states']})
    if states != [2, 6, 9, 13]:
        raise ValueError(('unexpected call state family', states))
    exact = []
    for labels in itertools.product(range(4), repeat=len(states) - 1):
        phase = dict(zip(states, (0, *labels)))
        if decode(call['states'], phase)[1:] == call_tx['expected_dibits'][1:]:
            exact.append(phase)
    if len(exact) != 1:
        raise ValueError(('phase constraint ambiguous or inconsistent', exact))
    phase = exact[0]
    cases = []
    with tempfile.TemporaryDirectory() as temp:
        controller, controller_sha = handoff.compiled_controller(temp)
        for selector, delay in (('40', 5), ('60', 18)):
            row = next(c for c in rx['cases'] if c['selector'] == selector)
            input_row = next(c for c in tx['cases'] if c['selector'] == selector
                             and c['timing'] == 'silence_start')
            decoded = decode(row['states'], phase)
            expected = input_row['expected_dibits']
            wrong = [i for i, (got, want) in enumerate(zip(decoded[1:], expected[1:]))
                     if got != want]
            offered = line_octets(PAYLOADS[selector], delay)
            readout = line.readout_result(decoded, expected, offered,
                                          controller, selector, delay)
            cases.append(dict(selector=selector,
                              role='call_training' if selector == '40' else 'answer_holdout',
                              wrong_indices=wrong, decoded_dibits=decoded,
                              readout=readout))
            print(selector, 'wrong', len(wrong),
                  'line match', readout['recovered_matches_offered'], flush=True)
    report = dict(experiment='call-constrained offset-32 phase labels with answer holdout',
                  rule=dict(phase={f'{k:X}': v for k, v in phase.items()},
                            anchor='state 2 = phase 0; arbitrary global rotation',
                            formula='QUADRANT_TO_DIBIT[(after-before-2) mod 4]',
                            exact_call_maps=1, tested_maps=4 ** (len(states) - 1)),
                  fixture=dict(timing='silence_start', offset=32,
                               controller_probe_sha256=controller_sha),
                  cases=cases,
                  limitations=['The phase labels were inferred from call-side known data.',
                               'There is no identified hardware mechanism that selects labels after a phase change.',
                               'Converter, clock, analog and serial routes remain assumed.'],
                  source_sha256={str(p.relative_to(HERE.parents[4])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (Path(__file__), TX, RX,
                                           HERE / 'joint_mask04_q05_phase_level_map.py',
                                           HERE.parent / 'assumed/execute.py')})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
