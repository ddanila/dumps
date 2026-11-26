"""Find irreducible dibit gaps in the saved 12A buffered-line readouts."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'results/joint-mask04-12a-buffered-line.json'
READOUTS = ('fixed_46_93', 'fixed_47_94', 'fixed_94_141')
DATA_DIBITS = 32


def audit(case):
    readouts = case['receiver_handoff']['readouts']
    if set(READOUTS) - set(readouts):
        raise ValueError('fixed-pair family changed')
    no_correct = []
    all_unknown = []
    only_wrong = []
    conflicting = []
    correct_known_counts = []
    for index in range(DATA_DIBITS):
        known = [name for name in READOUTS
                 if index not in readouts[name]['data_unknown_indices']]
        wrong = [name for name in known
                 if index in readouts[name]['data_wrong_indices']]
        correct = [name for name in known if name not in wrong]
        correct_known_counts.append(len(correct))
        if not correct:
            row = dict(data_dibit=index,
                       serial_bit_positions=[2 * index, 2 * index + 1],
                       byte_index=index // 4,
                       known_wrong=wrong)
            no_correct.append(row)
            (all_unknown if not known else only_wrong).append(row)
        if correct and wrong:
            conflicting.append(dict(data_dibit=index, correct=correct,
                                    wrong=wrong))
    if len(no_correct) != sum(count == 0 for count in correct_known_counts):
        raise ValueError('readout coverage accounting failed')
    return dict(selector=case['selector'],
                transmitter_trace_digest=case['tx_trace_digest'],
                receiver_trace_digest=case['receiver_handoff']['rx_trace_digest'],
                no_correct_dibit=no_correct,
                all_unknown=all_unknown,
                only_known_wrong=only_wrong,
                conflicting_known_labels=conflicting,
                correct_known_count_distribution={str(n): correct_known_counts.count(n)
                                                  for n in range(4)})


def run(out=HERE / 'results/joint-mask04-12a-readout-gap-audit.json'):
    source = json.loads(SOURCE.read_text())
    cases = [audit(case) for case in source['cases']]
    if [case['selector'] for case in cases] != ['40', '60']:
        raise ValueError('buffered controller cases changed')
    report = dict(experiment='dibit-level information gaps among saved 12A fixed readouts',
                  source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                  readouts=list(READOUTS),
                  cases=cases,
                  implication='A selector choosing one whole dibit from these three fixed readouts cannot produce all 32 correct data dibits in either mode.',
                  limitations=[
                      'This is a bound on the three saved fixed-pair decisions, not every possible DSC output or bit-level combination.',
                      'Expected dibits come from the controller stimulus and are used only to audit the saved holdout results.',
                      'No physical DAC, ADC, decision circuit or USART RxD net is identified.'
                  ],
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    for case in run()['cases']:
        print(case['selector'],
              'no correct', [row['data_dibit'] for row in case['no_correct_dibit']],
              'conflicts', [row['data_dibit'] for row in case['conflicting_known_labels']])
