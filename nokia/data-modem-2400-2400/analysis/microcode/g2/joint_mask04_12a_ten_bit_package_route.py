"""Execute a ten-bit receive gate from photographed package capacities."""

import hashlib
import json
from pathlib import Path

from joint_mask04_12a_0d_feature_graph import code, solve
from joint_mask04_12a_two_bit_package_route2 import CAPTURES, FEATURES as NINE_BITS, STEPS
from joint_mask04_12a_two_bit_package_mode_audit import EDGE, HELD, LATE
from joint_mask04_12a_two_bit_package_latch import staged_code
import joint_mask04_12a_row0_serial_timing as serial

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
INVENTORY = HERE.parent / 'board/inventory.json'
OUT = RESULTS / 'joint-mask04-12a-ten-bit-package-route.json'
FEATURES = NINE_BITS + (('94', 'y3f8', 6),)
CAPTURES = (*CAPTURES, *EDGE, *HELD, *LATE)


def nand(*inputs):
    return 1 - int(all(inputs))


def nor(*inputs):
    return 1 - int(any(inputs))


def gate_phase(state):
    """Absolute phase with global offset +3 on the development graph."""
    s = [(state >> bit) & 1 for bit in range(10)]
    qbar = [1 - bit for bit in s]

    # U12/U14 complementary Q supplies the required captured complements.
    # U13a/b inverts U3's s3 and s5 outputs.
    u21a = nor(s[1], qbar[3])          # ~s1 & s3
    u19a = nand(s[2], qbar[5], s[7])  # complement of a 3-input term
    pre = 1 - u19a                     # U13c
    arm4 = u21a & qbar[7] & qbar[8] & qbar[9]
    arm2a = qbar[2] & qbar[3]
    arm3 = u21a & s[7] & s[8]
    arm2b = pre & 1
    u15y = 1 - int(bool(arm4 | arm2a | arm3 | arm2b))
    p0 = 1 - u15y                      # U13d

    u21b = nor(s[0], s[1])            # ~s0 & ~s1
    u19b = nand(u21b, s[4], s[9])    # complement of a 4-literal term
    u21c = nor(qbar[6], s[7])         # s6 & ~s7
    n_u21c = 1 - u21c                 # U13e
    p1 = nand(s[2], n_u21c, u19b)    # U19c
    return p0 | (p1 << 1)


def staged_ten_bit_code(symbol):
    return (staged_code(symbol) |
            (((symbol['visits']['94']['y3f8'] >> 6) & 1) << 9))


def run(out=OUT):
    cases = [case for path in CAPTURES
             for case in json.loads(path.read_text())['cases']]
    if len(cases) != 58 or any(len(case['multi_visit_symbols']) != 65
                                for case in cases):
        raise ValueError('development stream count changed')
    graph = solve(cases, FEATURES, STEPS)
    if (graph['state_codes'], graph['directed_conflicts'], graph['components']) != (54, 0, [38, 16]):
        raise ValueError('ten-bit phase graph changed')
    labels = {int(key, 16): phase for key, phase in graph['relative_phase'].items()}
    wrong_labels = [f'{state:03X}' for state, phase in labels.items()
                    if gate_phase(state) != ((phase + 3) & 3)]
    if wrong_labels:
        raise ValueError(('gate label mismatches', wrong_labels))
    inverse = {step: dibit for dibit, step in enumerate(STEPS)}
    checks = []
    staged_mismatches = 0
    row_shifts = 0
    for path in CAPTURES:
        for case in json.loads(path.read_text())['cases']:
            states = []
            for symbol in case['multi_visit_symbols']:
                value = staged_ten_bit_code(symbol)
                staged_mismatches += value != code(symbol, FEATURES)
                row_shifts += bool((symbol['visits']['46']['row0'] ^
                                    symbol['visits']['47']['row0']) & 3)
                states.append(value)
            wrong = [index for index in range(1, len(states))
                     if inverse[(gate_phase(states[index]) -
                                 gate_phase(states[index - 1])) & 3]
                     != case['expected_dibits'][index]]
            checks.append(dict(source=path.name, selector=case.get('selector'),
                               wrong_decision_indices=wrong))
    if staged_mismatches or row_shifts or any(row['wrong_decision_indices']
                                             for row in checks):
        raise ValueError('staged capture or decision differs')
    inventory = {item['ref']: item['marking'] for item in
                 json.loads(INVENTORY.read_text())['parts']}
    expected = dict(U12='SN74LS175N', U13='DM74LS04N',
                    U14='SN74LS75N', U15='SN74S64J',
                    U19='SN74LS10N', U21='HD74LS02P')
    if {ref: inventory.get(ref) for ref in expected} != expected:
        raise ValueError('photographed package inventory changed')
    last_capture = serial.Y3F8_CYCLE + 94 * serial.CYCLES_PER_VISIT
    setup = serial.VARIANTS['aligned']['first_rxc_cycle'] - last_capture
    if setup != 2929:
        raise ValueError('modeled serial setup changed')
    paths = (Path(__file__), INVENTORY, *CAPTURES,
             HERE / 'joint_mask04_12a_two_bit_package_mode_audit.py',
             HERE / 'joint_mask04_12a_two_bit_package_latch.py',
             HERE / 'joint_mask04_12a_0d_feature_graph.py')
    report = dict(experiment='ten-bit package-capacity receive phase route',
                  fixture=dict(streams=len(cases), symbols=65 * len(cases),
                               decisions=64 * len(cases),
                               phase_convention=STEPS,
                               observed_state_codes=len(labels),
                               global_phase_offset=3,
                               last_capture_cycle=last_capture,
                               first_RxC_cycle=serial.VARIANTS['aligned']['first_rxc_cycle'],
                               modeled_setup_cycles=setup),
                  packages=expected,
                  resource_use=dict(U12_flipflops=3, U14_latches=4,
                                    U3_latches=3, U13_inverters=5,
                                    U15_AOI_outputs=1, U19_three_input_NANDs=3,
                                    U21_two_input_NORs=3),
                  phase_graph=graph,
                  gate_label_mismatches=wrong_labels,
                  staged_state_mismatches=staged_mismatches,
                  row0_y01_46_to_47_shifts=row_shifts,
                  saved_stream_checks=checks,
                  limitations=[
                      'The ten-bit feature and gate network were selected using all 58 streams; zero saved errors are a development fit.',
                      'The observed phase graph has two disconnected components, so their relative global phase remains unconstrained by these streams.',
                      'Actual package data/enable nets, complementary-Q use, tie-high points, analog path and USART connection are not identified.',
                      'The modeled 2,929-cycle setup interval is not a measured electrical timing margin.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    report = run()
    print('streams', report['fixture']['streams'], 'states',
          report['fixture']['observed_state_codes'], 'stage mismatches',
          report['staged_state_mismatches'])
