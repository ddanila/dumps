"""Screen A1 bit-swap phase-loop bytes as possible DAC latch sources."""

import hashlib
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]
from common import save
from photo_12c_divided_state_latch import profile
from photo_127_liveness import ROM, check_loop, run_case
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

STEP = 0x88
SAMPLES = 640
TARGET_HZ = 2100
SOURCES = ('phase_r1', 'rom_byte', 'y129', 'y12a', 'carry129')


def sources_at_visit(rom, bank, visit):
    phase = (3 + visit * STEP) & 255
    value = rom[bank + phase]
    carry = int(phase >= value)
    return dict(phase_r1=phase, rom_byte=value,
                y129=(phase - value) & 255,
                y12a=(phase + 1 + carry) & 255, carry129=carry)


def samples(rom, bank, divisor, offset):
    if 375 % divisor:
        raise ValueError('integer-spaced source screen only')
    interval = 375 // divisor
    values = {source: [] for source in SOURCES}
    for sample in range(SAMPLES):
        visit = 1 + offset + sample * interval
        item = sources_at_visit(rom, bank, visit)
        for source in SOURCES:
            values[source].append(item[source])
    return {source: tuple(values[source]) for source in SOURCES}


def run(out=HERE / 'results/photo-cd4094-bit-swap-data-sites.json'):
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    rom = ROM.read_bytes()
    cases = []
    period = 256 // math.gcd(STEP, 256)
    for bank in (0, 256):
        _, execution, trace = run_case(mapping, base, STEP, bank)
        reads, _ = check_loop(trace, rom, STEP, bank)
        if not execution['clean'] or len(reads) != 740:
            raise ValueError('bit-swap first-loop execution changed')
        for n, index in enumerate(reads, 1):
            expected = sources_at_visit(rom, bank, n)
            before, row, after = trace[index - 2], trace[index], trace[index + 1]
            if (before['registers'].get('1') != expected['phase_r1'] or
                    row['external_read']['value'] != expected['rom_byte'] or
                    row['alu']['y'] != expected['y129'] or
                    row['alu']['carry'] != expected['carry129'] or
                    after['alu']['y'] != expected['y12a']):
                raise ValueError(f'projected source differs from execution at {n}')
        for divisor in (1, 3):
            baseline = samples(rom, bank, divisor, 0)
            for source in SOURCES:
                rotations = {baseline[source][i:] + baseline[source][:i]
                             for i in range(period)}
                if any(samples(rom, bank, divisor, offset)[source] not in rotations
                       for offset in range(period)):
                    raise ValueError('source spectrum depends on divider alignment')
            spectra = {}
            for source in SOURCES:
                values = baseline[source]
                spectra[source] = dict(full_byte=profile(values),
                                       photo_b5_y7=profile([value >> 7
                                                           for value in values]))
            cases.append(dict(rom_bank=bank, microinstruction_divisor=divisor,
                              phase_alignments_checked=period,
                              executed_pc129_reads=len(reads),
                              spectra=spectra,
                              execution_trace_digest=execution['trace_digest']))
    upper_one = next(case for case in cases
                     if case['rom_bank'] == 256 and
                     case['microinstruction_divisor'] == 1)
    if (upper_one['spectra']['y129']['full_byte']['peak_hz'] != TARGET_HZ or
            upper_one['spectra']['rom_byte']['full_byte']['peak_hz'] == TARGET_HZ or
            upper_one['spectra']['y12a']['full_byte']['target_r2'] <=
            upper_one['spectra']['y129']['full_byte']['target_r2']):
        raise ValueError('bit-swap source ordering changed')
    paths = [Path(__file__), ROM, HERE / 'photo_cd4094_bit_swap_tone.py',
             HERE / 'photo_12c_divided_state_latch.py',
             HERE / 'photo_127_liveness.py', HERE / 'photo_controller_path.py',
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3']]
    report = dict(status='A1 bit-swap phase-loop candidate DAC-byte source screen',
                  fixture=dict(mapping='q3 photo-swapped', d127='88 from the untraced CD4094 D0/D3 swap',
                               rom_banks=[0, 256], output_sites=list(SOURCES),
                               sample_hz=9600, samples=SAMPLES,
                               oscillator_periods_per_microinstruction=[1, 3],
                               photo_b5_candidate='source bit 7→LS273 D4→Q4→DAC08 B5'),
                  cases=cases,
                  limitations=[
                      'The D0/D3 crossing, ROM A8, LS273 data/clock and full DAC bus are untraced hypotheses.',
                      'Only 740 PC129/PC12A visits are executed per bank; 640 divided samples project their checked recurrence.',
                      'A target-bin spectral peak does not identify a low-distortion analog tone or a physical latch source.',
                      'This is an A1 tone-state candidate, not a controller-driven dibit transmitter or receiver demonstration.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    for case in run()['cases']:
        print(case['rom_bank'], case['microinstruction_divisor'],
              [(source, data['full_byte']['peak_hz'],
                data['full_byte']['target_r2'])
               for source, data in case['spectra'].items()])
