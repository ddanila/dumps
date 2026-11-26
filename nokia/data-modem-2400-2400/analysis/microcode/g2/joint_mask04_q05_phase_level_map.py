"""Extend the phase map from call-side levels and hold out answer-side levels."""

import hashlib
import json
import tempfile
from pathlib import Path

import joint_mask04_12a_analog_holdout as holdout
import joint_mask04_12a_buffered_line as line
import joint_mask04_buffered_serial_handoff as handoff
from joint_mask04_q05_phase_state_holdout import PHASE as BASE_PHASE
from reference_modem import QUADRANT_TO_DIBIT
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
PRIOR = HERE / 'results/joint-mask04-q05-phase-level.json'
INVERSE_DIBIT = {value: index for index, value in
                 enumerate(QUADRANT_TO_DIBIT)}


def transitions(case):
    states = [int(value, 16) for value in case['states']]
    expected = case['expected_dibits']
    return [(a, b, (INVERSE_DIBIT[expected[i]] + 2) & 3,
             expected[i], i)
            for i, (a, b) in enumerate(zip(states, states[1:]), 1)]


def derive_phase(cases):
    phase = dict(BASE_PHASE)
    edges = [edge for case in cases for edge in transitions(case)]
    changed = True
    while changed:
        changed = False
        for before, after, advance, _, _ in edges:
            if before in phase and after not in phase:
                phase[after] = (phase[before] + advance) & 3
                changed = True
            if after in phase and before not in phase:
                phase[before] = (phase[after] - advance) & 3
                changed = True
    failures = [(before, after, index) for before, after, advance, _, index
                in edges if before not in phase or after not in phase or
                ((phase[after] - phase[before]) & 3) != advance]
    if failures:
        raise ValueError(('call-side phase constraints conflict', failures[:8]))
    return phase


def decode(states, phase):
    values = [int(value, 16) for value in states]
    return [None] + [QUADRANT_TO_DIBIT[(phase[b] - phase[a] - 2) & 3]
                     if a in phase and b in phase else None
                     for a, b in zip(values, values[1:])]


def run(out=HERE / 'results/joint-mask04-q05-phase-level-map.json'):
    prior = json.loads(PRIOR.read_text())
    training = [case for case in prior['cases']
                if case['selector'] == '40' and case['level'] != 1.0]
    holdout_cases = [case for case in prior['cases']
                     if case['selector'] == '60' and case['level'] != 1.0]
    if len(training) != 2 or len(holdout_cases) != 2:
        raise ValueError('expected two call and answer level fixtures')
    phase = derive_phase(training)
    if phase != {**BASE_PHASE, 0x6: 0, 0x9: 1, 0xB: 2}:
        raise ValueError(('unexpected phase extension', phase))
    results = []
    with tempfile.TemporaryDirectory() as temp:
        controller, controller_sha = handoff.compiled_controller(temp)
        for case in prior['cases']:
            decoded = decode(case['states'], phase)
            expected = case['expected_dibits']
            selector = case['selector']
            delay = 5 if selector == '40' else 18
            offered = line_octets(holdout.PAYLOADS[1], delay)
            result = line.readout_result(decoded, expected, offered,
                                         controller, selector, delay)
            results.append(dict(selector=selector, level=case['level'],
                                role=('development' if case in training else
                                      'answer_holdout' if case in holdout_cases else
                                      'nominal_control'),
                                rx_trace_digest=case['rx_trace_digest'],
                                pcm_sha256=case['pcm_sha256'],
                                decoded_dibits=decoded,
                                preamble_wrong=sum(got is not None and got != want
                                                   for got, want in zip(
                                                       decoded[1:handoff.PREAMBLE +
                                                               handoff.PIPELINE_SYMBOLS],
                                                       expected[1:handoff.PREAMBLE +
                                                                handoff.PIPELINE_SYMBOLS])),
                                preamble_unknown=sum(got is None
                                                     for got in decoded[1:handoff.PREAMBLE +
                                                                        handoff.PIPELINE_SYMBOLS]),
                                readout=result))
    report = dict(experiment='call-trained seven-state phase map on answer level holdouts',
                  rule=dict(base_phase={f'{key:X}': value for key, value in BASE_PHASE.items()},
                            learned_phase={f'{key:X}': value for key, value in
                                           phase.items() if key not in BASE_PHASE},
                            phase_difference='QUADRANT_TO_DIBIT[(after-before-2) mod 4]',
                            training='call selector, 75% and 125% level only',
                            holdout='answer selector, 75% and 125% level'),
                  fixture=dict(source_report=str(PRIOR.name),
                               payload='second nonzero holdout per selector',
                               line='12A Q=0.5, bus 0, +6, zero-run fixed gain',
                               controller_probe_sha256=controller_sha),
                  cases=results,
                  limitations=[
                      'The new phase labels are inferred from labelled call-side data, not identified board logic.',
                      'Call and answer use the same decoded payload but different scrambled line streams and controller selectors.',
                      'Line, ADC, capture, phase logic, USART and SYNDET circuits remain assumed.'
                  ],
                  source_sha256={str(p.relative_to(HERE.parents[4])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (Path(__file__), PRIOR,
                                           HERE / 'joint_mask04_q05_phase_level.py',
                                           HERE / 'joint_mask04_q05_phase_state_holdout.py',
                                           HERE.parent / 'assumed/execute.py')})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    report = run()
    for case in report['cases']:
        print(case['selector'], case['level'], case['role'],
              len(case['readout']['data_wrong_indices']),
              len(case['readout']['data_unknown_indices']),
              case['readout']['recovered_matches_offered'])
