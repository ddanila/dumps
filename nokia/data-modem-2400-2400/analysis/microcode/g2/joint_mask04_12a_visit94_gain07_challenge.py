"""Challenge the frozen visit-94 gate at a new carrier and lower gain."""

import hashlib
import json
import tempfile
from collections import Counter
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
BASE_GAIN = RESULTS / 'joint-mask04-12a-fixed-gain-phase.json'
LOW_GAIN = RESULTS / 'joint-mask04-12a-visit94-gain07-fixture.json'
GAIN08 = RESULTS / 'joint-mask04-12a-mode-phase133-lowgain-fixture.json'
GRAPH = RESULTS / 'joint-mask04-12a-mode-phase131-gain-graph-audit.json'
OUT = RESULTS / 'joint-mask04-12a-visit94-gain07-challenge.json'
OFFSET = 141
PAYLOADS = {
    '40': (0xD8, 0x35, 0xA1, 0x6C, 0xF2, 0x09, 0x47, 0xBE),
    '60': (0x2C, 0xE7, 0x50, 0x9B, 0x14, 0xF8, 0x63, 0xA5),
}


def make_gain_fixture():
    baseline = json.loads(BASE_GAIN.read_text())
    cases = []
    for case in baseline['cases']:
        bus = next(row for row in case['bus_cases'] if row['bus_index'] == 0)
        cases.append(dict(selector=case['selector'], bus_cases=[
            dict(bus_index=0, gain=bus['gain'] * 0.7)]))
    fixture = dict(experiment='frozen 0.7x bus-0 gain challenge fixture',
                   source_file=BASE_GAIN.name,
                   source_sha256=hashlib.sha256(BASE_GAIN.read_bytes()).hexdigest(),
                   gain_factor=0.7, cases=cases)
    LOW_GAIN.write_text(json.dumps(fixture, indent=2) + '\n')
    return fixture


def run(out=OUT):
    make_gain_fixture()
    known = {int(code, 16) for code in json.loads(GRAPH.read_text())[
        'combined_mode81_phase_labels']}
    model = json.loads(gate.MODEL.read_text())
    inverse = {step: dibit for dibit, step in
               enumerate(model['fixture']['phase_convention'])}
    rows = []
    expanded_paths = []
    with tempfile.TemporaryDirectory() as temporary:
        exe, controller_sha = handoff.compiled_controller(temporary)
        def captured(symbol, variant, covers):
            return gate.candidate_phase(symbol), gate.READY, sample_state(symbol, SELECTED)
        for factor, gain in ((0.7, LOW_GAIN), (0.8, GAIN08)):
            path = RESULTS / f'joint-mask04-12a-visit94-gain07-challenge-{factor}.json'
            expanded_paths.append(path)
            with patch.object(edge, 'CAPTURE_VISITS', (46, 47, 93, 94, 141)), \
                    patch.object(challenge, 'GAIN', gain), \
                    patch.object(challenge, 'FACTOR', factor), \
                    patch.object(challenge, 'OFFSET', OFFSET), \
                    patch.object(challenge, 'PAYLOADS', PAYLOADS):
                saved = challenge.run(out=path)
            if saved['fixture']['controller_probe_sha256'] != controller_sha:
                raise ValueError('controller probe changed')
            with patch.object(serial, 'captured_phase', captured):
                for case in saved['cases']:
                    selector = case['selector']
                    payload = list(PAYLOADS[selector])
                    offered = line_octets(payload, 5 if selector == '40' else 18)
                    score = serial.replay(dict(case, offered_line_bytes=[
                        f'{value:02X}' for value in offered]),
                        serial.VARIANTS['aligned'], None, inverse, exe)
                    states = [sample_state(symbol, SELECTED)
                              for symbol in case['multi_visit_symbols']]
                    active = [index for index, symbol in
                              enumerate(case['multi_visit_symbols'])
                              if corrected_phase(states[index], 1) & 1 and
                              symbol['visits']['94']['y3f8'] & 0x40]
                    rows.append(dict(gain_factor=factor, selector=selector,
                                     payload=[f'{value:02X}' for value in payload],
                                     tx_trace_digest=case['tx_trace_digest'],
                                     rx_trace_digest=case['rx_trace_digest'],
                                     pc_digest=case['pc_digest'],
                                     pcm_sha256=case['pcm_sha256'],
                                     clipped_samples=case['clipped_samples'],
                                     states={f'{state:02X}': count for state, count
                                             in sorted(Counter(states).items())},
                                     unseen_states=sorted(f'{state:02X}'
                                                          for state in set(states)-known),
                                     active_symbols=active,
                                     active_states=[f'{states[i]:02X}' for i in active],
                                     old_veto_wrong_indices=case['corrected_wrong_indices'],
                                     candidate_wrong_indices=score['wrong_decision_indices'],
                                     recovered_matches_offered=score['recovered_matches_offered'],
                                     controller_decoded_bytes=score['controller_decoded_bytes'],
                                     controller_errors=score['controller_errors'],
                                     controller_overruns=score['controller_overruns'],
                                     minimum_setup_cycles=score['minimum_setup_cycles']))
                    print('gain07 challenge', factor, selector,
                          'unseen', rows[-1]['unseen_states'],
                          'active', rows[-1]['active_states'],
                          'old/new', len(case['corrected_wrong_indices']),
                          len(score['wrong_decision_indices']), flush=True)
    for selector in PAYLOADS:
        pair = [row for row in rows if row['selector'] == selector]
        if (len(pair) != 2 or pair[0]['tx_trace_digest'] != pair[1]['tx_trace_digest'] or
                pair[0]['pc_digest'] != pair[1]['pc_digest'] or
                pair[0]['pcm_sha256'] == pair[1]['pcm_sha256']):
            raise ValueError(('matched gain control changed', selector))
    paths = (Path(__file__), BASE_GAIN, LOW_GAIN, GAIN08, GRAPH,
             gate.MODEL, Path(gate.__file__), Path(challenge.__file__),
             Path(edge.__file__), *expanded_paths)
    report = dict(experiment='frozen visit-94 gate at new carrier 141, matched 0.7x/0.8x gains',
                  fixture=dict(carrier_offset=OFFSET, gains=[0.7, 0.8],
                               payloads={selector: [f'{value:02X}' for value in payload]
                                         for selector, payload in PAYLOADS.items()},
                               controller_probe_sha256=controller_sha),
                  cases=rows,
                  limitations=[
                      'Both payloads and carrier 141 are new; the phase gate and sample timing are unchanged.',
                      'The gain fixture changes only modeled ADC amplitude; the analog line and ADC connections are assumed.',
                      'A positive modeled serial handoff would not establish physical latch, phase-gate or USART nets.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
