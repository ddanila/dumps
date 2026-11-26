"""Audit frozen row-0 holdouts and explicitly post-hoc phase extensions."""

import hashlib
import json
from pathlib import Path

from joint_mask04_12a_multivisit_phase_screen import HERE, INPUTS, SELECTED, score

SCREEN = HERE / 'results/joint-mask04-12a-multivisit-phase-screen.json'
FRESH = {offset: HERE / f'results/joint-mask04-12a-row0-fresh-{offset}.json'
         for offset in (0, 64)}


def run(out=HERE / 'results/joint-mask04-12a-row0-fresh-audit.json'):
    development = [case for path in INPUTS
                   for case in json.loads(path.read_text())['cases']]
    fresh = {offset: json.loads(path.read_text())
             for offset, path in FRESH.items()}
    outcomes = []
    for offset, report in fresh.items():
        for case in report['cases']:
            result = case['row_phase']
            outcomes.append(dict(offset=offset, selector=case['selector'],
                                 payload=case['payload'],
                                 wrong_indices=result['wrong_indices'],
                                 unknown_indices=result['unknown_indices'],
                                 payload_wrong=sum(i >= 33 for i in result['wrong_indices']),
                                 payload_unknown=sum(i >= 33 for i in result['unknown_indices']),
                                 new_states=result['new_states'],
                                 six_bit_lookup_wrong_indices=case['wrong_indices'],
                                 six_bit_lookup_unknown_indices=case['unknown_indices'],
                                 reference_wrong_indices=case['reference_wrong_indices'],
                                 recovered_line_bytes=result['readout']['recovered_line_bytes']))
    graph = {name: {key: value for key, value in score(cases, SELECTED).items()
                    if key in ('minimum_conflicts', 'observed_states',
                               'component_sizes', 'zero_conventions')}
             for name, cases in (
                 ('development', development),
                 ('plus0', development + fresh[0]['cases']),
                 ('plus64', development + fresh[64]['cases']),
                 ('all', development + fresh[0]['cases'] + fresh[64]['cases']))}
    paths = (Path(__file__), SCREEN, *INPUTS, *FRESH.values(),
             HERE / 'joint_mask04_12a_multivisit_phase_screen.py',
             HERE / 'joint_mask04_12a_row0_fresh.py')
    report = dict(experiment='frozen row-0 phase holdout and post-hoc graph audit',
                  fixture=dict(decisions_per_run=64, payload_dibits_per_run=32,
                               feature=SELECTED, offsets=[0, 64]),
                  outcomes=outcomes, graph_compatibility=graph,
                  limitations=[
                      'The graph extension uses the fresh labels after the frozen rule abstained; it is development evidence, not holdout success.',
                      'The internal row-0 bit is not a traced external latch or USART input.',
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    print('graph', {name: (row['minimum_conflicts'], row['observed_states'],
                          row['component_sizes']) for name, row in graph.items()},
          flush=True)
    return report


if __name__ == '__main__':
    run()
