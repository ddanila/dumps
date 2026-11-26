"""Capture adjacent real-PROM receive visits under the failing 1.15x line."""

import hashlib
import itertools
import json
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_buffered_line as line
import joint_mask04_12a_row_mode_edge as edge
from joint_mask04_12a_mode_phase131_adc_range import pcm_for
from photo_u15_u19_u21_phase_route import circuit

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
RANGE = RESULTS / 'joint-mask04-12a-mode-phase131-adc-range.json'
BOUNDARY = RESULTS / 'joint-mask04-12a-mode-phase131-gain-boundary.json'
MODEL = RESULTS / 'joint-mask04-12a-mode-phase-twelve.json'
OUT = RESULTS / 'joint-mask04-12a-phase131-adjacent-capture.json'
FACTOR = 1.15
VISITS = (46, 47, 93, 94)


def state(symbol, first_visit, second_visit, row_visit):
    visits = symbol['visits']
    first = visits[str(first_visit)]['y3f8']
    second = visits[str(second_visit)]['y3f8']
    row = visits[str(row_visit)]['row0']
    return (((first >> 5) & 7) | (((second >> 7) & 1) << 3) |
            (((second >> 4) & 1) << 4) | (((second >> 6) & 1) << 5) |
            ((row & 1) << 6))


def run(out=OUT):
    spectrum = json.loads(RANGE.read_text())
    boundary = json.loads(BOUNDARY.read_text())
    model = json.loads(MODEL.read_text())
    inverse = {step: dibit for dibit, step in
               enumerate(model['fixture']['phase_convention'])}
    previous = {case['selector']: case for case in boundary['cases']
                if case['factor'] == FACTOR}
    mapping = line.candidate(line.mapping_with_upper_source(0, '17.6'),
                             line.mapped(line.MAPPINGS['q3']), 4)
    _, base = line.fixture()
    mode_values = [0x81] * edge.EDGE + [0xA1] * (edge.MODE_READS - edge.EDGE)
    captures = []
    with patch.object(edge, 'CAPTURE_VISITS', VISITS):
        for wave_case in spectrum['cases']:
            selector = wave_case['selector']
            pcm = pcm_for(wave_case['selected_wave'],
                          wave_case['calibrated_gain'], FACTOR)
            digest = hashlib.sha256(bytes(value + 127 for value in pcm)).hexdigest()
            if digest != previous[selector]['pcm_sha256']:
                raise ValueError(('adjacent capture PCM changed', selector))
            rx, pc_digest, symbols, gate_edges = edge.execute_case(
                mapping, base, pcm, mode_values)
            if (rx['trace_digest'] != previous[selector]['rx_trace_digest'] or
                    pc_digest != previous[selector]['pc_digest'] or
                    gate_edges != previous[selector]['gate_edges']):
                raise ValueError(('adjacent capture execution changed', selector))
            captures.append(dict(selector=selector,
                                 symbols=[symbols[index] for index in range(65)],
                                 expected=previous[selector]['expected_dibits'],
                                 rx_trace_digest=rx['trace_digest'],
                                 pcm_sha256=digest))
            print('captured adjacent', selector, flush=True)
    variants = []
    for first_visit, second_visit, row_visit in itertools.product(
            (46, 47), (93, 94), (46, 47)):
        cases = []
        for case in captures:
            states = [state(symbol, first_visit, second_visit, row_visit)
                      for symbol in case['symbols']]
            phases = [circuit(value, 1) for value in states]
            wrong = [index for index in range(1, len(phases))
                     if inverse[(phases[index] - phases[index - 1]) & 3]
                     != case['expected'][index]]
            cases.append(dict(selector=case['selector'],
                              errors=len(wrong), wrong_indices=wrong,
                              distinct_states=sorted(f'{value:02X}' for value
                                                     in set(states))))
        variants.append(dict(first_y_visit=first_visit,
                             second_y_visit=second_visit,
                             row0_visit=row_visit, cases=cases,
                             total_errors=sum(case['errors'] for case in cases)))
    baseline = next(row for row in variants if
                    (row['first_y_visit'], row['second_y_visit'],
                     row['row0_visit']) == (46, 93, 46))
    if ([case['errors'] for case in baseline['cases']] != [12, 11] or
            len(variants) != 8):
        raise ValueError('adjacent-capture control changed')
    paths = (Path(__file__), RANGE, BOUNDARY, MODEL,
             HERE / 'joint_mask04_12a_row_mode_edge.py',
             HERE / 'photo_u15_u19_u21_phase_route.py')
    report = dict(experiment='adjacent 46/47 and 93/94 capture timing screen',
                  fixture=dict(factor=FACTOR, R1_offset=131,
                               same_pcm_as=BOUNDARY.name,
                               visits=VISITS),
                  variants=variants,
                  source_runs=[dict(selector=case['selector'],
                                    pcm_sha256=case['pcm_sha256'],
                                    rx_trace_digest=case['rx_trace_digest'])
                               for case in captures],
                  limitations=[
                      'The PROM receiver is rerun on identical PCM with four retained visits; no board latch or RxC arrival is traced.',
                      'Only whole-visit changes to the three capture groups are tested; individual bit timing and other visits remain open.',
                      'A same-fixture score is a screen, not an independent holdout.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    for row in sorted(variants, key=lambda row: row['total_errors']):
        print(row['first_y_visit'], row['second_y_visit'],
              row['row0_visit'], [case['errors'] for case in row['cases']])
    return report


if __name__ == '__main__':
    run()
