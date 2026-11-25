"""Replay a main-frame CD4094 D0/D4 swap as an 1800 Hz carrier candidate."""

import hashlib
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]
from common import save
from photo_12c_prom_edge_latch import run_trace
from photo_127_liveness import ROM
from photo_cd4094_order import frames_from_reports, shift_four_bytes
from photo_controller_path import fixture
from photo_dac08_bus_order_screen import q_to_dac, swap_bits
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

SAMPLES = 640
SAMPLE_HZ = 9600
TARGET_HZ = 1800
MAIN_STATES = ('main_00', 'main_20', 'main_40', 'main_60')
TARGET_STEPS = {0x50, 0xB0, 0xF0, 0x10}


def spectrum(values):
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
        raise ValueError('target frequency is not an exact DFT bin')
    peak = max(powers, key=powers.get)
    return dict(peak_hz=peak * SAMPLE_HZ / count,
                target_r2=round(2 * powers[target_bin] / (count * variance), 6),
                distinct_codes=len(set(values)))


def projected(rom, bank, step, divisor, offset):
    if 375 % divisor:
        raise ValueError('noninteger PC129 visits per sample')
    interval = 375 // divisor
    phase = []
    rom_byte = []
    y129 = []
    y12a = []
    for sample in range(SAMPLES):
        visit = 1 + offset + sample * interval
        index = (3 + visit * step) & 255
        value = rom[bank + index]
        phase.append(index)
        rom_byte.append(value)
        y129.append((index - value) & 255)
        y12a.append((index + 1 + int(index >= value)) & 255)
    return dict(phase=tuple(phase), rom_byte=tuple(rom_byte),
                y129=tuple(y129), y12a=tuple(y12a))


def run(out=HERE / 'results/photo-main-frame-carrier-swap.json'):
    frames = frames_from_reports()
    swaps = []
    for low in range(8):
        for high in range(low + 1, 8):
            value = swap_bits(0xA1, low, high)
            if value in TARGET_STEPS:
                swaps.append(dict(bits=[low, high], output=f'{value:02X}'))
    if swaps != [dict(bits=[0, 4], output='B0')]:
        raise ValueError('single-swap carrier candidate changed')
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    rom = ROM.read_bytes()
    cases = []
    for name in MAIN_STATES:
        frame = frames[name]
        chips = shift_four_bytes(frame)
        raw = chips[1]['q8_to_d0']
        step = swap_bits(raw, 0, 4)
        other = chips[0]['q8_to_d0']
        if raw != 0xA1 or step != 0xB0 or other not in (0x22, 0xBA):
            raise ValueError('real controller frame candidate changed')
        result, trace = run_trace(mapping, base, step, other)
        reads = [row for row in trace if row['pc'] == 0x129]
        if (not result['clean'] or len(reads) != 740 or
                any(row['pc'] == 0x12E for row in trace)):
            raise ValueError('carrier-loop execution changed')
        for n, row in enumerate(reads, 1):
            phase = (3 + n * step) & 255
            value = rom[256 + phase]
            if (row['external_read']['address'] != 256 + phase or
                    row['external_read']['value'] != value or
                    row['alu']['y'] != (phase - value) & 255):
                raise ValueError(f'carrier ROM/Y recurrence changed at read {n}')
        cases.append(dict(controller_class=name, frame=frame.hex(' ').upper(),
                          logical_chip1=f'{raw:02X}', crossed_d127=f'{step:02X}',
                          logical_chip0=f'{other:02X}',
                          executed_pc129_reads=len(reads),
                          executed_pc12e_reads=0,
                          candidate_output_visits=sum(row['pc'] in (0x392, 0x39E)
                                                      for row in trace),
                          trace_digest=result['trace_digest']))
    if len({row['trace_digest'] for row in cases}) != 1:
        raise ValueError('same D127 input changed execution by controller class')

    tone = []
    period = 256 // math.gcd(0xB0, 256)
    for bank in (0, 256):
        for divisor in (1, 3):
            samples = projected(rom, bank, 0xB0, divisor, 0)
            for source in samples:
                baseline = samples[source]
                rotations = {baseline[i:] + baseline[:i] for i in range(period)}
                if any(projected(rom, bank, 0xB0, divisor, offset)[source]
                       not in rotations for offset in range(period)):
                    raise ValueError('carrier spectrum depends on gate alignment')
            dac = tuple(q_to_dac(value, 'swap_q4_q5')
                        for value in samples['y129'])
            b5 = tuple((value >> 3) & 1 for value in dac)
            tone.append(dict(rom_bank=bank, microinstruction_divisor=divisor,
                             sample_hz=SAMPLE_HZ, alignments_checked=period,
                             phase=spectrum(samples['phase']),
                             selected_rom=spectrum(samples['rom_byte']),
                             y129=spectrum(samples['y129']),
                             y12a=spectrum(samples['y12a']),
                             photo_compatible_minimal_bus_dac=spectrum(dac),
                             photo_candidate_b5=spectrum(b5),
                             first_16_dac_codes=[f'{value:02X}' for value in dac[:16]]))
    main = next(row for row in tone if
                (row['rom_bank'], row['microinstruction_divisor']) == (256, 1))
    if (main['y129']['peak_hz'] != TARGET_HZ or
            main['photo_compatible_minimal_bus_dac']['peak_hz'] != TARGET_HZ or
            main['photo_compatible_minimal_bus_dac']['target_r2'] < 0.6):
        raise ValueError('candidate carrier projection changed')
    paths = [Path(__file__), ROM,
             HERE / 'results/main-loop-serial.json',
             HERE / 'results/controller-frames.json',
             HERE / 'photo_cd4094_order.py',
             HERE / 'photo_12c_prom_edge_latch.py',
             HERE / 'photo_dac08_bus_order_screen.py',
             HERE / 'photo_controller_path.py',
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3']]
    report = dict(status='main-controller-frame to 1800 Hz carrier-rate candidate',
                  fixture=dict(mapping='q3 photo-swapped',
                               controller='four real 8031 main-loop USART-01 stream classes',
                               cd4094='logical chip 1 Q8→D0 then D0/D4 crossed before D127',
                               d12c='held logical chip 0, unselected in this loop',
                               rom_bank_candidates=[0, 256],
                               sample_hz=SAMPLE_HZ, samples=SAMPLES,
                               output_candidate='ALU Y129→LS273 ordered; Q4/Q5 swapped to DAC08 B pins'),
                  single_bit_swap_tone_matches=swaps,
                  cases=cases, tone=tone,
                  limitations=[
                      'The D0/D4 crossing, chip route, q3 mapping, held-I0 level, DAC bus, clock and ROM A8 are hypotheses.',
                      'The four controller frames come from ROM-executed main-loop classes, but their USART-01 bits are not yet coupled to this carrier loop.',
                      'Only 740 PC129 reads are executed per class; 640 divided samples project the checked recurrence.',
                      'A 1800 Hz peak and 0.604 target-bin variance fraction do not prove a low-distortion analog line carrier.',
                      'No dibit phase reversals, 2100 Hz state, receive decision or echo cancellation are shown by this fixture.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    print('frames', len(report['cases']), 'swap', report['single_bit_swap_tone_matches'])
    for row in report['tone']:
        print(row['rom_bank'], row['microinstruction_divisor'],
              row['y129']['peak_hz'],
              row['photo_compatible_minimal_bus_dac']['peak_hz'],
              row['photo_compatible_minimal_bus_dac']['target_r2'])
