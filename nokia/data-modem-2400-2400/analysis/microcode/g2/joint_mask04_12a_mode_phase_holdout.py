"""Freeze a call-trained mode-aware phase gate, then challenge the answer side."""

import hashlib
import json
import tempfile
from pathlib import Path

import joint_mask04_12a_analog_holdout as holdout
import joint_mask04_12a_buffered_line as line
import joint_mask04_12a_frozen_sixth_new_payloads as frozen
import joint_mask04_buffered_serial_handoff as handoff
from joint_mask04_12a_multivisit_phase_screen import SELECTED, sample_state, solve
from joint_mask04_12a_row0_boolean import minimize, phase
from joint_mask04_12a_row0_serial_timing import covers_from_model, replay, VARIANTS
from joint_mask04_12a_row_mode_edge import EDGE, MODE_READS, execute_case
from joint_mask04_tx_12a_delayed_latch import capturing_execute
from photo_dac_bus_permutations import mapped_codes
from photo_joint_line_filter_screen import SILENCE_END, TONE_END, bandpass
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'results/joint-mask04-12a-row0-boolean-phase112.json'
CALL = HERE / 'results/joint-mask04-12a-row-mode-edge.json'
OLD_GATE = HERE / 'results/joint-mask04-12a-row0-boolean-twentytwo.json'
FIXED = HERE / 'results/joint-mask04-12a-fixed-gain-phase.json'
OUT = HERE / 'results/joint-mask04-12a-mode-phase-holdout.json'


def train(call, source, old_model):
    old = next(case for case in source['cases'] if case['selector'] == '40')
    cases = [dict(multi_visit_symbols=old['multi_visit_symbols'],
                  expected_dibits=old['expected_dibits'])]
    cases.extend(dict(multi_visit_symbols=case['states'],
                      expected_dibits=old['expected_dibits'])
                 for case in call['cases'])
    convention = tuple(old_model['fixture']['phase_convention'])
    potentials, conflicts, components = solve(cases, SELECTED, convention)
    if conflicts or len(components) != 1 or len(potentials) != 8:
        raise ValueError('call-side mode phase graph changed')
    old_covers = covers_from_model(old_model)
    baseline = {sample_state(symbol, SELECTED)
                for symbol in old['multi_visit_symbols']}
    anchor = min(baseline)
    offset = (phase(anchor, old_covers) - potentials[anchor]) & 3
    anchored = {state: (value + offset) & 3
                for state, value in potentials.items()}
    if any(anchored[state] != phase(state, old_covers) for state in baseline):
        raise ValueError('old baseline labels cannot anchor new phase graph')
    optimized = [minimize(anchored, bit) for bit in (0, 1)]
    covers = [row[2] for row in optimized]
    if any(phase(state, covers) != value for state, value in anchored.items()):
        raise ValueError('Boolean cover changed a trained state')
    return anchored, covers, optimized, baseline, convention


def answer_pcm(old, fixed, mapping, base):
    payload = tuple(int(value, 16) for value in old['payload'])
    tx, raw, expected = line.transmitter(
        capturing_execute((frozen.PHASE_VISIT, 112)), mapping, base,
        line_octets(payload, 18))
    if (tx['trace_digest'] != old['tx_trace_digest'] or
            hashlib.sha256(bytes(raw)).hexdigest() != old['raw_sha256'] or
            expected != old['expected_dibits']):
        raise ValueError('answer transmitter changed')
    gain = next(bus for bus in next(case for case in fixed['cases']
                    if case['selector'] == '60')['bus_cases']
                if bus['bus_index'] == 0)['gain']
    codes = mapped_codes(raw, holdout.BUSES[0])
    gated = codes[:TONE_END] + [128] * (SILENCE_END - TONE_END) + codes[SILENCE_END:]
    wave = bandpass([value - 128 for value in gated], 0.5)
    selected = wave[SILENCE_END + 6:SILENCE_END + 6 + line.RX_SYMBOLS * 8]
    pcm = [max(-127, min(127, round(value * gain))) for value in selected]
    if hashlib.sha256(bytes(value + 127 for value in pcm)).hexdigest() != old['pcm_sha256']:
        raise ValueError('answer line PCM changed')
    return pcm


def run(out=OUT):
    source = json.loads(SOURCE.read_text())
    call = json.loads(CALL.read_text())
    old_model = json.loads(OLD_GATE.read_text())
    anchored, covers, optimized, baseline, convention = train(
        call, source, old_model)
    inverse = {step: dibit for dibit, step in enumerate(convention)}
    old = next(case for case in source['cases'] if case['selector'] == '60')
    mapping = line.candidate(line.mapping_with_upper_source(0, '17.6'),
                             line.mapped(line.MAPPINGS['q3']), 4)
    _, base = line.fixture()
    pcm = answer_pcm(old, json.loads(FIXED.read_text()), mapping, base)
    scenarios = {
        'held_81': [0x81] * MODE_READS,
        'edge_81_A1': [0x81] * EDGE + [0xA1] * (MODE_READS - EDGE),
    }
    cases = []
    pc_digests = []
    with tempfile.TemporaryDirectory() as temporary:
        exe, controller_sha = handoff.compiled_controller(temporary)
        for name, values in scenarios.items():
            rx, pc_digest, symbols, gate_edges = execute_case(mapping, base, pcm, values)
            pc_digests.append(pc_digest)
            states = [sample_state(symbols[symbol], SELECTED)
                      for symbol in range(handoff.RX_SYMBOLS)]
            compared = dict(multi_visit_symbols=[symbols[s] for s in
                                                 range(handoff.RX_SYMBOLS)],
                            expected_dibits=old['expected_dibits'],
                            selector='60', payload=old['payload'],
                            offered_line_bytes=old['offered_line_bytes'])
            score = replay(compared, VARIANTS['aligned'], covers, inverse, exe)
            old_score = replay(compared, VARIANTS['aligned'],
                               covers_from_model(old_model), inverse, exe)
            cases.append(dict(mode=name, rx_trace_digest=rx['trace_digest'],
                              pc_digest=pc_digest, gate_edges=gate_edges,
                              observed_states=sorted(f'{state:02X}' for state in set(states)),
                              unseen_states=sorted(f'{state:02X}' for state in
                                                   set(states) - set(anchored)),
                              frozen_gate_wrong_indices=score['wrong_decision_indices'],
                              prior_gate_wrong_indices=old_score['wrong_decision_indices'],
                              recovered_matches_offered=score['recovered_matches_offered'],
                              controller_decoded_bytes=score['controller_decoded_bytes'],
                              controller_errors=score['controller_errors'],
                              minimum_setup_cycles=score['minimum_setup_cycles']))
            print('mode holdout', name,
                  len(score['wrong_decision_indices']),
                  len(old_score['wrong_decision_indices']), flush=True)
    if len(set(pc_digests)) != 1:
        raise ValueError('answer mode edge changed PC path')
    paths = (Path(__file__), SOURCE, CALL, OLD_GATE, FIXED,
             HERE / 'joint_mask04_12a_row_mode_edge.py')
    report = dict(experiment='call-frozen mode-aware phase gates on answer-side full-PROM receive',
                  fixture=dict(development='call 01, held 81, 81-to-A1 edge at offset 112',
                               holdout='answer held 81 and 81-to-A1 on untouched payload',
                               assumed_D3EB_mode_edge=EDGE,
                               controller_probe_sha256=controller_sha,
                               phase_convention=convention),
                  trained_state_phase={f'{state:02X}': value
                                       for state, value in sorted(anchored.items())},
                  baseline_states=[f'{state:02X}' for state in sorted(baseline)],
                  phase_bits=[dict(bit=bit, product_terms=optimized[bit][0],
                                   literals=optimized[bit][1],
                                   cubes=[''.join('*' if x < 0 else str(x) for x in cube)
                                          for cube in covers[bit]])
                              for bit in (0, 1)],
                  cases=cases,
                  limitations=[
                      'Call-side mode states and their known dibits are development data; only answer-side streams are holdouts.',
                      'The frame byte to D3EB route, U24 reset and all latch/USART nets remain assumptions.',
                      'Unseen states receive Boolean extrapolations; the gates are not identified DSC instructions.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
