"""Diagnose the new state in the thirteen-bit nominal-level holdout."""

import hashlib
import json
from pathlib import Path

import joint_mask04_12a_modebit97_exact_products as exact
from joint_mask04_12a_0d_feature_graph import solve
from joint_mask04_12a_modebit66_graph import CAPTURES, RAW, boundary
from joint_mask04_12a_modebit70_level_feature_screen import TRIALS
from joint_mask04_12a_modebit91_gain110_diagnosis import NEW as FAILED_189
from joint_mask04_12a_modebit97_cover import STEPS
from joint_mask04_12a_modebit97_staged_capture import FRESH
from joint_mask04_12a_modebit102_gain095_feature_screen import GAIN105, GAIN095
from joint_mask04_12a_modebit156_staged_transfer import THIRTEEN
from joint_mask04_12a_ten_bit_product_bound import cube_hit

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
CAPTURE = RESULTS / 'joint-mask04-12a-modebit156-staged-transfer.json'
GATE = RESULTS / 'joint-mask04-12a-modebit156-gain100-holdout.json'
NEW = tuple(RESULTS / f'joint-mask04-12a-modebit156-gain100-holdout-{mode}-199.json'
            for mode in ('edge32', 'edge48'))
OUT = RESULTS / 'joint-mask04-12a-modebit159-nominal-diagnosis.json'


def run(out=OUT):
    cases = []
    paths = []

    def append(path, edge):
        paths.append(path)
        for case in json.loads(path.read_text())['cases']:
            limit = edge(case) if callable(edge) else edge
            for index, symbol in enumerate(case['multi_visit_symbols']):
                symbol['visits']['46']['mode_bit5'] = int(
                    limit is not None and index >= limit)
            cases.append(case)

    for path in (*CAPTURES, *RAW):
        append(path, lambda case, path=path: boundary(path, case))
    for offset, version, prefix, modes in TRIALS:
        for mode in modes:
            path = RESULTS / (f'joint-mask04-12a-{version}-{prefix}-'
                              f'{mode}-{offset}.json')
            append(path, None if mode == 'held81' else
                   48 if mode == 'edge48' else 32)
    for mode, path in zip(('edge32', 'edge48'), FAILED_189):
        append(path, 32 if mode == 'edge32' else 48)
    for mode, path in zip(('edge32', 'edge48'), FRESH):
        append(path, 32 if mode == 'edge32' else 48)
    for mode, path in zip(('edge32', 'edge48'), GAIN105):
        append(path, 32 if mode == 'edge32' else 48)
    for mode, path in zip(('edge32', 'edge48'), GAIN095):
        append(path, 32 if mode == 'edge32' else 48)
    prior_count = len(cases)
    for mode, path in zip(('edge32', 'edge48'), NEW):
        append(path, 32 if mode == 'edge32' else 48)
    graph = solve(cases, THIRTEEN, STEPS)
    if ((prior_count, len(cases), graph['state_codes'],
         graph['components'], graph['directed_conflicts']) !=
            (108, 112, 159, [159], 0)):
        raise ValueError('joined nominal thirteen-bit graph changed')
    prior = json.loads(CAPTURE.read_text())['phase_graph']
    unseen = sorted(set(graph['relative_phase']) - set(prior['relative_phase']))
    if unseen != ['190C', '1FCC', '3DE']:
        raise ValueError(('nominal unseen states changed', unseen))
    rows = [(int(state, 16), phase) for state, phase in
            graph['relative_phase'].items()]
    old_width = exact.WIDTH
    try:
        exact.WIDTH = 13
        bounds = [exact.solve(rows, bit, polarity)
                  for bit in (0, 1) for polarity in (0, 1)]
    finally:
        exact.WIDTH = old_width
    counts = {(row['phase_bit'], row['on_polarity']):
              row['minimum_direct_products'] for row in bounds}
    if counts != {(0, 0): 9, (0, 1): 8, (1, 0): 6, (1, 1): 5}:
        raise ValueError(('nominal direct-product bounds changed', counts))
    gate = json.loads(GATE.read_text())
    cubes = (gate['fixture']['phase_bit0_cubes'],
             gate['fixture']['phase_bit1_cubes'])
    target = int('190C', 16)
    frozen_phase = sum(int(any(cube_hit(target, cube) for cube in terms)) << bit
                       for bit, terms in enumerate(cubes))
    if (frozen_phase, graph['relative_phase']['190C']) != (3, 1):
        raise ValueError('frozen bit-1 mislabel at 190C changed')
    failed = next(row for row in gate['cases']
                  if row['mode'] == 'edge48' and row['selector'] == '40')
    if failed['wrong_decision_indices'] != [34, 35, 44, 45, 47, 48]:
        raise ValueError('nominal holdout decision failures changed')
    sources = (Path(__file__), CAPTURE, GATE,
               HERE / 'joint_mask04_12a_modebit97_exact_products.py',
               HERE / 'joint_mask04_12a_modebit156_staged_transfer.py',
               HERE / 'joint_mask04_12a_0d_feature_graph.py', *paths)
    report = dict(experiment='nominal thirteen-bit unseen-state phase diagnosis',
                  fixture=dict(streams=len(cases), states=graph['state_codes'],
                               new_states=unseen),
                  joined_phase_graph=graph,
                  direct_product_bounds=bounds,
                  state_190C=dict(frozen_phase=frozen_phase,
                                  constrained_phase=graph['relative_phase']['190C'],
                                  wrong_phase_bit=1,
                                  failing_edge48_call_symbol_indices=[34, 44, 47],
                                  failing_decision_indices=failed['wrong_decision_indices']),
                  holdout_cases=gate['cases'],
                  limitations=[
                      'State 190C and the revised direct-product witness are post-holdout development evidence; another untouched carrier/level fixture is needed.',
                      'The joined graph establishes consistency of the chosen thirteen-bit representation on these streams, not a physical gate circuit or robustness on every signal condition.',
                      'The U14/U3/U25/U28 timing and ADC/USART connections remain photo-compatible assumptions.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print('states', result['fixture']['states'],
          'conflicts', result['joined_phase_graph']['directed_conflicts'],
          'new mislabel', result['state_190C'])
