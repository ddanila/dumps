"""Project photo-B5 tone steps through fast-clock 9600 Hz latch gating."""

import hashlib
import math
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent/'assumed'), str(HERE)]

from common import save
from photo_127_liveness import ROM, run_case
from photo_127_tone_probe import spectrum
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

OSCILLATOR_HZ = 14_400_000
SAMPLE_HZ = 9_600
SAMPLES = 640
STEPS = ((48, 1800), (56, 2100))
DIVISORS = (1, 2, 3, 4)
VISITS_NUMERATOR = OSCILLATOR_HZ//(4*SAMPLE_HZ)


def phase(n, increment):
    return (3+n*increment) & 255


def projected_b5(rom, increment, visits):
    values = []
    for n in visits:
        index = phase(n, increment)
        y = (index-rom[256+index]) & 255
        values.append(y >> 7)
    return values


def run(out=HERE/'results/photo-127-clock-alias.json'):
    if OSCILLATOR_HZ % (4*SAMPLE_HZ) or VISITS_NUMERATOR != 375:
        raise ValueError('oscillator-to-PC129 ratio changed')
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    rom = ROM.read_bytes()
    cases = []
    for increment, expected_hz in STEPS:
        _, execution, trace = run_case(mapping, base, increment, 256)
        reads = [row for row in trace if row['pc'] == 0x129]
        if not execution['clean'] or len(reads) != 740:
            raise ValueError(f'phase-step execution changed for {increment}')
        for n, row in enumerate(reads, 1):
            address = 256+phase(n, increment)
            y = (phase(n, increment)-rom[address]) & 255
            if (row['external_read']['address'] != address or
                    row['external_read']['value'] != rom[address] or
                    row['alu']['y'] != y or
                    row['alu']['y'] >> 7 != projected_b5(rom, increment, [n])[0]):
                raise ValueError(f'projected recurrence differs at PC129 read {n}')

        direct = spectrum(projected_b5(rom, increment, range(1, SAMPLES+1)),
                          expected_hz)
        if direct['peak_hz'] != expected_hz:
            raise ValueError('direct PC129-per-sample baseline changed')
        variants = []
        period = 256//math.gcd(increment, 256)
        for divisor in DIVISORS:
            outcomes = []
            for fractional_phase in range(divisor):
                for visit_offset in range(period):
                    visits = [visit_offset+
                              ((sample*VISITS_NUMERATOR+fractional_phase)//divisor)
                              for sample in range(1, SAMPLES+1)]
                    shape = spectrum(projected_b5(rom, increment, visits),
                                     expected_hz)
                    outcomes.append((fractional_phase, visit_offset, shape))
            peaks = Counter(value['peak_hz'] for _, _, value in outcomes)
            best = max(outcomes, key=lambda row: row[2]['sinusoid_r2'])
            variants.append(dict(oscillator_periods_per_microinstruction=divisor,
                                 pc129_visits_per_sample=f'{VISITS_NUMERATOR}/{divisor}',
                                 alignments=len(outcomes),
                                 peak_hz_counts={str(key): count for key, count
                                                 in sorted(peaks.items())},
                                 target_r2_min=min(value['sinusoid_r2']
                                                   for _, _, value in outcomes),
                                 target_r2_max=best[2]['sinusoid_r2'],
                                 best_target_alignment=dict(
                                     fractional_phase=best[0],
                                     visit_offset=best[1],
                                     peak_hz=best[2]['peak_hz'])))
        expected_peaks = {48: (3000, 1500, 4200, 4050),
                          56: (300, 150, 3300, 4725)}[increment]
        if any(row['peak_hz_counts'] != {str(float(peak)): row['alignments']}
               for row, peak in zip(variants, expected_peaks)):
            raise ValueError(f'fast-clock aliases changed for {increment}')
        cases.append(dict(d127_increment=increment,
                          target_hz=expected_hz,
                          verified_pc129_reads=len(reads),
                          execution_trace_digest=execution['trace_digest'],
                          direct_9600_pc129_per_sample=direct,
                          projected_fast_clock=variants))

    paths = [Path(__file__), ROM, HERE/'photo_127_liveness.py',
             HERE/'photo_127_tone_probe.py', HERE/'photo_controller_path.py',
             HERE/'photo_mapping_q_sweep.py', HERE/'photo_mapping_stream_screen.py',
             HERE.parent/'assumed/execute.py', MAPPINGS['q3'],
             HERE.parents[2]/'analysis/microcode/board/inventory.json',
             HERE.parents[2]/'photos/PXL_20261123_114926601.jpg']
    report = dict(status='validated PC129 recurrence with projected fast-clock alias screen',
                  fixture=dict(mapping='q3 photo-swapped', initial_q=0,
                               pc129_rom_bank=256,
                               assumed_b5_route='Y7→LS273 D4→Q4→DAC08 B5',
                               held_d127_steps=[step for step, _ in STEPS],
                               oscillator_hz=OSCILLATOR_HZ,
                               target_sample_rate_hz=SAMPLE_HZ,
                               projected_samples=SAMPLES,
                               fast_microinstruction_divisors=list(DIVISORS),
                               sample_visit_rule='n=offset+floor((sample*375+fractional_phase)/divisor)'),
                  cases=cases,
                  limitations=[
                      'Only the first 740 PC129 visits per step are executed; longer sample sequences use the checked phase/ROM/Y recurrence.',
                      'The 14.4 MHz oscillator marking is visible, but its connection and divisor to the 8X02 and LS273 clock are untraced.',
                      'A 9600 Hz output gate at PC129, Y7→D4, A8 bank, held-I0 and D127 source are hypotheses.',
                      'The tested divisors 1–4 and fixed-gate alignments do not exhaust slower or independently generated clocks, other paths or full DAC wiring.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    for case in report['cases']:
        print(case['d127_increment'],
              [next(iter(row['peak_hz_counts']))
               for row in case['projected_fast_clock']])
