"""Move the assumed 81-to-A1 mode edge from symbol 32 to symbol 48."""

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
from joint_mask04_12a_multivisit_phase_screen import SELECTED, sample_state
from joint_mask04_12a_two_bit_package_route2 import gate_phase
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
GRAPH = RESULTS / 'joint-mask04-12a-two-bit-package-holdout-audit.json'
PACKAGE = RESULTS / 'joint-mask04-12a-two-bit-package-route2.json'
BASE_GAIN = RESULTS / 'joint-mask04-12a-fixed-gain-phase.json'
GAIN = RESULTS / 'joint-mask04-12a-two-bit-gain1-fixture.json'
OUT = RESULTS / 'joint-mask04-12a-two-bit-package-mode-late48.json'
FACTOR = 1.0
LATE_EDGE = 48 * edge.loopback.VISITS_PER_SYMBOL * 4 + 1
FIXTURES = (
    (165, {'40': (0x7B, 0xC2, 0x19, 0xE4, 0x50, 0xAD, 0x36, 0x8F),
           '60': (0xD5, 0x06, 0xB8, 0x43, 0xFC, 0x21, 0x9A, 0x6E)}),
    (167, {'40': (0xA6, 0x3D, 0xF1, 0x08, 0xC9, 0x75, 0x2B, 0xE4),
           '60': (0x4F, 0xD0, 0x26, 0xBA, 0x81, 0x5C, 0xE7, 0x13)}),
)


def state_key(symbol):
    return sample_state(symbol, SELECTED) | \
        (((symbol['visits']['46']['row0'] >> 1) & 1) << 7) | \
        (((symbol['visits']['94']['y3f8'] >> 4) & 1) << 8)


def make_gain_fixture():
    base = json.loads(BASE_GAIN.read_text())
    fixture = dict(experiment='1.0x calibrated bus-0 receive gain fixture',
                   source_file=BASE_GAIN.name,
                   source_sha256=hashlib.sha256(BASE_GAIN.read_bytes()).hexdigest(),
                   gain_factor=FACTOR,
                   cases=[dict(selector=case['selector'], bus_cases=[
                       dict(bus_index=0, gain=next(bus['gain'] for bus in
                           case['bus_cases'] if bus['bus_index'] == 0))])
                       for case in base['cases']])
    GAIN.write_text(json.dumps(fixture, indent=2) + '\n')


def run(out=OUT, capture=True):
    make_gain_fixture()
    package = json.loads(PACKAGE.read_text())
    route_source = Path(gate_phase.__code__.co_filename)
    if (package['fixture']['observed_state_codes'] != 45 or
            package['source_sha256'][str(route_source.relative_to(HERE.parents[4]))] !=
            hashlib.sha256(route_source.read_bytes()).hexdigest()):
        raise ValueError('frozen package route changed')
    graph = json.loads(GRAPH.read_text())
    selected = graph['phase_graph']
    if (selected['state_codes'] != 45 or
            selected['directed_conflicts'] != 0 or
            selected['components'] != [45]):
        raise ValueError('frozen two-bit graph changed')
    phase_map = {int(code, 16): value for code, value in
                 selected['relative_phase'].items()}
    steps = graph['fixture']['phase_convention']
    inverse = {step: dibit for dibit, step in enumerate(steps)}
    rows = []
    expanded = []
    with tempfile.TemporaryDirectory() as temporary:
        exe, controller_sha = handoff.compiled_controller(temporary)
        original_execute = fresh.execute_case
        late_values = [0x81] * LATE_EDGE + [0xA1] * (edge.MODE_READS - LATE_EDGE)
        expected_values = [0x81] * edge.EDGE + [0xA1] * (edge.MODE_READS - edge.EDGE)
        def late_execute(mapping, base, pcm, mode_values):
            if mode_values != expected_values:
                raise ValueError('original mode-edge stimulus changed')
            return original_execute(mapping, base, pcm, late_values)
        def captured(symbol, variant, covers):
            key = state_key(symbol)
            return gate_phase(key), serial.Y3F8_CYCLE + 94 * serial.CYCLES_PER_VISIT, key
        for offset, payloads in FIXTURES:
            path = RESULTS / f'joint-mask04-12a-two-bit-package-mode-late48-{offset}.json'
            expanded.append(path)
            if capture:
                with patch.object(edge, 'CAPTURE_VISITS', (46, 47, 93, 94, 141)), \
                        patch.object(challenge, 'GAIN', GAIN), \
                        patch.object(challenge, 'FACTOR', FACTOR), \
                        patch.object(challenge, 'OFFSET', offset), \
                        patch.object(challenge, 'PAYLOADS', payloads), \
                        patch.object(fresh, 'execute_case', late_execute):
                    saved = challenge.run(out=path)
                saved['fixture']['assumed_mode'] = '81-to-A1 at D3EB read after symbol 48'
                saved['experiment'] = 'late-48 mode-edge real-PROM receive challenge'
                saved['limitations'].append(
                    'The D3EB mode edge was moved to symbol 48 by the source-hashed wrapper.')
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
                keys = [state_key(symbol) for symbol in symbols]
                unseen = sorted(set(keys) - set(phase_map))
                gate_wrong = [index for index in range(1, len(keys))
                              if inverse[(gate_phase(keys[index]) -
                                          gate_phase(keys[index - 1])) & 3]
                              != case['expected_dibits'][index]]
                payload = list(payloads[selector])
                offered = line_octets(payload, 5 if selector == '40' else 18)
                with patch.object(serial, 'captured_phase', captured):
                    score = serial.replay(dict(case, offered_line_bytes=[
                        f'{value:02X}' for value in offered]),
                        serial.VARIANTS['aligned'], None, inverse, exe)
                if gate_wrong != score['wrong_decision_indices']:
                    raise ValueError('gate and serial decisions differ')
                decoded = score['controller_decoded_bytes']
                byte_mismatches = [index for index, (actual, expected) in
                                   enumerate(zip(decoded, payload))
                                   if actual != expected]
                if len(decoded) != len(payload):
                    byte_mismatches.extend(range(min(len(decoded), len(payload)),
                                                 max(len(decoded), len(payload))))
                rows.append(dict(carrier_offset=offset, selector=selector,
                                 assumed_mode='81-to-A1 after symbol 48',
                                 payload=[f'{value:02X}' for value in payloads[selector]],
                                 gain_factor=FACTOR,
                                 tx_trace_digest=case['tx_trace_digest'],
                                 rx_trace_digest=case['rx_trace_digest'],
                                 pc_digest=case['pc_digest'],
                                 pcm_sha256=case['pcm_sha256'],
                                 clipped_samples=case['clipped_samples'],
                                 captured_keys=[f'{key:03X}' for key in keys],
                                 unseen_keys=[f'{key:03X}' for key in unseen],
                                 gate_wrong_indices=gate_wrong,
                                 old_veto_errors=len(case['corrected_wrong_indices']),
                                 decoded_wrong_indices=score['wrong_decision_indices'],
                                 recovered_matches_offered=score['recovered_matches_offered'],
                                 controller_decoded_bytes=score['controller_decoded_bytes'],
                                 controller_status_errors=score['controller_errors'],
                                 controller_matches_payload=decoded == payload,
                                 controller_byte_mismatch_indices=byte_mismatches,
                                 minimum_setup_cycles=score['minimum_setup_cycles']))
                print('package mode late48', offset, selector,
                      'unseen', rows[-1]['unseen_keys'],
                      'gate errors', len(gate_wrong),
                      'line exact', score['recovered_matches_offered'],
                      'payload exact', decoded == payload,
                      'USART status errors', score['controller_errors'], flush=True)
    paths = (Path(__file__), GRAPH, PACKAGE, route_source, BASE_GAIN, GAIN,
             Path(challenge.__file__), Path(edge.__file__), Path(fresh.__file__),
             *(path for path in expanded))
    report = dict(experiment='matched late-48 D3EB edge challenge of frozen photographed-package phase route',
                  fixture=dict(payloads={str(offset): {selector: [f'{value:02X}'
                      for value in payload] for selector, payload in payloads.items()}
                      for offset, payloads in FIXTURES},
                               carrier_offsets=[offset for offset, _ in FIXTURES],
                               gain_factor=FACTOR,
                               state='seven captured bits plus row-0 Y1 at visit 46 and 3F8 Y4 at visit 94',
                               phase_table_codes=len(phase_map),
                               assumed_mode='81-to-A1 at D3EB read after symbol 48',
                               mode_edge_read=LATE_EDGE,
                               controller_probe_sha256=controller_sha),
                  cases=rows,
                  limitations=[
                      'The package network and carrier-165/167 payloads were frozen before the late-48 mode-input runs.',
                      'The simulated gate network uses photographed package capacities but its nets are not identified Nokia wiring.',
                      'DAC/line, ADC, latch, controller mode, RxD/RxC and SYNDET connections remain assumed.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
