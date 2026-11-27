"""Audit matched mode schedules and alternate early-bit phase routes."""

import hashlib
import json
from pathlib import Path

from joint_mask04_12a_0d_feature_graph import solve
from joint_mask04_12a_two_bit_package_route2 import CAPTURES, FEATURES, STEPS

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
EDGE = tuple(RESULTS / f'joint-mask04-12a-two-bit-package-route2-holdout-{n}.json'
             for n in (165, 167))
HELD = tuple(RESULTS / f'joint-mask04-12a-two-bit-package-mode81-{n}.json'
             for n in (165, 167))
LATE = tuple(RESULTS / f'joint-mask04-12a-two-bit-package-mode-late48-{n}.json'
             for n in (165, 167))
EDGE_SUMMARY = RESULTS / 'joint-mask04-12a-two-bit-package-route2-holdout.json'
HELD_SUMMARY = RESULTS / 'joint-mask04-12a-two-bit-package-mode81.json'
LATE_SUMMARY = RESULTS / 'joint-mask04-12a-two-bit-package-mode-late48.json'
OUT = RESULTS / 'joint-mask04-12a-two-bit-package-mode-audit.json'
VISITS = ('46', '47', '93', '94', '141')
SITES = ('row0', 'y3f8')


def run(out=OUT):
    summaries = [json.loads(path.read_text())['cases']
                 for path in (EDGE_SUMMARY, HELD_SUMMARY, LATE_SUMMARY)]
    if any(len(rows) != 4 for rows in summaries):
        raise ValueError('mode-control case count changed')
    matched = []
    for edge_case, held_case, late_case in zip(*summaries):
        source_cases = [json.loads(path.read_text())['cases']
                        for path in (EDGE[edge_case['carrier_offset'] == 167],
                                     HELD[edge_case['carrier_offset'] == 167],
                                     LATE[edge_case['carrier_offset'] == 167])]
        raw = [next(case for case in source
                    if case['selector'] == edge_case['selector'])
               for source in source_cases]
        row = dict(carrier_offset=edge_case['carrier_offset'],
                   selector=edge_case['selector'],
                   tx_trace_match=len({case['tx_trace_digest'] for case in
                                       (edge_case, held_case, late_case)}) == 1,
                   pcm_match=len({case['pcm_sha256'] for case in
                                  (edge_case, held_case, late_case)}) == 1,
                   pc_path_match=len({case['pc_digest'] for case in raw}) == 1,
                   receive_traces_distinct=len({case['rx_trace_digest'] for case in
                                                (edge_case, held_case, late_case)}) == 3,
                   edge_wrong_indices=edge_case['gate_wrong_indices'],
                   held_wrong_indices=held_case['gate_wrong_indices'],
                   late_wrong_indices=late_case['gate_wrong_indices'],
                   edge_exact_payload=edge_case['controller_matches_payload'],
                   held_exact_payload=held_case['controller_matches_payload'],
                   late_exact_payload=late_case['controller_matches_payload'],
                   clipped_samples=[case['clipped_samples'] for case in
                                    (edge_case, held_case, late_case)])
        if (not all(row[key] for key in ('tx_trace_match', 'pcm_match',
                                         'pc_path_match', 'receive_traces_distinct',
                                         'edge_exact_payload')) or
                row['held_exact_payload'] or row['late_exact_payload'] or
                row['edge_wrong_indices'] or any(row['clipped_samples']) or
                any(index < 32 for index in row['held_wrong_indices']) or
                any(index < 32 or index > 48 for index in row['late_wrong_indices'])):
            raise ValueError(('matched mode result changed', row))
        for case in (held_case, late_case):
            if any(case['captured_keys'][index] != '01C' and
                   case['captured_keys'][index - 1] != '01C'
                   for index in case['gate_wrong_indices']):
                raise ValueError('wrong transition no longer touches 01C')
        matched.append(row)
    if ([len(row['held_wrong_indices']) for row in matched] != [8, 10, 11, 13] or
            [len(row['late_wrong_indices']) for row in matched] != [4, 4, 4, 6]):
        raise ValueError('mode-edge error counts changed')

    cases = []
    row_shifts = 0
    early_later_y4_differences = 0
    for path in (*CAPTURES, *EDGE, *HELD, *LATE):
        source = json.loads(path.read_text())
        for case in source['cases']:
            boundary = (None if path in HELD or case.get('mode') == 'held_81'
                        else 48 if path in LATE else 32)
            for index, symbol in enumerate(case['multi_visit_symbols']):
                visits = symbol['visits']
                visits['46']['mode_bit5'] = int(boundary is not None and
                                                 index >= boundary)
                row_shifts += bool((visits['46']['row0'] ^
                                    visits['47']['row0']) & 3)
                early_later_y4_differences += bool(
                    (visits['46']['y3f8'] ^ visits['94']['y3f8']) & 0x10)
            cases.append(case)
    if len(cases) != 58 or row_shifts != 0 or early_later_y4_differences != 2046:
        raise ValueError('capture population changed')
    base = solve(cases, FEATURES, STEPS)
    mode = solve(cases, FEATURES + (('46', 'mode_bit5', 0),), STEPS)
    first_y4 = solve(cases, FEATURES + (('46', 'y3f8', 4),), STEPS)
    if ((base['state_codes'], base['directed_conflicts']) != (47, 102) or
            (mode['state_codes'], mode['directed_conflicts'], mode['components'])
            != (54, 0, [54]) or
            (first_y4['state_codes'], first_y4['directed_conflicts'],
             first_y4['components']) != (48, 0, [48])):
        raise ValueError('mode or early-bit graph changed')
    candidates = []
    for visit in VISITS:
        for site in SITES:
            for bit in range(8):
                graph = solve(cases, FEATURES + ((visit, site, bit),), STEPS)
                candidates.append(dict(visit=visit, site=site, bit=bit,
                                       state_codes=graph['state_codes'],
                                       directed_conflicts=graph['directed_conflicts']))
    zero = [row for row in candidates if row['directed_conflicts'] == 0]
    if len(candidates) != 80 or not any(
            row['visit'] == '46' and row['site'] == 'y3f8' and row['bit'] == 4
            for row in zero):
        raise ValueError('captured-bit screen changed')
    paths = (Path(__file__), EDGE_SUMMARY, HELD_SUMMARY, LATE_SUMMARY,
             *CAPTURES, *EDGE, *HELD, *LATE,
             HERE / 'joint_mask04_12a_two_bit_package_route2.py',
             HERE / 'joint_mask04_12a_two_bit_package_mode81.py',
             HERE / 'joint_mask04_12a_two_bit_package_mode_late48.py',
             HERE / 'joint_mask04_12a_0d_feature_graph.py')
    report = dict(experiment='matched D3EB mode schedules and physical captured-bit alternatives',
                  fixture=dict(streams=len(cases), symbols=65 * len(cases),
                               phase_convention=STEPS,
                               default_edge_symbol=32, late_edge_symbol=48,
                               screen_visits=VISITS, screen_sites=SITES),
                  matched_cases=matched,
                  row0_y01_46_to_47_shifts=row_shifts,
                  first_later_y4_differences=early_later_y4_differences,
                  nine_bit_graph=base, mode_bit5_graph=mode,
                  first_y4_graph=first_y4,
                  captured_bit_screen=candidates,
                  zero_conflict_captured_bits=zero,
                  limitations=[
                      'The D3EB mode value and edge are imposed inputs; the physical controller-to-DSC net is untraced.',
                      'The early Y4 feature was selected using these failed mode controls; its graph is development evidence, not a new holdout.',
                      'A conflict-free phase graph is not a photographed-package gate circuit or proof of the analog/USART path.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    report = run()
    print('graphs', [(name, report[name]['state_codes'],
                      report[name]['directed_conflicts']) for name in
                     ('nine_bit_graph', 'mode_bit5_graph', 'first_y4_graph')],
          'zero captured bits', len(report['zero_conflict_captured_bits']))
