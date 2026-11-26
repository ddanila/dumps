"""Challenge the frozen cross-visit gate with new controller payloads."""

import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_phasebit0_veto_lowgain133_challenge as challenge
import joint_mask04_12a_row_mode_edge as edge
import joint_mask04_12a_row0_serial_timing as serial
import joint_mask04_12a_visit94_phase_gate as gate
import joint_mask04_buffered_serial_handoff as handoff
from joint_mask04_12a_multivisit_phase_screen import SELECTED, sample_state
from joint_mask04_12a_phasebit0_veto import corrected_phase
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
OUT = RESULTS / 'joint-mask04-12a-visit94-phase-holdout.json'
FIXTURES = (
    (133, {'40': (0x21, 0x9A, 0x6F, 0xC4, 0x08, 0xD3, 0x75, 0xBE),
           '60': (0xF6, 0x14, 0xCB, 0x39, 0x82, 0x5D, 0xE0, 0xA7)}),
    (135, {'40': (0x4B, 0xE5, 0x12, 0xA8, 0x73, 0x0D, 0xC6, 0x9F),
           '60': (0x91, 0x2E, 0xF4, 0x58, 0xB0, 0x67, 0x1C, 0xDA)}),
)


def run(out=OUT):
    model = json.loads(gate.MODEL.read_text())
    inverse = {step: dibit for dibit, step in
               enumerate(model['fixture']['phase_convention'])}
    rows = []
    expanded_paths = []
    with tempfile.TemporaryDirectory() as temporary:
        exe, controller_sha = handoff.compiled_controller(temporary)
        def captured(symbol, variant, covers):
            return gate.candidate_phase(symbol), gate.READY, sample_state(symbol, SELECTED)
        for offset, payloads in FIXTURES:
            path = RESULTS / f'joint-mask04-12a-visit94-phase-holdout-{offset}.json'
            expanded_paths.append(path)
            with patch.object(edge, 'CAPTURE_VISITS', (46, 47, 93, 94, 141)), \
                    patch.object(challenge, 'OFFSET', offset), \
                    patch.object(challenge, 'PAYLOADS', payloads):
                saved = challenge.run(out=path)
            if saved['fixture']['controller_probe_sha256'] != controller_sha:
                raise ValueError('controller probe changed')
            with patch.object(serial, 'captured_phase', captured):
                for case in saved['cases']:
                    selector = case['selector']
                    payload = list(payloads[selector])
                    offered = line_octets(payload, 5 if selector == '40' else 18)
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
                    rows.append(dict(carrier_offset=offset, selector=selector,
                                     payload=[f'{value:02X}' for value in payload],
                                     pcm_sha256=case['pcm_sha256'],
                                     rx_trace_digest=case['rx_trace_digest'],
                                     old_veto_errors=len(case['corrected_wrong_indices']),
                                     active_symbols=active,
                                     active_states=[f'{states[i]:02X}' for i in active],
                                     candidate_wrong_indices=score['wrong_decision_indices'],
                                     recovered_matches_offered=score['recovered_matches_offered'],
                                     controller_decoded_bytes=score['controller_decoded_bytes'],
                                     controller_errors=score['controller_errors'],
                                     controller_overruns=score['controller_overruns'],
                                     minimum_setup_cycles=score['minimum_setup_cycles']))
                    print('visit94 holdout', offset, selector,
                          'active', len(active), 'old', len(case['corrected_wrong_indices']),
                          'new', len(score['wrong_decision_indices']), flush=True)
    paths = (Path(__file__), gate.MODEL, Path(gate.__file__),
             Path(challenge.__file__), Path(edge.__file__),
             *(path for path in expanded_paths))
    report = dict(experiment='frozen visit-94 phase gate on fresh payload/carrier cases',
                  fixture=dict(payloads={str(offset): {
                      selector: [f'{value:02X}' for value in values]
                      for selector, values in payloads.items()}
                      for offset, payloads in FIXTURES},
                               carrier_offsets=[133, 135], gain_factor=0.8,
                               controller_probe_sha256=controller_sha,
                               rule='P0 = frozen_veto_P0 AND NOT(visit94_3F8_Y6)'),
                  cases=rows,
                  limitations=[
                      'The gate is frozen from the earlier 0.8x/1.15x/1.25x screen; all payloads are new and carrier offset 135 is new.',
                      'Visit-94 latch, extra gate, ADC/line and serial nets are assumed; success is not a physical C3 pass.',
                      'The 0.8x gain uses the declared ADC fixture; clipping and analog calibration are model properties.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
