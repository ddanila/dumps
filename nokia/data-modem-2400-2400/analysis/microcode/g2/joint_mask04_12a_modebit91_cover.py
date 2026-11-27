"""Freeze an eleven-bit phase cover with late row-0 Y2 capture."""

import hashlib
import json
from pathlib import Path

from joint_mask04_12a_0d_feature_graph import code
from joint_mask04_12a_modebit66_graph import CAPTURES, RAW, boundary
from joint_mask04_12a_modebit70_level_feature_screen import TRIALS
from joint_mask04_12a_modebit70_revision import FEATURES as TEN_BITS, STEPS
from joint_mask04_12a_ten_bit_product_bound import cube_hit

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
SCREEN = RESULTS / 'joint-mask04-12a-modebit70-level-feature-screen.json'
OUT = RESULTS / 'joint-mask04-12a-modebit91-cover.json'
FEATURES = TEN_BITS + (('93', 'row0', 2),)
P0_CUBES = (
    '1****1*0***', '*01***1*0**', '00******0*0', '010*******1',
    '**01***00**', '**1*00*1***', '*1*1*1*****', '**10*0*****',
    '0*000****0*', '11*0*******', '00**1****0*',
)
P1_CUBES = (
    '1011*******', '0*1***0****', '0*1*****0*1',
    '00******0*0', '**0*1**0***', '**1****11**',
)


def gate_phase(state):
    return (int(any(cube_hit(state, cube) for cube in P0_CUBES)) |
            (int(any(cube_hit(state, cube) for cube in P1_CUBES)) << 1))


def run(out=OUT):
    screen = json.loads(SCREEN.read_text())
    graph = screen['selected_row0_y2_graphs']['93-row0-2']['all_streams']
    if ((graph['state_codes'], graph['components'],
         graph['directed_conflicts']) != (91, [91], 0) or
            screen['fixture']['streams'] != 92):
        raise ValueError('frozen eleven-bit graph changed')
    labels = {int(key, 16): value for key, value in graph['relative_phase'].items()}
    wrong_labels = [f'{key:03X}' for key, phase in labels.items()
                    if gate_phase(key) != phase]
    if wrong_labels:
        raise ValueError(('Boolean cover changes observed labels', wrong_labels))
    inverse = {step: dibit for dibit, step in enumerate(STEPS)}
    checks = []
    sources = [Path(__file__), SCREEN,
               HERE / 'joint_mask04_12a_modebit70_level_feature_screen.py',
               HERE / 'joint_mask04_12a_modebit70_revision.py',
               HERE / 'joint_mask04_12a_0d_feature_graph.py',
               HERE / 'joint_mask04_12a_ten_bit_product_bound.py']

    def check(path, mode_limit):
        sources.append(path)
        for case in json.loads(path.read_text())['cases']:
            limit = mode_limit(case) if callable(mode_limit) else mode_limit
            for index, symbol in enumerate(case['multi_visit_symbols']):
                symbol['visits']['46']['mode_bit5'] = int(
                    limit is not None and index >= limit)
            states = [code(symbol, FEATURES)
                      for symbol in case['multi_visit_symbols']]
            wrong = [index for index in range(1, len(states))
                     if inverse[(gate_phase(states[index]) -
                                 gate_phase(states[index - 1])) & 3]
                     != case['expected_dibits'][index]]
            checks.append(dict(source=path.name,
                               selector=case.get('selector'),
                               wrong_decision_indices=wrong))

    for path in (*CAPTURES, *RAW):
        check(path, lambda case, path=path: boundary(path, case))
    for offset, version, prefix, modes in TRIALS:
        for mode in modes:
            path = RESULTS / (f'joint-mask04-12a-{version}-{prefix}-'
                              f'{mode}-{offset}.json')
            check(path, None if mode == 'held81' else
                  48 if mode == 'edge48' else 32)
    if len(checks) != 92 or any(row['wrong_decision_indices'] for row in checks):
        raise ValueError('development-stream cover replay changed')
    report = dict(experiment='frozen eleven-bit mode and late-row phase Boolean cover',
                  fixture=dict(development_streams=len(checks),
                               observed_states=len(labels),
                               phase_convention=STEPS,
                               features=FEATURES,
                               global_phase_offset=0,
                               late_row_capture_visit=93),
                  phase_bit0_cubes=P0_CUBES,
                  phase_bit1_cubes=P1_CUBES,
                  phase_graph=graph,
                  observed_label_mismatches=wrong_labels,
                  development_checks=checks,
                  limitations=[
                      'The 11/6 product cover is a greedy Boolean fit to all 92 development streams; it is not minimal and exceeds one U15 output or the earlier package allocation.',
                      'The late row-0 Y2 storage path, mode input, gate nets, analog path and USART timing are assumed, not traced.',
                      'Zero development errors do not validate unseen states or a new gain/carrier fixture.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print('states', result['fixture']['observed_states'],
          'streams', result['fixture']['development_streams'],
          'terms', len(P0_CUBES), len(P1_CUBES))
