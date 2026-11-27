"""Prove a five-product lower bound for the observed ten-bit phase bit 0."""

import hashlib
import itertools
import json
from pathlib import Path

from joint_mask04_12a_0d_feature_graph import solve
from joint_mask04_12a_ten_bit_package_route2 import CAPTURES, FEATURES, NINE_BITS, STEPS
import joint_mask04_12a_row0_serial_timing as serial

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
RAW = tuple(RESULTS / f'joint-mask04-12a-ten-bit-package-route2-mode81-holdout-{n}.json'
            for n in (173, 175))
OUT = RESULTS / 'joint-mask04-12a-ten-bit-product-bound.json'
WITNESSES = {
    0: ('005', '0C8', '149', '1CA', '25C'),
    1: ('082', '1C8', '049', '12D', '2CD'),
}
# Bit positions increase left to right; * means that input is not used.
FIVE_PRODUCT_COVERS = {
    0: ('**10*****0', '*00*00*10*', '***1*0*01*', '*****0*0*1', '*1*1******'),
    1: ('*011***1**', '**00*0***0', '000100*110', '**1*01001*', '*0*1***000'),
}
VISITS = ('46', '47', '93', '94', '141')
SITES = ('row0', 'y3f8')


def cube_hit(state, cube):
    return all(char == '*' or int(char) == ((state >> bit) & 1)
               for bit, char in enumerate(cube))


def pair_cannot_share_product(first, second, off_states):
    """Every product covering both must include their common-bit cube."""
    common = ~(first ^ second) & 0x3FF
    return any((off & common) == (first & common) for off in off_states)


def run(out=OUT):
    paths = (*CAPTURES, *RAW)
    cases = [case for path in paths for case in json.loads(path.read_text())['cases']]
    graph = solve(cases, FEATURES, STEPS)
    if (len(cases), graph['state_codes'], graph['directed_conflicts'],
            graph['components']) != (66, 60, 0, [40, 20]):
        raise ValueError('ten-bit graph changed')
    labels = {int(key, 16): phase
              for key, phase in graph['relative_phase'].items()}
    proofs = []
    for polarity in (0, 1):
        on = {state for state, phase in labels.items() if (phase + polarity) & 1}
        off = set(labels) - on
        witness = [int(key, 16) for key in WITNESSES[polarity]]
        if not set(witness) <= on or not all(
                pair_cannot_share_product(a, b, off)
                for a, b in itertools.combinations(witness, 2)):
            raise ValueError('five-state incompatibility witness changed')
        cover = FIVE_PRODUCT_COVERS[polarity]
        if any(any(cube_hit(state, cube) for cube in cover) != (state in on)
               for state in labels):
            raise ValueError('five-product upper-bound cover changed')
        proofs.append(dict(global_offsets=[polarity, polarity + 2],
                           on_states=len(on), off_states=len(off),
                           pairwise_incompatible_on_states=WITNESSES[polarity],
                           lower_bound_products=5,
                           exact_cover_products=len(cover),
                           exact_cover_cubes=cover))
    screen = []
    for visit in VISITS:
        for site in SITES:
            for bit in range(8):
                candidate = solve(cases, NINE_BITS + ((visit, site, bit),), STEPS)
                screen.append(dict(visit=visit, site=site, bit=bit,
                                   states=candidate['state_codes'],
                                   conflicts=candidate['directed_conflicts'],
                                   components=candidate['components']))
    zero = [row for row in screen if row['conflicts'] == 0]
    if (len(screen), len(zero)) != (80, 24):
        raise ValueError('expanded alternate-capture screen changed')
    last_141 = serial.Y3F8_CYCLE + 141 * serial.CYCLES_PER_VISIT
    setup_141 = serial.VARIANTS['aligned']['first_rxc_cycle'] - last_141
    if setup_141 != 1425:
        raise ValueError('visit-141 modeled timing changed')
    sources = (Path(__file__), HERE / 'joint_mask04_12a_ten_bit_package_route2.py',
               HERE / 'joint_mask04_12a_0d_feature_graph.py',
               HERE / 'joint_mask04_12a_row0_serial_timing.py', *paths)
    report = dict(experiment='ten-bit observed phase-bit-0 product lower bound and alternate capture screen',
                  fixture=dict(streams=len(cases), symbols=65 * len(cases),
                               phase_convention=STEPS),
                  ten_bit_graph=dict(states=graph['state_codes'],
                                     conflicts=graph['directed_conflicts'],
                                     components=graph['components']),
                  phase_bit0_product_proofs=proofs,
                  alternate_capture_screen=screen,
                  zero_conflict_captures=zero,
                  visit_141_modeled_setup_cycles=setup_141,
                  limitations=[
                      'Five products are necessary only for a direct sum-of-products readout of this ten-bit state on the 60 observed codes. Multistage logic or a different capture may evade the bound.',
                      'The capture screen tests graph consistency, not gate realizability or physical nets.',
                      'The observed graph has two components; their relative phase is not independently anchored.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print('products', [row['lower_bound_products'] for row in
                       result['phase_bit0_product_proofs']],
          'zero-conflict alternatives', len(result['zero_conflict_captures']))
