"""Fresh nominal-level real-PROM challenge of frozen thirteen-bit phase cover."""

import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_phasebit0_veto_lowgain133_challenge as challenge
import joint_mask04_12a_row_mode_edge as edge
import joint_mask04_12a_mode_fresh_phase120 as fresh
import joint_mask04_12a_row0_serial_timing as serial
import joint_mask04_buffered_serial_handoff as handoff
from joint_mask04_12a_0d_feature_graph import code
from joint_mask04_12a_modebit97_cover import STEPS
from joint_mask04_12a_modebit156_staged_transfer import THIRTEEN, staged_state
from joint_mask04_12a_ten_bit_product_bound import cube_hit
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
CAPTURE = RESULTS / 'joint-mask04-12a-modebit156-staged-transfer.json'
EXACT = RESULTS / 'joint-mask04-12a-modebit156-exact-products.json'
ORIGINAL_GAIN = RESULTS / 'joint-mask04-12a-fixed-gain-phase.json'
GAIN = RESULTS / 'joint-mask04-12a-modebit156-gain100-fixture.json'
OUT = RESULTS / 'joint-mask04-12a-modebit156-gain100-holdout.json'
OFFSET = 199
FACTOR = 1.00
PAYLOADS = {
    '40': (0x67, 0x0E, 0xB4, 0x39, 0xD1, 0x8A, 0x25, 0xFC),
    '60': (0x92, 0x5D, 0xE1, 0x48, 0x0C, 0xB7, 0x36, 0xAF),
}
MODES = ('edge32', 'edge48')
LATE_EDGE = 48 * edge.loopback.VISITS_PER_SYMBOL * 4 + 1
U28_LOAD_CYCLE = 5000


def make_gain_fixture():
    base = json.loads(ORIGINAL_GAIN.read_text())
    fixture = dict(experiment='nominal calibrated bus-0 receive gain fixture',
                   source_file=ORIGINAL_GAIN.name,
                   source_sha256=hashlib.sha256(ORIGINAL_GAIN.read_bytes()).hexdigest(),
                   gain_factor=FACTOR,
                   cases=[dict(selector=case['selector'], bus_cases=[
                       dict(bus_index=0, gain=FACTOR * next(
                           bus['gain'] for bus in case['bus_cases']
                           if bus['bus_index'] == 0))])
                       for case in base['cases']])
    GAIN.write_text(json.dumps(fixture, indent=2) + '\n')


def run(out=OUT, capture=True):
    frozen = json.loads(EXACT.read_text())
    stage = json.loads(CAPTURE.read_text())
    if (frozen['fixture']['observed_states'] != 156 or
            stage['phase_graph']['state_codes'] != 156):
        raise ValueError('frozen thirteen-bit development fixture changed')
    cubes = [next(row['witness_cubes'] for row in frozen['bounds']
                  if (row['phase_bit'], row['on_polarity']) == (bit, 1))
             for bit in (0, 1)]
    if tuple(map(len, cubes)) != (8, 5):
        raise ValueError('frozen thirteen-bit direct witness changed')

    def phase(state):
        return sum(int(any(cube_hit(state, cube) for cube in terms)) << bit
                   for bit, terms in enumerate(cubes))

    known = {int(key, 16) for key in stage['phase_graph']['relative_phase']}
    inverse = {step: dibit for dibit, step in enumerate(STEPS)}
    make_gain_fixture()
    rows = []
    raw_paths = []
    with tempfile.TemporaryDirectory() as temporary:
        exe, controller_sha = handoff.compiled_controller(temporary)
        original_execute = fresh.execute_case
        late_values = [0x81] * LATE_EDGE + [0xA1] * (edge.MODE_READS - LATE_EDGE)
        expected_values = [0x81] * edge.EDGE + [0xA1] * (edge.MODE_READS - edge.EDGE)

        def late_execute(mapping, base, pcm, mode_values):
            if mode_values != expected_values:
                raise ValueError('underlying mode stimulus changed')
            return original_execute(mapping, base, pcm, late_values)

        def captured(symbol, variant, covers):
            state = staged_state(symbol)
            if state != code(symbol, THIRTEEN):
                raise ValueError('fresh staged thirteen-bit value changed')
            return phase(state), U28_LOAD_CYCLE, state

        for mode in MODES:
            path = RESULTS / f'joint-mask04-12a-modebit156-gain100-holdout-{mode}-{OFFSET}.json'
            raw_paths.append(path)
            if capture:
                with patch.object(edge, 'CAPTURE_VISITS', (46, 47, 93, 94, 141)), \
                        patch.object(challenge, 'GAIN', GAIN), \
                        patch.object(challenge, 'FACTOR', FACTOR), \
                        patch.object(challenge, 'OFFSET', OFFSET), \
                        patch.object(challenge, 'PAYLOADS', PAYLOADS):
                    if mode == 'edge48':
                        with patch.object(fresh, 'execute_case', late_execute):
                            saved = challenge.run(out=path)
                    else:
                        saved = challenge.run(out=path)
                saved['experiment'] = 'fresh nominal-level real-PROM thirteen-bit mode-boundary challenge'
                saved['fixture']['assumed_mode'] = mode
                saved['limitations'].append(
                    'The edge-48 mode schedule is an imposed wrapper over the original edge-32 fixture.')
                saved['source_sha256'][str(Path(__file__).relative_to(HERE.parents[4]))] = (
                    hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
                path.write_text(json.dumps(saved, indent=2) + '\n')
            else:
                saved = json.loads(path.read_text())
            if saved['fixture']['controller_probe_sha256'] != controller_sha:
                raise ValueError('controller probe changed')
            for case in saved['cases']:
                selector = case['selector']
                limit = 48 if mode == 'edge48' else 32
                for index, symbol in enumerate(case['multi_visit_symbols']):
                    symbol['visits']['46']['mode_bit5'] = int(index >= limit)
                states = [staged_state(symbol) for symbol in case['multi_visit_symbols']]
                if any(state != code(symbol, THIRTEEN)
                       for state, symbol in zip(states, case['multi_visit_symbols'])):
                    raise ValueError('fresh thirteen-bit staged capture differs')
                phases = [phase(state) for state in states]
                wrong = [index for index in range(1, len(states))
                         if inverse[(phases[index] - phases[index - 1]) & 3]
                         != case['expected_dibits'][index]]
                payload = list(PAYLOADS[selector])
                offered = line_octets(payload, 5 if selector == '40' else 18)
                with patch.object(serial, 'captured_phase', captured):
                    score = serial.replay(dict(case, offered_line_bytes=[
                        f'{value:02X}' for value in offered]),
                        serial.VARIANTS['aligned'], None, inverse, exe)
                if wrong != score['wrong_decision_indices']:
                    raise ValueError('gate and serial decision indices differ')
                rows.append(dict(mode=mode, selector=selector,
                                 carrier_offset=OFFSET,
                                 payload=[f'{value:02X}' for value in payload],
                                 tx_trace_digest=case['tx_trace_digest'],
                                 rx_trace_digest=case['rx_trace_digest'],
                                 pc_digest=case['pc_digest'],
                                 pcm_sha256=case['pcm_sha256'],
                                 clipped_samples=case['clipped_samples'],
                                 reference_wrong_indices=case['reference_wrong_indices'],
                                 unseen_keys=[f'{state:04X}' for state in
                                              sorted(set(states) - known)],
                                 wrong_decision_indices=wrong,
                                 line_exact=score['recovered_matches_offered'],
                                 controller_decoded_bytes=score['controller_decoded_bytes'],
                                 controller_exact=score['controller_decoded_bytes'] == payload,
                                 controller_status_errors=score['controller_errors'],
                                 minimum_setup_cycles=score['minimum_setup_cycles']))
                print('modebit156', mode, selector,
                      'unseen', rows[-1]['unseen_keys'],
                      'wrong', len(wrong),
                      'line', rows[-1]['line_exact'],
                      'controller', rows[-1]['controller_exact'], flush=True)
    sources = (Path(__file__), CAPTURE, EXACT, ORIGINAL_GAIN, GAIN,
               HERE / 'joint_mask04_12a_modebit156_staged_transfer.py',
               HERE / 'joint_mask04_12a_modebit156_exact_products.py',
               Path(challenge.__file__), Path(edge.__file__), Path(fresh.__file__),
               *raw_paths)
    report = dict(experiment='fresh offset-199 nominal-level challenge of frozen thirteen-bit direct cover',
                  fixture=dict(carrier_offset=OFFSET, gain_factor=FACTOR,
                               payloads={key: [f'{value:02X}' for value in values]
                                         for key, values in PAYLOADS.items()},
                               modes=MODES, frozen_observed_states=len(known),
                               phase_convention=STEPS,
                               phase_bit0_cubes=cubes[0],
                               phase_bit1_cubes=cubes[1],
                               assumed_U28_load_cycle=U28_LOAD_CYCLE,
                               controller_probe_sha256=controller_sha),
                  cases=rows,
                  limitations=[
                      'The thirteen-bit witness was fitted to the 108 saved streams that selected visit-141 Y6; offset-199 is the untouched challenge.',
                      'U14-to-U3 transfer, U25 late-Y6 capture, U28 load, D3EB mode and all actual data/clock nets are assumptions.',
                      'Direct products do not establish a photographed-package gate, phase-subtraction or bit-select circuit.',
                      'DAC/ADC/line and RxD/RxC/SYNDET paths remain conditional model routes.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
