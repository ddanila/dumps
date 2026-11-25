"""Find phase steps that survive fast PC129-to-9600 Hz gating."""

import hashlib
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent/'assumed'), str(HERE)]

from common import save
from photo_127_clock_alias import SAMPLE_HZ, SAMPLES, projected_b5
from photo_127_liveness import ROM, run_case
from photo_127_tone_probe import spectrum
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

INTEGER_DIVISORS = (1, 3)
FRACTIONAL_DIVISORS = (2, 4)
TARGETS = ((48, 1800), (56, 2100))


def run(out=HERE/'results/photo-127-fast-step-candidates.json'):
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    rom = ROM.read_bytes()
    cases = []
    for divisor in INTEGER_DIVISORS:
        visits_per_sample = 375//divisor
        for target_step, target_hz in TARGETS:
            baseline = projected_b5(rom, target_step, range(1, SAMPLES+1))
            for direction, effective_step in (('forward', target_step),
                                              ('reverse', -target_step)):
                choices = [value for value in range(1, 256)
                           if ((value*visits_per_sample) & 255) ==
                           (effective_step & 255)]
                if len(choices) != 1:
                    raise ValueError('integer-ratio modular solution changed')
                increment = choices[0]
                _, execution, trace = run_case(mapping, base, increment, 256)
                reads = [row for row in trace if row['pc'] == 0x129]
                if not execution['clean'] or len(reads) != 740:
                    raise ValueError(f'D127={increment:02X} execution changed')
                for n, row in enumerate(reads, 1):
                    phase = (3+n*increment) & 255
                    if (not row['external_read']['selected_by_alu'] or
                            row['external_read']['address'] != 256+phase or
                            row['external_read']['value'] != rom[256+phase] or
                            row['alu']['y'] != ((phase-rom[256+phase]) & 255)):
                        raise ValueError(f'D127={increment:02X} recurrence changed at {n}')
                period = 256//math.gcd(increment, 256)
                shapes = []
                exact_baseline = True
                for offset in range(period):
                    visits = [offset+sample*visits_per_sample
                              for sample in range(1, SAMPLES+1)]
                    b5 = projected_b5(rom, increment, visits)
                    shapes.append(spectrum(b5, target_hz))
                    if offset == 0 and direction == 'forward':
                        exact_baseline = b5 == baseline
                if (any(shape['peak_hz'] != target_hz for shape in shapes) or
                        (direction == 'forward' and not exact_baseline)):
                    raise ValueError(f'D127={increment:02X} target profile changed')
                region_hits = [f'{address:02X}' for address in range(0x30, 0x80)
                               if rom[address] == increment]
                cases.append(dict(microinstruction_divisor=divisor,
                                  pc129_visits_per_sample=visits_per_sample,
                                  target_step=target_step,
                                  target_hz=target_hz,
                                  direction=direction,
                                  candidate_d127=f'{increment:02X}',
                                  effective_step=(increment*visits_per_sample)&255,
                                  executed_pc129_visits=len(reads),
                                  execution_trace_digest=execution['trace_digest'],
                                  projected_start_phase_alignments=period,
                                  all_alignments_peak_at_target=True,
                                  target_r2_range=[min(shape['sinusoid_r2'] for shape in shapes),
                                                   max(shape['sinusoid_r2'] for shape in shapes)],
                                  offset_zero_matches_direct_profile=(exact_baseline
                                                                      if direction == 'forward'
                                                                      else None),
                                  rom_30_7f_value_offsets=region_hits))

    fractional = []
    for divisor in FRACTIONAL_DIVISORS:
        intervals = sorted({((sample+1)*375)//divisor-(sample*375)//divisor
                            for sample in range(1, 100)})
        if len(intervals) != 2 or intervals[1]-intervals[0] != 1 or any(
                (value*intervals[0]) % 256 == (value*intervals[1]) % 256
                for value in range(1, 256)):
            raise ValueError('fractional gate interval argument changed')
        fractional.append(dict(microinstruction_divisor=divisor,
                               pc129_visit_intervals=intervals,
                               nonzero_byte_with_uniform_phase_advance=False))

    expected = {(1, 48, 'forward'): '50', (1, 48, 'reverse'): 'B0',
                (1, 56, 'forward'): '88', (1, 56, 'reverse'): '78',
                (3, 48, 'forward'): 'F0', (3, 48, 'reverse'): '10',
                (3, 56, 'forward'): '98', (3, 56, 'reverse'): '68'}
    if (len(cases) != 8 or any(case['candidate_d127'] != expected[
            (case['microinstruction_divisor'], case['target_step'], case['direction'])]
            for case in cases)):
        raise ValueError('fast-step candidate table changed')

    paths = [Path(__file__), ROM, HERE/'photo_127_clock_alias.py',
             HERE/'photo_127_liveness.py', HERE/'photo_127_tone_probe.py',
             HERE/'photo_controller_path.py', HERE/'photo_mapping_q_sweep.py',
             HERE/'photo_mapping_stream_screen.py',
             HERE.parent/'assumed/execute.py', MAPPINGS['q3']]
    report = dict(status='executed alternate D127 steps and projected fast-gate tones',
                  fixture=dict(mapping='q3 photo-swapped', initial_q=0,
                               pc129_rom_bank=256,
                               assumed_b5_route='Y7→LS273 D4→Q4→DAC08 B5',
                               target_sample_rate_hz=SAMPLE_HZ,
                               integer_microinstruction_divisors=list(INTEGER_DIVISORS),
                               fractional_microinstruction_divisors=list(FRACTIONAL_DIVISORS),
                               projected_samples=SAMPLES),
                  integer_ratio_candidates=cases,
                  fractional_ratio_constraint=fractional,
                  limitations=[
                      'The eight candidate steps execute for 740 PC129 visits each; longer sampled streams project the checked phase/ROM/Y recurrence.',
                      'ROM region 30–7F value matches are co-occurrences, not a traced D127 source or command mapping.',
                      'The oscillator-to-microinstruction divisor, PC129 gate, DAC bit route, held-I0 and bank select remain hypotheses.',
                      'For fractional divisors, uniform phase advance is impossible with a fixed nonzero byte, but phase-jittered spectra and other clock circuits are not excluded.',
                      'No full DAC sample, controller tone command or physical line output is demonstrated.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    for row in report['integer_ratio_candidates']:
        print(row['microinstruction_divisor'], row['target_hz'],
              row['direction'], row['candidate_d127'])
