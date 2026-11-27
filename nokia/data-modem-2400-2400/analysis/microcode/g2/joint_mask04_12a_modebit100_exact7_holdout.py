"""Challenge the frozen seven/five-product phase cover on fresh PROM runs."""

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
from joint_mask04_12a_modebit97_cover import FEATURES, STEPS
from joint_mask04_12a_ten_bit_product_bound import cube_hit
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
EXACT = RESULTS / 'joint-mask04-12a-modebit97-exact-products.json'
ORIGINAL_GAIN = RESULTS / 'joint-mask04-12a-fixed-gain-phase.json'
GAIN = RESULTS / 'joint-mask04-12a-modebit100-exact7-gain105-fixture.json'
OUT = RESULTS / 'joint-mask04-12a-modebit100-exact7-gain105-holdout.json'
OFFSET = 193
FACTOR = 1.05
PAYLOADS = {
    '40': (0x5E, 0xA3, 0x19, 0xC7, 0x42, 0xD8, 0x6B, 0xF0),
    '60': (0x91, 0x2C, 0xE5, 0x70, 0x0B, 0xB6, 0x4D, 0x83),
}
MODES = ('edge32', 'edge48')
LATE_EDGE = 48 * edge.loopback.VISITS_PER_SYMBOL * 4 + 1


def make_gain_fixture():
    base = json.loads(ORIGINAL_GAIN.read_text())
    fixture = dict(experiment='1.05x calibrated bus-0 receive gain fixture',
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
    exact_source = HERE / 'joint_mask04_12a_modebit97_exact_products.py'
    key = str(exact_source.relative_to(HERE.parents[4]))
    if (frozen['source_sha256'][key] !=
            hashlib.sha256(exact_source.read_bytes()).hexdigest() or
            frozen['post_holdout_phase_graph']['state_codes'] != 100):
        raise ValueError('frozen exact-product cover changed')
    screen = next(row for row in frozen['screens']
                  if row['name'] == 'post_holdout_100')
    cubes = [next(row['witness_cubes'] for row in screen['results']
                  if (row['phase_bit'], row['on_polarity']) == (bit, 1))
             for bit in (0, 1)]
    if tuple(map(len, cubes)) != (7, 5):
        raise ValueError('frozen seven/five-product witness changed')

    def frozen_phase(state):
        return sum(int(any(cube_hit(state, cube) for cube in terms)) << bit
                   for bit, terms in enumerate(cubes))

    known = {int(key, 16) for key in
             frozen['post_holdout_phase_graph']['relative_phase']}
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
            state = code(symbol, FEATURES)
            return frozen_phase(state), serial.Y3F8_CYCLE + 94 * serial.CYCLES_PER_VISIT, state

        for mode in MODES:
            path = RESULTS / f'joint-mask04-12a-modebit100-exact7-gain105-holdout-{mode}-{OFFSET}.json'
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
                saved['experiment'] = 'fresh 1.05x real-PROM seven/five-product mode-boundary challenge'
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
                symbols = case['multi_visit_symbols']
                boundary_index = 48 if mode == 'edge48' else 32
                for index, symbol in enumerate(symbols):
                    symbol['visits']['46']['mode_bit5'] = int(index >= boundary_index)
                states = [code(symbol, FEATURES) for symbol in symbols]
                phases = [frozen_phase(state) for state in states]
                wrong = [index for index in range(1, len(states))
                         if inverse[(phases[index] - phases[index - 1]) & 3]
                         != case['expected_dibits'][index]]
                payload = list(PAYLOADS[selector])
                offered = line_octets(payload, 5 if selector == '40' else 18)
                replay_case = dict(case, offered_line_bytes=[f'{value:02X}'
                                                          for value in offered])
                with patch.object(serial, 'captured_phase', captured):
                    score = serial.replay(replay_case, serial.VARIANTS['aligned'],
                                          None, inverse, exe)
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
                                 unseen_keys=[f'{state:03X}' for state in
                                              sorted(set(states) - known)],
                                 wrong_decision_indices=wrong,
                                 line_exact=score['recovered_matches_offered'],
                                 controller_decoded_bytes=score['controller_decoded_bytes'],
                                 controller_exact=score['controller_decoded_bytes'] == payload,
                                 controller_status_errors=score['controller_errors'],
                                 minimum_setup_cycles=score['minimum_setup_cycles']))
                print('exact7', mode, selector, 'unseen', rows[-1]['unseen_keys'],
                      'wrong', len(wrong), 'line', rows[-1]['line_exact'],
                      'controller', rows[-1]['controller_exact'], flush=True)
    sources = (Path(__file__), EXACT, exact_source, ORIGINAL_GAIN, GAIN,
               Path(challenge.__file__), Path(edge.__file__), Path(fresh.__file__),
               HERE / 'joint_mask04_12a_modebit97_cover.py',
               HERE / 'joint_mask04_12a_ten_bit_product_bound.py', *raw_paths)
    report = dict(experiment='fresh 1.05x offset-193 challenge of frozen exact seven/five-product cover',
                  fixture=dict(carrier_offset=OFFSET, gain_factor=FACTOR,
                               payloads={key: [f'{value:02X}' for value in value]
                                         for key, value in PAYLOADS.items()},
                               modes=MODES, frozen_observed_states=len(known),
                               phase_convention=STEPS,
                               phase_bit0_cubes=cubes[0], phase_bit1_cubes=cubes[1],
                               controller_probe_sha256=controller_sha),
                  cases=rows,
                  limitations=[
                      'The exact-product witness was fitted to 100 earlier streams including offset-191; offset-193 is the untouched challenge.',
                      'The D3EB mode schedule and additional captures remain assumptions, not traced board connections.',
                      'The direct-product count does not establish a photographed-package gate network or phase-subtraction and serial-select logic.',
                      'DAC/ADC/latch and RxD/RxC/SYNDET nets remain untraced; controller recovery is conditional on the modeled line and external-sync handoff.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
