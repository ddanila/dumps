"""Test simple DAC08 byte orders compatible with the photo B5←Q4 segment."""

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


def swap_bits(value, a, b):
    mask = (1 << a) | (1 << b)
    return ((value & ~mask) | ((value >> a & 1) << b) |
            ((value >> b & 1) << a))


def q_to_dac(value, order):
    if order == 'reverse':
        return int(f'{value:08b}'[::-1], 2)
    if order == 'rotate_q_to_next_b':
        return (value >> 1) | ((value & 1) << 7)
    if order == 'swap_q4_q5':
        return swap_bits(value, 4, 3)
    raise ValueError(order)


def raw_source(rom, bank, visit, site):
    phase = (3 + visit * STEP) & 255
    value = rom[bank + phase]
    if site == '129_Y':
        return (phase - value) & 255
    if site == '12A_Y':
        return (phase + 1 + int(phase >= value)) & 255
    raise ValueError(site)


def run(out=HERE / 'results/photo-dac08-bus-order-screen.json'):
    orders = ('reverse', 'rotate_q_to_next_b', 'swap_q4_q5')
    for order in orders:
        if q_to_dac(0x10, order) != 0x08:
            raise ValueError(f'{order} does not map Q4 to DAC B5')
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    rom = ROM.read_bytes()
    cases = []
    period = 256 // math.gcd(STEP, 256)
    for bank in (0, 256):
        _, execution, trace = run_case(mapping, base, STEP, bank)
        reads, _ = check_loop(trace, rom, STEP, bank)
        if not execution['clean'] or len(reads) != 740:
            raise ValueError('A1 phase-loop execution changed')
        for n, index in enumerate(reads, 1):
            if (trace[index]['alu']['y'] != raw_source(rom, bank, n, '129_Y') or
                    trace[index+1]['alu']['y'] != raw_source(rom, bank, n, '12A_Y')):
                raise ValueError('projected byte differs from executed byte')
        for site in ('129_Y', '12A_Y'):
            raw = tuple(raw_source(rom, bank, 1 + sample * 375, site)
                        for sample in range(SAMPLES))
            rotations = {raw[i:] + raw[:i] for i in range(period)}
            if any(tuple(raw_source(rom, bank, 1 + offset + sample * 375, site)
                         for sample in range(SAMPLES)) not in rotations
                   for offset in range(period)):
                raise ValueError('divider start phase changed source spectrum')
            for input_order in ('ordered_y_to_d', 'swap_y7_y4_to_d'):
                q_bytes = (raw if input_order == 'ordered_y_to_d' else
                           tuple(swap_bits(value, 7, 4) for value in raw))
                for output_order in orders:
                    dac = tuple(q_to_dac(value, output_order) for value in q_bytes)
                    b5 = tuple((value >> 3) & 1 for value in dac)
                    expected_b5 = tuple((value >> (4 if input_order ==
                                                     'ordered_y_to_d' else 7)) & 1
                                        for value in raw)
                    if b5 != expected_b5:
                        raise ValueError('photo-candidate B5 mapping changed')
                    cases.append(dict(rom_bank=bank, site=site,
                                      y_to_ls273=input_order,
                                      ls273_q_to_dac=output_order,
                                      full_dac_code=profile(dac),
                                      dac_b5=profile(b5),
                                      phase_alignments_checked=period,
                                      first_16_codes=[f'{value:02X}'
                                                      for value in dac[:16]],
                                      executed_pc129_reads=len(reads),
                                      execution_trace_digest=execution['trace_digest']))
    selected = next(row for row in cases if
                    (row['rom_bank'], row['site'], row['y_to_ls273'],
                     row['ls273_q_to_dac']) ==
                    (256, '129_Y', 'swap_y7_y4_to_d', 'reverse'))
    if (selected['dac_b5']['peak_hz'] != 2100 or
            selected['full_dac_code']['peak_hz'] != 4800):
        raise ValueError('single-bit versus full-byte discriminator changed')
    paths = [Path(__file__), ROM,
             HERE / 'photo_127_liveness.py',
             HERE / 'photo_12c_divided_state_latch.py',
             HERE / 'photo_cd4094_bit_swap_tone.py',
             HERE / 'photo_controller_path.py',
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3'],
             HERE.parents[2] / 'photos/PXL_20261123_114854803.jpg']
    report = dict(status='photo-B5-compatible simple DAC byte bus-order screen',
                  fixture=dict(mapping='q3 photo-swapped', d127='88 from hypothetical CD4094 D0/D3 crossing',
                               rom_banks=[0, 256], sites=['129_Y', '12A_Y'],
                               sample_hz=9600, samples=SAMPLES,
                               oscillator_periods_per_microinstruction=1,
                               photo_segment='74LS273 Q4→DAC08 B5 candidate',
                               assumed_y_to_d=['ordered', 'Y7/Y4 swap'],
                               assumed_q_to_b=list(orders)),
                  cases=cases,
                  limitations=[
                      'Only Q4→DAC08 B5 is photo-suggested; the other seven DAC data wires, LS273 D bus and clock are untraced.',
                      'The three Q/B assignments are simple hypotheses compatible with one visible segment, not an exhaustive wiring search.',
                      'First 740 ROM/ALU visits are executed; 640 divided samples project their checked recurrence.',
                      'The CD4094 D0/D3 crossing, sample rate, microcycle divisor, ROM bank and q3 mapping remain hypotheses.',
                      'A spectral peak in one DAC bit or a candidate full byte is not proof of analog line output or dibit modulation.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    for row in result['cases']:
        if row['rom_bank'] == 256 and row['site'] == '129_Y':
            print(row['y_to_ls273'], row['ls273_q_to_dac'],
                  row['full_dac_code']['peak_hz'], row['dac_b5']['peak_hz'])
