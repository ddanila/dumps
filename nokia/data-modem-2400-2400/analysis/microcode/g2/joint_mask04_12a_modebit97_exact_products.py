"""Find exact direct-product counts for the observed twelve-bit phase labels."""

import hashlib
import json
from pathlib import Path

from joint_mask04_12a_0d_feature_graph import solve as phase_graph
from joint_mask04_12a_modebit66_graph import CAPTURES, RAW, boundary
from joint_mask04_12a_modebit70_level_feature_screen import TRIALS
from joint_mask04_12a_modebit91_gain110_diagnosis import NEW as FAILED_189
from joint_mask04_12a_modebit97_cover import FEATURES, STEPS
from joint_mask04_12a_modebit97_staged_capture import FRESH
from joint_mask04_12a_ten_bit_product_bound import cube_hit

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
SOURCE = RESULTS / 'joint-mask04-12a-modebit97-cover.json'
OUT = RESULTS / 'joint-mask04-12a-modebit97-exact-products.json'
WIDTH = 12


def weight(value):
    return bin(value).count('1')


def cube(mask, value):
    return ''.join('*' if not (mask >> bit) & 1 else str((value >> bit) & 1)
                   for bit in range(WIDTH))


def solve(rows, bit, polarity):
    on = [state for state, phase in rows if ((phase >> bit) & 1) == polarity]
    off = [state for state, phase in rows if ((phase >> bit) & 1) != polarity]
    # For each subset of input bits, retain only patterns that hit at least
    # one on-state and no observed off-state. Equivalent on-state coverage
    # needs only its least-literal representative for this product-count proof.
    valid = {}
    for mask in range(1, 1 << WIDTH):
        forbidden = {state & mask for state in off}
        classes = {}
        for index, state in enumerate(on):
            value = state & mask
            if value not in forbidden:
                classes[value] = classes.get(value, 0) | (1 << index)
        for value, hits in classes.items():
            old = valid.get(hits)
            if old is None or weight(mask) < weight(old[0]):
                valid[hits] = mask, value
    # A product covering a strict subset of another valid product is never
    # needed to minimize the number of direct OR terms.
    maximal = [hits for hits in valid
               if not any(hits != other and hits & ~other == 0
                          for other in valid)]
    choices = [[hits for hits in maximal if hits & (1 << index)]
               for index in range(len(on))]
    full = (1 << len(on)) - 1
    rejected_limits = []

    for limit in range(1, len(on) + 1):
        failed = set()
        calls = [0]

        def search(left, slots):
            calls[0] += 1
            if left == 0:
                return ()
            if slots == 0 or (left, slots) in failed:
                return None
            maximum = max(weight(hits & left) for hits in maximal)
            if (weight(left) + maximum - 1) // maximum > slots:
                return None
            pivot = min((index for index in range(len(on))
                         if left & (1 << index)),
                        key=lambda index: len(choices[index]))
            for hits in sorted(choices[pivot],
                               key=lambda item: weight(item & left),
                               reverse=True):
                suffix = search(left & ~hits, slots - 1)
                if suffix is not None:
                    return (hits,) + suffix
            failed.add((left, slots))
            return None

        answer = search(full, limit)
        if answer is None:
            rejected_limits.append(dict(products=limit, search_calls=calls[0]))
            continue
        witness = [cube(*valid[hits]) for hits in answer]
        if any(any(cube_hit(state, term) for term in witness) !=
               (((phase >> bit) & 1) == polarity)
               for state, phase in rows):
            raise ValueError('exact-product witness differs from labels')
        return dict(phase_bit=bit, on_polarity=polarity,
                    on_states=len(on), off_states=len(off),
                    distinct_valid_coverages=len(valid),
                    maximal_candidate_coverages=len(maximal),
                    rejected_product_limits=rejected_limits,
                    minimum_direct_products=limit,
                    witness_cubes=witness,
                    successful_search_calls=calls[0])
    raise ValueError('no direct-product cover found')


def run(out=OUT):
    source = json.loads(SOURCE.read_text())
    development = [(int(state, 16), phase) for state, phase in
                   source['phase_graph']['relative_phase'].items()]
    if len(development) != 97 or source['phase_graph']['directed_conflicts']:
        raise ValueError('frozen twelve-bit phase graph changed')
    paths = []
    cases = []

    def append(path, edge):
        paths.append(path)
        for case in json.loads(path.read_text())['cases']:
            limit = edge(case) if callable(edge) else edge
            for index, symbol in enumerate(case['multi_visit_symbols']):
                symbol['visits']['46']['mode_bit5'] = int(
                    limit is not None and index >= limit)
            cases.append(case)

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
    joined = phase_graph(cases, FEATURES, STEPS)
    if (len(cases), joined['state_codes'], joined['components'],
            joined['directed_conflicts']) != (100, 100, [100], 0):
        raise ValueError('joined post-holdout phase graph changed')
    post_holdout = [(int(state, 16), phase) for state, phase in
                    joined['relative_phase'].items()]
    screens = []
    for name, rows in (('development_97', development),
                       ('post_holdout_100', post_holdout)):
        results = [solve(rows, bit, polarity)
                   for bit in (0, 1) for polarity in (0, 1)]
        counts = {(row['phase_bit'], row['on_polarity']):
                  row['minimum_direct_products'] for row in results}
        if counts != {(0, 0): 8, (0, 1): 7, (1, 0): 5, (1, 1): 5}:
            raise ValueError(('exact direct-product bounds changed', name, counts))
        screens.append(dict(name=name, observed_states=len(rows), results=results))
    old_bit0 = next(row['witness_cubes'] for row in screens[0]['results']
                    if (row['phase_bit'], row['on_polarity']) == (0, 1))
    wrong_new = [f'{state:03X}' for state, phase in post_holdout
                 if any(cube_hit(state, term) for term in old_bit0) !=
                 bool(phase & 1)]
    if not wrong_new:
        raise ValueError('development-only witness no longer fails new states')
    sources = (Path(__file__), SOURCE,
               HERE / 'joint_mask04_12a_ten_bit_product_bound.py',
               HERE / 'joint_mask04_12a_0d_feature_graph.py',
               HERE / 'joint_mask04_12a_modebit66_graph.py',
               HERE / 'joint_mask04_12a_modebit70_level_feature_screen.py',
               HERE / 'joint_mask04_12a_modebit91_gain110_diagnosis.py',
               HERE / 'joint_mask04_12a_modebit97_cover.py',
               HERE / 'joint_mask04_12a_modebit97_staged_capture.py', *paths)
    report = dict(experiment='exhaustive direct-product bounds on development and post-holdout twelve-bit phase labels',
                  input_width=WIDTH, phase_convention=source['fixture']['phase_convention'],
                  search='All nonempty 12-bit input masks and observed patterns represent possible cubes; only off-state-free coverage sets are retained. Strictly dominated coverage sets are removed, then exact bounded set cover rejects every smaller product count.',
                  screens=screens,
                  post_holdout_phase_graph=joined,
                  development_witness_wrong_post_holdout_states=wrong_new,
                  limitations=[
                      'Bounds apply to separate direct sum-of-products outputs on 97 or 100 observed labels, with unobserved states as don’t-cares.',
                      'The post-holdout witness uses offset-191 streams as fitting constraints; it requires a new untouched fixture for validation.',
                      'They do not bound multistage/factored logic, shared products, phase subtraction, serial selection, or the physical photographed-package circuit.',
                      'The phase graph and labels inherit the saved real-PROM/controller development fixture and its assumed mode input.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    report = run()
    for screen in report['screens']:
        print(screen['name'],
              {(row['phase_bit'], row['on_polarity']): row['minimum_direct_products']
               for row in screen['results']})
