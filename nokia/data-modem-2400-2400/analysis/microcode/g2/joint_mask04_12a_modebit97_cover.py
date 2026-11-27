"""Freeze a twelve-bit phase cover with later 3F8 Y7 capture."""

import hashlib
import json
from pathlib import Path

from joint_mask04_12a_0d_feature_graph import code, solve
from joint_mask04_12a_modebit66_graph import CAPTURES, RAW, boundary
from joint_mask04_12a_modebit70_level_feature_screen import TRIALS
from joint_mask04_12a_modebit91_cover import FEATURES as ELEVEN_BITS, STEPS
from joint_mask04_12a_ten_bit_product_bound import cube_hit

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
DIAGNOSIS = RESULTS / 'joint-mask04-12a-modebit91-gain110-diagnosis.json'
NEW = tuple(RESULTS / f'joint-mask04-12a-modebit91-gain110-holdout-{mode}-189.json'
            for mode in ('edge32', 'edge48'))
OUT = RESULTS / 'joint-mask04-12a-modebit97-cover.json'
FEATURES = ELEVEN_BITS + (('94', 'y3f8', 7),)
P0_CUBES = (
    '***0*0******', '*0110**1****', '*****1*****1', '**1****1***1',
    '****0**00**1', '00***1******', '**1***0**1*1', '**1*****0*11',
)
P1_CUBES = (
    '**0*********', '***0*0******', '00**1****0**',
    '******10**0*', '******101***',
)


def gate_phase(state):
    return (int(any(cube_hit(state, cube) for cube in P0_CUBES)) |
            (int(any(cube_hit(state, cube) for cube in P1_CUBES)) << 1))


def run(out=OUT):
    diagnosis = json.loads(DIAGNOSIS.read_text())
    if not any(row['visit'] == '94' and row['site'] == 'y3f8' and
               row['bit'] == 7 and row['state_codes'] == 97 and
               row['directed_conflicts'] == 0 and
               row['components'] == [97]
               for row in diagnosis['zero_conflict_bits']):
        raise ValueError('selected late-Y7 feature changed')
    sources = [Path(__file__), DIAGNOSIS,
               HERE / 'joint_mask04_12a_modebit91_gain110_diagnosis.py',
               HERE / 'joint_mask04_12a_modebit91_cover.py',
               HERE / 'joint_mask04_12a_modebit70_level_feature_screen.py',
               HERE / 'joint_mask04_12a_0d_feature_graph.py',
               HERE / 'joint_mask04_12a_ten_bit_product_bound.py']
    cases = []

    def append(path, edge):
        sources.append(path)
        for case in json.loads(path.read_text())['cases']:
            limit = edge(case) if callable(edge) else edge
            for index, symbol in enumerate(case['multi_visit_symbols']):
                symbol['visits']['46']['mode_bit5'] = int(
                    limit is not None and index >= limit)
            cases.append((path, case))

    for path in (*CAPTURES, *RAW):
        append(path, lambda case, path=path: boundary(path, case))
    for offset, version, prefix, modes in TRIALS:
        for mode in modes:
            path = RESULTS / (f'joint-mask04-12a-{version}-{prefix}-'
                              f'{mode}-{offset}.json')
            append(path, None if mode == 'held81' else
                   48 if mode == 'edge48' else 32)
    for mode, path in zip(('edge32', 'edge48'), NEW):
        append(path, 32 if mode == 'edge32' else 48)
    graph = solve([case for _, case in cases], FEATURES, STEPS)
    if ((len(cases), graph['state_codes'], graph['components'],
         graph['directed_conflicts']) != (96, 97, [97], 0)):
        raise ValueError('twelve-bit development graph changed')
    wrong_labels = [key for key, phase in graph['relative_phase'].items()
                    if gate_phase(int(key, 16)) != phase]
    if wrong_labels:
        raise ValueError(('Boolean cover changes observed labels', wrong_labels))
    inverse = {step: dibit for dibit, step in enumerate(STEPS)}
    checks = []
    for path, case in cases:
        states = [code(symbol, FEATURES)
                  for symbol in case['multi_visit_symbols']]
        wrong = [index for index in range(1, len(states))
                 if inverse[(gate_phase(states[index]) -
                             gate_phase(states[index - 1])) & 3]
                 != case['expected_dibits'][index]]
        checks.append(dict(source=path.name,
                           selector=case.get('selector'),
                           wrong_decision_indices=wrong))
    if any(row['wrong_decision_indices'] for row in checks):
        raise ValueError('development-stream cover replay changed')
    report = dict(experiment='frozen twelve-bit mode and late-Y7 phase Boolean cover',
                  fixture=dict(development_streams=len(cases),
                               observed_states=graph['state_codes'],
                               phase_convention=STEPS,
                               features=FEATURES,
                               global_phase_offset=0,
                               late_y7_capture_visit=94),
                  phase_bit0_cubes=P0_CUBES,
                  phase_bit1_cubes=P1_CUBES,
                  phase_graph=graph,
                  observed_label_mismatches=wrong_labels,
                  development_checks=checks,
                  limitations=[
                      'The eight/five product cover is a greedy fit to all 96 development streams; it is not an exact minimum or a photographed-package circuit.',
                      'Late row-0 Y2 and later 3F8 Y7 require separate storage/clock hypotheses; board nets and serial timing remain untraced.',
                      'Zero development errors do not validate an unseen state or fresh mode/level fixture.'
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
