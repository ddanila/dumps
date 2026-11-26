"""Audit matched-gain control, new-state graph, and frozen circuit failure."""

import collections
import hashlib
import json
from pathlib import Path

from photo_u15_phase_gate_capacity import fit
from photo_u15_u19_u21_phase_route import circuit

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
MODE0 = RESULTS / 'joint-mask04-12a-row0-boolean-twentytwo.json'
MODEL = RESULTS / 'joint-mask04-12a-mode-phase-twelve.json'
PHASE125 = RESULTS / 'joint-mask04-12a-mode-phase125-audit.json'
BASELINE = RESULTS / 'joint-mask04-12a-mode-phase131-baseline-control.json'
GAIN = RESULTS / 'joint-mask04-12a-mode-phase131-gain-challenge.json'
OUT = RESULTS / 'joint-mask04-12a-mode-phase131-gain-audit.json'


def relative_graph(cases, steps):
    edges = collections.defaultdict(list)
    for case in cases:
        states = [int(code, 16) for code in case['observed_states']]
        for index in range(1, len(states)):
            step = steps[case['expected_dibits'][index]]
            edges[states[index - 1]].append((states[index], step))
            edges[states[index]].append((states[index - 1], -step))
    start = 0x48
    phases = {start: 0}
    pending = collections.deque([start])
    conflicts = 0
    while pending:
        state = pending.popleft()
        for neighbor, step in edges[state]:
            expected = (phases[state] + step) & 3
            if neighbor not in phases:
                phases[neighbor] = expected
                pending.append(neighbor)
            elif phases[neighbor] != expected:
                conflicts += 1
    if set(phases) != set(edges):
        raise ValueError('new-state graph is disconnected')
    return phases, conflicts


def run(out=OUT):
    mode0 = json.loads(MODE0.read_text())
    model = json.loads(MODEL.read_text())
    phase125 = json.loads(PHASE125.read_text())
    baseline = json.loads(BASELINE.read_text())
    gain = json.loads(GAIN.read_text())
    if (phase125['cases'][0]['inferred_phase'] != 1 or
            phase125['cases'][1]['inferred_phase'] != 1 or
            baseline['fixture']['gain_factor'] != 1.0 or
            gain['fixture']['gain_factor'] != 1.25 or
            baseline['fixture']['R1_offset'] != 131 or
            gain['fixture']['R1_offset'] != 131):
        raise ValueError('matched fixture changed')
    steps = model['fixture']['phase_convention']
    labels = {int(code, 16): value for code, value in
              model['trained_state_phase'].items()}
    labels[0x3D] = 1
    cases = []
    all_4c_anchors = []
    for original, boosted in zip(baseline['cases'], gain['cases']):
        if original['selector'] != boosted['selector'] or original['payload'] != boosted['payload']:
            raise ValueError('paired selector/payload changed')
        states = [int(code, 16) for code in original['observed_states']]
        anchors = []
        for index, state in enumerate(states):
            if state != 0x4C:
                continue
            if index and states[index - 1] in labels:
                anchors.append((labels[states[index - 1]] +
                                steps[original['expected_dibits'][index]]) & 3)
            if index + 1 < len(states) and states[index + 1] in labels:
                anchors.append((labels[states[index + 1]] -
                                steps[original['expected_dibits'][index + 1]]) & 3)
        all_4c_anchors.extend(anchors)
        if (not anchors or set(anchors) != {1} or circuit(0x4C, 1) != 1 or
                original['package_circuit_unseen_states'] != ['4C'] or
                boosted['package_circuit_unseen_states'] != ['2F', '42', '48', '5D'] or
                original['package_circuit_wrong_indices'] or
                boosted['package_circuit_serial']['recovered_matches_offered'] or
                not boosted['package_circuit_wrong_indices'] or
                original['tx_trace_digest'] != boosted['tx_trace_digest'] or
                original['raw_sha256'] != boosted['raw_sha256'] or
                original['pcm_sha256'] == boosted['pcm_sha256'] or
                original['pc_digest'] != boosted['pc_digest']):
            raise ValueError(('matched gain control changed', original['selector']))
        cases.append(dict(selector=original['selector'],
                          same_tx_and_raw=True, same_pc_path=True,
                          different_pcm=True,
                          baseline_new_state='4C',
                          baseline_4c_anchor_constraints=len(anchors),
                          baseline_reference_errors=len(original['reference_wrong_indices']),
                          baseline_old_cover_errors=len(original['frozen_gate_wrong_indices']),
                          baseline_package_errors=0,
                          gain_new_states=boosted['package_circuit_unseen_states'],
                          gain_reference_errors=len(boosted['reference_wrong_indices']),
                          gain_old_cover_errors=len(boosted['frozen_gate_wrong_indices']),
                          gain_package_errors=len(boosted['package_circuit_wrong_indices']),
                          gain_exact_line_bytes=False))
    if len(cases) != 2 or [case['gain_package_errors'] for case in cases] != [16, 10]:
        raise ValueError('gain failure count changed')
    phases, conflicts = relative_graph(gain['cases'], steps)
    if conflicts or phases != {0x48: 0, 0x42: 1, 0x5D: 3, 0x2F: 2}:
        raise ValueError(('new-state graph changed', phases, conflicts))
    predicted = {code: circuit(code, 1) for code in phases}
    normalized_predicted = {code: (value - predicted[0x48]) & 3
                            for code, value in predicted.items()}
    if normalized_predicted == phases:
        raise ValueError('frozen circuit unexpectedly fits new relative graph')
    rows = ([(int(code, 16), value) for code, value in mode0['state_phase'].items()] +
            [(code | 128, value) for code, value in labels.items()] +
            [(0x4C | 128, 1)])
    capacity = []
    for rotation in range(4):
        examples = rows + [(code | 128, (value + rotation) & 3)
                           for code, value in phases.items()]
        direct = {str(bit): fit(examples, bit, 0)['fit'] is not None
                  for bit in (0, 1)}
        inverted = {str(bit): fit(examples, bit, 1)['fit'] is not None
                    for bit in (0, 1)}
        capacity.append(dict(relative_rotation=rotation,
                             direct_single_u15=direct,
                             inverted_single_u15=inverted))
    if any(row['direct_single_u15']['0'] or
           row['inverted_single_u15']['0'] for row in capacity):
        raise ValueError('U15 direct-input capacity classification changed')
    paths = (Path(__file__), MODE0, MODEL, PHASE125, BASELINE, GAIN,
             HERE / 'photo_u15_phase_gate_capacity.py',
             HERE / 'photo_u15_u19_u21_phase_route.py')
    report = dict(experiment='matched-gain new-state phase-131 control and graph',
                  cases=cases,
                  baseline_4c_phase=1,
                  baseline_4c_anchor_constraints=len(all_4c_anchors),
                  gain_relative_graph=dict(anchor='48=0, arbitrary global rotation',
                                           labels={f'{code:02X}': value for code, value
                                                   in phases.items()}, conflicts=conflicts),
                  frozen_circuit_relative_labels={f'{code:02X}': value
                                                  for code, value in
                                                  normalized_predicted.items()},
                  direct_u15_capacity_by_rotation=capacity,
                  limitations=[
                      'The four boosted-gain states form a disjoint alphabet, so their absolute phase cannot be anchored to the earlier states without another observation.',
                      'A conflict-free relative graph shows a state-phase readout is possible under these input symbols, but the frozen package circuit fails it.',
                      'The single-U15 screen excludes only direct eight-input realizations; preprocessing and other gates remain possible.',
                      'Neither gain setting identifies the physical DAC/ADC, mode, logic or serial connections.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    summary = run()
    print(summary['cases'])
    print(summary['gain_relative_graph'])
