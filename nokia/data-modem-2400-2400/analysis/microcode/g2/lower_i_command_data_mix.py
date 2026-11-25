"""Replay executed 8031 frame/line streams through two candidate D inputs."""

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent/'assumed'), str(HERE)]

from common import save
from controller_bit_dispatch import CONTROLLER_ROM, CONTROLLER_SHA
from lower_i_d3f8_input import run_trace
from lower_i_late_byte_relay import output_quartets, scenario_with_trigger
from lower_i_prom_data_route import mapping_for
from photo_controller_path import fixture

CONTROLLER_REPORT = HERE/'results/main-loop-serial.json'
SELECTORS = ('00', '20', '40', '60')
FRAME_PC = 0x3A4
LINE_PC = 0x3A6


def quartet(frame_byte, line_byte):
    m = frame_byte & 15
    n = line_byte & 15
    return (0xF0 | n, 0xF0 | ((m+n) & 15), n, 15-n)


def bits_from_bytes(values):
    return [(value >> bit) & 1 for value in values for bit in range(8)]


def execute_pair(mapping, base, frame_values, line_values, cycles):
    scenario = scenario_with_trigger(base)
    scenario['io']['read']['pc_sequences'][str(LINE_PC)] = line_values
    result = run_trace(mapping, scenario, FRAME_PC, frame_values, cycles=cycles)
    return result, output_quartets(result['trace'])


def run(out=HERE/'results/lower-i-command-data-mix.json'):
    controller = json.loads(CONTROLLER_REPORT.read_text())
    if (controller['controller_rom_sha256'] != CONTROLLER_SHA or
            hashlib.sha256(CONTROLLER_ROM.read_bytes()).hexdigest() != CONTROLLER_SHA):
        raise ValueError('saved main-loop streams do not match the controller ROM')
    rows = {row['selector']: row for row in controller['rows']
            if row['selector'] in SELECTORS}
    if set(rows) != set(SELECTORS):
        raise ValueError('missing executed main-loop class')
    _, base = fixture()
    mapping = mapping_for('!10.6', '11.2')

    # Verify the two-input rule over every low-nibble pair, then all high-byte
    # choices of the held input with the line input fixed at one.
    checks = 0
    for n in range(16):
        for m in range(16):
            result, values = execute_pair(mapping, base, [m]*32, [n]*32, 512)
            if (result['site_visits'] != 14 or len(values) != 14 or
                    set(values) != {quartet(m, n)}):
                raise ValueError(f'low-nibble pair fails: {m:01X}, {n:01X}')
            checks += 1
    for m in range(256):
        result, values = execute_pair(mapping, base, [m]*32, [1]*32, 512)
        if (result['site_visits'] != 14 or len(values) != 14 or
                set(values) != {quartet(m, 1)}):
            raise ValueError(f'held-byte high-nibble check fails: {m:02X}')
        checks += 1

    classes = []
    combined_line = []
    combined_frame = []
    for selector in SELECTORS:
        row = rows[selector]
        frames = [bytes.fromhex(value.replace(' ', '')) for value in row['frames']]
        first_line = row['first_line_iteration']-1
        frame_lane = frames[first_line][1]
        if (len(frames) != 12 or first_line not in (4, 6) or
                any(frame[1] != frame_lane for frame in frames[first_line:])):
            raise ValueError(f'frame lane 1 changes during line stream {selector}')
        bits = bits_from_bytes(row['line_bytes'])
        line_values = [1 | (bit << 1) for bit in bits]
        result, values = execute_pair(mapping, base, [frame_lane]*192,
                                      line_values, 2000)
        if (result['site_visits'] != 138 or len(values) != 138 or
                any(values[index] != quartet(frame_lane, line_values[index])
                    for index in range(len(bits)))):
            raise ValueError(f'actual controller class relay fails: {selector}')
        combined_line.extend(line_values)
        combined_frame.extend([frame_lane]*len(bits))
        classes.append(dict(selector=selector,
                            controller_states=row['states'],
                            controller_line_bytes=row['line_bytes'],
                            first_line_frame=' '.join(f'{value:02X}' for value in frames[first_line]),
                            held_frame_lane_1=frame_lane,
                            bits_checked=len(bits),
                            first_8_quartets=values[:8],
                            distinct_quartets=len(set(values[:len(bits)])),
                            trace_digest=result['result']['trace_digest']))

    combined, combined_values = execute_pair(mapping, base, combined_frame,
                                             combined_line, 3200)
    if (len(combined_line) != 224 or len(combined_values) < 224 or
            any(combined_values[index] != quartet(combined_frame[index],
                                                   combined_line[index])
                for index in range(224))):
        raise ValueError('concatenated controller stream relay fails')

    # Isolate the state-frame effect while holding the line bits identical.
    first_line = combined_line[:64]
    frame_47, outputs_47 = execute_pair(mapping, base, [0x47]*192,
                                        first_line, 2000)
    frame_42, outputs_42 = execute_pair(mapping, base, [0x42]*192,
                                        first_line, 2000)
    changed_by_slot = [sum(a[slot] != b[slot]
                           for a, b in zip(outputs_47[:64], outputs_42[:64]))
                       for slot in range(4)]
    if changed_by_slot != [0, 64, 0, 0]:
        raise ValueError('state-frame class does not isolate the second slot')

    paths = [Path(__file__), CONTROLLER_REPORT, CONTROLLER_ROM,
             HERE/'lower_i_late_byte_relay.py', HERE/'lower_i_d3f8_input.py',
             HERE/'lower_i_prom_data_route.py', HERE/'photo_controller_path.py',
             HERE.parent/'assumed/execute.py']
    report = dict(status='conditional executed controller frame and line-bit mix',
                  fixture=dict(mapping='I7/A0=!10.6, I0/A1=11.2, lower I6=11.0',
                               condition_select_0='previous carry, inverted',
                               initial_q=5, d3f8_trigger='D1 pulse at visit 20',
                               assumed_frame_lane='CD4094 byte lane 1 held at D3A4',
                               assumed_line_route='USART-01 bits LSB first on D1 of D3A6',
                               virtual_output_sites=['3B3', '3B4', '3B5', '3B6']),
                  two_byte_rule='m=D3A4&0F, n=D3A6&0F; Y=(F0|n, F0|((m+n)&0F), n, 0F-n)',
                  exhaustive_checks=dict(low_nibble_pairs=256,
                                         all_frame_bytes_at_line_one=256,
                                         total=checks, quartets_per_check=14),
                  executed_controller_classes=classes,
                  concatenated_diagnostic=dict(bits_checked=224,
                                                output_quartets=len(combined_values),
                                                trace_digest=combined['result']['trace_digest']),
                  isolated_frame_lane_change=dict(frame_bytes=['47', '42'],
                                                  same_line_bits=64,
                                                  changed_outputs_by_slot=changed_by_slot,
                                                  trace_digests=[frame_47['result']['trace_digest'],
                                                                 frame_42['result']['trace_digest']]),
                  limitations=[
                      'D3F8 trigger, CD4094-to-D3A4 and USART-to-D3A6 routes, flag source, and virtual output sites are untraced hypotheses.',
                      'The saved 8031 main-loop streams use diagnostic receive/status/timer events; the four-class concatenation is not one uninterrupted call.',
                      'Only frame byte lane 1 is tested during the 8031 stream; full 32-bit parallel control routing is unknown.',
                      'The low-nibble quartet is not a verified DAC input stream or carrier waveform.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    print('two-input checks', result['exhaustive_checks']['total'])
    print('controller bits', [row['bits_checked'] for row in result['executed_controller_classes']])
    print('frame change by output slot',
          result['isolated_frame_lane_change']['changed_outputs_by_slot'])
