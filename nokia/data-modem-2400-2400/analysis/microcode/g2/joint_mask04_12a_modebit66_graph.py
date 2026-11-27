"""Audit imposed controller-mode phase input on 66 real-PROM streams."""

import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

from joint_mask04_12a_0d_feature_graph import solve
from joint_mask04_12a_ten_bit_package_route2 import CAPTURES, FEATURES, NINE_BITS, STEPS
from joint_mask04_12a_two_bit_package_mode_audit import HELD, LATE
from joint_mask04_12a_ten_bit_product_bound import RAW, cube_hit, pair_cannot_share_product

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
OUT = RESULTS / 'joint-mask04-12a-modebit66-graph.json'
MODE_FEATURE = ('46', 'mode_bit5', 0)
WITNESSES = {
    0: ('089', '109', '2E5', '21E', '24C', '01C', '21D'),
    1: ('082', '1C8', '249', '2CC', '21C', '12D'),
}
COVERS = {
    0: ('100100*01*', '0011*010*1', '**1*1*00*0', '1*1***0001',
        '1010*111*1', '*1*1******', '*00*00*10*'),
    1: ('1011010010', '*011***1**', '100100*00*', '001*100001',
        '**00*0****', '00*10***1*'),
}


def boundary(path, case):
    if (path in HELD or path in RAW or
            'ten-bit-package-mode81' in path.name or
            case.get('mode') == 'held_81'):
        return None
    return 48 if path in LATE else 32


def run(out=OUT):
    paths = (*CAPTURES, *RAW)
    cases = []
    schedules = Counter()
    for path in paths:
        source = json.loads(path.read_text())
        for case in source['cases']:
            edge = boundary(path, case)
            schedules['held81' if edge is None else f'edge{edge}'] += 1
            for index, symbol in enumerate(case['multi_visit_symbols']):
                symbol['visits']['46']['mode_bit5'] = int(edge is not None and
                                                           index >= edge)
            cases.append(case)
    if len(cases) != 66 or schedules != {'edge32': 49, 'held81': 13,
                                         'edge48': 4}:
        raise ValueError('mode schedule population changed')
    mode = solve(cases, NINE_BITS + (MODE_FEATURE,), STEPS)
    later_y6 = solve(cases, FEATURES, STEPS)
    if ((mode['state_codes'], mode['directed_conflicts'], mode['components'])
            != (61, 0, [61]) or
            (later_y6['state_codes'], later_y6['directed_conflicts'],
             later_y6['components']) != (60, 0, [40, 20])):
        raise ValueError('expanded phase graphs changed')
    labels = {int(key, 16): value for key, value in mode['relative_phase'].items()}
    proofs = []
    for parity in (0, 1):
        on = {state for state, phase in labels.items() if (phase + parity) & 1}
        off = set(labels) - on
        witness = [int(key, 16) for key in WITNESSES[parity]]
        if not set(witness) <= on or not all(
                pair_cannot_share_product(a, b, off)
                for a, b in itertools.combinations(witness, 2)):
            raise ValueError('mode-bit product lower-bound witness changed')
        cover = COVERS[parity]
        if any(any(cube_hit(state, cube) for cube in cover) != (state in on)
               for state in labels):
            raise ValueError('mode-bit product upper-bound cover changed')
        proofs.append(dict(global_phase_offsets=[parity, parity + 2],
                           on_states=len(on), off_states=len(off),
                           pairwise_incompatible_on_states=WITNESSES[parity],
                           exact_minimum_products=len(cover),
                           exact_cover_cubes=cover))
    sources = (Path(__file__),
               HERE / 'joint_mask04_12a_two_bit_package_mode_audit.py',
               HERE / 'joint_mask04_12a_ten_bit_package_route2.py',
               HERE / 'joint_mask04_12a_ten_bit_product_bound.py',
               HERE / 'joint_mask04_12a_0d_feature_graph.py', *paths)
    report = dict(experiment='mode-bit-conditioned phase graph across 66 real-PROM streams',
                  fixture=dict(streams=len(cases), symbols=65 * len(cases),
                               phase_convention=STEPS,
                               schedule_case_counts=dict(schedules),
                               mode_feature=MODE_FEATURE,
                               source='imposed D3EB bit-5 schedule'),
                  mode_bit_graph=mode,
                  later_y6_graph=dict(states=later_y6['state_codes'],
                                      conflicts=later_y6['directed_conflicts'],
                                      components=later_y6['components']),
                  phase_bit0_product_proofs=proofs,
                  limitations=[
                      'The mode-bit feature is assigned from each fixture schedule, not from a traced controller-to-gate net.',
                      'The connected graph removes a relative-phase ambiguity on these observed states; it does not identify a physical phase circuit or USART route.',
                      'A direct sum-of-products phase-bit-0 readout needs six or seven terms; multistage logic or another state encoding may differ.',
                      'The gate equations and holdout behavior are not established by this graph fit.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print('mode states', result['mode_bit_graph']['state_codes'],
          'components', result['mode_bit_graph']['components'],
          'product minima', [row['exact_minimum_products'] for row in
                             result['phase_bit0_product_proofs']])
