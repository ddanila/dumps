"""Diagnose the frozen mode-bit cover's matched-mode holdout failure."""

import hashlib
import json
from pathlib import Path

from joint_mask04_12a_0d_feature_graph import code, solve
from joint_mask04_12a_modebit66_cover import FEATURES, STEPS, gate_phase
from joint_mask04_12a_modebit66_graph import CAPTURES, RAW, boundary

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
GRAPH = RESULTS / 'joint-mask04-12a-modebit66-graph.json'
HOLDOUT = RESULTS / 'joint-mask04-12a-modebit66-holdout.json'
RAW_HOLDOUT = tuple(RESULTS / f'joint-mask04-12a-modebit66-holdout-{mode}-177.json'
                    for mode in ('held81', 'edge32'))
OUT = RESULTS / 'joint-mask04-12a-modebit66-diagnosis.json'


def run(out=OUT):
    old = []
    for path in (*CAPTURES, *RAW):
        for case in json.loads(path.read_text())['cases']:
            limit = boundary(path, case)
            for index, symbol in enumerate(case['multi_visit_symbols']):
                symbol['visits']['46']['mode_bit5'] = int(
                    limit is not None and index >= limit)
            old.append(case)
    prior_labels = json.loads(GRAPH.read_text())['mode_bit_graph']['relative_phase']
    known = {int(key, 16) for key in prior_labels}
    summary = json.loads(HOLDOUT.read_text())
    fresh = []
    diagnostics = []
    for mode, path in zip(('held81', 'edge32'), RAW_HOLDOUT):
        for case in json.loads(path.read_text())['cases']:
            for index, symbol in enumerate(case['multi_visit_symbols']):
                symbol['visits']['46']['mode_bit5'] = int(
                    mode == 'edge32' and index >= 32)
            fresh.append(case)
            keys = [code(symbol, FEATURES)
                    for symbol in case['multi_visit_symbols']]
            row = next(item for item in summary['cases']
                       if item['mode'] == mode and
                       item['selector'] == case['selector'])
            wrong = row['wrong_decision_indices']
            involving_unseen = [index for index in wrong
                                if keys[index] not in known or
                                keys[index - 1] not in known]
            diagnostics.append(dict(
                mode=mode, selector=case['selector'],
                wrong_decisions=len(wrong),
                wrong_involving_unseen=len(involving_unseen),
                unseen_frequencies={f'{key:03X}': keys.count(key)
                                    for key in sorted(set(keys) - known)}))
    if len(old) != 66 or len(fresh) != 4:
        raise ValueError('case population changed')
    joined = solve(old + fresh, FEATURES, STEPS)
    if ((joined['state_codes'], joined['components'],
         joined['directed_conflicts']) != (64, [64], 0)):
        raise ValueError('joined phase graph changed')
    new_labels = {key: (phase + 1) & 3
                  for key, phase in joined['relative_phase'].items()
                  if int(key, 16) not in known}
    frozen_labels = {key: gate_phase(int(key, 16)) for key in new_labels}
    if (new_labels != {'0C2': 1, '32D': 3, '336': 2} or
            frozen_labels != {'0C2': 1, '32D': 2, '336': 2} or
            any(row['wrong_decisions'] != row['wrong_involving_unseen']
                for row in diagnostics)):
        raise ValueError('holdout failure classification changed')
    sources = (Path(__file__), GRAPH, HOLDOUT, *RAW_HOLDOUT,
               HERE / 'joint_mask04_12a_modebit66_cover.py',
               HERE / 'joint_mask04_12a_modebit66_graph.py',
               HERE / 'joint_mask04_12a_0d_feature_graph.py',
               *CAPTURES, *RAW)
    report = dict(experiment='frozen mode-bit cover holdout failure diagnosis',
                  development_streams=len(old), holdout_streams=len(fresh),
                  prior_states=len(known), joined_graph=joined,
                  new_state_desired_labels=new_labels,
                  new_state_frozen_labels=frozen_labels,
                  holdout_diagnostics=diagnostics,
                  limitations=[
                      'The joined labels use holdout expected dibits; these streams are now development data for any revised decoder.',
                      'A zero-conflict graph does not identify a photo-package gate or physical mode route.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print('joined states', result['joined_graph']['state_codes'],
          'conflicts', result['joined_graph']['directed_conflicts'],
          'wrong labels', {key: label for key, label in
                           result['new_state_frozen_labels'].items()
                           if label != result['new_state_desired_labels'][key]})
