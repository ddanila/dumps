"""Replay staged U14/U12/U3 capture with the revised package gate."""

import hashlib
import json
from pathlib import Path

from joint_mask04_12a_0d_feature_graph import code, solve
from joint_mask04_12a_two_bit_package_route2 import CAPTURES, FEATURES, STEPS, gate_phase
import joint_mask04_12a_row0_serial_timing as serial

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
FRESH = tuple(RESULTS / f'joint-mask04-12a-two-bit-package-route2-holdout-{n}.json'
              for n in (165, 167))
SUMMARY = RESULTS / 'joint-mask04-12a-two-bit-package-route2-holdout.json'
OUT = RESULTS / 'joint-mask04-12a-two-bit-package-latch.json'


def staged_code(symbol):
    visits = symbol['visits']
    first = visits['46']['y3f8']
    second = visits['93']['y3f8']
    row = visits['47']['row0']
    later = visits['94']['y3f8']
    return (((first >> 5) & 7) |
            (((second >> 7) & 1) << 3) |
            (((second >> 4) & 1) << 4) |
            (((second >> 6) & 1) << 5) |
            ((row & 1) << 6) |
            ((row & 2) << 6) |
            (((later >> 4) & 1) << 8))


def run(out=OUT):
    cases = [case for path in (*CAPTURES, *FRESH)
             for case in json.loads(path.read_text())['cases']]
    if len(cases) != 50 or any(len(case['multi_visit_symbols']) != 65
                                for case in cases):
        raise ValueError('staged-capture case count changed')
    inverse = {step: dibit for dibit, step in enumerate(STEPS)}
    checks = []
    row_shifts = 0
    state_mismatches = 0
    for case in cases:
        symbols = case['multi_visit_symbols']
        states = []
        for symbol in symbols:
            row_shifts += bool((symbol['visits']['46']['row0'] ^
                                symbol['visits']['47']['row0']) & 3)
            staged = staged_code(symbol)
            state_mismatches += staged != code(symbol, FEATURES)
            states.append(staged)
        wrong = [index for index in range(1, len(states))
                 if inverse[(gate_phase(states[index]) -
                             gate_phase(states[index - 1])) & 3]
                 != case['expected_dibits'][index]]
        checks.append(dict(selector=case.get('selector'),
                           wrong_decision_indices=wrong))
    if row_shifts or state_mismatches or any(item['wrong_decision_indices']
                                           for item in checks):
        raise ValueError('staged capture or gate differs')
    graph = solve(cases, FEATURES, STEPS)
    if (graph['state_codes'], graph['directed_conflicts'], graph['components']) != (46, 0, [46]):
        raise ValueError('staged-state phase graph changed')
    summary = json.loads(SUMMARY.read_text())
    if not all(not item['gate_wrong_indices'] and
               item['recovered_matches_offered'] and
               item['controller_matches_payload'] and
               item['clipped_samples'] == 0
               for item in summary['cases']):
        raise ValueError('fresh package holdout changed')
    timing = dict(U14_first_y=serial.Y3F8_CYCLE + 46 * serial.CYCLES_PER_VISIT,
                  U12_row_and_copy=serial.ROW0_CYCLE + 47 * serial.CYCLES_PER_VISIT,
                  U3_second_y=serial.Y3F8_CYCLE + 93 * serial.CYCLES_PER_VISIT,
                  U14_later_y4=serial.Y3F8_CYCLE + 94 * serial.CYCLES_PER_VISIT,
                  first_RxC=serial.VARIANTS['aligned']['first_rxc_cycle'])
    timing['minimum_setup_cycles'] = timing['first_RxC'] - timing['U14_later_y4']
    if timing['minimum_setup_cycles'] != 2929:
        raise ValueError('modeled setup interval changed')
    paths = (Path(__file__), SUMMARY, *CAPTURES, *FRESH,
             HERE / 'joint_mask04_12a_two_bit_package_route2.py',
             HERE / 'joint_mask04_12a_two_bit_package_route2_holdout.py',
             HERE / 'joint_mask04_12a_row0_serial_timing.py')
    report = dict(experiment='staged nine-bit capture and revised package gate',
                  fixture=dict(streams=len(cases), symbols=65 * len(cases),
                               decisions=64 * len(cases)),
                  timing=timing,
                  row0_y01_46_to_47_shifts=row_shifts,
                  staged_state_mismatches=state_mismatches,
                  phase_graph=graph,
                  saved_stream_checks=checks,
                  fresh_holdout=[dict(carrier_offset=item['carrier_offset'],
                                      selector=item['selector'],
                                      unseen_keys=item['unseen_keys'],
                                      wrong_dibits=len(item['gate_wrong_indices']),
                                      exact_line=item['recovered_matches_offered'],
                                      exact_payload=item['controller_matches_payload'])
                                 for item in summary['cases']],
                  limitations=[
                      'Package storage and gate inputs are assumed nets; this replay does not trace them on the Nokia board.',
                      'The first 46 streams selected the revised gate; only the final four are untouched gate holdouts.',
                      'The modeled setup interval is in microcode cycles, not a measured electrical delay.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    report = run()
    print(report['fixture'], report['timing'],
          report['staged_state_mismatches'])
