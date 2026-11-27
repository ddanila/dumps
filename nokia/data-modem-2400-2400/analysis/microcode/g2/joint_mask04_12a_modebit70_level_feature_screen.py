"""Screen one extra captured bit after the frozen ten-bit level failure."""

import hashlib
import json
from pathlib import Path

from joint_mask04_12a_0d_feature_graph import solve
from joint_mask04_12a_modebit66_graph import CAPTURES, RAW, boundary
from joint_mask04_12a_modebit70_revision import FEATURES, STEPS

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
OUT = RESULTS / 'joint-mask04-12a-modebit70-level-feature-screen.json'
VISITS = ('46', '47', '93', '94', '141')
SITES = ('row0', 'y3f8')
TRIALS = (
    (177, 'modebit66', 'holdout', ('held81', 'edge32')),
    (179, 'modebit70', 'holdout', ('held81', 'edge32')),
    (181, 'modebit70', 'late48', ('edge32', 'edge48')),
    (183, 'modebit70', 'lowgain', ('edge32', 'edge48')),
    (185, 'modebit70', 'gain105', ('edge32',)),
    (185, 'modebit70', 'gain115', ('edge32', 'edge48')),
    (185, 'modebit70', 'highgain', ('edge32', 'edge48')),
)
SELECTED = (('93', 'row0', 2), ('94', 'row0', 2))


def run(out=OUT):
    cases = []
    without_known_reference_errors = []
    sources = [Path(__file__),
               HERE / 'joint_mask04_12a_modebit70_revision.py',
               HERE / 'joint_mask04_12a_modebit66_graph.py',
               HERE / 'joint_mask04_12a_0d_feature_graph.py']
    for path in (*CAPTURES, *RAW):
        sources.append(path)
        for case in json.loads(path.read_text())['cases']:
            limit = boundary(path, case)
            for index, symbol in enumerate(case['multi_visit_symbols']):
                symbol['visits']['46']['mode_bit5'] = int(
                    limit is not None and index >= limit)
            cases.append(case)
            without_known_reference_errors.append(case)
    trial_counts = {}
    for offset, version, prefix, modes in TRIALS:
        for mode in modes:
            path = RESULTS / (f'joint-mask04-12a-{version}-{prefix}-'
                              f'{mode}-{offset}.json')
            sources.append(path)
            trial_counts[f'{prefix}-{mode}-{offset}'] = 0
            for case in json.loads(path.read_text())['cases']:
                limit = None if mode == 'held81' else 48 if mode == 'edge48' else 32
                for index, symbol in enumerate(case['multi_visit_symbols']):
                    symbol['visits']['46']['mode_bit5'] = int(
                        limit is not None and index >= limit)
                cases.append(case)
                trial_counts[f'{prefix}-{mode}-{offset}'] += 1
                if not (prefix in ('gain105', 'gain115') and
                        case['selector'] == '40'):
                    without_known_reference_errors.append(case)
    if len(cases) != 92 or len(without_known_reference_errors) != 89:
        raise ValueError('level-screen stream population changed')
    base = solve(cases, FEATURES, STEPS)
    if (base['state_codes'], base['components'],
            base['directed_conflicts']) != (82, [82], 314):
        raise ValueError('ten-bit level graph changed')
    candidates = []
    for visit in VISITS:
        for site in SITES:
            for bit in range(8):
                feature = (visit, site, bit)
                graph = solve(cases, FEATURES + (feature,), STEPS)
                candidates.append(dict(visit=visit, site=site, bit=bit,
                                       state_codes=graph['state_codes'],
                                       directed_conflicts=graph['directed_conflicts'],
                                       components=graph['components']))
    zero = [row for row in candidates if row['directed_conflicts'] == 0]
    if (len(candidates), len(zero)) != (80, 6):
        raise ValueError('one-bit level screen changed')
    chosen = {}
    for feature in SELECTED:
        full = solve(cases, FEATURES + (feature,), STEPS)
        clean = solve(without_known_reference_errors, FEATURES + (feature,), STEPS)
        if ((full['state_codes'], full['directed_conflicts'],
             full['components']) != (91, 0, [91]) or
                (clean['state_codes'], clean['directed_conflicts'],
                 clean['components']) != (91, 0, [91])):
            raise ValueError(('row-0 Y2 phase graph changed', feature))
        chosen[f'{feature[0]}-{feature[1]}-{feature[2]}'] = dict(
            all_streams=full, known_reference_error_excluded_subset=clean)
    row2_shifts = sum(bool((symbol['visits']['93']['row0'] ^
                            symbol['visits']['94']['row0']) & 4)
                      for case in cases
                      for symbol in case['multi_visit_symbols'])
    report = dict(experiment='one-extra-bit capture screen across frozen mode-bit level failures',
                  fixture=dict(streams=len(cases),
                               known_reference_error_excluded_streams=len(without_known_reference_errors),
                               symbols=65 * len(cases),
                               phase_convention=STEPS,
                               base_features=FEATURES,
                               trial_counts=trial_counts),
                  ten_bit_graph=dict(states=base['state_codes'],
                                     directed_conflicts=base['directed_conflicts'],
                                     components=base['components']),
                  candidate_bits=candidates,
                  zero_conflict_bits=zero,
                  selected_row0_y2_graphs=chosen,
                  row0_y2_93_to_94_shifts=row2_shifts,
                  limitations=[
                      'All 92 streams were used to select the extra bit; zero conflicts are development evidence, not a fresh holdout.',
                      'Three call-side 1.05x/1.15x streams with independent reference errors are excluded only from the separate 89-stream subset check.',
                      'The mode bit and extra row-0 Y2 capture are assumed inputs; gate logic, pin nets and serial timing remain unproved.',
                      'A conflict-free graph does not by itself supply a Boolean phase decoder or a package-budgeted circuit.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print('streams', result['fixture']['streams'],
          'zero-conflict candidates', len(result['zero_conflict_bits']),
          'row2 shifts', result['row0_y2_93_to_94_shifts'])
