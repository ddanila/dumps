"""Freeze a two-term mode-qualified veto for the observed phase-bit-0 errors."""

import hashlib
import json
from pathlib import Path

from joint_mask04_12a_multivisit_phase_screen import SELECTED, sample_state
from photo_u15_u19_u21_phase_route import circuit

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
MODE0 = RESULTS / 'joint-mask04-12a-row0-boolean-twentytwo.json'
GRAPH = RESULTS / 'joint-mask04-12a-mode-phase131-gain-graph-audit.json'
INPUTS = (
    (0, 'joint-mask04-12a-row0-boolean-twenty-fresh-88.json'),
    (1, 'joint-mask04-12a-mode-twelve-holdout.json'),
    (1, 'joint-mask04-12a-mode-phase128-challenge.json'),
    (1, 'joint-mask04-12a-mode-phase125-challenge.json'),
    (1, 'joint-mask04-12a-mode-phase131-baseline-control.json'),
    (1, 'joint-mask04-12a-mode-phase131-intermediate-gain.json'),
    (1, 'joint-mask04-12a-mode-phase131-gain-boundary.json'),
    (1, 'joint-mask04-12a-mode-phase131-gain-challenge.json'),
)
OUT = RESULTS / 'joint-mask04-12a-phasebit0-veto.json'
INVERSE = {step: dibit for dibit, step in enumerate((2, 1, 3, 0))}


def corrected_phase(state, mode):
    original = circuit(state, mode)
    if not mode:
        return original
    s0 = state & 1
    s1 = (state >> 1) & 1
    s2 = (state >> 2) & 1
    s6 = (state >> 6) & 1
    veto_2f = s0 & s1
    veto_48 = (1 - s1) & (1 - s2) & s6
    return original & ~(veto_2f | veto_48)


def run(out=OUT):
    mode0 = json.loads(MODE0.read_text())['state_phase']
    mode1 = json.loads(GRAPH.read_text())['combined_mode81_phase_labels']
    labels = ((0, mode0), (1, mode1))
    label_errors = [dict(mode=mode, state=code, expected=value,
                         actual=corrected_phase(int(code, 16), mode))
                    for mode, group in labels for code, value in group.items()
                    if corrected_phase(int(code, 16), mode) != value]
    if label_errors or len(mode0) != 22 or len(mode1) != 20:
        raise ValueError(('corrected label set changed', label_errors))
    cases = []
    for mode, name in INPUTS:
        saved = json.loads((RESULTS / name).read_text())
        for case in saved['cases']:
            states = [sample_state(symbol, SELECTED)
                      for symbol in case['multi_visit_symbols']]
            phases = [corrected_phase(state, mode) for state in states]
            wrong = [index for index in range(1, len(phases))
                     if INVERSE[(phases[index] - phases[index - 1]) & 3]
                     != case['expected_dibits'][index]]
            if len(states) != 65 or wrong:
                raise ValueError(('corrected saved replay changed', name,
                                  case['selector'], wrong))
            cases.append(dict(source=name, selector=case['selector'],
                              mode=mode, gain=case.get('factor'),
                              states=len(set(states)), errors=0,
                              rx_trace_digest=case['rx_trace_digest']))
    if len(cases) != 22:
        raise ValueError('saved replay count changed')
    changed = {str(mode): [f'{state:02X}' for state in range(128)
                           if corrected_phase(state, mode) != circuit(state, mode)]
               for mode in (0, 1)}
    if changed['0'] or not {'2F', '48'} <= set(changed['1']):
        raise ValueError('mode-qualified veto changed')
    paths = (Path(__file__), MODE0, GRAPH,
             HERE / 'photo_u15_u19_u21_phase_route.py',
             *(RESULTS / name for _, name in INPUTS))
    report = dict(experiment='frozen two-term external phase-bit-0 veto',
                  fixture=dict(original='photo_u15_u19_u21_phase_route.py',
                               mode='only assumed 81/A1 mode bit',
                               veto_2f='s0 AND s1',
                               veto_48='NOT s1 AND NOT s2 AND s6',
                               corrected='P0 = original P0 AND NOT(mode AND (veto_2f OR veto_48)); P1 unchanged'),
                  observed_labels=dict(mode01=len(mode0), mode81_A1=len(mode1),
                                       errors=label_errors),
                  saved_real_prom_replays=cases,
                  changed_unobserved_code_counts={mode: len(codes)
                                                  for mode, codes in changed.items()},
                  limitations=[
                      'The two veto terms were selected using the same gain runs they repair; these 22 replays are development evidence, not a holdout.',
                      'The correction is a logical external gate hypothesis. No photographed package budget, fan-out, timing or board net is established for the extra mode-qualified veto.',
                      'It changes predictions for unobserved mode-81 states; a fresh real-PROM phase/gain/payload challenge is required.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print(result['observed_labels'], len(result['saved_real_prom_replays']),
          result['changed_unobserved_code_counts'])
