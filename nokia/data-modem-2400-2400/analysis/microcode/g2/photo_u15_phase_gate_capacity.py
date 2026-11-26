"""Test whether the pictured S64 AOI gate can encode observed phase bits."""

import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
INVENTORY = HERE.parent / 'board/inventory.json'
MODE0 = HERE / 'results/joint-mask04-12a-row0-boolean-twentytwo.json'
MODE1 = HERE / 'results/joint-mask04-12a-mode-phase-twelve.json'
PHOTO = HERE.parent.parent.parent / 'photos/PXL_20261123_114926601.jpg'
OUT = HERE / 'results/photo-u15-phase-gate-capacity.json'
CAPACITIES = (2, 2, 3, 4)  # S64 groups EF, JK, GHI, ABCD; order for search.


def cube_hit(value, cube):
    return all(bit < 0 or ((value >> position) & 1) == bit
               for position, bit in enumerate(cube))


def candidates(rows, bit, sum_value):
    on = [value for value, label in rows if ((label >> bit) & 1) == sum_value]
    off = [value for value, label in rows if ((label >> bit) & 1) != sum_value]
    by_capacity = {capacity: {0: (0, 'GROUND')} for capacity in set(CAPACITIES)}
    for width in range(1, 5):
        for positions in itertools.combinations(range(8), width):
            for bits in itertools.product((0, 1), repeat=width):
                cube = tuple(bits[positions.index(index)] if index in positions
                             else -1 for index in range(8))
                if any(cube_hit(value, cube) for value in off):
                    continue
                mask = sum(1 << index for index, value in enumerate(on)
                           if cube_hit(value, cube))
                if not mask:
                    continue
                pattern = ''.join('*' if value < 0 else str(value) for value in cube)
                for capacity in by_capacity:
                    if width <= capacity:
                        old = by_capacity[capacity].get(mask)
                        if old is None or (width, pattern) < old:
                            by_capacity[capacity][mask] = (width, pattern)
    return on, by_capacity


def fit(rows, bit, sum_value):
    on, available = candidates(rows, bit, sum_value)
    full = (1 << len(on)) - 1
    best = None
    for first, first_cube in available[2].items():
        for second, second_cube in available[2].items():
            for third, third_cube in available[3].items():
                remainder = full & ~(first | second | third)
                for fourth, fourth_cube in available[4].items():
                    if remainder & ~fourth:
                        continue
                    terms = (first_cube, second_cube, third_cube, fourth_cube)
                    active = tuple(term for term in terms if term[0])
                    key = (sum(term[0] for term in active),
                           len(active), tuple(term[1] for term in active))
                    if best is None or key < best[0]:
                        best = (key, terms)
    result = None
    if best is not None:
        slots = [dict(group=name, capacity=capacity,
                      literals=term[0], cube=term[1])
                 for name, capacity, term in zip(
                     ('EF', 'JK', 'GHI', 'ABCD'), CAPACITIES, best[1])]
        for value, label in rows:
            summed = any(slot['cube'] != 'GROUND' and
                         cube_hit(value, tuple(-1 if char == '*' else int(char)
                                               for char in slot['cube']))
                         for slot in slots)
            if summed != (((label >> bit) & 1) == sum_value):
                raise ValueError('AOI witness does not reproduce observed labels')
        result = dict(total_literals=best[0][0], active_terms=best[0][1],
                      slots=slots)
    return dict(output_relation=('direct' if sum_value == 0 else
                                 'S64 output inverted by another gate'),
                target_examples=len(on),
                candidate_masks_by_capacity={str(cap): len(values)
                                             for cap, values in available.items()},
                fit=result)


def unrestricted_cover(rows, bit, sum_value):
    """Find the smallest cover if every group could accept four inputs."""
    on, available = candidates(rows, bit, sum_value)
    full = (1 << len(on)) - 1
    options = [(mask, term) for mask, term in available[4].items() if mask]
    best = {0: (0, 0, ())}
    for limit in range(1, 7):
        updated = dict(best)
        for prior_mask, prior in best.items():
            if prior[0] >= limit:
                continue
            for mask, (width, cube) in options:
                union = prior_mask | mask
                candidate = (prior[0] + 1, prior[1] + width,
                             prior[2] + (cube,))
                if union not in updated or candidate < updated[union]:
                    updated[union] = candidate
        best = updated
        if full in best:
            count, literals, cubes = best[full]
            return dict(terms=count, literals=literals, cubes=cubes)
    return None


def run(out=OUT):
    inventory = json.loads(INVENTORY.read_text())
    u15 = next(part for part in inventory['parts'] if part['ref'] == 'U15')
    if u15['marking'] != 'SN74S64J' or u15['package_pins'] != 14:
        raise ValueError('U15 photo/package identification changed')
    labels = (json.loads(MODE0.read_text())['state_phase'],
              json.loads(MODE1.read_text())['trained_state_phase'])
    rows = [[(int(key, 16) | (mode << 7), value)
             for key, value in group.items()]
            for mode, group in enumerate(labels)]
    if [len(group) for group in rows] != [22, 12]:
        raise ValueError('observed phase-label count changed')
    screens = []
    for scope, examples in (('mode01', rows[0]), ('mode81_A1', rows[1]),
                            ('combined_with_mode_bit7', rows[0] + rows[1])):
        for bit in (0, 1):
            direct = fit(examples, bit, 0)
            inverted = fit(examples, bit, 1)
            screens.append(dict(scope=scope, phase_bit=bit,
                                examples=len(examples),
                                direct=direct, output_inverted=inverted))
    combined = [row for row in screens if row['scope'] == 'combined_with_mode_bit7']
    if (combined[0]['direct']['fit'] is not None or
            combined[0]['output_inverted']['fit'] is not None or
            combined[1]['direct']['fit'] is None or
            any(row['direct']['fit'] is None for row in screens
                if row['scope'] != 'combined_with_mode_bit7')):
        raise ValueError('U15 capacity classification changed')
    paths = (Path(__file__), INVENTORY, MODE0, MODE1, PHOTO)
    report = dict(experiment='exhaustive S64 AOI capacity screen for observed mode-conditioned phase labels',
                  fixture=dict(part='U15 SN74S64J, photographed 14 pins',
                               logic='Y=NOT(ABCD+EF+GHI+JK)',
                               group_capacities=(4, 2, 3, 2),
                               input_bits='seven captured state bits plus assumed D3EB bit7 as bit7',
                               candidate_cubes='all 8-bit cubes with 1–4 literals; no observed opposite-label hit',
                               unused_groups='assumed tied low',
                               unused_inputs_in_active_group='assumed tied high',
                               datasheet='https://www.ti.com/lit/ds/symlink/sn54s64.pdf'),
                  screens=screens,
                  unrestricted_combined_bit0={
                      'direct': unrestricted_cover(rows[0] + rows[1], 0, 0),
                      'output_inverted': unrestricted_cover(rows[0] + rows[1], 0, 1)},
                  limitations=[
                      'This is a Boolean capacity test on 34 observed labels, not a traced connection or proof U15 is available for phase logic.',
                      'The bit-0 no-fit result assumes only the seven state wires and one mode bit feed U15 directly; preprocessing or additional gates can change it.',
                      'Unobserved states are don’t-cares, and electrical fan-out, polarity, delays and unused-input ties are not verified.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    for row in result['screens']:
        print(row['scope'], row['phase_bit'],
              bool(row['direct']['fit']), bool(row['output_inverted']['fit']))
