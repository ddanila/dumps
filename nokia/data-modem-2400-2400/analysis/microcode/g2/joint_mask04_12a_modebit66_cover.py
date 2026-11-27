"""Freeze a mode-bit-conditioned Boolean phase cover for fresh challenges."""

import hashlib
import json
from pathlib import Path

from joint_mask04_12a_0d_feature_graph import code
from joint_mask04_12a_modebit66_graph import (
    CAPTURES, MODE_FEATURE, NINE_BITS, RAW, STEPS, boundary,
)
from joint_mask04_12a_ten_bit_product_bound import cube_hit

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
GRAPH = RESULTS / 'joint-mask04-12a-modebit66-graph.json'
OUT = RESULTS / 'joint-mask04-12a-modebit66-cover.json'
FEATURES = NINE_BITS + (MODE_FEATURE,)
P0_CUBES = ('1011010010', '*011***1**', '100100*00*',
            '001*100001', '**00*0****', '00*10***1*')
P1_CUBES = ('*****1*0**', '*1****00**', '**1***00*1', '**1****1**')


def gate_phase(state):
    return (int(any(cube_hit(state, cube) for cube in P0_CUBES)) |
            (int(any(cube_hit(state, cube) for cube in P1_CUBES)) << 1))


def run(out=OUT):
    graph = json.loads(GRAPH.read_text())['mode_bit_graph']
    if ((graph['state_codes'], graph['directed_conflicts'],
         graph['components']) != (61, 0, [61])):
        raise ValueError('frozen mode-bit graph changed')
    labels = {int(key, 16): phase
              for key, phase in graph['relative_phase'].items()}
    wrong_labels = [f'{state:03X}' for state, phase in labels.items()
                    if gate_phase(state) != ((phase + 1) & 3)]
    if wrong_labels:
        raise ValueError(('Boolean cover changes observed labels', wrong_labels))
    inverse = {step: dibit for dibit, step in enumerate(STEPS)}
    checks = []
    for path in (*CAPTURES, *RAW):
        for case in json.loads(path.read_text())['cases']:
            edge = boundary(path, case)
            for index, symbol in enumerate(case['multi_visit_symbols']):
                symbol['visits']['46']['mode_bit5'] = int(edge is not None and
                                                           index >= edge)
            states = [code(symbol, FEATURES)
                      for symbol in case['multi_visit_symbols']]
            wrong = [index for index in range(1, len(states))
                     if inverse[(gate_phase(states[index]) -
                                 gate_phase(states[index - 1])) & 3]
                     != case['expected_dibits'][index]]
            checks.append(dict(source=path.name, selector=case.get('selector'),
                               assumed_mode_edge_symbol=edge,
                               wrong_decision_indices=wrong))
    if len(checks) != 66 or any(row['wrong_decision_indices'] for row in checks):
        raise ValueError('development-stream cover replay changed')
    sources = (Path(__file__), GRAPH,
               HERE / 'joint_mask04_12a_modebit66_graph.py',
               HERE / 'joint_mask04_12a_ten_bit_product_bound.py',
               HERE / 'joint_mask04_12a_0d_feature_graph.py',
               *CAPTURES, *RAW)
    report = dict(experiment='frozen 61-state mode-conditioned phase Boolean cover',
                  fixture=dict(development_streams=len(checks),
                               observed_states=len(labels),
                               phase_convention=STEPS,
                               global_phase_offset=1,
                               features=FEATURES),
                  phase_bit0_cubes=P0_CUBES,
                  phase_bit1_cubes=P1_CUBES,
                  observed_label_mismatches=wrong_labels,
                  development_checks=checks,
                  limitations=[
                      'This cover was selected using all 66 streams; zero development errors do not validate unseen states.',
                      'Six and four direct products exceed one U15 4-2-3-2 AOI output; no photographed-package realization is claimed.',
                      'The mode-bit input is an imposed D3EB schedule; its physical route, latch and USART nets are unknown.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print('states', result['fixture']['observed_states'],
          'streams', result['fixture']['development_streams'])
