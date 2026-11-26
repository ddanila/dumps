"""Run the phase-131 receiver at an unclipped 1.125x gain."""

import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_buffered_line as line
import joint_mask04_12a_row0_serial_timing as serial
import joint_mask04_buffered_serial_handoff as handoff
from joint_mask04_12a_mode_phase131_adc_range import pcm_for
from joint_mask04_12a_multivisit_phase_screen import SELECTED, sample_state
from joint_mask04_12a_row_mode_edge import EDGE, MODE_READS, execute_case
from joint_mask04_12a_row0_boolean import phase
from photo_u15_u19_u21_phase_route import circuit
from reference_modem import receive
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
RANGE = HERE / 'results/joint-mask04-12a-mode-phase131-adc-range.json'
BASELINE = HERE / 'results/joint-mask04-12a-mode-phase131-baseline-control.json'
MODEL = HERE / 'results/joint-mask04-12a-mode-phase-twelve.json'
OUT = HERE / 'results/joint-mask04-12a-mode-phase131-intermediate-gain.json'
FACTOR = 1.125


def run(out=OUT):
    spectrum = json.loads(RANGE.read_text())
    baseline = json.loads(BASELINE.read_text())
    model = json.loads(MODEL.read_text())
    inverse = {step: dibit for dibit, step in
               enumerate(model['fixture']['phase_convention'])}
    covers = serial.covers_from_model(model)
    known = {int(code, 16) for code in model['trained_state_phase']}
    known.update((0x3D, 0x4C))
    mapping = line.candidate(line.mapping_with_upper_source(0, '17.6'),
                             line.mapped(line.MAPPINGS['q3']), 4)
    _, base = line.fixture()
    mode_values = [0x81] * EDGE + [0xA1] * (MODE_READS - EDGE)
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        exe, controller_sha = handoff.compiled_controller(temporary)
        with patch.object(serial, 'phase', lambda state, covers: circuit(state, 1)):
            for wave_case, source in zip(spectrum['cases'], baseline['cases']):
                selector = wave_case['selector']
                if selector != source['selector']:
                    raise ValueError('wave/source selector changed')
                fixture = next(row for row in wave_case['factors']
                               if row['factor'] == FACTOR)
                if fixture['clipped_samples']:
                    raise ValueError('intermediate gain is clipped')
                pcm = pcm_for(wave_case['selected_wave'],
                              wave_case['calibrated_gain'], FACTOR)
                pcm_digest = hashlib.sha256(
                    bytes(value + 127 for value in pcm)).hexdigest()
                if pcm_digest != fixture['pcm_sha256']:
                    raise ValueError('intermediate PCM changed')
                expected = source['expected_dibits']
                reference_wrong = [index for index, (got, want) in
                                   enumerate(zip(receive(pcm), expected[1:]), 1)
                                   if got != want]
                rx, pc_digest, symbols, gate_edges = execute_case(
                    mapping, base, pcm, mode_values)
                captured = [symbols[index] for index in range(handoff.RX_SYMBOLS)]
                states = [sample_state(symbol, SELECTED) for symbol in captured]
                package_phases = [circuit(state, 1) for state in states]
                old_phases = [phase(state, covers) for state in states]
                def wrong(phases):
                    return [index for index in range(1, len(phases))
                            if inverse[(phases[index] - phases[index - 1]) & 3]
                            != expected[index]]
                package_wrong = wrong(package_phases)
                old_wrong = wrong(old_phases)
                payload = [int(value, 16) for value in source['payload']]
                delay = 5 if selector == '40' else 18
                offered = line_octets(payload, delay)
                replay_case = dict(multi_visit_symbols=captured,
                                   expected_dibits=expected,
                                   selector=selector,
                                   offered_line_bytes=[f'{x:02X}' for x in offered])
                score = serial.replay(replay_case, serial.VARIANTS['aligned'],
                                      None, inverse, exe)
                if len(states) != 65 or len(expected) != 65:
                    raise ValueError(('intermediate symbol count', selector))
                cases.append(dict(selector=selector,
                                  payload=source['payload'],
                                  tx_trace_digest=source['tx_trace_digest'],
                                  raw_sha256=source['raw_sha256'],
                                  pcm_sha256=pcm_digest,
                                  rx_trace_digest=rx['trace_digest'],
                                  pc_digest=pc_digest,
                                  gate_edges=gate_edges,
                                  expected_dibits=expected,
                                  reference_wrong_indices=reference_wrong,
                                  observed_states=[f'{value:02X}' for value in states],
                                  unseen_states=sorted(f'{value:02X}' for value in
                                                       set(states) - known),
                                  old_cover_wrong_indices=old_wrong,
                                  package_circuit_wrong_indices=package_wrong,
                                  package_circuit_serial=score,
                                  multi_visit_symbols=captured))
                print(selector, 'reference', len(reference_wrong),
                      'old', len(old_wrong), 'package', len(package_wrong),
                      'unseen', cases[-1]['unseen_states'], flush=True)
    paths = (Path(__file__), RANGE, BASELINE, MODEL,
             HERE / 'photo_u15_u19_u21_phase_route.py',
             HERE / 'joint_mask04_12a_row_mode_edge.py')
    report = dict(experiment='unclipped 1.125x phase-131 receive gain challenge',
                  fixture=dict(gain_factor=FACTOR, R1_offset=131,
                               assumed_mode='81-to-A1 at D3EB read 48001',
                               controller_probe_sha256=controller_sha),
                  cases=cases,
                  limitations=[
                      'The raw transmitted stream is reused from the verified phase-131 baseline; only the gain and receiver execution change.',
                      'DAC, line, ADC, mode, capture, logic and serializer connections are assumed, not traced.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
