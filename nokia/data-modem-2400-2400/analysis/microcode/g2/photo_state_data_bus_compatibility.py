"""Check whether one fixed chip-1 wiring can explain tone and data steps."""

import hashlib
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]
from common import save
from photo_12c_divided_state_latch import profile
from photo_12c_prom_edge_latch import run_trace
from photo_127_liveness import ROM
from photo_cd4094_order import frames_from_reports, shift_four_bytes
from photo_controller_path import fixture
from photo_dac08_bus_order_screen import q_to_dac, swap_bits
from photo_main_frame_carrier_swap import spectrum
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

OSCILLATOR_HZ = 14_400_000
SAMPLE_HZ = 9600
SAMPLES = 640


def steps(target, divisor):
    interval = OSCILLATOR_HZ // (4 * SAMPLE_HZ * divisor)
    if OSCILLATOR_HZ != interval * 4 * SAMPLE_HZ * divisor:
        raise ValueError('noninteger visit interval')
    phase = round(target * 256 / SAMPLE_HZ)
    if phase * SAMPLE_HZ != target * 256:
        raise ValueError('target is not an exact 256-step phase rate')
    return [value for value in range(256)
            if (value * interval) & 255 in (phase, (-phase) & 255)]


def projected_dac(rom, step, offset=0):
    return [q_to_dac(((phase - rom[256 + phase]) & 255), 'swap_q4_q5')
            for phase in ((3 + (1 + offset + sample * 375) * step) & 255
                          for sample in range(SAMPLES))]


def run(out=HERE / 'results/photo-state-data-bus-compatibility.json'):
    frames = frames_from_reports()
    state_chips = shift_four_bytes(frames['state_A1'])
    data_chips = shift_four_bytes(frames['main_00'])
    state_raw = state_chips[1]['q8_to_d0']
    data_raw = data_chips[1]['q8_to_d0']
    if (state_raw, data_raw) != (0x81, 0xA1):
        raise ValueError('executed controller frame bytes changed')
    source_distance = bin(state_raw ^ data_raw).count('1')
    if source_distance != 1:
        raise ValueError('one-bit controller distinction changed')
    target_pairs = []
    for tone_divisor in (1, 3):
        tone = steps(2100, tone_divisor)
        for data_divisor in (1, 3):
            data = steps(1800, data_divisor)
            distances = [bin(a ^ b).count('1') for a in tone for b in data]
            target_pairs.append(dict(tone_divisor=tone_divisor,
                                     data_divisor=data_divisor,
                                     tone_steps=[f'{value:02X}' for value in tone],
                                     data_steps=[f'{value:02X}' for value in data],
                                     minimum_hamming_distance=min(distances)))
    if any(row['minimum_hamming_distance'] != 2 for row in target_pairs):
        raise ValueError('phase-step distance constraint changed')

    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    rom = ROM.read_bytes()
    cases = []
    for crossing in ((0, 3), (0, 4)):
        for mode, chips in (('A1_tone_state', state_chips),
                            ('main_data_frame', data_chips)):
            raw = chips[1]['q8_to_d0']
            d127 = swap_bits(raw, *crossing)
            d12c = chips[0]['q8_to_d0']
            result, trace = run_trace(mapping, base, d127, d12c)
            reads = [row for row in trace if row['pc'] == 0x129]
            if (not result['clean'] or len(reads) != 740 or
                    any(row['pc'] == 0x12E for row in trace)):
                raise ValueError('crossed candidate left first phase loop')
            for n, row in enumerate(reads, 1):
                phase = (3 + n * d127) & 255
                byte = rom[256 + phase]
                if (row['external_read']['address'] != 256 + phase or
                        row['external_read']['value'] != byte or
                        row['alu']['y'] != (phase - byte) & 255):
                    raise ValueError('crossed ROM/Y recurrence changed')
            codes = projected_dac(rom, d127)
            period = 256 // math.gcd(d127, 256)
            rotations = {tuple(codes[i:] + codes[:i]) for i in range(period)}
            if any(tuple(projected_dac(rom, d127, offset)) not in rotations
                   for offset in range(period)):
                raise ValueError('spectrum start-phase rotation changed')
            target = 2100 if mode == 'A1_tone_state' else 1800
            measured = profile(codes) if target == 2100 else spectrum(codes)
            cases.append(dict(wire_crossing=list(crossing), mode=mode,
                              raw_chip1=f'{raw:02X}', d127=f'{d127:02X}',
                              effective_step=f'{(d127 * 375) & 255:02X}',
                              proposed_target_hz=target,
                              candidate_full_dac_peak_hz=measured['peak_hz'],
                              target_r2=measured['target_r2'],
                              pc129_reads=len(reads), trace_digest=result['trace_digest']))
    expected = {(0, 3, 'A1_tone_state'): 2100,
                (0, 3, 'main_data_frame'): 900,
                (0, 4, 'A1_tone_state'): 600,
                (0, 4, 'main_data_frame'): 1800}
    if any(row['candidate_full_dac_peak_hz'] !=
           expected[(*row['wire_crossing'], row['mode'])] for row in cases):
        raise ValueError('crossed-wire mode frequencies changed')
    paths = [Path(__file__), ROM,
             HERE / 'results/main-loop-serial.json',
             HERE / 'results/controller-frames.json',
             HERE / 'photo_cd4094_order.py',
             HERE / 'photo_12c_prom_edge_latch.py',
             HERE / 'photo_dac08_bus_order_screen.py',
             HERE / 'photo_main_frame_carrier_swap.py',
             HERE / 'photo_controller_path.py',
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3']]
    report = dict(status='one fixed chip-1 bitwise wiring cannot explain both exact tone and carrier steps',
                  fixture=dict(mapping='q3 photo-swapped',
                               controller='ROM-executed A1 state and main_00 data frames',
                               raw_chip1_state=f'{state_raw:02X}',
                               raw_chip1_data=f'{data_raw:02X}',
                               oscillator_hz=OSCILLATOR_HZ,
                               sample_hz=SAMPLE_HZ,
                               tested_divisors=[1, 3],
                               candidate_dac='Y129→LS273 ordered; Q4/Q5 swapped to DAC08'),
                  source_hamming_distance=source_distance,
                  target_step_pairs=target_pairs,
                  crossed_wire_executions=cases,
                  invariant='Any one-to-one bit permutation plus any fixed per-bit inversion preserves pairwise Hamming distance; source distance 1 cannot become target distance >=2.',
                  limitations=[
                      'The A1 state as 2100 Hz tone and main frame as 1800 Hz data mode are protocol hypotheses, not identified physical commands.',
                      'The result excludes only one fixed chip-1 byte route with bit permutation and fixed inversions at the tested integer clock ratios.',
                      'State-dependent decoding, a second frame chip, different clock/sample relation or other output path can escape this constraint.',
                      'The CD4094-to-DSP route, DAC bus/clock and q3 mapping remain untraced.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    print('raw distance', result['source_hamming_distance'])
    for row in result['crossed_wire_executions']:
        print(row['wire_crossing'], row['mode'], row['d127'],
              row['candidate_full_dac_peak_hz'])
