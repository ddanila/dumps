"""Diagnose the eleven-bit late-edge holdout and screen one more bit."""

import hashlib
import json
from pathlib import Path

from joint_mask04_12a_0d_feature_graph import code, solve
from joint_mask04_12a_modebit66_graph import CAPTURES, RAW, boundary
from joint_mask04_12a_modebit70_level_feature_screen import TRIALS, VISITS, SITES
from joint_mask04_12a_modebit91_cover import FEATURES, STEPS, gate_phase

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
COVER = RESULTS / 'joint-mask04-12a-modebit91-cover.json'
HOLDOUT = RESULTS / 'joint-mask04-12a-modebit91-gain110-holdout.json'
NEW = tuple(RESULTS / f'joint-mask04-12a-modebit91-gain110-holdout-{mode}-189.json'
            for mode in ('edge32', 'edge48'))
OUT = RESULTS / 'joint-mask04-12a-modebit91-gain110-diagnosis.json'


def annotate(case, limit):
    for index, symbol in enumerate(case['multi_visit_symbols']):
        symbol['visits']['46']['mode_bit5'] = int(
            limit is not None and index >= limit)


def run(out=OUT):
    old = []
    sources = [Path(__file__), COVER, HOLDOUT,
               HERE / 'joint_mask04_12a_modebit91_cover.py',
               HERE / 'joint_mask04_12a_0d_feature_graph.py',
               HERE / 'joint_mask04_12a_modebit70_level_feature_screen.py',
               HERE / 'joint_mask04_12a_modebit66_graph.py']
    for path in (*CAPTURES, *RAW):
        sources.append(path)
        for case in json.loads(path.read_text())['cases']:
            annotate(case, boundary(path, case))
            old.append(case)
    for offset, version, prefix, modes in TRIALS:
        for mode in modes:
            path = RESULTS / (f'joint-mask04-12a-{version}-{prefix}-'
                              f'{mode}-{offset}.json')
            sources.append(path)
            for case in json.loads(path.read_text())['cases']:
                annotate(case, None if mode == 'held81' else
                         48 if mode == 'edge48' else 32)
                old.append(case)
    graph = json.loads(COVER.read_text())['phase_graph']
    if (len(old), solve(old, FEATURES, STEPS)['relative_phase']) != (
            92, graph['relative_phase']):
        raise ValueError('frozen eleven-bit development graph changed')
    known = {int(key, 16) for key in graph['relative_phase']}
    summary = json.loads(HOLDOUT.read_text())
    fresh = []
    case_checks = []
    for mode, path in zip(('edge32', 'edge48'), NEW):
        sources.append(path)
        for case in json.loads(path.read_text())['cases']:
            annotate(case, 32 if mode == 'edge32' else 48)
            fresh.append(case)
            keys = [code(symbol, FEATURES)
                    for symbol in case['multi_visit_symbols']]
            row = next(item for item in summary['cases']
                       if item['mode'] == mode and
                       item['selector'] == case['selector'])
            wrong = row['wrong_decision_indices']
            touching_unseen = [index for index in wrong
                               if keys[index] not in known or
                               keys[index - 1] not in known]
            known_conflicts = [dict(index=index,
                                    from_state=f'{keys[index-1]:03X}',
                                    to_state=f'{keys[index]:03X}',
                                    frozen_step=(gate_phase(keys[index]) -
                                                 gate_phase(keys[index-1])) & 3,
                                    required_step=STEPS[case['expected_dibits'][index]])
                               for index in wrong
                               if keys[index] in known and
                               keys[index - 1] in known]
            case_checks.append(dict(mode=mode, selector=case['selector'],
                                    wrong_decisions=len(wrong),
                                    wrong_touching_unseen=len(touching_unseen),
                                    known_state_conflicts=known_conflicts,
                                    reference_wrong_indices=case['reference_wrong_indices'],
                                    clipped_samples=row['clipped_samples']))
    joined = solve(old + fresh, FEATURES, STEPS)
    if ((len(fresh), joined['state_codes'], joined['components'],
         joined['directed_conflicts']) != (4, 94, [94], 132) or
            [(row['wrong_decisions'], row['wrong_touching_unseen'],
              len(row['known_state_conflicts'])) for row in case_checks]
            != [(0, 0, 0), (0, 0, 0), (4, 1, 3), (4, 1, 3)] or
            any(row['reference_wrong_indices'] or row['clipped_samples']
                for row in case_checks)):
        raise ValueError('fresh failure classification changed')
    candidates = []
    for visit in VISITS:
        for site in SITES:
            for bit in range(8):
                feature = (visit, site, bit)
                candidate = solve(old + fresh, FEATURES + (feature,), STEPS)
                candidates.append(dict(visit=visit, site=site, bit=bit,
                                       state_codes=candidate['state_codes'],
                                       directed_conflicts=candidate['directed_conflicts'],
                                       components=candidate['components']))
    zero = [row for row in candidates if row['directed_conflicts'] == 0]
    if len(candidates) != 80 or len(zero) != 13:
        raise ValueError('next captured-bit screen changed')
    report = dict(experiment='eleven-bit 1.10x late-edge failure and next-bit screen',
                  development_streams=len(old),
                  fresh_streams=len(fresh),
                  eleven_bit_joined_graph=joined,
                  case_checks=case_checks,
                  candidate_bits=candidates,
                  zero_conflict_bits=zero,
                  limitations=[
                      'The 80-bit feature screen uses all four offset-189 streams; candidates are development hypotheses, not independent validation.',
                      'Known-state phase conflicts rule out a static relabeling of the eleven-bit state under these fixtures.',
                      'Late row-0 Y2 storage, a further capture, gate logic and mode/serial/analog nets remain assumed.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print('joined conflicts', result['eleven_bit_joined_graph']['directed_conflicts'],
          'zero-conflict extra bits', len(result['zero_conflict_bits']))
