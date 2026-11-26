"""Join real-PROM phase graphs across the matched receive gain sweep."""

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
ADC = RESULTS / 'joint-mask04-12a-mode-phase131-adc-range.json'
RUNS = (
    (1.0, RESULTS / 'joint-mask04-12a-mode-phase131-baseline-control.json'),
    (1.125, RESULTS / 'joint-mask04-12a-mode-phase131-intermediate-gain.json'),
    (None, RESULTS / 'joint-mask04-12a-mode-phase131-gain-boundary.json'),
    (1.25, RESULTS / 'joint-mask04-12a-mode-phase131-gain-challenge.json'),
)
OUT = RESULTS / 'joint-mask04-12a-mode-phase131-gain-graph-audit.json'


def run(out=OUT):
    mode0 = json.loads(MODE0.read_text())
    model = json.loads(MODEL.read_text())
    phase125 = json.loads(PHASE125.read_text())
    adc = json.loads(ADC.read_text())
    steps = model['fixture']['phase_convention']
    known = {int(code, 16): value for code, value in
             model['trained_state_phase'].items()}
    if {case['inferred_phase'] for case in phase125['cases']} != {1}:
        raise ValueError('prior 3D anchor changed')
    known[0x3D] = 1
    edges = collections.defaultdict(list)
    cases = []
    for declared_factor, path in RUNS:
        saved = json.loads(path.read_text())
        for case in saved['cases']:
            factor = case.get('factor', declared_factor)
            if factor is None:
                raise ValueError('gain factor missing')
            states = [int(code, 16) for code in case['observed_states']]
            expected = case['expected_dibits']
            for index in range(1, len(states)):
                step = steps[expected[index]]
                edges[states[index - 1]].append((states[index], step))
                edges[states[index]].append((states[index - 1], -step))
            pcm_fixture = next(row for row in next(
                entry for entry in adc['cases']
                if entry['selector'] == case['selector'])['factors']
                if row['factor'] == factor) if factor in (1.0, 1.125, 1.25) else None
            clipped = (pcm_fixture['clipped_samples'] if pcm_fixture else
                       case['clipped_samples'])
            if (len(states) != 65 or len(expected) != 65 or
                    (factor in (1.0, 1.125, 1.15) and clipped != 0)):
                raise ValueError(('gain sweep fixture changed', factor,
                                  case['selector']))
            wrong = (case.get('package_circuit_wrong_indices') or [])
            cases.append(dict(selector=case['selector'], factor=factor,
                              states=len(set(states)), clipped_samples=clipped,
                              reference_errors=len(case['reference_wrong_indices']),
                              package_errors=len(wrong),
                              wrong_indices=wrong,
                              state_sequence=states))
    phases = dict(known)
    pending = collections.deque(known)
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
    if conflicts or set(edges) - set(phases):
        raise ValueError(('combined graph conflict or disconnected', conflicts))
    new = {code: value for code, value in phases.items() if code not in known}
    expected_new = {0x02: 3, 0x2F: 0, 0x42: 3, 0x48: 2,
                    0x4C: 1, 0x5D: 1, 0x6E: 0}
    if new != expected_new:
        raise ValueError(('new-state labels changed', new))
    predicted_errors = {code: (phases[code], circuit(code, 1))
                        for code in new if phases[code] != circuit(code, 1)}
    if predicted_errors != {0x2F: (0, 1), 0x48: (2, 3)}:
        raise ValueError(('frozen circuit mismatch changed', predicted_errors))
    for case in cases:
        states = case.pop('state_sequence')
        crossings = [index for index in range(1, len(states))
                     if ((states[index - 1] in predicted_errors) !=
                         (states[index] in predicted_errors))]
        if case['wrong_indices'] != crossings:
            raise ValueError(('wrong decisions not explained', case))
        case['wrong_indices_explained_by_2f_48'] = True
        case.pop('wrong_indices')
    if [(case['factor'], case['selector'], case['package_errors'])
        for case in cases] != [
        (1.0, '40', 0), (1.0, '60', 0),
        (1.125, '40', 0), (1.125, '60', 0),
        (1.15, '40', 12), (1.15, '60', 11),
        (1.175, '40', 12), (1.175, '60', 11),
        (1.25, '40', 16), (1.25, '60', 10)]:
        raise ValueError('gain sweep case coverage changed')
    rows = ([(int(code, 16), value) for code, value in
             mode0['state_phase'].items()] +
            [(code | 128, value) for code, value in phases.items()])
    capacity = {str(bit): {relation: fit(rows, bit, target)['fit'] is not None
                           for relation, target in (('direct', 0),
                                                    ('output_inverted', 1))}
                for bit in (0, 1)}
    if capacity != {'0': {'direct': False, 'output_inverted': False},
                    '1': {'direct': True, 'output_inverted': True}}:
        raise ValueError(('single U15 capacity changed', capacity))
    paths = (Path(__file__), MODE0, MODEL, PHASE125, ADC,
             *(path for _, path in RUNS),
             HERE / 'photo_u15_phase_gate_capacity.py',
             HERE / 'photo_u15_u19_u21_phase_route.py')
    report = dict(experiment='joined phase-131 real-PROM gain graph and circuit mismatch',
                  cases=cases,
                  combined_mode81_phase_labels={f'{code:02X}': value for
                                                code, value in sorted(phases.items())},
                  new_state_labels={f'{code:02X}': value for
                                    code, value in sorted(new.items())},
                  graph_conflicts=conflicts,
                  frozen_circuit_wrong_state_phases={
                      f'{code:02X}': dict(expected=expected, circuit=actual)
                      for code, (expected, actual) in predicted_errors.items()},
                  single_u15_direct_input_capacity=capacity,
                  limitations=[
                      'Phase labels are relative to the prior mode-81 anchor and expected offered dibits under the assumed line; no physical phase bus has been traced.',
                      'The graph gives a consistent state-phase explanation of these saved streams, not a guarantee across arbitrary gain or carrier phase.',
                      'The gate-capacity test assumes only direct seven-bit state plus mode inputs; additional preprocessing or another capture point can alter it.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print(result['new_state_labels'])
    print(result['frozen_circuit_wrong_state_phases'])
