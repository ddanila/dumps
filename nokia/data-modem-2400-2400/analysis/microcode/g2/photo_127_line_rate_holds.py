"""Replay joined controller frame/line inputs at oscillator-derived bit holds."""

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

CYCLES = 9000
DIVISORS = (1, 2, 3, 4)
OSCILLATOR_HZ = 14_400_000
DATA_RATE = 2400
LOOP_WORDS = 4


def run(out=HERE / 'results/photo-127-line-rate-holds.json'):
    frames = frame_lanes()
    controller = json.loads(CONTROLLER_REPORT.read_text())
    streams = {row['selector']: row['line_bytes'] for row in controller['rows']
               if row['selector'] in SELECTORS}
    if set(streams) != set(SELECTORS):
        raise ValueError('controller classes missing')
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    rom = ROM.read_bytes()
    cases = []
    for divisor in DIVISORS:
        if OSCILLATOR_HZ % (divisor * DATA_RATE * LOOP_WORDS):
            raise ValueError('expected integral loop visits per bit')
        hold = OSCILLATOR_HZ // (divisor * DATA_RATE * LOOP_WORDS)
        for selector in SELECTORS:
            frame_byte = frames[selector][1]
            bits = bits_from_bytes(streams[selector])
            values = [bit for bit in bits for _ in range(hold)] + [0]
            scenario = hold_candidate(base)
            scenario['initial']['q'] = 0
            scenario['io']['read']['pc_sequences'][str(0x127)] = [frame_byte]
            scenario['io']['read']['pc_sequences'][str(0x12C)] = values
            scenario['io']['read']['address']['bank_by_pc'] = {str(0x129): 256}
            with tempfile.TemporaryDirectory() as temporary:
                result = execute(mapping, scenario, CYCLES, mode='integrated',
                                 out=temporary, trace_limit=CYCLES)
                trace = [json.loads(line) for line in
                         (Path(temporary) / 'trace.jsonl').read_text().splitlines()]
            if not result['clean'] or len(trace) != CYCLES:
                raise ValueError('timed controller run incomplete')
            input_127 = [row for row in trace if row['pc'] == 0x127]
            input_12c = [row for row in trace if row['pc'] == 0x12C]
            rom_12e = [row for row in trace if row['pc'] == 0x12E]
            if (not input_127 or
                    any(row['external_read']['value'] != frame_byte or
                        not row['external_read']['selected_by_alu']
                        for row in input_127)):
                raise ValueError('frame lane not selected at D127')
            if len(input_12c) != len(rom_12e):
                raise ValueError('second loop input/ROM visits differ')
            phase = 1
            for index, (input_row, rom_row) in enumerate(zip(input_12c, rom_12e)):
                expected = values[min(index, len(values) - 1)]
                if (input_row['external_read']['value'] != expected or
                        not input_row['external_read']['selected_by_alu']):
                    raise ValueError('line bit not selected at D12C')
                phase = (phase + expected) & 255
                event = rom_row['external_read']
                if (event['address'] != 256 + phase or
                        event['value'] != rom[256 + phase] or
                        not event['selected_by_alu']):
                    raise ValueError('timed PC12E phase/ROM recurrence changed')
            waits = [row['cycle'] for row in trace if row['pc'] == 0x084]
            first_bit_reads = rom_12e[:min(hold, len(rom_12e))]
            cases.append(dict(selector=selector, frame_lane_1=f'{frame_byte:02X}',
                              divisor=divisor, visits_per_bit=hold,
                              line_bits=len(bits), first_8_line_bits=bits[:8],
                              selected_d127_visits=len(input_127),
                              selected_d12c_visits=len(input_12c),
                              first_bit_positions_touched=(
                                  (len(input_12c) - 1) // hold + 1 if input_12c else 0),
                              first_bit_rom_addresses=sorted({
                                  f'{row["external_read"]["address"]:03X}'
                                  for row in first_bit_reads}),
                              final_phase=phase,
                              first_wait_cycle=waits[0] if waits else None,
                              candidate_output_visits=sum(row['pc'] in (0x392, 0x39E)
                                                          for row in trace),
                              trace_digest=result['trace_digest']))
    report = dict(fixture=dict(mapping='q3 photo-swapped', q=0,
                               controller_frame_lane_1_at_d127=True,
                               controller_line_bits_at_d12c=True,
                               oscillator_hz=OSCILLATOR_HZ,
                               assumed_microinstruction_divisors=list(DIVISORS),
                               data_rate_bps=DATA_RATE, loop_words=LOOP_WORDS,
                               cycles_per_case=CYCLES),
                  cases=cases,
                  limitations=[
                      'The controller bytes are ROM-executed but both D-site connections and their timing are untraced.',
                      'The 14.4 MHz oscillator is observed, but its divider to the 8X02 microcycle is not measured.',
                      'No DAC-bound output or receive behavior is established; this only tests the direct serial-bit-to-D12C route.'])
    save(out, report)
    return report


if __name__ == '__main__':
    for case in run()['cases']:
        print(case['divisor'], case['selector'], case['selected_d12c_visits'],
              case['first_wait_cycle'])
