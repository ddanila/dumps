"""Test development-trained five-bit receive transitions on controller A4/A5."""

import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_controller_continuation as bridge
import joint_mask04_12a_joined_a4_data as joined
from joint_mask04_12a_fifth_receive_bit import feature
from receiver_mask04_offset_visit_phase import project

HERE = Path(__file__).resolve().parent
DEVELOPMENT = HERE / 'results/joint-mask04-12a-fifth-receive-bit.json'
PRIOR = HERE / 'results/joint-mask04-12a-controller-continuation.json'
CANDIDATES = (('first', 4), ('second', 5), ('second', 6))


def training_table(cases, source, bit):
    table = {}
    for case in cases:
        states = [feature(a, b, source, bit)
                  for a, b in zip(case['first_y'], case['second_y'])]
        for i, (before, after) in enumerate(zip(states, states[1:]), 1):
            key = (before << 5) | after
            value = case['expected_dibits'][i]
            if key in table and table[key] != value:
                raise ValueError(('development key conflict', source, bit, key))
            table[key] = value
    return table


def run(out=HERE / 'results/joint-mask04-12a-fifth-bit-holdout.json'):
    development = json.loads(DEVELOPMENT.read_text())
    prior = json.loads(PRIOR.read_text())
    observed = []
    original = joined.loopback.capture

    def capture_with_y(mapping, base, pcm, expected):
        result = original(mapping, base, pcm, expected)
        rows = project(result[2], 46, 93)
        observed.append(dict(expected_dibits=expected,
                             first_y=[r['visits']['47']['y3f8'] for r in rows],
                             second_y=[r['visits']['94']['y3f8'] for r in rows]))
        return result

    with tempfile.TemporaryDirectory() as temp:
        with patch.object(joined.loopback, 'capture', capture_with_y):
            replay = bridge.run(Path(temp) / 'bridge.json')
    if len(observed) != 2:
        raise ValueError('joined controller capture count changed')
    cases = []
    for index, selector in enumerate(('40', '60')):
        source = observed[index]
        saved = next(c for c in prior['cases'] if c['selector'] == selector)
        current = next(c for c in replay['cases'] if c['selector'] == selector)
        if (current['tx_trace_digest'] != saved['tx_trace_digest'] or
                current['rx_trace_digest'] != saved['rx_trace_digest']):
            raise ValueError(('joined controller replay changed', selector))
        rows = []
        for which, bit in CANDIDATES:
            table = training_table(development['cases'], which, bit)
            states = [feature(a, b, which, bit)
                      for a, b in zip(source['first_y'], source['second_y'])]
            decisions = [None] + [table.get((a << 5) | b)
                                  for a, b in zip(states, states[1:])]
            wrong = [i for i, (got, want) in enumerate(zip(
                decisions[1:], source['expected_dibits'][1:]), 1)
                     if got is not None and got != want]
            unknown = [i for i, got in enumerate(decisions[1:], 1)
                       if got is None]
            rows.append(dict(source=which, bit=bit,
                             trained_transition_keys=len(table),
                             wrong_indices=wrong,
                             unknown_indices=unknown,
                             a4_wrong=sum(33 <= i <= 64 for i in wrong),
                             a4_unknown=sum(33 <= i <= 64 for i in unknown),
                             a5_wrong=sum(65 <= i <= 96 for i in wrong),
                             a5_unknown=sum(65 <= i <= 96 for i in unknown)))
        cases.append(dict(selector=selector,
                          tx_trace_digest=current['tx_trace_digest'],
                          rx_trace_digest=current['rx_trace_digest'],
                          expected_dibits=source['expected_dibits'],
                          first_y=source['first_y'],
                          second_y=source['second_y'],
                          candidates=rows))
        print(selector,[(r['source'],r['bit'],r['a5_wrong'],r['a5_unknown'])
                        for r in rows],flush=True)
    paths = (Path(__file__), DEVELOPMENT, PRIOR,
             HERE / 'joint_mask04_12a_controller_continuation.py',
             HERE / 'joint_mask04_12a_joined_a4_data.py',
             HERE / 'joint_mask04_12a_fifth_receive_bit.py',
             HERE.parent / 'assumed/execute.py')
    report = dict(experiment='five-bit static transition rule on controller A4/A5 holdout',
                  fixture=dict(development='fresh payloads at 75/100/125% plus half-quadrant fresh payloads',
                               holdout='separate controller-derived A4/A5 continuous DSC run',
                               candidate_bits=CANDIDATES,
                               capture_visits=[46,93]),
                  cases=cases,
                  limitations=['Known development payload labels select the candidate feature and transition table.',
                               'A4/A5 holdout labels are used only for scoring, not table fitting.',
                               'The two capture clocks, external logic, converter buses and serial route remain hypotheses.'],
                  source_sha256={str(p.relative_to(HERE.parents[4])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
