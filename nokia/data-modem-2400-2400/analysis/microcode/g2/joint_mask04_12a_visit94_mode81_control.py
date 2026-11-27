"""Hold D3EB at 81 on the same carrier-141, 0.7x receive waveform."""

import hashlib
import json
import tempfile
from collections import Counter
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_mode_fresh_phase120 as fresh
import joint_mask04_12a_phasebit0_veto_lowgain133_challenge as challenge
import joint_mask04_12a_row_mode_edge as edge
import joint_mask04_12a_row0_serial_timing as serial
import joint_mask04_12a_visit94_phase_gate as gate
import joint_mask04_12a_visit94_gain07_challenge as gain07
import joint_mask04_buffered_serial_handoff as handoff
from joint_mask04_12a_multivisit_phase_screen import SELECTED, sample_state
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
EDGE = RESULTS / 'joint-mask04-12a-visit94-gain07-challenge-0.7.json'
EDGE_SUMMARY = RESULTS / 'joint-mask04-12a-visit94-gain07-challenge.json'
OUT = RESULTS / 'joint-mask04-12a-visit94-mode81-control.json'
CAPTURE = RESULTS / 'joint-mask04-12a-visit94-mode81-control-expanded.json'


def run(out=OUT):
    original = fresh.execute_case
    def held(mapping, base, pcm, mode_values):
        if len(mode_values) != edge.MODE_READS or set(mode_values) != {0x81, 0xA1}:
            raise ValueError('expected original 81-to-A1 mode edge')
        return original(mapping, base, pcm, [0x81] * len(mode_values))
    with patch.object(edge, 'CAPTURE_VISITS', (46, 47, 93, 94, 141)), \
            patch.object(fresh, 'execute_case', held), \
            patch.object(challenge, 'GAIN', gain07.LOW_GAIN), \
            patch.object(challenge, 'FACTOR', 0.7), \
            patch.object(challenge, 'OFFSET', gain07.OFFSET), \
            patch.object(challenge, 'PAYLOADS', gain07.PAYLOADS):
        saved = challenge.run(out=CAPTURE)
    edge_cases = {case['selector']: case for case in json.loads(EDGE.read_text())['cases']}
    edge_scores = {case['selector']: case for case in json.loads(
        EDGE_SUMMARY.read_text())['cases'] if case['gain_factor'] == 0.7}
    model = json.loads(gate.MODEL.read_text())
    inverse = {step: dibit for dibit, step in
               enumerate(model['fixture']['phase_convention'])}
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        exe, controller_sha = handoff.compiled_controller(temporary)
        if saved['fixture']['controller_probe_sha256'] != controller_sha:
            raise ValueError('controller probe changed')
        def captured(symbol, variant, covers):
            return gate.candidate_phase(symbol), gate.READY, sample_state(symbol, SELECTED)
        with patch.object(serial, 'captured_phase', captured):
            for case in saved['cases']:
                selector = case['selector']
                prior = edge_cases[selector]
                prior_score = edge_scores[selector]
                for key in ('tx_trace_digest', 'raw_sha256', 'pcm_sha256'):
                    if case[key] != prior[key]:
                        raise ValueError(('held mode changed waveform', selector, key))
                payload = list(gain07.PAYLOADS[selector])
                offered = line_octets(payload, 5 if selector == '40' else 18)
                score = serial.replay(dict(case, offered_line_bytes=[
                    f'{value:02X}' for value in offered]),
                    serial.VARIANTS['aligned'], None, inverse, exe)
                states = [sample_state(symbol, SELECTED)
                          for symbol in case['multi_visit_symbols']]
                zero_d = [symbol for symbol, state in
                          zip(case['multi_visit_symbols'], states) if state == 0x0D]
                cases.append(dict(selector=selector,
                                  tx_trace_digest=case['tx_trace_digest'],
                                  pcm_sha256=case['pcm_sha256'],
                                  rx_trace_digest=case['rx_trace_digest'],
                                  edge_rx_trace_digest=prior['rx_trace_digest'],
                                  pc_digest=case['pc_digest'],
                                  edge_pc_digest=prior['pc_digest'],
                                  states={f'{state:02X}': count for state, count
                                          in sorted(Counter(states).items())},
                                  state_0d_count=len(zero_d),
                                  state_0d_later_bit_counts={str(bit): count
                                      for bit, count in sorted(Counter(
                                          (symbol['visits']['94']['y3f8'] >> 6) & 1
                                          for symbol in zero_d).items())},
                                  edge_candidate_errors=len(prior_score['candidate_wrong_indices']),
                                  held_candidate_wrong_indices=score['wrong_decision_indices'],
                                  recovered_matches_offered=score['recovered_matches_offered'],
                                  controller_decoded_bytes=score['controller_decoded_bytes'],
                                  controller_errors=score['controller_errors'],
                                  clipped_samples=case['clipped_samples']))
                print('held81', selector, 'states', len(set(states)),
                      '0D', len(zero_d), 'edge/held errors',
                      len(prior_score['candidate_wrong_indices']),
                      len(score['wrong_decision_indices']), flush=True)
    paths = (Path(__file__), EDGE, EDGE_SUMMARY, CAPTURE, gain07.LOW_GAIN,
             Path(gain07.__file__), Path(fresh.__file__),
             Path(challenge.__file__), Path(edge.__file__),
             Path(gate.__file__))
    report = dict(experiment='held-81 mode control on carrier-141 0.7x waveform',
                  fixture=dict(carrier_offset=gain07.OFFSET, gain_factor=0.7,
                               selectors=['40', '60'],
                               controller_probe_sha256=controller_sha,
                               input_mode='81 held instead of 81-to-A1 at D3EB'),
                  cases=cases,
                  limitations=[
                      'The D3EB input is a hypothesized frame-byte connection, not a traced physical mode wire.',
                      'Only the held versus switched mode input changes; the candidate phase gate remains frozen.',
                      'This test can distinguish the modeled mode fixture but not prove its physical source.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
