"""Audit phase constraints behind the carrier-141 receive failure."""

import hashlib
import json
from collections import defaultdict, deque
from pathlib import Path

from joint_mask04_12a_multivisit_phase_screen import SELECTED, sample_state
from joint_mask04_12a_visit94_phase_gate import candidate_phase

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
GRAPH = RESULTS / 'joint-mask04-12a-mode-phase131-gain-graph-audit.json'
MODEL = RESULTS / 'joint-mask04-12a-mode-phase-twelve.json'
RUNS = (
    RESULTS / 'joint-mask04-12a-lowgain133-expanded-visits.json',
    RESULTS / 'joint-mask04-12a-mode1-expanded-1.15.json',
    RESULTS / 'joint-mask04-12a-mode1-expanded-1.25.json',
    RESULTS / 'joint-mask04-12a-visit94-phase-holdout-133.json',
    RESULTS / 'joint-mask04-12a-visit94-phase-holdout-135.json',
    RESULTS / 'joint-mask04-12a-visit94-gain07-challenge-0.7.json',
    RESULTS / 'joint-mask04-12a-visit94-gain07-challenge-0.8.json',
    RESULTS / 'joint-mask04-12a-visit94-mode81-control-expanded.json',
)
CHALLENGE = RESULTS / 'joint-mask04-12a-visit94-gain07-challenge.json'
OLD0D = RESULTS / 'joint-mask04-12a-visit94-old0d-replay.json'
MODE81 = RESULTS / 'joint-mask04-12a-visit94-mode81-control.json'
OUT = RESULTS / 'joint-mask04-12a-visit94-gain07-graph-audit.json'


def run(out=OUT):
    known = {int(code, 16): phase for code, phase in json.loads(
        GRAPH.read_text())['combined_mode81_phase_labels'].items()}
    steps = json.loads(MODEL.read_text())['fixture']['phase_convention']
    inverse = {step: dibit for dibit, step in enumerate(steps)}
    edges = defaultdict(list)
    extra_bit = defaultdict(set)
    cases = []
    for path in RUNS:
        for case in json.loads(path.read_text())['cases']:
            states = [sample_state(symbol, SELECTED)
                      for symbol in case['multi_visit_symbols']]
            bits = [((symbol['visits']['94']['y3f8'] >> 6) & 1)
                    for symbol in case['multi_visit_symbols']]
            for state, bit in zip(states, bits):
                extra_bit[state].add(bit)
            for index in range(1, len(states)):
                step = steps[case['expected_dibits'][index]]
                edges[states[index - 1]].append((states[index], step))
                edges[states[index]].append((states[index - 1], -step))
            cases.append((path, case, states))
    labels = {0x49: known[0x49]}
    queue = deque(labels)
    conflicts = 0
    while queue:
        state = queue.popleft()
        for neighbor, step in edges[state]:
            value = (labels[state] + step) & 3
            if neighbor in labels:
                conflicts += labels[neighbor] != value
            else:
                labels[neighbor] = value
                queue.append(neighbor)
    if conflicts or set(extra_bit) != set(labels):
        raise ValueError(('current phase graph conflicts/disconnects', conflicts))
    disagreements = {f'{state:02X}': dict(older=known[state], new=labels[state])
                     for state in sorted(set(known) & set(labels))
                     if known[state] != labels[state]}
    if disagreements != {'0D': {'older': 1, 'new': 0}}:
        raise ValueError(('old/new label disagreements changed', disagreements))
    varying_extra = {f'{state:02X}': sorted(values)
                     for state, values in extra_bit.items() if len(values) > 1}
    if varying_extra:
        raise ValueError(('visit-94 Y6 split a state', varying_extra))
    per_state = {}
    for state in sorted(labels):
        bit = next(iter(extra_bit[state]))
        sample = next(symbol for path, case, states in cases
                      for symbol, value in zip(case['multi_visit_symbols'], states)
                      if value == state)
        per_state[f'{state:02X}'] = dict(inferred_phase=labels[state],
                                      visit94_y6=bit,
                                      candidate_phase=candidate_phase(sample),
                                      older_phase=known.get(state))
    mismatches = {code: row for code, row in per_state.items()
                  if row['inferred_phase'] != row['candidate_phase']}
    if set(mismatches) != {'0A', '1C', '4A', '53'}:
        raise ValueError(('mismatched state set changed', mismatches))
    challenge = json.loads(CHALLENGE.read_text())
    scored = []
    for path, case, states in cases:
        if path not in RUNS[-3:-1]:
            continue
        predicted = [labels[state] for state in states]
        observed = [candidate_phase(symbol)
                    for symbol in case['multi_visit_symbols']]
        wrong = [index for index in range(1, len(states))
                 if inverse[(observed[index] - observed[index - 1]) & 3]
                 != case['expected_dibits'][index]]
        inferred_wrong = [index for index in range(1, len(states))
                          if inverse[(predicted[index] - predicted[index - 1]) & 3]
                          != case['expected_dibits'][index]]
        scored.append(dict(source=path.name, selector=case['selector'],
                           predicted_wrong_indices=wrong,
                           inferred_phase_wrong_indices=inferred_wrong))
    # Match the independently scored holdout by gain and selector.
    for row in scored:
        factor = 0.7 if row['source'].endswith('0.7.json') else 0.8
        independent = next(case for case in challenge['cases']
                           if case['gain_factor'] == factor and
                           case['selector'] == row['selector'])
        if (row['predicted_wrong_indices'] !=
                independent['candidate_wrong_indices'] or
                row['inferred_phase_wrong_indices']):
            raise ValueError(('phase graph does not explain holdout', row))
        row['gain_factor'] = factor
        row['errors'] = len(row['predicted_wrong_indices'])
        del row['predicted_wrong_indices'], row['inferred_phase_wrong_indices']
    if len(scored) != 4 or [row['errors'] for row in scored] != [19, 22, 6, 14]:
        raise ValueError('challenge scoring changed')
    older = json.loads(OLD0D.read_text())
    old0d = {case['mode']: dict(occurrences=len(case['state_0d_occurrences']),
                                 later_bit_counts=case['state_0d_visit94_y6_counts'],
                                 candidate_errors=len(case['candidate_wrong_indices']))
             for case in older['cases']}
    if (old0d != {
            'held_81': dict(occurrences=43,
                            later_bit_counts={'0': 4, '1': 39},
                            candidate_errors=7),
            'edge_81_A1': dict(occurrences=32,
                               later_bit_counts={'1': 32},
                               candidate_errors=7)} or
            per_state['0D']['visit94_y6'] != 1 or
            per_state['0D']['inferred_phase'] != 0):
        raise ValueError('older 0D timing contradiction changed')
    mode_control = json.loads(MODE81.read_text())
    if ([(case['selector'], case['state_0d_count'],
          len(case['held_candidate_wrong_indices']))
         for case in mode_control['cases']] !=
            [('40', 7, 15), ('60', 11, 23)]):
        raise ValueError('held-81 challenge result changed')
    paths = (Path(__file__), GRAPH, MODEL, CHALLENGE, OLD0D, MODE81, *RUNS,
             HERE / 'joint_mask04_12a_visit94_phase_gate.py')
    report = dict(experiment='joined carrier-141 phase-state failure audit',
                  fixture=dict(anchor='older state 49 phase 2',
                               cases=len(cases),
                               state_codes=len(labels),
                               phase_convention=steps),
                  graph_conflicts=conflicts,
                  older_label_disagreements=disagreements,
                  extra_bit_varies_within_state=varying_extra,
                  per_state=per_state,
                  candidate_wrong_state_phases=mismatches,
                  challenge_cases=scored,
                  older_0d_replay=old0d,
                  held_81_control=[dict(selector=case['selector'],
                                        state_0d_count=case['state_0d_count'],
                                        candidate_errors=len(case['held_candidate_wrong_indices']))
                                   for case in mode_control['cases']],
                  limitations=[
                      'The inferred phases use offered dibits and the assumed line/ADC input; they are not physical latch labels.',
                      'Visit-94 Y6 is deterministic for each observed seven-bit state in these 16 streams; the older phase-112 answer replay shows that this is not globally true.',
                      'State 0D conflicts with an older label, and holding 81 on the new waveform does not remove the conflict; a single static map of these inputs cannot explain both evidence sets without another distinction.',
                      'The graph explains the observed errors but does not synthesize a board circuit.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print(result['older_label_disagreements'],
          list(result['candidate_wrong_state_phases']))
