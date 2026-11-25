"""Jointly offer real 8031 frame lane 1 and line bits to two q3 D sites."""

import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]
from common import save
from execute import execute
from lower_i_command_data_mix import bits_from_bytes
from photo_12c_controller_frame_steps import (CONTROLLER_REPORT, SELECTORS,
                                                frame_lanes)
from photo_127_liveness import ROM
from photo_controller_path import fixture
from photo_i0_hold_screen import hold_candidate
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

CYCLES = 4200
HOLDS = (1, 4, 8)


def run(out=HERE / 'results/photo-127-frame-line-joint.json'):
    frames = frame_lanes()
    controller = json.loads(CONTROLLER_REPORT.read_text())
    streams = {row['selector']: row['line_bytes'] for row in controller['rows']
               if row['selector'] in SELECTORS}
    if set(streams) != set(SELECTORS):
        raise ValueError('missing real controller line stream')
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    rom = ROM.read_bytes()
    cases = []
    for selector in SELECTORS:
        frame_byte = frames[selector][1]
        bits = bits_from_bytes(streams[selector])
        for hold in HOLDS:
            offered = [bit for bit in bits for _ in range(hold)]
            scenario = hold_candidate(base)
            scenario['initial']['q'] = 0
            scenario['io']['read']['pc_sequences'][str(0x127)] = [frame_byte]
            scenario['io']['read']['pc_sequences'][str(0x12C)] = offered + [0]
            scenario['io']['read']['address']['bank_by_pc'] = {str(0x129): 256}
            with tempfile.TemporaryDirectory() as temporary:
                result = execute(mapping, scenario, CYCLES, mode='integrated',
                                 out=temporary, trace_limit=CYCLES)
                trace = [json.loads(line) for line in
                         (Path(temporary) / 'trace.jsonl').read_text().splitlines()]
            if not result['clean'] or len(trace) != CYCLES:
                raise ValueError('joined controller run incomplete')
            first = [row for row in trace if row['pc'] == 0x127]
            first_rom = [row for row in trace if row['pc'] == 0x129]
            second = [row for row in trace if row['pc'] == 0x12C]
            rom_rows = [row for row in trace if row['pc'] == 0x12E]
            if (not first or
                    any(row['external_read']['value'] != frame_byte or
                        not row['external_read']['selected_by_alu'] for row in first)):
                raise ValueError('frame lane not selected at D127')
            if len(first) - len(first_rom) not in (0, 1):
                raise ValueError('PC127/PC129 visits differ beyond a partial final loop')
            for n, row in enumerate(first_rom, 1):
                address = 256 + ((3 + n * frame_byte) & 255)
                event = row['external_read']
                if (event['address'] != address or
                        event['value'] != rom[address] or
                        not event['selected_by_alu']):
                    raise ValueError('frame-driven PC129 recurrence changed')
            for index, row in enumerate(second):
                expected = offered[index] if index < len(offered) else 0
                if (row['external_read']['value'] != expected or
                        not row['external_read']['selected_by_alu']):
                    raise ValueError('line bit not selected at D12C')
            phase = 1
            if len(second) - len(rom_rows) not in (0, 1):
                raise ValueError('PC12C/PC12E visits differ beyond a partial final loop')
            for input_row, rom_row in zip(second, rom_rows):
                phase = (phase + input_row['external_read']['value']) & 255
                event = rom_row['external_read']
                if (event['address'] != 256 + phase or
                        event['value'] != rom[256 + phase] or
                        not event['selected_by_alu']):
                    raise ValueError('controller-driven PC12E recurrence changed')
            waits = [row['cycle'] for row in trace if row['pc'] == 0x084]
            cases.append(dict(selector=selector, frame_lane_1=f'{frame_byte:02X}',
                              controller_line_bytes=[f'{v:02X}' for v in streams[selector]],
                              line_bits=len(bits), line_ones=sum(bits),
                              hold_visits=hold, offered_d12c_values=len(offered),
                              selected_d127_visits=len(first),
                              pc129_rom_reads=len(first_rom),
                              selected_d12c_visits=len(second),
                              consumed_full_line_stream=len(second) >= len(offered),
                              pc12e_rom_reads=len(rom_rows), final_phase=phase,
                              first_wait_cycle=waits[0] if waits else None,
                              candidate_output_visits=sum(row['pc'] in (0x392, 0x39E)
                                                          for row in trace),
                              trace_digest=result['trace_digest']))
    report = dict(fixture=dict(mapping='q3 photo-swapped', q=0,
                               frame_route='held controller frame lane 1 at D127',
                               line_route='real USART-01 bits LSB-first at D12C',
                               holds=list(HOLDS), cycles_per_case=CYCLES,
                               rom_bank_at_129='upper'),
                  cases=cases,
                  limitations=[
                      'Controller frame and line bytes come from executed 8031 main-loop runs, but both D-site connections are untraced.',
                      'The D127/D12C input schedule, q3 mapping, held I0, ROM bank and Q=0 are hypotheses.',
                      'No candidate DAC output site is reached and no physical line waveform is identified.'])
    save(out, report)
    return report


if __name__ == '__main__':
    for case in run()['cases']:
        print(case['selector'], case['hold_visits'], case['selected_d12c_visits'],
              case['first_wait_cycle'])
