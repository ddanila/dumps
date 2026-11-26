"""Screen a cross-visit phase-bit-0 gate on saved real-PROM receiver traces."""

import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_row0_serial_timing as serial
import joint_mask04_buffered_serial_handoff as handoff
from joint_mask04_12a_multivisit_phase_screen import SELECTED, sample_state
from joint_mask04_12a_phasebit0_veto import corrected_phase
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
INPUTS = (
    ('0.80', RESULTS / 'joint-mask04-12a-lowgain133-expanded-visits.json'),
    ('1.15', RESULTS / 'joint-mask04-12a-mode1-expanded-1.15.json'),
    ('1.25', RESULTS / 'joint-mask04-12a-mode1-expanded-1.25.json'),
)
MODEL = RESULTS / 'joint-mask04-12a-mode-phase-twelve.json'
OUT = RESULTS / 'joint-mask04-12a-visit94-phase-gate.json'
READY = serial.Y3F8_CYCLE + 94 * serial.CYCLES_PER_VISIT


def candidate_phase(symbol):
    state = sample_state(symbol, SELECTED)
    later_bit = (symbol['visits']['94']['y3f8'] >> 6) & 1
    return corrected_phase(state, 1) & ~later_bit


def run(out=OUT):
    model = json.loads(MODEL.read_text())
    inverse = {step: dibit for dibit, step in
               enumerate(model['fixture']['phase_convention'])}
    if inverse != {2: 0, 1: 1, 3: 2, 0: 3}:
        raise ValueError('phase convention changed')
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        exe, controller_sha = handoff.compiled_controller(temporary)
        def captured(symbol, variant, covers):
            state = sample_state(symbol, SELECTED)
            return candidate_phase(symbol), READY, state
        with patch.object(serial, 'captured_phase', captured):
            for gain, path in INPUTS:
                saved = json.loads(path.read_text())
                for case in saved['cases']:
                    payload = [int(value, 16) for value in case['payload']]
                    delay = 5 if case['selector'] == '40' else 18
                    offered = line_octets(payload, delay)
                    replay_case = dict(case, offered_line_bytes=[
                        f'{value:02X}' for value in offered])
                    score = serial.replay(replay_case,
                                          serial.VARIANTS['aligned'],
                                          None, inverse, exe)
                    states = [sample_state(symbol, SELECTED)
                              for symbol in case['multi_visit_symbols']]
                    active = [index for index, symbol in
                              enumerate(case['multi_visit_symbols'])
                              if corrected_phase(states[index], 1) & 1 and
                              symbol['visits']['94']['y3f8'] & 0x40]
                    if (score['wrong_decision_indices'] or
                            not score['recovered_matches_offered'] or
                            score['controller_decoded_bytes'] != payload or
                            score['controller_errors'] or
                            score['controller_overruns']):
                        raise ValueError(('cross-visit gate failed saved case',
                                          gain, case['selector'], score))
                    cases.append(dict(gain=gain, selector=case['selector'],
                                      active_symbols=active,
                                      active_states=[f'{states[i]:02X}'
                                                     for i in active],
                                      wrong_decisions=score['wrong_decision_indices'],
                                      recovered_matches_offered=True,
                                      controller_decoded_bytes=payload,
                                      minimum_setup_cycles=score['minimum_setup_cycles'],
                                      rx_trace_digest=case['rx_trace_digest']))
    paths = (Path(__file__), MODEL,
             HERE / 'joint_mask04_12a_phasebit0_veto.py',
             HERE / 'joint_mask04_12a_row0_serial_timing.py',
             *(path for _, path in INPUTS))
    report = dict(experiment='development screen of visit-94 Y6 phase-bit-0 gate',
                  fixture=dict(rule='P0 = frozen_veto_P0 AND NOT(visit94_3F8_Y6); P1 unchanged',
                               ready_cycle=READY,
                               controller_probe_sha256=controller_sha),
                  cases=cases,
                  limitations=[
                      'The visit-94 gate was selected after observing the low-gain failure; these six cases are development evidence, not a holdout.',
                      'The Y6 latch, additional gate, board wiring and serial clock are assumptions, not photographed connections.',
                      'Exact modeled controller bytes do not establish the physical ADC or line output route.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    report = run()
    for case in report['cases']:
        print(case['gain'], case['selector'], case['active_states'],
              case['minimum_setup_cycles'])
