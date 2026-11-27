"""Check new lower-gain states against the frozen 159-state phase graph."""

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from joint_mask04_12a_0d_feature_graph import code
from joint_mask04_12a_modebit156_staged_transfer import THIRTEEN
from joint_mask04_12a_modebit97_cover import STEPS
from joint_mask04_12a_ten_bit_product_bound import cube_hit

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
FROZEN = RESULTS / 'joint-mask04-12a-modebit159-nominal-diagnosis.json'
COVER = RESULTS / 'joint-mask04-12a-modebit159-revised-cover.json'
HOLDOUT = RESULTS / 'joint-mask04-12a-modebit159-gain085-holdout.json'
RAW = tuple(RESULTS / f'joint-mask04-12a-modebit159-gain085-holdout-{mode}-203.json'
            for mode in ('edge32', 'edge48'))
OUT = RESULTS / 'joint-mask04-12a-modebit160-gain085-diagnosis.json'


def run(out=OUT):
    frozen = json.loads(FROZEN.read_text())['joined_phase_graph']['relative_phase']
    known = {int(state, 16): phase for state, phase in frozen.items()}
    cover = json.loads(COVER.read_text())['bounds']
    cubes = [next(row['witness_cubes'] for row in cover
                  if (row['phase_bit'], row['on_polarity']) == (bit, 1))
             for bit in (0, 1)]
    holdout = json.loads(HOLDOUT.read_text())
    cases = []
    all_edges = []
    visits = Counter()
    for mode, path in zip(('edge32', 'edge48'), RAW):
        for case in json.loads(path.read_text())['cases']:
            states = []
            for index, symbol in enumerate(case['multi_visit_symbols']):
                symbol['visits']['46']['mode_bit5'] = int(index >= (32 if mode == 'edge32' else 48))
                states.append(code(symbol, THIRTEEN))
            for state in states:
                visits[state] += 1
            edges = [(states[index - 1], states[index], STEPS[case['expected_dibits'][index]])
                     for index in range(1, len(states))]
            all_edges.extend(edges)
            cases.append(dict(mode=mode, selector=case['selector'],
                              states=len(set(states)),
                              unseen=[f'{state:X}' for state in sorted(set(states) - known.keys())]))
    labels = dict(known)
    changed = True
    while changed:
        changed = False
        for previous, current, step in all_edges:
            if previous in labels and current not in labels:
                labels[current] = (labels[previous] + step) & 3
                changed = True
            if current in labels and previous not in labels:
                labels[previous] = (labels[current] - step) & 3
                changed = True
    conflicts = [(f'{previous:X}', f'{current:X}', step)
                 for previous, current, step in all_edges
                 if previous in labels and current in labels
                 and (labels[current] - labels[previous]) & 3 != step]
    newly_seen = sorted(set(visits) - known.keys())
    if newly_seen != [0x1909] or conflicts or len(labels) != 160:
        raise ValueError((newly_seen, conflicts[:8], len(labels)))
    state = newly_seen[0]
    predicted = sum(int(any(cube_hit(state, cube) for cube in terms)) << bit
                    for bit, terms in enumerate(cubes))
    neighboring = defaultdict(Counter)
    for previous, current, step in all_edges:
        if current == state and previous in known:
            neighboring['incoming'][f'{previous:X}'] += 1
        if previous == state and current in known:
            neighboring['outgoing'][f'{current:X}'] += 1
    if predicted != labels[state]:
        raise ValueError(('frozen gate disagrees on unseen state', predicted, labels[state]))
    report = dict(experiment='offset-203 low-gain unseen-state phase constraint',
                  frozen_states=len(known), joined_states=len(labels),
                  transition_edges=len(all_edges), transition_conflicts=len(conflicts),
                  cases=cases,
                  new_state=dict(code=f'{state:X}', visits=visits[state],
                                 constrained_phase=labels[state], frozen_phase=predicted,
                                 adjacent_known_states={direction: dict(counts)
                                                        for direction, counts in neighboring.items()}),
                  holdout_summary=holdout['cases'],
                  limitations=[
                      'This constrains one new state, not all possible receiver states or levels.',
                      'The ADC, latch, mode, gate, USART and line connections are assumed.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in (Path(__file__), FROZEN, COVER, HOLDOUT, *RAW)})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print('new state', result['new_state'], 'conflicts', result['transition_conflicts'])
