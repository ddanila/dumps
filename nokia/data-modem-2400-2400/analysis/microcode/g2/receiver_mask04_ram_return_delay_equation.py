"""Verify the legal-carrier 3FA high output is a delayed 3F9 recoding."""

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


def run(out=HERE / 'results/receiver-mask04-ram-return-delay-equation.json'):
    prior = json.loads(PRIOR.read_text())
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    execute = instrumented_execute()
    cases = []
    for seed, degrees in CASES:
        samples, adc = case_input(seed, degrees)
        result = execute(mapping, scenario_for(base, adc, True, True),
                         CYCLES, mode='integrated', trace_limit=0)
        old = next(c for c in prior['cases']
                   if c['seed'] == seed and c['route'] == 'high_return_3fa')
        y = result['external_ram_candidate']['y_by_pc']
        y9, ya = y[0x3F9], y[0x3FA]
        if (not result['clean'] or result['trace_digest'] != old['trace_digest'] or
                len(y9) != VISITS or len(ya) != VISITS or
                hashlib.sha256(bytes(ya)).hexdigest() != old['y3fa_sha256']):
            raise ValueError('legal RAM-return trace changed')
        mismatches = []
        nonconstant_source_samples = []
        high_map = Counter()
        for sample in range(len(samples)):
            start = first_visit(sample)
            stop = first_visit(sample + 1) if sample + 1 < len(samples) else VISITS
            if len(set(y9[start:stop])) != 1:
                nonconstant_source_samples.append(sample)
            source = y9[first_visit(sample - 3)] & 0xF0 if sample >= 3 else 0
            expected_hi = (source + 0x20) & 0xF0
            if sample >= 3:
                high_map[(source, expected_hi)] += stop - start
            mismatches.extend(visit for visit in range(start, stop)
                              if ya[visit] & 0xF0 != expected_hi)
        if mismatches or nonconstant_source_samples:
            raise ValueError(('delayed high-code equation changed',
                              seed, mismatches[:8],
                              nonconstant_source_samples[:8]))
        cases.append(dict(seed=seed, degrees=degrees,
                          trace_digest=result['trace_digest'],
                          y3f9_sha256=hashlib.sha256(bytes(y9)).hexdigest(),
                          y3fa_sha256=hashlib.sha256(bytes(ya)).hexdigest(),
                          samples=len(samples), visits_checked=VISITS,
                          source_samples_constant=len(samples),
                          high_nibble_mismatches=0,
                          initial_high_20_visits=first_visit(3),
                          low_bit_one_visits=sum(value & 1 for value in ya),
                          observed_source_to_output_high=[
                              dict(source=f'{source:02X}', output=f'{output:02X}',
                                   visits=count)
                              for (source, output), count in sorted(high_map.items())]))
    report = dict(experiment='legal-carrier 3FA delayed high-nibble equation',
                  fixture=dict(route='3F9 Y high -> external RAM offset -3 -> 3FA D high',
                               equation='Y3FA_high(sample s)=(Y3F9_high(sample s-3)+0x20)&0xF0; first three samples 0x20',
                               source_sample_hold='47/46 visits; 128 samples; one address tick per sample'),
                  cases=cases, total_checked_visits=sum(c['visits_checked'] for c in cases),
                  total_high_nibble_mismatches=0,
                  source_sha256={str(p.relative_to(HERE.parents[4])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (Path(__file__), PRIOR,
                                           HERE / 'receiver_mask04_legal_ram_return.py',
                                           HERE / 'joint_upper_ram_feedback_screen.py')},
                  limitations=[
                      'The equation covers Y high nibble; the low bit comes from separate ALU carry behavior.',
                      'The external RAM address, latch, return mux, TEST and output path are assumed.',
                      'A delayed sample transform is not a decoded dibit or demonstrated echo cancellation.'
                  ])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print('checked', result['total_checked_visits'],
          'high-nibble outputs with',
          result['total_high_nibble_mismatches'], 'mismatches')
