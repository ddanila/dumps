"""Replay one candidate CD4094 D0/D3 bus swap through the real PROMs."""

import hashlib
import json
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
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from photo_output_clock_bit_screen import CHIPS, edges

SAMPLES = 640
CONTROLLER = HERE / 'results/controller-state-pin-channels.json'


def swap_d0_d3(value):
    return (value & ~0x09) | ((value & 1) << 3) | ((value & 8) >> 3)


def single_bit_swaps_matching_a1_tone():
    required = {0x88, 0x78, 0x98, 0x68}
    matches = []
    for low in range(8):
        for high in range(low + 1, 8):
            def swapped(value):
                mask = (1 << low) | (1 << high)
                return ((value & ~mask) | ((value >> low & 1) << high) |
                        ((value >> high & 1) << low))
            a1 = swapped(0x81)
            if a1 in required:
                matches.append(dict(swapped_bits=[low, high],
                                    a0_d127=f'{swapped(0x88):02X}',
                                    a1_d127=f'{a1:02X}'))
    return matches


def first_loop_samples(rom, step, divisor, offset):
    if 375 % divisor:
        raise ValueError('this projection requires integer visit spacing')
    interval = 375 // divisor
    y = []
    for sample in range(SAMPLES):
        visit = 1 + offset + sample * interval
        index = (3 + visit * step) & 255
        y.append((index - rom[256 + index]) & 255)
    return tuple(y)


def run(out=HERE / 'results/photo-cd4094-bit-swap-tone.json'):
    controller = json.loads(CONTROLLER.read_text())
    state_rows = {row['state']: row for row in controller['rows']}
    frames = frames_from_reports()
    bit_swap_screen = single_bit_swaps_matching_a1_tone()
    if bit_swap_screen != [dict(swapped_bits=[0, 3], a0_d127='81',
                                a1_d127='88')]:
        raise ValueError('single-bit-swap tone screen changed')
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    rom = ROM.read_bytes()
    cases = []
    traces = {}
    for state in ('A0', 'A1', 'A2'):
        frame = frames[f'state_{state}']
        chips = shift_four_bytes(frame)
        raw = chips[1]['q8_to_d0']
        control = swap_d0_d3(raw)
        step = chips[0]['q8_to_d0']
        row = state_rows[state]
        if (row['frame'] != frame.hex(' ').upper() or
                int(row['cd4094_q8_chip1'], 16) != raw or
                (state, raw, control, step) not in (
                    ('A0', 0x88, 0x81, 0x7A),
                    ('A1', 0x81, 0x88, 0x7A),
                    ('A2', 0x88, 0x81, 0x7A))):
            raise ValueError('controller/frame/bit-swap witness changed')
        result, trace = run_trace(mapping, base, control, step)
        traces[state] = trace
        first = [item for item in trace if item['pc'] == 0x129]
        second = [item for item in trace if item['pc'] == 0x12E]
        if ((state == 'A1' and (len(first), len(second)) != (740, 0)) or
                (state != 'A1' and (len(first), len(second)) != (125, 613))):
            raise ValueError('swapped state/loop split changed')
        for n, item in enumerate(first, 1):
            phase = (3 + n * control) & 255
            if (item['external_read']['address'] != 256 + phase or
                    item['external_read']['value'] != rom[256 + phase] or
                    item['alu']['y'] != (phase - rom[256 + phase]) & 255):
                raise ValueError('first-loop ROM/Y recurrence changed')
        for n, item in enumerate(second, 1):
            phase = (1 + n * step) & 255
            if (item['external_read']['address'] != 256 + phase or
                    item['external_read']['value'] != rom[256 + phase]):
                raise ValueError('second-loop ROM recurrence changed')
        cases.append(dict(state=state, frame=row['frame'], p1_5=row['p1_5'],
                          raw_chip1=f'{raw:02X}', swapped_d127=f'{control:02X}',
                          chip0_d12c=f'{step:02X}', first_loop_reads=len(first),
                          second_loop_reads=len(second),
                          candidate_output_visits=sum(item['pc'] in (0x392, 0x39E)
                                                      for item in trace),
                          trace_digest=result['trace_digest']))

    a1, a0 = traces['A1'], traces['A0']
    target = {i for i, row in enumerate(a1) if row['pc'] == 0x129}
    other_loop = {i for i, row in enumerate(a0) if row['pc'] == 0x12E}
    raw_edge_candidates = []
    for lane, chip in enumerate(CHIPS):
        for bit in range(8):
            for rising in (0, 1):
                one = set(edges(a1, lane, bit, rising))
                if target <= one:
                    zero = set(edges(a0, lane, bit, rising))
                    raw_edge_candidates.append(dict(
                        chip=chip, bit=bit,
                        edge='rising' if rising else 'falling',
                        a1_target=len(target), a1_extra=len(one - target),
                        a0_second_loop=len(zero & other_loop)))
    if (len(raw_edge_candidates) != 11 or
            any(item['a0_second_loop'] != 613 for item in raw_edge_candidates)):
        raise ValueError('raw PROM clock screen changed')

    tone = {}
    step = 0x88
    period = 256 // math.gcd(step, 256)
    for divisor in (1, 3):
        y = first_loop_samples(rom, step, divisor, 0)
        rotations = {y[index:] + y[:index] for index in range(period)}
        if any(first_loop_samples(rom, step, divisor, offset) not in rotations
               for offset in range(period)):
            raise ValueError('start phase changed the projected spectrum')
        full = profile(y)
        b5 = profile([value >> 7 for value in y])
        tone[str(divisor)] = dict(full_y=full, photo_b5_y7=b5,
                                 alignments_checked=period,
                                 first_16_y=[f'{value:02X}' for value in y[:16]])
    if (tone['1']['full_y']['peak_hz'] != 2100 or
            tone['1']['photo_b5_y7']['peak_hz'] != 2100 or
            tone['3']['photo_b5_y7']['peak_hz'] == 2100):
        raise ValueError('bit-swap tone projection changed')

    paths = [Path(__file__), CONTROLLER, ROM,
             HERE / 'photo_12c_divided_state_latch.py',
             HERE / 'photo_12c_prom_edge_latch.py',
             HERE / 'photo_cd4094_order.py',
             HERE / 'photo_output_clock_bit_screen.py',
             HERE / 'photo_controller_path.py',
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3']]
    report = dict(status='candidate CD4094 bus-bit permutation and tone projection',
                  fixture=dict(mapping='q3 photo-swapped', q=0,
                               controller='executed A0/A1/A2 8031 frames and P1.5',
                               d127='logical CD4094 chip 1 Q8→D0, then D0/D3 swap',
                               d12c='held logical chip 0 Q8→D0',
                               rom_bank='upper at 129 and 12E',
                               sample_hz=9600, samples=SAMPLES,
                               photo_b5_candidate='Y7→LS273 D4→Q4→DAC08 B5'),
                  cases=cases, single_bit_swap_tone_matches=bit_swap_screen,
                  a1_first_loop_tone=tone,
                  raw_prom_edge_candidates=raw_edge_candidates,
                  limitations=[
                      'The D0/D3 crossing is a simple wiring hypothesis, not a photographed connection.',
                      'The q3 mapping, held-I0 levels, controller-to-DSP routes, sample clock and full DAC data bus remain untraced.',
                      'Only 740 first-loop reads are executed; 640 divided captures project the checked ROM/Y recurrence.',
                      'Every raw PROM bit edge at all A1 129 visits also occurs at all A0 12E visits; no mode-isolated direct PROM clock was found.',
                      'A 2100 Hz spectral peak in Y/B5 does not prove a sinusoidal DAC waveform, phase reversals, receiver behavior or modem line output.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    for case in report['cases']:
        print(case['state'], case['swapped_d127'], case['first_loop_reads'],
              case['second_loop_reads'])
    print('A1 k=1 peaks', report['a1_first_loop_tone']['1']['full_y']['peak_hz'],
          report['a1_first_loop_tone']['1']['photo_b5_y7']['peak_hz'])
