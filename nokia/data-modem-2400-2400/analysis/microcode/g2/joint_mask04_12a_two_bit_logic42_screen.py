"""Find minimum SOP covers after the 42-code gain-one phase audit."""

import hashlib
import json
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
GRAPH = HERE / 'results/joint-mask04-12a-two-bit-gain1-frozen37-audit.json'
PRIOR = HERE / 'results/joint-mask04-12a-two-bit-logic-screen.json'
PRIOR_GRAPH = HERE / 'results/joint-mask04-12a-two-bit-gain1-frozen36-audit.json'
OUT = HERE / 'results/joint-mask04-12a-two-bit-logic42-screen.json'
WIDTH = 9


def popcount(value):
    return bin(value).count('1')


def prime_cubes(on, off):
    """Return (care mask, high bits, covered on-set bits) for prime cubes."""
    ordered = sorted(on)
    cubes = []
    for mask in range(1 << WIDTH):
        value = mask
        while True:
            if not any((state & mask) == value for state in off):
                covered = sum(1 << index for index, state in enumerate(ordered)
                              if (state & mask) == value)
                if covered:
                    cubes.append((mask, value, covered))
            if value == 0:
                break
            value = (value - 1) & mask
    return [cube for cube in cubes if not any(
        other != cube and (other[0] & cube[0]) == other[0] and
        (cube[1] & other[0]) == other[1]
        for other in cubes)]


def minimum_cover(on, off):
    cubes = prime_cubes(on, off)
    ordered = sorted(on)
    all_on = (1 << len(ordered)) - 1
    by_bit = [tuple(index for index, cube in enumerate(cubes)
                    if cube[2] & (1 << bit)) for bit in range(len(ordered))]

    @lru_cache(None)
    def solve(remaining):
        if remaining == 0:
            return (0, 0, ())
        bits = [bit for bit in range(len(ordered)) if remaining & (1 << bit)]
        pivot = min(bits, key=lambda bit: len(by_bit[bit]))
        best = None
        for index in sorted(by_bit[pivot],
                            key=lambda i: (-popcount(cubes[i][2] & remaining),
                                           popcount(cubes[i][0]))):
            mask, value, covered = cubes[index]
            tail = solve(remaining & ~covered)
            candidate = (1 + tail[0], popcount(mask) + tail[1],
                         tuple(sorted((index, *tail[2]))))
            if best is None or candidate < best:
                best = candidate
        return best

    terms, literals, indices = solve(all_on)
    chosen = [cubes[index] for index in indices]
    assert all(any((state & mask) == value for mask, value, _ in chosen)
               for state in on)
    assert all(not any((state & mask) == value for mask, value, _ in chosen)
               for state in off)
    return dict(on_codes=len(on), off_codes=len(off), prime_cubes=len(cubes),
                minimum_terms=terms, minimum_literals=literals,
                product_widths=sorted((popcount(mask) for mask, _, _ in chosen),
                                      reverse=True),
                complemented_inputs=sorted({bit for mask, value, _ in chosen
                                            for bit in range(WIDTH)
                                            if mask & (1 << bit) and
                                            not value & (1 << bit)}),
                cubes=[dict(care_mask=f'{mask:03X}', high_bits=f'{value:03X}',
                            covered_codes=[f'{state:03X}' for state in ordered
                                           if (state & mask) == value])
                       for mask, value, _ in chosen],
                cached_subproblems=solve.cache_info().currsize)


def run(out=OUT):
    graph = json.loads(GRAPH.read_text())['phase_graph']
    if (graph['state_codes'], graph['directed_conflicts'], graph['components']) != (42, 0, [42]):
        raise ValueError('observed phase graph changed')
    labels = {int(code, 16): phase for code, phase in
              graph['relative_phase'].items()}
    offsets = {}
    for offset in range(4):
        bits = {}
        for bit in (0, 1):
            on = {state for state, phase in labels.items()
                  if ((phase + offset) & 3) & (1 << bit)}
            bits[str(bit)] = minimum_cover(on, set(labels) - on)
        offsets[str(offset)] = bits
    prior = json.loads(PRIOR.read_text())
    old_labels = set(json.loads(PRIOR_GRAPH.read_text())['phase_graph']['relative_phase'])
    prior_checks = []
    for state in sorted(set(graph['relative_phase']) - old_labels):
        code = int(state, 16)
        output_bits = [int(any((code & int(cube['care_mask'], 16)) ==
                               int(cube['high_bits'], 16)
                               for cube in prior['offsets']['3'][str(bit)]['cubes']))
                       for bit in (0, 1)]
        predicted = (((output_bits[1] << 1) | output_bits[0]) - 3) & 3
        prior_checks.append(dict(code=state, inferred_phase=labels[code],
                                 prior_sop_phase=predicted,
                                 agrees=predicted == labels[code]))
    if [item['code'] for item in prior_checks if not item['agrees']] != ['1ED']:
        raise ValueError('prior SOP holdout prediction changed')
    report = dict(experiment='minimum observed-state phase SOP screen after 42-code audit',
                  fixture=dict(state_bits=WIDTH, observed_states=len(labels),
                               phase_offsets=list(range(4))),
                  offsets=offsets,
                  prior_sop_new_key_predictions=prior_checks,
                  limitations=[
                      'The 470 unobserved nine-bit keys are treated as dont-cares; a minimum observed-state cover does not predict their phases.',
                      'SOP term and literal minima do not prove a physical gate network, fan-out, delay, input inversion or the photographed net assignments.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in (Path(__file__), GRAPH, PRIOR, PRIOR_GRAPH)})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print({offset: [(bit, row['minimum_terms'], row['minimum_literals'],
                      row['product_widths']) for bit, row in bits.items()]
           for offset, bits in result['offsets'].items()})
