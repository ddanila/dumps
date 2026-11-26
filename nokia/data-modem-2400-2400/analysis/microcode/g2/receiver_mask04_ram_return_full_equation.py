"""Verify both nibbles of 3FA Y under the legal delayed-RAM route."""

import hashlib
import json
from collections import Counter
from pathlib import Path

from joint_mask04_12a_buffered_line import MAPPINGS, candidate, fixture, mapped, mapping_with_upper_source
from joint_upper_ram_feedback_screen import instrumented_execute
from receiver_mask04_legal_ram_return import CASES, CYCLES, VISITS, scenario_for
from receiver_mask04_postvisit_state_history import case_input, first_visit

HERE = Path(__file__).resolve().parent
PRIOR = HERE / 'results/receiver-mask04-legal-ram-return.json'
CODEBOOK = HERE / 'results/joint-mask04-receive-3f9-3fa-codebook.json'
HIGH = HERE / 'results/receiver-mask04-ram-return-delay-equation.json'


def run(out=HERE / 'results/receiver-mask04-ram-return-full-equation.json'):
    prior = json.loads(PRIOR.read_text())
    codebook = json.loads(CODEBOOK.read_text())
    high = json.loads(HIGH.read_text())
    low_by_nibble = {}
    for nibble in range(16):
        values = codebook['codebooks']['3FA']['values_by_current'][f'{nibble:X}']
        if len(values) != 1:
            raise ValueError('3FA current-ADC codebook is ambiguous')
        low_by_nibble[nibble] = int(values[0], 16) & 1
    if [f'{n:X}' for n in range(16) if low_by_nibble[n]] != ['6', 'B', 'C']:
        raise ValueError('3FA low-bit codebook changed')
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    execute = instrumented_execute()
    cases = []
    for seed, degrees in CASES:
        samples, adc = case_input(seed, degrees)
        streams = {}
        for route, feedback in (('write_only', False),
                                ('high_return_3fa', True)):
            result = execute(mapping, scenario_for(base, adc, feedback, True),
                             CYCLES, mode='integrated', trace_limit=0)
            old = next(c for c in prior['cases']
                       if c['seed'] == seed and c['route'] == route)
            y = result['external_ram_candidate']['y_by_pc']
            if (not result['clean'] or result['trace_digest'] != old['trace_digest'] or
                    len(y[0x3F9]) != VISITS or len(y[0x3FA]) != VISITS or
                    hashlib.sha256(bytes(y[0x3FA])).hexdigest() !=
                    old['y3fa_sha256']):
                raise ValueError(('saved legal route changed', seed, route))
            streams[route] = y
        feedback_y9 = streams['high_return_3fa'][0x3F9]
        feedback_ya = streams['high_return_3fa'][0x3FA]
        control_ya = streams['write_only'][0x3FA]
        prior_high = next(c for c in high['cases'] if c['seed'] == seed)
        if hashlib.sha256(bytes(feedback_y9)).hexdigest() != prior_high['y3f9_sha256']:
            raise ValueError('saved 3F9 source stream changed')
        counts = Counter()
        for sample, adc_byte in enumerate(samples):
            start = first_visit(sample)
            stop = first_visit(sample + 1) if sample + 1 < len(samples) else VISITS
            delayed_hi = (feedback_y9[first_visit(sample - 3)] & 0xF0
                          if sample >= 3 else 0)
            expected_hi = (delayed_hi + 0x20) & 0xF0
            expected_lo = low_by_nibble[adc_byte >> 4]
            expected = expected_hi | expected_lo
            for visit in range(start, stop):
                counts['checked'] += 1
                counts['full_mismatch'] += feedback_ya[visit] != expected
                counts['low_control_mismatch'] += (
                    (feedback_ya[visit] & 1) != (control_ya[visit] & 1))
                counts['control_low_codebook_mismatch'] += (
                    (control_ya[visit] & 1) != expected_lo)
                counts[f'current_nibble_{adc_byte >> 4:X}'] += 1
        if (counts['checked'] != VISITS or counts['full_mismatch'] or
                counts['low_control_mismatch'] or
                counts['control_low_codebook_mismatch']):
            raise ValueError(('full 3FA equation changed', seed, dict(counts)))
        cases.append(dict(seed=seed, degrees=degrees,
                          feedback_trace_digest=next(c['trace_digest']
                              for c in prior['cases'] if c['seed'] == seed
                              and c['route'] == 'high_return_3fa'),
                          checked_visits=counts['checked'],
                          full_byte_mismatches=counts['full_mismatch'],
                          feedback_vs_control_low_mismatches=counts['low_control_mismatch'],
                          control_low_vs_codebook_mismatches=
                              counts['control_low_codebook_mismatch'],
                          current_adc_high_nibble_visit_counts={
                              f'{n:X}': counts[f'current_nibble_{n:X}']
                              for n in range(16)}))
    report = dict(experiment='complete legal-carrier 3FA Y equation under delayed RAM return',
                  fixture=dict(equation='Y3FA(s) = ((Y3F9(s-3)&0xF0)+0x20)&0xF0 | bit(current_ADC_high in {6,B,C}); first three source highs 0',
                               codebook='independently executed three-carrier 3FA current-nibble table',
                               routes=['write_only', 'high_return_3fa']),
                  cases=cases, checked_feedback_visits=sum(c['checked_visits']
                                                            for c in cases),
                  low_bit_one_nibbles=['6', 'B', 'C'],
                  full_byte_mismatches=0,
                  source_sha256={str(p.relative_to(HERE.parents[4])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (Path(__file__), PRIOR, CODEBOOK, HIGH,
                                           HERE / 'receiver_mask04_legal_ram_return.py',
                                           HERE / 'joint_upper_ram_feedback_screen.py')},
                  limitations=[
                      'This is an exact equation for the stated legal carriers and assumed RAM/TEST fixture, not a proof of physical wiring.',
                      'The equation describes a delayed sample code plus a current-sample code bit; it is not a demonstrated differential decision or echo residual.'
                  ])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print('checked', result['checked_feedback_visits'],
          'full Y bytes with', result['full_byte_mismatches'], 'mismatches')
