"""Screen a four-state counter qualifier against executed 3ED row bytes."""

import hashlib
import json
from pathlib import Path

from joint_mask04_12a_all_row_latch import decisions

HERE = Path(__file__).resolve().parent
CALL = HERE / 'results/joint-mask04-12a-all-row-latch.json'
ANSWER = HERE / 'results/joint-mask04-12a-all-row-answer.json'
SOURCE = HERE / 'results/joint-mask04-12a-row0-boolean-twenty-fresh-88.json'
LOGIC = HERE / 'results/joint-mask04-12a-row0-boolean-twenty.json'
OUT = HERE / 'results/joint-mask04-12a-u24-phase-screen.json'


def run(out=OUT):
    source = json.loads(SOURCE.read_text())
    model = json.loads(LOGIC.read_text())
    covers = [tuple(tuple(-1 if char == '*' else int(char) for char in cube)
                    for cube in row['cubes']) for row in model['phase_bits']]
    inverse = {step: dibit for dibit, step in enumerate(model['fixture']['phase_convention'])}
    cases = []
    for path in (CALL, ANSWER):
        captured = json.loads(path.read_text())
        selector = captured['fixture']['selector']
        old = next(c for c in source['cases'] if c['selector'] == selector and
                   c['level'] == captured['fixture']['level'])
        if captured['rx_trace_digest'] != old['rx_trace_digest']:
            raise ValueError('all-row trace differs from original real-PROM holdout')
        rows = {(item['symbol'], item['visit']): item for item in captured['sample_rows']}
        if len(rows) != 260:
            raise ValueError('four-row capture changed')
        phase_cases = []
        for timing in ('before_increment', 'after_increment'):
            for decode in range(4):
                # The candidate U24 low bits count 0,1,2,3 over the four
                # executed 3ED rows. A rising edge may expose old or new Q.
                row = decode if timing == 'before_increment' else (decode - 1) & 3
                got = decisions(rows, row, covers, inverse)
                wrong = [index for index, (actual, want) in enumerate(
                    zip(got, old['expected_dibits'][1:]), 1) if actual != want]
                phase_cases.append(dict(timing=timing, decoded_counter=f'{decode:02b}',
                                        selected_row=row, wrong_indices=wrong))
        winners = [item for item in phase_cases if not item['wrong_indices']]
        if [(x['timing'], x['decoded_counter']) for x in winners] != [
                ('before_increment', '00'), ('after_increment', '01')]:
            raise ValueError('counter qualifier phase result changed')
        cases.append(dict(selector=selector, level=captured['fixture']['level'],
                          rx_trace_digest=captured['rx_trace_digest'],
                          unqualified_every_row_wrong_indices=captured[
                              'every_row_latch_wrong_indices'],
                          counter_phase_cases=phase_cases))
    paths = (Path(__file__), CALL, ANSWER, SOURCE, LOGIC,
             HERE / 'joint_mask04_12a_all_row_latch.py')
    report = dict(experiment='four-state U24-style counter phase for candidate 3ED row clock',
                  fixture=dict(counter='assumed modulo-four low-bit index 0,1,2,3',
                               clock='candidate raw-PROM 3ED->3EA edge after every row',
                               data='executed all-row Y bit 0 from two real-PROM streams',
                               timings=['before_increment', 'after_increment'],
                               decodes=['00', '01', '10', '11']),
                  cases=cases,
                  limitations=[
                      'U24 74LS161 is photographed, but its clock, reset, outputs and U19/U12 connections are not traced.',
                      'The counter phase screen reuses saved real-PROM row snapshots and the fitted external phase gates; it is not a new execution.',
                      'Only the candidate row clock is tested; the remaining capture storage and USART routes are still assumed.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    for case in cases:
        print('counter', case['selector'], [(x['timing'], x['decoded_counter'],
                                            len(x['wrong_indices']))
                                           for x in case['counter_phase_cases']], flush=True)
    return report


if __name__ == '__main__':
    run()
