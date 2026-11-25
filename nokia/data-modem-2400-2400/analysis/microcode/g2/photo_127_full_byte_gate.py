"""Screen full selected-ROM bytes at a hypothetical 9,600 Hz DAC gate."""

import math
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]
from common import save
from lower_i_dac_sample_clock_screen import capture
from photo_127_liveness import ROM, run_case
from photo_127_tone_probe import spectrum
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

SAMPLES = 64
CASES = ((1, 0x50, 1800), (1, 0x88, 2100),
         (3, 0xF0, 1800), (3, 0x98, 2100))
SOURCES = ('rom_raw', 'rom_xor80', 'alu_y', 'phase_ramp')


def project(rom, increment, visits, source):
    phases = [(3 + visit * increment) & 255 for visit in visits]
    if source == 'phase_ramp':
        return phases
    if source == 'rom_raw':
        return [rom[256 + phase] for phase in phases]
    if source == 'rom_xor80':
        return [rom[256 + phase] ^ 0x80 for phase in phases]
    if source == 'alu_y':
        return [(phase - rom[256 + phase]) & 255 for phase in phases]
    raise ValueError(source)


def run(out=HERE / 'results/photo-127-full-byte-gate.json'):
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    rom = ROM.read_bytes()
    cases = []
    for divisor, increment, target in CASES:
        _, result, trace = run_case(mapping, base, increment, 256)
        reads = [row for row in trace if row['pc'] == 0x129]
        if not result['clean'] or len(reads) != 740:
            raise ValueError('PC129 loop execution changed')
        for visit, row in enumerate(reads, 1):
            phase = (3 + visit * increment) & 255
            if (not row['external_read']['selected_by_alu'] or
                    row['external_read']['address'] != 256 + phase or
                    row['external_read']['value'] != rom[256 + phase] or
                    row['alu']['y'] != (phase - rom[256 + phase]) & 255):
                raise ValueError(f'PC129 recurrence failed at visit {visit}')
        visits_per_sample = 375 // divisor
        step = (increment * visits_per_sample) & 255
        alignments = 256 // math.gcd(step, 256)
        sources = {}
        for source in SOURCES:
            shapes = []
            for offset in range(alignments):
                visits = [offset + (sample + 1) * visits_per_sample
                          for sample in range(SAMPLES)]
                codes = capture(project(rom, increment, visits, source))
                shape = spectrum(codes, target)
                shapes.append(shape)
            sources[source] = dict(
                peak_hz_counts=dict(Counter(str(s['peak_hz']) for s in shapes)),
                target_r2_min=min(s['sinusoid_r2'] for s in shapes),
                target_r2_max=max(s['sinusoid_r2'] for s in shapes),
                phase_zero_first_16=capture(project(
                    rom, increment,
                    [(sample + 1) * visits_per_sample for sample in range(16)],
                    source)))
        cases.append(dict(divisor=divisor, d127=f'{increment:02X}',
                          target_hz=target, visits_per_sample=visits_per_sample,
                          effective_phase_step=step, alignments=alignments,
                          executed_rom_visits=len(reads),
                          trace_digest=result['trace_digest'], sources=sources))
    report = dict(fixture=dict(mapping='q3 photo-swapped', initial_q=0,
                               rom_bank='upper', assumed_sample_rate_hz=9600,
                               projected_samples=SAMPLES,
                               selected_rom_byte_to_ls273='untraced candidate',
                               xor80='untraced high-bit inversion candidate'),
                  cases=cases,
                  limitations=[
                      'Each candidate executes 740 PC129 ROM visits; longer 64-sample spectra project the checked recurrence.',
                      'D127 bytes, 14.4 MHz divisor, 9,600 Hz gate, ROM-to-74LS273 route and DAC byte order are untraced.',
                      'A target-bin peak alone does not establish a sine carrier; the ROM upper bank is not a full 256-byte sine cycle.',
                      'No controller command, dibit phase step, physical line output or receiver is established.'])
    save(out, report)
    return report


if __name__ == '__main__':
    print([(row['d127'], row['target_hz']) for row in run()['cases']])
