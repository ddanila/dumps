"""Diagnose the frozen receiver's 1.25x high-level holdout failure."""

import hashlib
import json
from pathlib import Path

from joint_mask04_12a_0d_feature_graph import code, solve
from joint_mask04_12a_modebit66_graph import CAPTURES, RAW, boundary
from joint_mask04_12a_modebit70_revision import FEATURES, STEPS, gate_phase

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
REVISION = RESULTS / 'joint-mask04-12a-modebit70-revision.json'
HOLDOUT = RESULTS / 'joint-mask04-12a-modebit70-highgain.json'
BASE_NEW = tuple(RESULTS / f'joint-mask04-12a-modebit66-holdout-{mode}-177.json'
                 for mode in ('held81', 'edge32'))
HIGH_RAW = tuple(RESULTS / f'joint-mask04-12a-modebit70-highgain-{mode}-185.json'
                 for mode in ('edge32', 'edge48'))
OUT = RESULTS / 'joint-mask04-12a-modebit70-highgain-diagnosis.json'


def annotate(case, edge):
    for index, symbol in enumerate(case['multi_visit_symbols']):
        symbol['visits']['46']['mode_bit5'] = int(
            edge is not None and index >= edge)


def run(out=OUT):
    old = []
    for path in (*CAPTURES, *RAW):
        for case in json.loads(path.read_text())['cases']:
            annotate(case, boundary(path, case))
            old.append(case)
    for mode, path in zip(('held81', 'edge32'), BASE_NEW):
        for case in json.loads(path.read_text())['cases']:
            annotate(case, None if mode == 'held81' else 32)
            old.append(case)
    prior = json.loads(REVISION.read_text())['mode_bit_graph']
    base = solve(old, FEATURES, STEPS)
    if (len(old), base['state_codes'], base['directed_conflicts'],
            base['components'], base['relative_phase']) != (
                70, 64, 0, [64], prior['relative_phase']):
        raise ValueError('frozen development graph changed')
    known = {int(key, 16) for key in prior['relative_phase']}
    challenge = json.loads(HOLDOUT.read_text())
    high = []
    diagnostics = []
    for mode, path in zip(('edge32', 'edge48'), HIGH_RAW):
        for case in json.loads(path.read_text())['cases']:
            annotate(case, 32 if mode == 'edge32' else 48)
            high.append(case)
            keys = [code(symbol, FEATURES)
                    for symbol in case['multi_visit_symbols']]
            scored = next(row for row in challenge['cases']
                          if row['mode'] == mode and
                          row['selector'] == case['selector'])
            wrong = scored['wrong_decision_indices']
            touching_new = [index for index in wrong
                            if keys[index] not in known or
                            keys[index - 1] not in known]
            diagnostics.append(dict(
                mode=mode, selector=case['selector'],
                wrong_decisions=len(wrong),
                wrong_touching_unseen=len(touching_new),
                unseen_frequencies={f'{key:03X}': keys.count(key)
                                    for key in sorted(set(keys) - known)},
                clipped_samples=scored['clipped_samples'],
                reference_wrong_indices=case['reference_wrong_indices']))
    joined = solve(old + high, FEATURES, STEPS)
    if (len(high), joined['state_codes'], joined['components'],
            joined['directed_conflicts']) != (4, 70, [70], 0):
        raise ValueError('high-level joined graph changed')
    new_desired = {key: (phase + 1) & 3
                   for key, phase in joined['relative_phase'].items()
                   if int(key, 16) not in known}
    new_frozen = {key: gate_phase(int(key, 16)) for key in new_desired}
    wrong_labels = {key: dict(desired=new_desired[key],
                              frozen=new_frozen[key])
                    for key in new_desired if new_desired[key] != new_frozen[key]}
    if (wrong_labels != {
            '02E': dict(desired=3, frozen=2),
            '108': dict(desired=0, frozen=1),
            '22E': dict(desired=3, frozen=2),
            '308': dict(desired=0, frozen=1)} or
            any(row['wrong_decisions'] != row['wrong_touching_unseen']
                or row['reference_wrong_indices'] or
                row['clipped_samples'] != 2 for row in diagnostics)):
        raise ValueError('high-level failure classification changed')
    sources = (Path(__file__), REVISION, HOLDOUT, *HIGH_RAW,
               *BASE_NEW, *CAPTURES, *RAW,
               HERE / 'joint_mask04_12a_modebit70_revision.py',
               HERE / 'joint_mask04_12a_modebit66_graph.py',
               HERE / 'joint_mask04_12a_0d_feature_graph.py')
    report = dict(experiment='frozen mode-bit receiver high-level failure diagnosis',
                  development_streams=len(old),
                  high_level_streams=len(high),
                  frozen_state_codes=len(known),
                  joined_graph=joined,
                  new_desired_labels=new_desired,
                  new_frozen_labels=new_frozen,
                  wrong_new_labels=wrong_labels,
                  case_diagnostics=diagnostics,
                  limitations=[
                      'The joined labels use high-level expected dibits; offset-185 streams become development data for any revised decoder.',
                      'Two clipped samples occur in each stream, but this audit does not establish whether clipping causes the state changes or decision errors.',
                      'Zero graph conflicts do not prove a package gate or physical mode/serial connection.'
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
          'wrong new labels', result['wrong_new_labels'])
