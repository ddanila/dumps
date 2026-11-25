"""Project A1 frame bytes through a divided second-loop PROM strobe."""

import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]
from common import save
from photo_12c_latch_tone import sample_values
from photo_12c_prom_edge_latch import run_trace
from photo_127_liveness import ROM
from photo_cd4094_order import frames_from_reports, shift_four_bytes
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from photo_output_clock_bit_screen import CHIPS, edges

SAMPLES = 640
SAMPLE_HZ = 9600
TARGET_HZ = 2100
DIVISORS = (1, 3)
STROBE_REPORT = HERE / 'results/photo-12c-prom-edge-latch.json'


def profile(values):
    count = len(values)
    mean = sum(values) / count
    centered = [value - mean for value in values]
    variance = sum(value * value for value in centered)
    if not variance:
        return dict(peak_hz=None, target_r2=0, distinct_codes=1)
    powers = {}
    for bin_index in range(1, count // 2 + 1):
        angle = 2 * math.pi * bin_index / count
        real = sum(value * math.cos(angle * index)
                   for index, value in enumerate(centered))
        imag = sum(value * math.sin(angle * index)
                   for index, value in enumerate(centered))
        powers[bin_index] = real * real + imag * imag
    target_bin = TARGET_HZ * count // SAMPLE_HZ
    if target_bin * SAMPLE_HZ != TARGET_HZ * count:
        raise ValueError('target frequency is not a DFT bin')
    peak = max(powers, key=powers.get)
    factor = 1 if target_bin == count // 2 else 2
    return dict(peak_hz=peak * SAMPLE_HZ / count,
                target_r2=round(factor * powers[target_bin] /
                                (count * variance), 6),
                distinct_codes=len(set(values)))


def rotations_cover_offsets(rom, step, interval, site, period):
    def values(offset):
        visits = [1 + offset + sample * interval for sample in range(SAMPLES)]
        _, _, e, f = sample_values(rom, step, visits)
        return tuple(e if site == '12E' else f)
    baseline = values(0)
    if SAMPLES % period:
        raise ValueError('projection window does not contain whole periods')
    rotations = {baseline[index:] + baseline[:index]
                 for index in range(period)}
    if any(values(offset) not in rotations for offset in range(period)):
        raise ValueError('divider phase changes the sample spectrum')
    return baseline


def run(out=HERE / 'results/photo-12c-divided-state-latch.json'):
    prior = json.loads(STROBE_REPORT.read_text())
    prior_by_chip = {row['step_chip']: row for row in prior['cases']}
    chips = shift_four_bytes(frames_from_reports()['state_A1'])
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    rom = ROM.read_bytes()
    cases = []
    for chip in (0, 2, 3):
        step = chips[chip]['q8_to_d0']
        result, trace = run_trace(mapping, base, 0x81, step)
        if (result['trace_digest'] != prior_by_chip[chip]['trace_digests']['A1'] or
                step != int(prior_by_chip[chip]['d12c'], 16)):
            raise ValueError('A1 strobe witness changed')
        reads = [row for row in trace if row['pc'] == 0x12E]
        strobe = edges(trace, CHIPS.index('18'), 1, 1)
        if (len(reads) != 613 or
                sum(trace[index]['pc'] == 0x12E for index in strobe) != 613):
            raise ValueError('A1 ROM/strobe recurrence changed')
        phases, selected, executed_e, executed_f = sample_values(
            rom, step, range(1, 614))
        if (phases != [row['external_read']['address'] & 255 for row in reads] or
                selected != [row['external_read']['value'] for row in reads] or
                executed_e != [row['alu']['y'] for row in reads] or
                executed_f != [row['alu']['y'] for row in trace
                              if row['pc'] == 0x12F]):
            raise ValueError('projected sample recurrence differs from execution')
        period = 256 // math.gcd(step, 256)
        for divisor in DIVISORS:
            interval = 375 // divisor
            if 375 % divisor:
                raise ValueError('noninteger strobe/sample ratio')
            by_site = {}
            for site in ('12E', '12F'):
                y = rotations_cover_offsets(rom, step, interval, site, period)
                b5 = tuple((value >> 7) & 1 for value in y)
                by_site[site] = dict(full_y=profile(y),
                                     photo_b5_y7=profile(b5),
                                     first_16_y=[f'{value:02X}' for value in y[:16]])
            expected_step = (step * interval) & 255
            if any(row['full_y']['peak_hz'] == TARGET_HZ or
                   row['photo_b5_y7']['peak_hz'] == TARGET_HZ
                   for row in by_site.values()):
                raise ValueError('A1 held-byte tone result changed')
            cases.append(dict(step_chip=chip, held_d12c=f'{step:02X}',
                              microinstruction_divisor=divisor,
                              strobes_per_sample=interval,
                              effective_phase_step=expected_step,
                              phase_alignments_checked=period,
                              alignment_invariant_spectrum=True,
                              sites=by_site,
                              executed_pc12e_reads=len(reads),
                              execution_trace_digest=result['trace_digest']))
    paths = [Path(__file__), STROBE_REPORT, ROM,
             HERE / 'photo_12c_latch_tone.py',
             HERE / 'photo_12c_prom_edge_latch.py',
             HERE / 'photo_cd4094_order.py',
             HERE / 'photo_output_clock_bit_screen.py',
             HERE / 'photo_controller_path.py',
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3']]
    report = dict(status='A1 frame held-byte divided-strobe tone test',
                  fixture=dict(mapping='q3 photo-swapped', state='A1',
                               d127='81 from logical CD4094 chip 1 Q8→D0',
                               d12c='one held alternate CD4094 chip byte',
                               clock='U18 D1 rising at PC12E, then hypothetical divider',
                               candidate_latch_data='Y at 12E or delayed Y at 12F',
                               photo_b5_candidate='Y7→74LS273 D4→Q4→DAC08 B5',
                               sample_hz=SAMPLE_HZ, samples=SAMPLES,
                               target_hz=TARGET_HZ,
                               microinstruction_divisors=list(DIVISORS)),
                  cases=cases,
                  limitations=[
                      'The first 613 PC12E/12F visits per byte are executed; 640 gated samples project their checked phase/ROM/Y recurrence.',
                      'The CD4094, D-input, U18-clock and DAC byte connections, clock divider and sample rate are untraced hypotheses.',
                      'A1 is a candidate 2100 Hz handshake state, not an identified tone command.',
                      'The tested direct held-byte route failing a tone does not exclude decoded steps, another clock, or another output path.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    for case in run()['cases']:
        print(case['held_d12c'], case['microinstruction_divisor'],
              case['sites']['12E']['full_y']['peak_hz'],
              case['sites']['12E']['photo_b5_y7']['peak_hz'])
