"""Exhaust all ordered-Y DAC bit permutations preserving photo Q4 to B5."""

import hashlib
import itertools
import json
import math
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from photo_127_liveness import ROM
from photo_main_dibit_dac_decode import correlation, decision_result
from photo_main_dibit_pulse import (BASE, PULSE_VISITS, VISITS_PER_SAMPLE,
                                    VISITS_PER_SYMBOL, dibit_rule)
from reference_modem import QUADRANT_TO_DIBIT, raised_cosine, transmit

PULSE = HERE / 'results/photo-main-dibit-pulse.json'
SELECTED = (0, 1, 2, 4, 3, 5, 6, 7)
FIXED_SHIFT = 4
SAMPLE_HZ = 9600
CARRIER_HZ = 1800


def raw_y_codes(rom, dibits):
    phase = 3
    values = []
    for dibit in dibits:
        first = dibit_rule(dibit & 1, dibit >> 1)
        for visit in range(VISITS_PER_SYMBOL):
            phase = (phase + (first if visit < PULSE_VISITS else BASE)) & 255
            if visit % VISITS_PER_SAMPLE == 0:
                values.append((phase - rom[256 + phase]) & 255)
    return values


def mapped_codes(raw, permutation):
    return [sum(((value >> bit) & 1) << permutation[bit] for bit in range(8))
            for value in raw]


def matched_filter_basis(raw):
    aligned = raw[FIXED_SHIFT:]
    aligned = aligned[:len(aligned) // 8 * 8]
    rows = []
    for symbol in range(len(aligned) // 8):
        # Eight input-bit contributions plus the constant -128 AC center.
        terms = [0j] * 9
        for sample in range(max(0, 8 * symbol - 32),
                            min(len(aligned), 8 * symbol + 33)):
            angle = -2 * math.pi * CARRIER_HZ * sample / SAMPLE_HZ
            weight = complex(math.cos(angle), math.sin(angle)) * raised_cosine(
                (sample - 8 * symbol) / 8)
            terms[8] -= 128 * weight
            value = aligned[sample]
            for bit in range(8):
                if (value >> bit) & 1:
                    terms[bit] += weight
        rows.append(terms)
    return rows


def score(basis, dibits, permutation):
    estimates = [terms[8] + sum((1 << permutation[bit]) * terms[bit]
                                for bit in range(8)) for terms in basis]
    errors = 0
    for index, (previous, current) in enumerate(zip(estimates, estimates[1:])):
        delta = current * previous.conjugate()
        if abs(delta) < 1e-12:
            raise ValueError('candidate has no carrier for a decision')
        components = (delta.real, delta.imag, -delta.real, -delta.imag)
        quadrant = max(range(4), key=lambda value: components[value])
        errors += QUADRANT_TO_DIBIT[quadrant] != dibits[index + 1]
    return errors, len(estimates) - 1


def run(out=HERE / 'results/photo-dac-bus-permutations.json'):
    pulse = json.loads(PULSE.read_text())
    rom = ROM.read_bytes()
    if len(pulse['cases']) != 4:
        raise ValueError('controller stream cases changed')
    cases = []
    for case in pulse['cases']:
        dibits = case['all_dibits']
        raw = raw_y_codes(rom, dibits)
        selected_codes = mapped_codes(raw, SELECTED)
        if hashlib.sha256(bytes(selected_codes)).hexdigest() != case['dac_sample_sha256']:
            raise ValueError(('executed selected-bus code sequence changed', case['selector']))
        cases.append(dict(selector=case['selector'], dibits=dibits,
                          raw=raw, basis=matched_filter_basis(raw),
                          reference=transmit(dibits)))
    input_bits = tuple(bit for bit in range(8) if bit != 4)
    output_bits = tuple(bit for bit in range(8) if bit != 3)
    rows = []
    for order in itertools.permutations(output_bits):
        permutation = [0] * 8
        permutation[4] = 3  # LS273 Q4 to DAC08 B5, the photo candidate.
        for source, destination in zip(input_bits, order):
            permutation[source] = destination
        counts = [score(case['basis'], case['dibits'], permutation)
                  for case in cases]
        rows.append(dict(input_bit_to_dac_code_bit=permutation,
                         errors_by_selector={case['selector']: errors
                                             for case, (errors, _) in zip(cases, counts)},
                         total_errors=sum(errors for errors, _ in counts),
                         total_decisions=sum(decisions for _, decisions in counts)))
    if len(rows) != 5040 or any(row['total_decisions'] != 104 for row in rows):
        raise ValueError('permutation coverage changed')
    selected = next(row for row in rows if tuple(row['input_bit_to_dac_code_bit']) == SELECTED)
    if selected['total_errors'] != 1:
        raise ValueError('previous chosen DAC order changed')
    for row in rows:
        if row['total_errors'] == 0 or row is selected:
            permutation = row['input_bit_to_dac_code_bit']
            row['mean_abs_reference_correlation'] = round(sum(
                abs(correlation(mapped_codes(case['raw'], permutation)[FIXED_SHIFT:],
                                case['reference'][:-FIXED_SHIFT]))
                for case in cases) / len(cases), 6)
    # Check every headline zero/one-error mapping against the independent
    # receiver implementation, plus representative higher-error controls.
    checks = [row for row in rows if row['total_errors'] <= 1]
    checks.extend((rows[0], rows[1200], rows[3000], rows[-1]))
    for row in checks:
        permutation = row['input_bit_to_dac_code_bit']
        for case in cases:
            direct = decision_result(mapped_codes(case['raw'], permutation),
                                     case['dibits'])
            expected_decisions = 30 if case['selector'] in ('00', '20') else 22
            if (direct['errors'] != row['errors_by_selector'][case['selector']] or
                    direct['decisions'] != expected_decisions):
                raise ValueError(('matched-filter basis differs from receiver', row, case['selector']))
    total_histogram = dict(sorted(Counter(row['total_errors'] for row in rows).items()))
    zeros = [row for row in rows if row['total_errors'] == 0]
    one = [row for row in rows if row['total_errors'] == 1]
    if len(zeros) != 12 or len(one) != 172:
        raise ValueError('candidate error counts changed')
    source_paths = [Path(__file__), PULSE, ROM,
                    HERE / 'photo_main_dibit_pulse.py',
                    HERE / 'photo_main_dibit_dac_decode.py',
                    HERE / 'photo_dac08_bus_order_screen.py',
                    HERE / 'reference_modem.py',
                    HERE.parents[2] / 'photos/PXL_20261123_114854803.jpg']
    report = dict(status='photo B5 segment and controller dibit decisions do not uniquely identify the full DAC bit order',
                  fixture=dict(input='four real-controller dibit streams through the verified D127 pulse/PC129 recurrence',
                               y_to_ls273='ordered bit positions, held fixed',
                               q4_to_dac_b5='input bit 4 to DAC code bit 3, photo candidate',
                               all_other_bit_routes='all 7! one-to-one assignments',
                               receiver='independent known-carrier reference decoder at fixed four-sample shift',
                               total_decisions_per_permutation=104),
                  selected_prior_order=selected,
                  permutations_tested=len(rows),
                  zero_error_permutations=len(zeros),
                  one_error_permutations=len(one),
                  zero_error_candidates=zeros,
                  total_error_histogram=total_histogram,
                  all_candidates=rows,
                  validation='Selected DAC sequence hashes match executed PROM traces; every zero/one-error mapping and four higher-error controls agree with the independent reference receiver implementation on every selector.',
                  limitations=['Only the Q4→B5 segment is photo-suggested; ordered Y→LS273 D and the other seven bus routes are assumptions.',
                               'The four-visit dibit pulse, DAC clock, analog output and fixed decoder timing are also hypotheses.',
                               'Low decision error does not prove a unique Nokia bus, line output or DSC receive path.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in source_paths})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print(result['permutations_tested'], result['zero_error_permutations'],
          result['one_error_permutations'], result['selected_prior_order']['total_errors'])
