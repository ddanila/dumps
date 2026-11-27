"""Fresh 1.10x challenge of the frozen eleven-bit phase cover."""

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
from joint_mask04_12a_modebit91_cover import FEATURES, STEPS, gate_phase
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
COVER = RESULTS / 'joint-mask04-12a-modebit91-cover.json'
GRAPH = COVER
GAIN = RESULTS / 'joint-mask04-12a-modebit91-gain110-fixture.json'
ORIGINAL_GAIN = RESULTS / 'joint-mask04-12a-fixed-gain-phase.json'
OUT = RESULTS / 'joint-mask04-12a-modebit91-gain110-holdout.json'
OFFSET = 189
FACTOR = 1.10
PAYLOADS = {
    '40': (0xA7, 0x1C, 0xD4, 0x6B, 0x02, 0xE9, 0x35, 0x8F),
    '60': (0x5D, 0xB2, 0x49, 0xC0, 0x17, 0x6E, 0xF3, 0x84),
}
MODES = ('edge32', 'edge48')
LATE_EDGE = 48 * edge.loopback.VISITS_PER_SYMBOL * 4 + 1


def make_gain_fixture():
    base = json.loads(ORIGINAL_GAIN.read_text())
    fixture = dict(experiment='1.10x calibrated bus-0 receive gain fixture',
                   source_file=ORIGINAL_GAIN.name,
                   source_sha256=hashlib.sha256(ORIGINAL_GAIN.read_bytes()).hexdigest(),
                   gain_factor=FACTOR,
                   cases=[dict(selector=case['selector'], bus_cases=[
                       dict(bus_index=0, gain=FACTOR * next(
                           bus['gain'] for bus in case['bus_cases']
                           if bus['bus_index'] == 0))])
                       for case in base['cases']])
    GAIN.write_text(json.dumps(fixture, indent=2) + '\n')


def annotate(symbols, mode):
    for index, symbol in enumerate(symbols):
        symbol['visits']['46']['mode_bit5'] = int(
            index >= (48 if mode == 'edge48' else 32))


def run(out=OUT, capture=True):
    make_gain_fixture()
    frozen = json.loads(COVER.read_text())
    source = Path(gate_phase.__code__.co_filename)
    if (frozen['fixture']['observed_states'] != 91 or
            frozen['source_sha256'][str(source.relative_to(HERE.parents[4]))]
            != hashlib.sha256(source.read_bytes()).hexdigest()):
        raise ValueError('frozen mode-bit Boolean cover changed')
    graph = json.loads(GRAPH.read_text())['phase_graph']
    if (graph['state_codes'], graph['directed_conflicts'], graph['components']) != (91, 0, [91]):
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
            path = RESULTS / f'joint-mask04-12a-modebit91-gain110-holdout-{mode}-{OFFSET}.json'
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
                saved['experiment'] = 'fresh 1.10x real-PROM eleven-bit mode-boundary challenge'
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
                print('modebit91 gain110', mode, selector,
                      'unseen', rows[-1]['unseen_keys'],
                      'wrong', len(gate_wrong), 'line', rows[-1]['line_exact'],
                      'payload', rows[-1]['controller_exact'], flush=True)
    sources = (Path(__file__), COVER, GRAPH, source, GAIN,
               Path(challenge.__file__), Path(edge.__file__),
               Path(fresh.__file__), *raw_paths)
    report = dict(experiment='fresh 1.10x edge32 and edge48 challenge of frozen eleven-bit Boolean cover',
                  fixture=dict(carrier_offset=OFFSET,
                               payloads={selector: [f'{value:02X}' for value in payload]
                                         for selector, payload in PAYLOADS.items()},
                               modes=MODES,
                               gain_factor=FACTOR,
                               frozen_observed_states=len(known),
                               controller_probe_sha256=controller_sha),
                  cases=rows,
                  limitations=[
                      'The eleven-bit cover was fitted using 92 earlier streams, including offset-185; this offset-189 test uses untouched payloads, carrier start and 1.10x receive level.',
                      'Late row-0 Y2 is an assumed extra capture at visit 93; no package storage/clock route is established.',
                      'Clipping is reported per run; exact decision scores under clipping do not establish the unclipped analog transfer function.',
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
