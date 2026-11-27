"""Replay a photo-package-capacity twelve-bit receive capture schedule."""

import hashlib
import json
from pathlib import Path

import joint_mask04_12a_row0_serial_timing as serial
from joint_mask04_12a_0d_feature_graph import code
from joint_mask04_12a_modebit66_graph import CAPTURES, RAW, boundary
from joint_mask04_12a_modebit70_level_feature_screen import TRIALS
from joint_mask04_12a_modebit91_gain110_diagnosis import NEW as FAILED_189
from joint_mask04_12a_modebit97_cover import FEATURES, STEPS, gate_phase
from joint_mask04_12a_two_bit_package_latch import staged_code

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
FRESH = tuple(RESULTS / f'joint-mask04-12a-modebit97-gain110-holdout-{mode}-191.json'
              for mode in ('edge32', 'edge48'))
SUMMARY = RESULTS / 'joint-mask04-12a-modebit97-gain110-holdout.json'
INVENTORY = HERE.parent / 'board/inventory.json'
OUT = RESULTS / 'joint-mask04-12a-modebit97-staged-capture.json'


def staged_twelve_bit_code(symbol):
    visits = symbol['visits']
    return (staged_code(symbol) |
            ((visits['46']['mode_bit5'] & 1) << 9) |
            (((visits['93']['row0'] >> 2) & 1) << 10) |
            (((visits['94']['y3f8'] >> 7) & 1) << 11))


def run(out=OUT):
    cases = []
    sources = [Path(__file__), SUMMARY, INVENTORY,
               HERE / 'joint_mask04_12a_modebit97_cover.py',
               HERE / 'joint_mask04_12a_two_bit_package_latch.py',
               HERE / 'joint_mask04_12a_row0_serial_timing.py',
               HERE / 'joint_mask04_12a_modebit70_level_feature_screen.py',
               HERE / 'joint_mask04_12a_modebit91_gain110_diagnosis.py',
               HERE / 'joint_mask04_12a_0d_feature_graph.py']

    def append(path, edge):
        sources.append(path)
        for case in json.loads(path.read_text())['cases']:
            limit = edge(case) if callable(edge) else edge
            for index, symbol in enumerate(case['multi_visit_symbols']):
                symbol['visits']['46']['mode_bit5'] = int(
                    limit is not None and index >= limit)
            cases.append((path, case))

    for path in (*CAPTURES, *RAW):
        append(path, lambda case, path=path: boundary(path, case))
    for offset, version, prefix, modes in TRIALS:
        for mode in modes:
            path = RESULTS / (f'joint-mask04-12a-{version}-{prefix}-'
                              f'{mode}-{offset}.json')
            append(path, None if mode == 'held81' else
                   48 if mode == 'edge48' else 32)
    for mode, path in zip(('edge32', 'edge48'), FAILED_189):
        append(path, 32 if mode == 'edge32' else 48)
    for mode, path in zip(('edge32', 'edge48'), FRESH):
        append(path, 32 if mode == 'edge32' else 48)
    if len(cases) != 100 or any(len(case['multi_visit_symbols']) != 65
                                for _, case in cases):
        raise ValueError('staged-capture stream population changed')
    inverse = {step: dibit for dibit, step in enumerate(STEPS)}
    mismatches = 0
    early_row_shifts = [0, 0]
    late_row_shift = 0
    checks = []
    for path, case in cases:
        states = []
        for symbol in case['multi_visit_symbols']:
            visits = symbol['visits']
            early_delta = visits['46']['row0'] ^ visits['47']['row0']
            for bit in (0, 1):
                early_row_shifts[bit] += bool(early_delta & (1 << bit))
            late_row_shift += bool((visits['93']['row0'] ^
                                    visits['94']['row0']) & 4)
            staged = staged_twelve_bit_code(symbol)
            mismatches += staged != code(symbol, FEATURES)
            states.append(staged)
        wrong = [index for index in range(1, len(states))
                 if inverse[(gate_phase(states[index]) -
                             gate_phase(states[index - 1])) & 3]
                 != case['expected_dibits'][index]]
        checks.append(dict(source=path.name, selector=case.get('selector'),
                           wrong_decision_indices=wrong))
    if mismatches or early_row_shifts != [0, 0] or late_row_shift:
        raise ValueError(('staged capture differs from direct state',
                          mismatches, early_row_shifts, late_row_shift))
    if any(row['wrong_decision_indices'] for row in checks):
        raise ValueError('staged phase decisions differ')
    summary = json.loads(SUMMARY.read_text())
    if any(row['wrong_decision_indices'] or not row['line_exact'] or
           not row['controller_exact'] for row in summary['cases']):
        raise ValueError('fresh holdout score changed')
    inventory = {part['ref']: part['marking'] for part in
                 json.loads(INVENTORY.read_text())['parts']}
    expected = dict(U3='74LS373 PC', U12='SN74LS175N',
                    U14='SN74LS75N', U25='HD74LS74AP')
    if {ref: inventory.get(ref) for ref in expected} != expected:
        raise ValueError('photographed storage packages changed')
    timing = dict(U14_first_y=serial.Y3F8_CYCLE + 46 * serial.CYCLES_PER_VISIT,
                  U12_early_row=serial.ROW0_CYCLE + 47 * serial.CYCLES_PER_VISIT,
                  U25_late_row_y2=serial.ROW0_CYCLE + 93 * serial.CYCLES_PER_VISIT,
                  U3_second_y=serial.Y3F8_CYCLE + 93 * serial.CYCLES_PER_VISIT,
                  U14_and_U25_later_y=serial.Y3F8_CYCLE + 94 * serial.CYCLES_PER_VISIT,
                  first_RxC=serial.VARIANTS['aligned']['first_rxc_cycle'])
    if timing != dict(U14_first_y=1535, U12_early_row=1554,
                      U25_late_row_y2=3026, U3_second_y=3039,
                      U14_and_U25_later_y=3071, first_RxC=6000):
        raise ValueError('modeled capture timing changed')
    report = dict(experiment='photo-package-capacity staged twelve-bit receive capture',
                  fixture=dict(streams=len(cases), symbols=65 * len(cases),
                               phase_convention=STEPS),
                  packages=expected,
                  proposed_storage=dict(U12_early_bits=3, U14_first_and_later_bits=4,
                                        U3_second_bits=3, U25_independent_late_bits=2),
                  timing=timing,
                  minimum_modeled_setup_cycles=timing['first_RxC'] -
                                               timing['U14_and_U25_later_y'],
                  direct_state_mismatches=mismatches,
                  row0_y01_46_to_47_shifts=early_row_shifts,
                  row0_y2_93_to_94_shifts=late_row_shift,
                  saved_stream_checks=checks,
                  limitations=[
                      'The data and clock nets to U25 and other packages are assumptions; the photos establish package presence, not these connections.',
                      'The mode bit is assigned to the spare U12 flip-flop, assuming its source holds through the common visit-47 clock; that source and hold time are not traced.',
                      'U25 was previously assigned to previous-phase memory in another candidate route. This capture allocation displaces that role, leaving phase subtraction and serialization unallocated.',
                      'The modeled 2,929-cycle interval is not a measured setup, propagation or fan-out margin.',
                      'This replays saved PROM symbol snapshots; it does not rerun the PROM or prove physical RxD/RxC/SYNDET wiring.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print('streams', result['fixture']['streams'],
          'staged mismatches', result['direct_state_mismatches'],
          'modeled setup cycles', result['minimum_modeled_setup_cycles'])
