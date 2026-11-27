"""Audit the gate work needed beyond the nine-bit package circuit."""

import hashlib
import itertools
import json
from pathlib import Path

from joint_mask04_12a_0d_feature_graph import code
from joint_mask04_12a_modebit66_cover import FEATURES, STEPS
from joint_mask04_12a_modebit70_revision import gate_phase
from joint_mask04_12a_ten_bit_product_bound import cube_hit
from joint_mask04_12a_two_bit_package_route2 import gate_phase as prior_gate

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
REVISION = RESULTS / 'joint-mask04-12a-modebit70-revision.json'
HOLDOUT = RESULTS / 'joint-mask04-12a-modebit70-holdout.json'
RAW = tuple(RESULTS / f'joint-mask04-12a-modebit70-holdout-{mode}-179.json'
            for mode in ('held81', 'edge32'))
INVENTORY = HERE.parent / 'board/inventory.json'
OUT = RESULTS / 'joint-mask04-12a-modebit70-package-delta.json'


def shortest_cubes(targets, observed):
    others = observed - targets
    for width in range(1, 11):
        found = []
        for positions in itertools.combinations(range(10), width):
            for values in itertools.product('01', repeat=width):
                cube = ['*'] * 10
                for position, value in zip(positions, values):
                    cube[position] = value
                cube = ''.join(cube)
                if (all(cube_hit(state, cube) for state in targets) and
                        not any(cube_hit(state, cube) for state in others)):
                    found.append(cube)
        if found:
            return width, found
    raise ValueError('target set cannot be isolated')


def run(out=OUT):
    frozen = json.loads(REVISION.read_text())
    observed = {int(key, 16) for key in
                frozen['mode_bit_graph']['relative_phase']}
    if len(observed) != 64:
        raise ValueError('revised state population changed')
    mismatches = {}
    for state in sorted(observed):
        prior = prior_gate(state & 0x1FF)
        revised = gate_phase(state)
        if prior != revised:
            mismatches[f'{state:03X}'] = dict(prior=prior, revised=revised,
                                              changed_bits=prior ^ revised)
    if mismatches != {
            '01C': dict(prior=3, revised=0, changed_bits=3),
            '11C': dict(prior=3, revised=0, changed_bits=3),
            '12D': dict(prior=2, revised=3, changed_bits=1),
            '32D': dict(prior=2, revised=3, changed_bits=1)}:
        raise ValueError('package delta changed')
    groups = []
    for name, target in (('clear_both_phase_bits', {0x01C, 0x11C}),
                         ('set_phase_bit0', {0x12D, 0x32D})):
        width, cubes = shortest_cubes(target, observed)
        groups.append(dict(action=name,
                           states=[f'{state:03X}' for state in sorted(target)],
                           minimum_direct_literals=width,
                           all_shortest_cubes=cubes))
    if [group['minimum_direct_literals'] for group in groups] != [4, 5]:
        raise ValueError('direct correction decodes changed')
    inverse = {step: dibit for dibit, step in enumerate(STEPS)}
    challenge = json.loads(HOLDOUT.read_text())
    cases = []
    for mode, path in zip(('held81', 'edge32'), RAW):
        for case in json.loads(path.read_text())['cases']:
            symbols = case['multi_visit_symbols']
            for index, symbol in enumerate(symbols):
                symbol['visits']['46']['mode_bit5'] = int(
                    mode == 'edge32' and index >= 32)
            states = [code(symbol, FEATURES) for symbol in symbols]
            old_wrong = [index for index in range(1, len(states))
                         if inverse[(prior_gate(states[index] & 0x1FF) -
                                     prior_gate(states[index - 1] & 0x1FF)) & 3]
                         != case['expected_dibits'][index]]
            new_wrong = next(row['wrong_decision_indices']
                             for row in challenge['cases']
                             if row['mode'] == mode and
                             row['selector'] == case['selector'])
            cases.append(dict(mode=mode, selector=case['selector'],
                              prior_wrong_decisions=len(old_wrong),
                              revised_wrong_decisions=len(new_wrong),
                              correction_state_visits={
                                  f'{key:03X}': states.count(key)
                                  for key in (0x01C, 0x11C, 0x12D, 0x32D)}))
    if [(row['prior_wrong_decisions'], row['revised_wrong_decisions'])
            for row in cases] != [(13, 0), (16, 0), (13, 0), (16, 0)]:
        raise ValueError(('fresh case gate comparison changed', cases))
    inventory = {part['ref']: part['marking'] for part in
                 json.loads(INVENTORY.read_text())['parts']}
    expected = dict(U7='SN74LS30N', U13='DM74LS04N', U15='SN74S64J',
                    U19='SN74LS10N', U21='HD74LS02P')
    if {ref: inventory.get(ref) for ref in expected} != expected:
        raise ValueError('photographed package population changed')
    sources = (Path(__file__), REVISION, HOLDOUT, *RAW, INVENTORY,
               HERE / 'joint_mask04_12a_modebit70_revision.py',
               HERE / 'joint_mask04_12a_two_bit_package_route2.py',
               HERE / 'joint_mask04_12a_0d_feature_graph.py',
               HERE / 'joint_mask04_12a_ten_bit_product_bound.py')
    report = dict(experiment='photographed-package delta for the revised mode-bit phase rule',
                  observed_states=len(observed),
                  prior_package_gate_mismatches=mismatches,
                  correction_groups=groups,
                  photographed_packages=expected,
                  prior_network_resource_use=dict(U13_inverters=2,
                                                  U15_AOI_outputs=1,
                                                  U19_three_input_NANDs=3,
                                                  U21_two_input_NORs=3),
                  additional_visible_gate_capacity=dict(U7_eight_input_NANDs=1,
                                                        U13_inverters=4,
                                                        U21_two_input_NORs=1),
                  fresh_cases=cases,
                  limitations=[
                      'The old package network agrees on 60 observed states, but this audit does not construct the required correction and output-combination circuit.',
                      'Direct correction cube widths are minima only on these 64 observed states; unobserved states are unconstrained.',
                      'Photographed package presence is not evidence that its gates are unused, nearby nets connect, or propagation timing closes.',
                      'The mode bit, capture and RxD/RxC/SYNDET paths remain assumed.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print('package delta states', len(result['prior_package_gate_mismatches']),
          'shortest cube widths', [row['minimum_direct_literals']
                                  for row in result['correction_groups']])
