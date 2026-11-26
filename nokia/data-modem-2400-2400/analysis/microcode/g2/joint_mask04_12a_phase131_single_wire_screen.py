"""Screen one captured-bit substitution against saved real-PROM streams."""

import hashlib
import itertools
import json
from pathlib import Path

from joint_mask04_12a_multivisit_phase_screen import SELECTED, sample_state
from photo_u15_u19_u21_phase_route import circuit

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
INPUTS = (
    (0, 'prior', 'joint-mask04-12a-row0-boolean-twenty-fresh-88.json'),
    (1, 'prior', 'joint-mask04-12a-mode-twelve-holdout.json'),
    (1, 'prior', 'joint-mask04-12a-mode-phase128-challenge.json'),
    (1, 'prior', 'joint-mask04-12a-mode-phase125-challenge.json'),
    (1, 'prior', 'joint-mask04-12a-mode-phase131-baseline-control.json'),
    (1, 'prior', 'joint-mask04-12a-mode-phase131-intermediate-gain.json'),
    (1, 'gain', 'joint-mask04-12a-mode-phase131-gain-boundary.json'),
    (1, 'gain', 'joint-mask04-12a-mode-phase131-gain-challenge.json'),
)
OUT = RESULTS / 'joint-mask04-12a-phase131-single-wire-screen.json'
CONVENTION = (2, 1, 3, 0)
INVERSE = {step: dibit for dibit, step in enumerate(CONVENTION)}


def evaluate(cases, replacement):
    errors = {'prior': 0, 'gain': 0}
    for case in cases:
        phases = []
        for symbol in case['symbols']:
            state = sample_state(symbol, SELECTED)
            if replacement is not None:
                target, visit, site, bit, invert = replacement
                value = ((symbol['visits'][visit][site] >> bit) & 1) ^ invert
                state = (state & ~(1 << target)) | (value << target)
            phases.append(circuit(state, case['mode']))
        errors[case['group']] += sum(
            INVERSE[(phases[index] - phases[index - 1]) & 3]
            != case['expected'][index]
            for index in range(1, len(phases)))
    return errors


def run(out=OUT):
    cases = []
    counts = {'prior': 0, 'gain': 0}
    for mode, group, name in INPUTS:
        saved = json.loads((RESULTS / name).read_text())
        for case in saved['cases']:
            if len(case['multi_visit_symbols']) != 65 or len(case['expected_dibits']) != 65:
                raise ValueError(('saved symbol count changed', name))
            cases.append(dict(mode=mode, group=group,
                              symbols=case['multi_visit_symbols'],
                              expected=case['expected_dibits']))
            counts[group] += 1
    if counts != {'prior': 16, 'gain': 6}:
        raise ValueError(('saved case count changed', counts))
    baseline = evaluate(cases, None)
    if baseline != {'prior': 0, 'gain': 72}:
        raise ValueError(('frozen circuit score changed', baseline))
    rows = []
    for target, visit, site, bit, invert in itertools.product(
            range(7), ('46', '93'), ('y3f8', 'row0'), range(8), (0, 1)):
        errors = evaluate(cases, (target, visit, site, bit, invert))
        rows.append(dict(target_state_bit=target, visit=visit, site=site,
                         source_bit=bit, inverted=bool(invert),
                         prior_errors=errors['prior'],
                         gain_errors=errors['gain'],
                         total_errors=sum(errors.values())))
    preserving = [row for row in rows if row['prior_errors'] == 0]
    best = sorted(rows, key=lambda row: (
        row['total_errors'], row['prior_errors'], row['gain_errors'],
        row['target_state_bit'], row['visit'], row['site'],
        row['source_bit'], row['inverted']))
    if (len(rows) != 448 or len(preserving) != 137 or
            min(row['gain_errors'] for row in preserving) != 72 or
            best[0]['total_errors'] != 66 or
            (best[0]['prior_errors'], best[0]['gain_errors']) != (66, 0)):
        raise ValueError('single-wire screen classification changed')
    paths = (Path(__file__), HERE / 'photo_u15_u19_u21_phase_route.py',
             *(RESULTS / name for _, _, name in INPUTS))
    report = dict(experiment='one-wire capture substitution screen on frozen package circuit',
                  fixture=dict(prior_cases=counts['prior'], gain_cases=counts['gain'],
                               decisions_per_case=64,
                               candidate_sources='both visits 46/93, Y3F8/row0, bits 0..7, either polarity',
                               changed_outputs='one of seven captured state bits; all other wiring and logic frozen'),
                  original_errors=baseline,
                  candidates=len(rows),
                  prior_preserving_candidates=len(preserving),
                  minimum_gain_errors_given_zero_prior_errors=72,
                  best_total_candidates=best[:10],
                  minimum_prior_errors_given_zero_gain_errors=min(
                      row['prior_errors'] for row in rows if row['gain_errors'] == 0),
                  limitations=[
                      'This is a replay of saved real-PROM snapshots; it does not rerun the PROMs or sample a different capture edge.',
                      'Only one captured bit source or polarity changes at a time; multiwire logic and unrecorded visits are outside the screen.',
                      'A candidate is judged by the frozen external circuit, not by an independently synthesized decision function.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print(result['original_errors'], result['candidates'],
          result['prior_preserving_candidates'],
          result['minimum_gain_errors_given_zero_prior_errors'])
