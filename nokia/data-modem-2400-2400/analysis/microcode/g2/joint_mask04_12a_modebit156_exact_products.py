"""Bound direct thirteen-bit receiver phase products on observed states."""

import hashlib
import json
from pathlib import Path

import joint_mask04_12a_modebit97_exact_products as exact

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
SOURCE = RESULTS / 'joint-mask04-12a-modebit156-staged-transfer.json'
OUT = RESULTS / 'joint-mask04-12a-modebit156-exact-products.json'


def run(out=OUT):
    source = json.loads(SOURCE.read_text())
    graph = source['phase_graph']
    if (graph['state_codes'], graph['components'],
            graph['directed_conflicts']) != (156, [156], 0):
        raise ValueError('thirteen-bit development graph changed')
    rows = [(int(state, 16), phase) for state, phase in
            graph['relative_phase'].items()]
    old_width = exact.WIDTH
    try:
        exact.WIDTH = 13
        bounds = [exact.solve(rows, bit, polarity)
                  for bit in (0, 1) for polarity in (0, 1)]
    finally:
        exact.WIDTH = old_width
    counts = {(row['phase_bit'], row['on_polarity']):
              row['minimum_direct_products'] for row in bounds}
    if counts != {(0, 0): 8, (0, 1): 8, (1, 0): 6, (1, 1): 5}:
        raise ValueError(('thirteen-bit product bounds changed', counts))
    sources = (Path(__file__), SOURCE,
               HERE / 'joint_mask04_12a_modebit97_exact_products.py',
               HERE / 'joint_mask04_12a_ten_bit_product_bound.py')
    report = dict(experiment='exact direct-product bound on 156 observed thirteen-bit receiver states',
                  fixture=dict(input_width=13, observed_states=156,
                               streams=source['fixture']['streams'],
                               selected_extra_capture=['141', 'y3f8', 6]),
                  bounds=bounds,
                  limitations=[
                      'These are direct sum-of-products counts with unobserved thirteen-bit states as don’t-cares, not a minimum multistage or photographed-package gate circuit.',
                      'The 156 labels include the 0.95x streams that selected this extra bit; all witnesses are development fits requiring a new real-PROM holdout.',
                      'Storage timing is an assumed U14-to-U3 transfer with U25 late capture; physical nets and a phase/USART route remain untraced.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print({(row['phase_bit'], row['on_polarity']): row['minimum_direct_products']
           for row in result['bounds']})
