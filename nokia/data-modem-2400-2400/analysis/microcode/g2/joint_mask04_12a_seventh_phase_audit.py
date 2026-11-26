"""Audit frozen seven-bit holdouts and post-hoc graph compatibility."""

import hashlib
import json
from pathlib import Path

from joint_mask04_12a_seventh_phase_bit import DEVELOPMENT, HERE, score

SCREEN = HERE / 'results/joint-mask04-12a-seventh-phase-bit.json'
FRESH = {offset: HERE / f'results/joint-mask04-12a-seventh-phase-fresh-{offset}.json'
         for offset in (48, 112)}
FEATURES = (('first', 4), ('second', 5), 'full')


def run(out=HERE / 'results/joint-mask04-12a-seventh-phase-audit.json'):
    development = [case for path in DEVELOPMENT
                   for case in json.loads(path.read_text())['cases']]
    reports = {offset: json.loads(path.read_text())
               for offset, path in FRESH.items()}
    holdouts = []
    for offset, report in reports.items():
        for case in report['cases']:
            row = dict(offset=offset, selector=case['selector'],
                       payload=case['payload'],
                       reference_wrong_indices=case['reference_wrong_indices'],
                       sixth_bit_lookup_wrong_indices=case['wrong_indices'],
                       sixth_bit_lookup_unknown_indices=case['unknown_indices'],
                       seven_bit={})
            for name, candidate in case['seventh_phase'].items():
                row['seven_bit'][name] = dict(
                    wrong_indices=candidate['wrong_indices'],
                    unknown_indices=candidate['unknown_indices'],
                    payload_wrong=sum(index >= 33 for index
                                      in candidate['wrong_indices']),
                    payload_unknown=sum(index >= 33 for index
                                        in candidate['unknown_indices']),
                    new_states=candidate['new_states'],
                    cross_component_indices=candidate['cross_component_indices'],
                    recovered_line_bytes=candidate['readout']['recovered_line_bytes'])
            holdouts.append(row)
    graph_compatibility = {}
    for name, cases in (
            ('development', development),
            ('plus48', development + reports[48]['cases']),
            ('plus112', development + reports[112]['cases']),
            ('all', development + reports[48]['cases'] + reports[112]['cases'])):
        graph_compatibility[name] = {
            f'{feature[0]}{feature[1]}' if feature != 'full' else 'full':
            {key: value for key, value in score(cases, feature).items()
             if key in ('minimum_conflicts', 'observed_states',
                        'component_sizes', 'zero_conflict_conventions')}
            for feature in FEATURES}
    paths = (Path(__file__), SCREEN, *DEVELOPMENT, *FRESH.values(),
             HERE / 'joint_mask04_12a_seventh_phase_bit.py',
             HERE / 'joint_mask04_12a_seventh_phase_fresh.py')
    report = dict(experiment='seventh-bit frozen holdout and post-hoc compatibility audit',
                  fixture=dict(decisions_per_run=64, payload_dibits_per_run=32,
                               offsets=[48, 112],
                               candidate_features=[['first', 4], ['second', 5]]),
                  holdouts=holdouts,
                  graph_compatibility=graph_compatibility,
                  limitations=[
                      'Graph checks that include offset-48/112 labels are post-hoc diagnostics; those runs are no longer untouched holdouts for a refitted candidate.',
                      'Unknown decisions include unseen states and transitions across disconnected development components.',
                      'Neither tested seven-bit rule recovers complete payload bytes on the frozen holdouts.',
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    print('graph compatibility', {
        name: {feature: row['minimum_conflicts']
               for feature, row in variants.items()}
        for name, variants in graph_compatibility.items()}, flush=True)
    return report


if __name__ == '__main__':
    run()
