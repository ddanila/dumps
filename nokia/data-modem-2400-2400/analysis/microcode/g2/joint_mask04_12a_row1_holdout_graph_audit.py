"""Audit frozen row-0 Y1 holdout and two-bit graph capacity."""

import hashlib
import json
from pathlib import Path

from joint_mask04_12a_0d_feature_graph import INPUTS, solve

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
HOLDOUT = RESULTS / 'joint-mask04-12a-row1-phase-holdout.json'
RAW = (
    RESULTS / 'joint-mask04-12a-row1-phase-holdout-141.json',
    RESULTS / 'joint-mask04-12a-row1-phase-holdout-143.json',
)
OUT = RESULTS / 'joint-mask04-12a-row1-holdout-graph-audit.json'
VISITS = ('46', '47', '93', '94', '141')
SITES = ('row0', 'y3f8')
STEPS = (2, 1, 3, 0)


def candidates():
    return [(visit, site, bit) for visit in VISITS
            for site in SITES for bit in range(8)]


def compact(result):
    return dict(state_codes=result['state_codes'],
                directed_conflicts=result['directed_conflicts'],
                components=result['components'])


def run(out=OUT):
    holdout = json.loads(HOLDOUT.read_text())
    cases = [case for path in (*INPUTS, *RAW)
             for case in json.loads(path.read_text())['cases']]
    if len(cases) != 22 or any(len(case['multi_visit_symbols']) != 65
                                for case in cases):
        raise ValueError('combined receive case count changed')
    if ([(case['carrier_offset'], case['selector'],
          len(case['unseen_keys']),
          len(case['known_transition_wrong_indices']),
          case['recovered_matches_offered'])
         for case in holdout['cases']] != [
             (141, '40', 0, 0, True), (141, '60', 0, 0, True),
             (143, '40', 2, 5, None), (143, '60', 2, 4, None)]):
        raise ValueError('frozen row-1 holdout classification changed')
    if any(case['clipped_samples'] for case in holdout['cases']):
        raise ValueError('holdout clipping changed')
    single = []
    for feature in candidates():
        result = solve(cases, (feature,), STEPS)
        single.append(dict(feature=feature, **compact(result)))
    if (min(row['directed_conflicts'] for row in single) != 24 or
            any(row['directed_conflicts'] == 0 for row in single)):
        raise ValueError('single-feature screen changed')
    pairs = {}
    for name, seed in (('row0_bit1', ('46', 'row0', 1)),
                       ('first_y4', ('46', 'y3f8', 4))):
        rows = []
        for feature in candidates():
            if feature == seed:
                continue
            rows.append(dict(feature=feature,
                             **compact(solve(cases, (seed, feature), STEPS))))
        zero = [row['feature'] for row in rows
                if row['directed_conflicts'] == 0]
        if zero != [('94', 'y3f8', 4), ('94', 'y3f8', 5)]:
            raise ValueError(('two-feature screen changed', name, zero))
        pairs[name] = dict(seed=seed, zero_conflict_features=zero,
                           best=sorted(rows,
                                       key=lambda row: (row['directed_conflicts'],
                                                        row['state_codes']))[:5])
    selected = solve(cases, (('46', 'row0', 1), ('94', 'y3f8', 4)), STEPS)
    if (selected['state_codes'] != 31 or
            selected['directed_conflicts'] != 0 or
            selected['components'] != [31]):
        raise ValueError('selected two-bit graph changed')
    paths = (Path(__file__), HOLDOUT, *RAW, *INPUTS,
             HERE / 'joint_mask04_12a_0d_feature_graph.py',
             HERE / 'joint_mask04_12a_row1_phase_holdout.py')
    report = dict(experiment='fresh row-1 lookup holdout and two-bit phase graph capacity',
                  fixture=dict(streams=len(cases), symbols=65 * len(cases),
                               phase_convention=STEPS,
                               inspected_visits=VISITS, sites=SITES,
                               single_features=len(single)),
                  holdout_cases=[dict(carrier_offset=case['carrier_offset'],
                                      selector=case['selector'],
                                      unseen_keys=case['unseen_keys'],
                                      known_transition_errors=len(
                                          case['known_transition_wrong_indices']),
                                      exact_line=case['recovered_matches_offered'],
                                      exact_controller=(case['controller_decoded_bytes'] ==
                                          [int(value, 16) for value in case['payload']]
                                          if case['controller_decoded_bytes'] else None))
                                 for case in holdout['cases']],
                  single_feature_screen=single,
                  pair_screens=pairs,
                  selected_two_bit_graph=selected,
                  limitations=[
                      'The carrier-141 streams are genuine frozen-table holdouts; the two-bit graph screen uses them and the failed carrier-143 streams as development data.',
                      'Zero phase-graph conflicts do not implement a Boolean circuit or prove physical latch and serial connections.',
                      'The selected two-bit graph requires a fresh untouched payload/carrier/gain challenge before transfer can be claimed.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    report = run()
    print('single min', min(row['directed_conflicts'] for row in
                            report['single_feature_screen']),
          'selected', report['selected_two_bit_graph']['state_codes'])
