"""Check whether two-visit receive states admit a fixed differential phase label."""

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from receiver_mask04_four_bit_transition import HERE, state
from common import save
from reference_modem import PHASE_STEPS

MULTIVISIT = HERE / 'results/receiver-mask04-multivisit-capture.json'
GRID = HERE / 'results/receiver-mask04-three-bit-two-visit.json'
TRANSITIONS = HERE / 'results/receiver-mask04-four-bit-transition.json'


def observations():
    rows = []
    for case in json.loads(MULTIVISIT.read_text())['cases']:
        symbols = case['symbols']
        states = [state(symbol['visits']['47']['y3f8'],
                        symbol['visits']['94']['y3f8']) for symbol in symbols]
        for index, (before, after) in enumerate(zip(states, states[1:])):
            rows.append(dict(source='intermediate', degrees=case['degrees'],
                             symbol=index + 1, before=before, after=after,
                             dibit=symbols[index + 1]['dibit'],
                             trace_digest=case['trace_digest']))
    for case in json.loads(GRID.read_text())['fresh_cases']:
        states = [state(first, second) for first, second in
                  zip(case['first_visit_y'], case['second_visit_y'])]
        for index, (before, after) in enumerate(zip(states, states[1:])):
            rows.append(dict(source='grid', degrees=case['degrees'],
                             symbol=index + 1, before=before, after=after,
                             dibit=case['expected_dibits'][index + 1],
                             trace_digest=case['trace_digest']))
    return rows


def run(out=HERE / 'results/receiver-mask04-phase-state-audit.json'):
    rows = observations()
    saved = json.loads(TRANSITIONS.read_text())['rule']['table']
    by_edge = defaultdict(list)
    for row in rows:
        by_edge[(row['before'] << 4) | row['after']].append(row)
    labels = {f'{key:02X}': sorted({row['dibit'] for row in members})
              for key, members in sorted(by_edge.items())}
    if (len(rows) != 987 or len(by_edge) != 86 or
            any(len(values) != 1 for values in labels.values()) or
            {key: values[0] for key, values in labels.items()} != saved):
        raise ValueError('two-visit transition evidence changed')

    self_rows = [row for row in rows if row['before'] == row['after']]
    self_counts = Counter(row['dibit'] for row in self_rows)
    if self_counts != {3: 696}:
        raise ValueError('self-transition evidence changed')
    # A fixed phase label P[state] with constant phase advance c would require
    # step(dibit) = c + P[after] - P[before] (mod 4). A self-edge fixes c=2.
    # The three observed directed edges below form a cycle. Their required
    # residual phase advances sum to 3 (mod 4), not zero.
    cycle_keys = (0x04, 0x48, 0x80)
    cycle = []
    for key in cycle_keys:
        row = by_edge[key][0]
        cycle.append(dict(key=f'{key:02X}', dibit=row['dibit'],
                          required_residual=(PHASE_STEPS[row['dibit']] // 4 - 2) % 4,
                          witness=row))
    if ([row['dibit'] for row in cycle] != [3, 3, 1] or
            sum(row['required_residual'] for row in cycle) % 4 != 3):
        raise ValueError('phase-cycle counterexample changed')
    paths = (Path(__file__), MULTIVISIT, GRID, TRANSITIONS,
             HERE / 'receiver_mask04_four_bit_transition.py',
             HERE / 'reference_modem.py')
    report = dict(experiment='fixed phase-state feasibility for two-visit 3F8 Y6/Y7 capture',
                  model='step(dibit) = constant_advance + P[current_state] - P[previous_state] modulo four',
                  state='visit47 Y6/Y7 + visit94 Y6/Y7, four bits per symbol',
                  observations=len(rows), distinct_transition_keys=len(by_edge),
                  conflicting_direct_transition_keys=0,
                  self_transitions=dict(count=len(self_rows),
                                        dibit_counts=dict(self_counts),
                                        example=self_rows[0],
                                        forced_constant_advance_quadrants=2),
                  contradiction=dict(cycle=cycle,
                                     residual_sum_mod_four=3,
                                     required_sum_mod_four=0),
                  conclusion='No fixed phase label for the sixteen four-bit states, with any constant advance, explains all inspected transitions. A direct pair decision or additional retained/timing state is needed.',
                  limitations=['The ADC ingress, two symbol-relative captures and their clock routing remain hypotheses.',
                               'This excludes only a fixed per-state phase-label consumer; it does not exclude a direct transition logic network or a stateful receiver.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    print(result['observations'], result['self_transitions']['count'],
          result['contradiction']['residual_sum_mod_four'])
