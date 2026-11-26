"""Audit the mode-dependent phase label conflict and conditional gate mux."""

import hashlib
import json
from pathlib import Path

from joint_mask04_12a_multivisit_phase_screen import SELECTED, sample_state
from joint_mask04_12a_row0_boolean import phase
from joint_mask04_12a_row0_serial_timing import covers_from_model

HERE = Path(__file__).resolve().parent
OLD = HERE / 'results/joint-mask04-12a-row0-boolean-twentytwo.json'
NEW = HERE / 'results/joint-mask04-12a-mode-phase-holdout.json'
CALL = HERE / 'results/joint-mask04-12a-row-mode-edge.json'
BASELINES = (
    HERE / 'results/joint-mask04-12a-row0-boolean-twenty-fresh-88.json',
    HERE / 'results/joint-mask04-12a-row0-boolean-phase112.json',
)
OUT = HERE / 'results/joint-mask04-12a-mode-gate-merge-audit.json'


def score(symbols, expected, covers, inverse):
    states = [sample_state(symbol, SELECTED) for symbol in symbols]
    phases = [phase(state, covers) for state in states]
    wrong = [index for index, (before, after) in enumerate(
        zip(phases, phases[1:]), 1)
        if inverse[(after - before) & 3] != expected[index]]
    return wrong, states


def run(out=OUT):
    old = json.loads(OLD.read_text())
    new = json.loads(NEW.read_text())
    call = json.loads(CALL.read_text())
    old_covers = covers_from_model(old)
    new_covers = covers_from_model(new)
    inverse = {step: dibit for dibit, step in
               enumerate(old['fixture']['phase_convention'])}
    old_labels = {int(key, 16): value for key, value in old['state_phase'].items()}
    new_labels = {int(key, 16): value for key, value in
                  new['trained_state_phase'].items()}
    clashes = {f'{state:02X}': dict(mode01=old_labels[state],
                                  mode81=new_labels[state])
               for state in old_labels.keys() & new_labels.keys()
               if old_labels[state] != new_labels[state]}
    if clashes != {'09': dict(mode01=3, mode81=2)}:
        raise ValueError(('mode-specific state labels changed', clashes))
    baseline = []
    for path in BASELINES:
        for case in json.loads(path.read_text())['cases']:
            wrong, states = score(case['multi_visit_symbols'],
                                  case['expected_dibits'], old_covers, inverse)
            if wrong:
                raise ValueError(('old gate baseline changed', path.name, wrong))
            baseline.append(dict(source=path.name, selector=case['selector'],
                                 level=case['level'], wrong_indices=wrong,
                                 state09_visits=sum(value == 0x09 for value in states)))
    call_source = next(case for case in
                       json.loads(BASELINES[1].read_text())['cases']
                       if case['selector'] == '40')
    training = []
    for case in call['cases']:
        wrong, states = score(case['states'], call_source['expected_dibits'],
                              new_covers, inverse)
        if wrong:
            raise ValueError(('new mode gate call training changed', case['mode'], wrong))
        training.append(dict(mode=case['mode'], wrong_indices=wrong,
                             state09_visits=sum(value == 0x09 for value in states)))
    holdout = []
    answer_source = next(case for case in
                         json.loads(BASELINES[1].read_text())['cases']
                         if case['selector'] == '60')
    expected_payload = [int(value, 16) for value in answer_source['payload']]
    for case in new['cases']:
        if (case['frozen_gate_wrong_indices'] or
                not case['recovered_matches_offered'] or
                case['controller_errors'] or
                case['controller_decoded_bytes'] != expected_payload):
            raise ValueError(('answer holdout changed', case['mode']))
        holdout.append(dict(mode=case['mode'],
                            wrong_indices=case['frozen_gate_wrong_indices'],
                            recovered_matches_offered=case['recovered_matches_offered'],
                            controller_decoded_bytes=case['controller_decoded_bytes']))
    paths = (Path(__file__), OLD, NEW, CALL, *BASELINES)
    report = dict(experiment='mode-bit-gated phase readout consistency across saved PROM streams',
                  fixture=dict(mode_flag='assumed D3EB bit7: 01=0, 81/A1=1',
                               mode0_gate=OLD.name, mode1_gate=NEW.name,
                               phase_convention=old['fixture']['phase_convention']),
                  label_conflicts_without_mode_bit=clashes,
                  baseline_mode01=baseline,
                  call_mode81_A1=training,
                  answer_mode81_A1_holdout=holdout,
                  limitations=[
                      'This is a conditional mux of two external Boolean readouts, not an identified DSC instruction or photographed mode connection.',
                      'The answer-side rows are verified from the prior full-PROM holdout report; no new PROM execution occurs in this audit.',
                      'A carrier-offset change may also require a distinct gate; only the saved mode-01 and phase-112 mode-81/A1 fixtures are covered.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    report = run()
    print('mode-01 cases', len(report['baseline_mode01']))
    print('conflict', report['label_conflicts_without_mode_bit'])
