"""Fresh 0.8x line-level challenge of the frozen mode-bit phase cover."""

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
from joint_mask04_12a_modebit70_revision import FEATURES, STEPS, gate_phase
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
COVER = RESULTS / 'joint-mask04-12a-modebit70-revision.json'
GRAPH = COVER
GAIN = RESULTS / 'joint-mask04-12a-mode-phase133-lowgain-fixture.json'
OUT = RESULTS / 'joint-mask04-12a-modebit70-lowgain.json'
OFFSET = 183
FACTOR = 0.8
PAYLOADS = {
    '40': (0x83, 0x5E, 0xC1, 0x2B, 0xF6, 0x09, 0xA4, 0x7D),
    '60': (0x1A, 0xE7, 0x44, 0x9B, 0x30, 0xD5, 0x6C, 0x82),
}
MODES = ('edge32', 'edge48')
LATE_EDGE = 48 * edge.loopback.VISITS_PER_SYMBOL * 4 + 1


def annotate(symbols, mode):
    for index, symbol in enumerate(symbols):
        symbol['visits']['46']['mode_bit5'] = int(
            index >= (48 if mode == 'edge48' else 32))


def run(out=OUT, capture=True):
    frozen = json.loads(COVER.read_text())
    source = Path(gate_phase.__code__.co_filename)
    if (frozen['fixture']['observed_states'] != 64 or
            frozen['source_sha256'][str(source.relative_to(HERE.parents[4]))]
            != hashlib.sha256(source.read_bytes()).hexdigest()):
        raise ValueError('frozen mode-bit Boolean cover changed')
    graph = json.loads(GRAPH.read_text())['mode_bit_graph']
    if (graph['state_codes'], graph['directed_conflicts'], graph['components']) != (64, 0, [64]):
        raise ValueError('frozen phase graph changed')
    known = {int(key, 16) for key in graph['relative_phase']}
    inverse = {step: dibit for dibit, step in enumerate(STEPS)}
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
            key = code(symbol, FEATURES)
            return gate_phase(key), serial.Y3F8_CYCLE + 94 * serial.CYCLES_PER_VISIT, key

        for mode in MODES:
            path = RESULTS / f'joint-mask04-12a-modebit70-lowgain-{mode}-{OFFSET}.json'
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
                saved['experiment'] = 'matched fresh low-gain real-PROM mode-boundary challenge'
                saved['fixture']['assumed_mode'] = mode
                saved['limitations'].append(
                    'The edge-48 mode schedule is an imposed source-hashed wrapper over the original edge-32 fixture.')
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
                annotate(symbols, mode)
                keys = [code(symbol, FEATURES) for symbol in symbols]
                unseen = sorted(set(keys) - known)
                gate_wrong = [index for index in range(1, len(keys))
                              if inverse[(gate_phase(keys[index]) -
                                          gate_phase(keys[index - 1])) & 3]
                              != case['expected_dibits'][index]]
                payload = list(PAYLOADS[selector])
                offered = line_octets(payload, 5 if selector == '40' else 18)
                with patch.object(serial, 'captured_phase', captured):
                    score = serial.replay(dict(case, offered_line_bytes=[
                        f'{value:02X}' for value in offered]),
                        serial.VARIANTS['aligned'], None, inverse, exe)
                if gate_wrong != score['wrong_decision_indices']:
                    raise ValueError('gate and serial decision indices differ')
                rows.append(dict(mode=mode, carrier_offset=OFFSET,
                                 selector=selector,
                                 payload=[f'{value:02X}' for value in payload],
                                 tx_trace_digest=case['tx_trace_digest'],
                                 rx_trace_digest=case['rx_trace_digest'],
                                 pc_digest=case['pc_digest'],
                                 pcm_sha256=case['pcm_sha256'],
                                 clipped_samples=case['clipped_samples'],
                                 unseen_keys=[f'{key:03X}' for key in unseen],
                                 captured_keys=[f'{key:03X}' for key in keys],
                                 wrong_decision_indices=gate_wrong,
                                 line_exact=score['recovered_matches_offered'],
                                 controller_decoded_bytes=score['controller_decoded_bytes'],
                                 controller_exact=score['controller_decoded_bytes'] == payload,
                                 controller_status_errors=score['controller_errors'],
                                 minimum_setup_cycles=score['minimum_setup_cycles']))
                print('modebit lowgain', mode, selector,
                      'unseen', rows[-1]['unseen_keys'],
                      'wrong', len(gate_wrong), 'line', rows[-1]['line_exact'],
                      'payload', rows[-1]['controller_exact'], flush=True)
    sources = (Path(__file__), COVER, GRAPH, source, GAIN,
               Path(challenge.__file__), Path(edge.__file__),
               Path(fresh.__file__), *raw_paths)
    report = dict(experiment='fresh low-gain edge32 and edge48 challenge of frozen revised mode-bit Boolean cover',
                  fixture=dict(carrier_offset=OFFSET,
                               payloads={selector: [f'{value:02X}' for value in payload]
                                         for selector, payload in PAYLOADS.items()},
                               modes=MODES,
                               gain_factor=FACTOR,
                               frozen_observed_states=len(known),
                               controller_probe_sha256=controller_sha),
                  cases=rows,
                  limitations=[
                      'The exact-state 32D correction was fitted using offset-177 cases; this offset-183 0.8x-gain test uses untouched payloads and carrier start.',
                      'Moving the mode edge from symbol 32 to 48 is an imposed D3EB input, not a traced physical transition.',
                      'The cover is a Boolean development fit, not a photographed-package gate realization.',
                      'The D3EB mode schedule and mode-bit-to-gate connection are assumptions; DAC/ADC/latch and RxD/RxC/SYNDET nets remain untraced.',
                      'An exact modeled controller payload would be a conditional end-to-end result, not proof of Nokia wiring.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
