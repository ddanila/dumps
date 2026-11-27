"""Execute the revised photographed-package gate route for 45 states."""

import hashlib
import json
from pathlib import Path

from joint_mask04_12a_0d_feature_graph import INPUTS, code
from joint_mask04_12a_row1_holdout_graph_audit import RAW
from joint_mask04_12a_two_bit_phase_extension import NEW as FIRST_NEW
from joint_mask04_12a_two_bit_gain1_frozen37_audit import FROZEN, GAIN1, GAIN2, NEW
from joint_mask04_12a_two_bit_package_holdout_audit import RAW as FIRST_PACKAGE_RAW

HERE = Path(__file__).resolve().parent
GRAPH = HERE / 'results/joint-mask04-12a-two-bit-package-holdout-audit.json'
INVENTORY = HERE.parent / 'board/inventory.json'
OUT = HERE / 'results/joint-mask04-12a-two-bit-package-route2.json'
STEPS = (2, 1, 3, 0)
FEATURES = (('46', 'row0', 1), ('94', 'y3f8', 4))
CAPTURES = (*INPUTS, *RAW, *FIRST_NEW, *FROZEN, *GAIN1, *GAIN2, *NEW,
            *FIRST_PACKAGE_RAW)


def nand(*inputs):
    return 1 - int(all(inputs))


def nor(*inputs):
    return 1 - int(any(inputs))


def gate_phase(state):
    """Return absolute phase with global offset +1; only observed keys are fitted."""
    s = [(state >> bit) & 1 for bit in range(9)]
    qbar = [1 - bit for bit in s]

    # U12/U14 Q-bar supplies ~s0, ~s1, ~s2, ~s6, ~s7, ~s8.
    # U13a/b supplies ~s3 and ~s5 from U3 outputs.
    u19a = nand(s[2], qbar[5], s[7])
    u19b = nand(qbar[2], qbar[7], qbar[8])
    u21c = nor(u19b, u19b)

    # U15's 4-2-3-2 AOI arms, then U19c adds the fifth product.
    arm4 = qbar[1] & s[3] & s[7] & s[8]
    arm2a = qbar[2] & qbar[3]
    arm3 = qbar[0] & qbar[1] & qbar[6]
    arm2b = u21c & 1
    u15y = 1 - int(bool(arm4 | arm2a | arm3 | arm2b))
    p0 = nand(u15y, u19a, 1)

    u21a = nor(qbar[6], s[7])
    p1 = nor(qbar[2], u21a)  # U21b; this selects global offset +1.
    return (p1 << 1) | p0


def run(out=OUT):
    graph = json.loads(GRAPH.read_text())['phase_graph']
    if (graph['state_codes'], graph['directed_conflicts'], graph['components']) != (45, 0, [45]):
        raise ValueError('development graph changed')
    labels = {int(key, 16): value for key, value in graph['relative_phase'].items()}
    mismatches = [f'{state:03X}' for state, phase in labels.items()
                  if gate_phase(state) != ((phase + 1) & 3)]
    if mismatches:
        raise ValueError(('package network label mismatches', mismatches))
    inverse = {step: dibit for dibit, step in enumerate(STEPS)}
    checks = []
    for path in CAPTURES:
        for case in json.loads(path.read_text())['cases']:
            states = [code(symbol, FEATURES)
                      for symbol in case['multi_visit_symbols']]
            decoded = [inverse[(gate_phase(states[index]) -
                                gate_phase(states[index - 1])) & 3]
                       for index in range(1, len(states))]
            wrong = [index for index, actual in enumerate(decoded, 1)
                     if actual != case['expected_dibits'][index]]
            checks.append(dict(source=path.name, selector=case.get('selector'),
                               symbols=len(states), wrong_decision_indices=wrong))
    if len(checks) != 46 or any(item['symbols'] != 65 or
                             item['wrong_decision_indices'] for item in checks):
        raise ValueError('saved-stream package replay changed')
    inventory = {item['ref']: item['marking'] for item in
                 json.loads(INVENTORY.read_text())['parts']}
    expected = dict(U12='SN74LS175N', U13='DM74LS04N',
                    U14='SN74LS75N', U15='SN74S64J',
                    U19='SN74LS10N', U21='HD74LS02P')
    if {ref: inventory.get(ref) for ref in expected} != expected:
        raise ValueError('photographed package inventory changed')
    paths = (Path(__file__), GRAPH, INVENTORY, *CAPTURES)
    report = dict(experiment='revised two-bit receive phase network using photographed package capacities',
                  fixture=dict(streams=len(checks), symbols=65 * len(checks),
                               decisions=64 * len(checks),
                               observed_state_codes=len(labels),
                               global_phase_offset=1,
                               captured_features=FEATURES),
                  packages=expected,
                  resource_use=dict(U12_complementary_outputs=3,
                                    U14_complementary_outputs=3,
                                    U13_inverters=2, U15_AOI_outputs=1,
                                    U19_three_input_NANDs=3,
                                    U21_two_input_NORs=3),
                  label_mismatches=mismatches, saved_stream_checks=checks,
                  limitations=[
                      'The circuit is selected using all 46 saved streams; zero errors are a development fit, not a new holdout.',
                      'Complementary outputs, latch data/enables, gate input nets, fan-out, tie-high points, serial timing and line connections are assumed, not traced.',
                      'The gate computes every nine-bit key but unobserved-key phases are predictions with no supporting capture.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    report = run()
    print('saved streams', report['fixture']['streams'],
          'wrong decisions', sum(len(row['wrong_decision_indices'])
                                 for row in report['saved_stream_checks']))
