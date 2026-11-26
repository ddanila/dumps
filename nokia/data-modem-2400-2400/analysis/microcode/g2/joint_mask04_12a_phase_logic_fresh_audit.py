"""Audit new-state phase-logic challenges without refitting their predictions."""

import hashlib
import itertools
import json
from pathlib import Path

from joint_mask04_12a_phase_potential import HERE, phase_potential

DEVELOPMENT = (
    HERE / 'results/joint-mask04-12a-fifth-receive-bit.json',
    HERE / 'results/joint-mask04-12a-frozen-fifth-new-payloads.json',
)
FRESH = {offset: HERE / f'results/joint-mask04-12a-phase-logic-fresh-{offset}.json'
         for offset in (16, 80)}
POTENTIAL = HERE / 'results/joint-mask04-12a-phase-potential.json'


def graph_check(cases):
    results = [(conflicts, convention)
               for convention in itertools.permutations(range(4))
               for _, conflicts, _ in [phase_potential(cases, convention)]]
    return dict(zero_conflict_conventions=sum(conflicts == 0
                                              for conflicts, _ in results),
                minimum_conflicts=min(conflicts for conflicts, _ in results),
                best_conventions=[list(convention)
                                  for conflicts, convention in results
                                  if conflicts == min(value for value, _ in results)])


def run(out=HERE / 'results/joint-mask04-12a-phase-logic-fresh-audit.json'):
    development = [case for path in DEVELOPMENT
                   for case in json.loads(path.read_text())['cases']]
    reports = {offset: json.loads(path.read_text())
               for offset, path in FRESH.items()}
    known = set(json.loads(POTENTIAL.read_text())['state_phase'])
    cases = {}
    for offset, report in reports.items():
        rows = []
        for case in report['cases']:
            logic = case['phase_logic']
            states = logic['six_bit_states']
            old_errors = [i for i in logic['wrong_indices']
                          if states[i - 1] in known and states[i] in known]
            rows.append(dict(selector=case['selector'],
                             payload=case['payload'],
                             wrong=len(logic['wrong_indices']),
                             known_state_transition_wrong_indices=old_errors,
                             new_state_transition_wrong_indices=[i for i in logic['wrong_indices']
                                                                  if i not in old_errors],
                             new_states=logic['new_states'],
                             lookup_unknown=len(case['unknown_indices']),
                             lookup_new_keys=len(case['new_transition_keys']),
                             reference_wrong=len(case['reference_wrong_indices']),
                             line_bytes_recovered=logic['readout']['recovered_line_bytes']))
        cases[str(offset)] = rows
    graphs = {str(offset): graph_check(development + report['cases'])
              for offset, report in reports.items()}
    graphs['combined'] = graph_check(development +
                                     [case for report in reports.values()
                                      for case in report['cases']])
    paths = (Path(__file__), POTENTIAL, *DEVELOPMENT, *FRESH.values(),
             HERE / 'joint_mask04_12a_phase_potential.py',
             HERE / 'joint_mask04_12a_phase_logic_fresh.py')
    result = dict(experiment='fresh-payload carrier-start audit of frozen six-bit phase logic',
                  cases=cases, graph_compatibility=graphs,
                  limitations=[
                      'A graph contradiction excludes a static per-state phase rule for these exact six-bit captures; it does not exclude a receiver with additional carrier or timing state.',
                      'The carrier offsets and receive clock are diagnostic assumptions; physical routes remain untraced.',
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(result, indent=2) + '\n')
    print('graphs', graphs, flush=True)
    return result


if __name__ == '__main__':
    run()
