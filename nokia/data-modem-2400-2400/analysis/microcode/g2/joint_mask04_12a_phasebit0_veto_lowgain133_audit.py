"""Audit the unseen 1D failure of the frozen receive veto."""

import hashlib
import itertools
import json
from pathlib import Path

from joint_mask04_12a_multivisit_phase_screen import SELECTED, sample_state
from joint_mask04_12a_phasebit0_veto import corrected_phase
from joint_mask04_12a_row0_boolean import phase
from joint_mask04_12a_row0_serial_timing import covers_from_model
from photo_u15_u19_u21_phase_route import circuit

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
RUN = RESULTS / 'joint-mask04-12a-phasebit0-veto-lowgain133-challenge.json'
MODE0 = RESULTS / 'joint-mask04-12a-row0-boolean-twentytwo.json'
MODEL = RESULTS / 'joint-mask04-12a-mode-phase-twelve.json'
GRAPH = RESULTS / 'joint-mask04-12a-mode-phase131-gain-graph-audit.json'
OUT = RESULTS / 'joint-mask04-12a-phasebit0-veto-lowgain133-audit.json'


def isolating_cubes(rows, target):
    """Find the shortest direct-input cubes that could clear target P0."""
    off = [(state, mode) for state, mode, _ in rows
           if corrected_phase(state, mode) & 1]
    for width in range(1, 9):
        found = []
        for positions in itertools.combinations(range(8), width):
            for bits in itertools.product((0, 1), repeat=width):
                def hit(state, mode):
                    value = state | (mode << 7)
                    return all(((value >> position) & 1) == bit
                               for position, bit in zip(positions, bits))
                if not hit(target, 1) or any(hit(*pair) for pair in off):
                    continue
                found.append(''.join(
                    str(bits[positions.index(index)]) if index in positions else '*'
                    for index in range(8)))
        if found:
            return width, sorted(found)
    return None, []


def run(out=OUT):
    saved = json.loads(RUN.read_text())
    mode0 = json.loads(MODE0.read_text())['state_phase']
    model = json.loads(MODEL.read_text())
    graph = json.loads(GRAPH.read_text())
    labels = {int(code, 16): value for code, value in
              graph['combined_mode81_phase_labels'].items()}
    steps = model['fixture']['phase_convention']
    inverse = {step: dibit for dibit, step in enumerate(steps)}
    covers = covers_from_model(model)
    cases = []
    all_constraints = []
    for case in saved['cases']:
        states = [sample_state(symbol, SELECTED)
                  for symbol in case['multi_visit_symbols']]
        expected = case['expected_dibits']
        phase_values = [corrected_phase(state, 1) for state in states]
        wrong = [index for index in range(1, len(states))
                 if inverse[(phase_values[index] - phase_values[index - 1]) & 3]
                 != expected[index]]
        crossings = [index for index in range(1, len(states))
                     if (states[index - 1] == 0x1D) != (states[index] == 0x1D)]
        constraints = []
        for index, state in enumerate(states):
            if state != 0x1D:
                continue
            if index and states[index - 1] in labels:
                constraints.append((labels[states[index - 1]] +
                                    steps[expected[index]]) & 3)
            if index + 1 < len(states) and states[index + 1] in labels:
                constraints.append((labels[states[index + 1]] -
                                    steps[expected[index + 1]]) & 3)
        all_constraints.extend(constraints)
        serial = case['corrected_serial']
        payload = [int(value, 16) for value in case['payload']]
        if (len(states) != 65 or set(states) - set(labels) != {0x1D} or
                not constraints or set(constraints) != {0} or
                wrong != crossings or wrong != case['corrected_wrong_indices'] or
                case['clipped_samples'] != 0 or
                case['frozen_gate_wrong_indices'] or
                serial['recovered_matches_offered'] or
                serial['controller_decoded_bytes'] == payload or
                serial['controller_errors'] or serial['controller_overruns']):
            raise ValueError(('low-gain unseen-state audit failed',
                              case['selector']))
        cases.append(dict(selector=case['selector'], new_state='1D',
                          anchor_constraints=len(constraints),
                          reference_errors=len(case['reference_wrong_indices']),
                          old_12_state_cover_errors=0,
                          original_package_errors=len(wrong),
                          veto_errors=len(wrong),
                          clipped_samples=0,
                          wrong_line_and_controller_bytes=True))
    if (len(cases) != 2 or
            [case['veto_errors'] for case in cases] != [4, 7] or
            len(all_constraints) != 11 or
            phase(0x1D, covers) != 0 or circuit(0x1D, 1) != 1 or
            corrected_phase(0x1D, 1) != 1):
        raise ValueError('low-gain 1D classification changed')
    rows = ([(int(code, 16), 0, value) for code, value in mode0.items()] +
            [(int(code, 16), 1, value) for code, value in
             graph['combined_mode81_phase_labels'].items()])
    width, cubes = isolating_cubes(rows, 0x1D)
    if width != 4 or not cubes:
        raise ValueError(('1D correction cube classification changed', width))
    paths = (Path(__file__), RUN, MODE0, MODEL, GRAPH,
             HERE / 'joint_mask04_12a_phasebit0_veto.py')
    report = dict(experiment='unseen 1D low-gain frozen-veto failure audit',
                  cases=cases, inferred_1d_phase=0,
                  independent_anchor_constraints=len(all_constraints),
                  original_package_1d_phase=1, veto_1d_phase=1,
                  old_12_state_cover_1d_phase=0,
                  shortest_isolating_direct_cube_width=width,
                  shortest_isolating_direct_cubes=cubes,
                  limitations=[
                      'The 1D phase inference uses offered dibits and prior labels under the assumed line and capture route; it does not identify physical nets.',
                      'The shortest-cube search only describes direct state-plus-mode input terms that clear 1D without disturbing previously correct observed bit-0 labels.',
                      'A further fitted term is not implemented here; the negative holdout remains intact.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(run()['cases'])
