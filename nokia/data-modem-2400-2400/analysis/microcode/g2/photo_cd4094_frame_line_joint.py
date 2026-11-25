"""Replay real controller frames through candidate CD4094 lanes and line bits."""

import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]
from common import save
from execute import execute
from lower_i_command_data_mix import bits_from_bytes
from photo_127_frame_line_joint import CONTROLLER_REPORT, CYCLES, SELECTORS
from photo_127_liveness import ROM
from photo_cd4094_order import frames_from_reports, shift_four_bytes
from photo_controller_path import fixture
from photo_i0_hold_screen import hold_candidate
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

HOLD = 8  # diagnostic loop visits per bit; not the measured line-rate timing
ORIENTATIONS = ('q1_to_d0', 'q8_to_d0')


def run(out=HERE / 'results/photo-cd4094-frame-line-joint.json'):
    controller = json.loads(CONTROLLER_REPORT.read_text())
    streams = {row['selector']: row['line_bytes'] for row in controller['rows']
               if row['selector'] in SELECTORS}
    frames = frames_from_reports()
    if set(streams) != set(SELECTORS):
        raise ValueError('missing real controller line stream')
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    rom = ROM.read_bytes()
    cases = []
    for selector in SELECTORS:
        frame = frames[f'main_{selector}']
        chips = shift_four_bytes(frame)
        bits = bits_from_bytes(streams[selector])
        offered = [bit for bit in bits for _ in range(HOLD)] + [0]
        for chip, outputs in enumerate(chips):
            for orientation in ORIENTATIONS:
                value = outputs[orientation]
                scenario = hold_candidate(base)
                scenario['initial']['q'] = 0
                scenario['io']['read']['pc_sequences'][str(0x127)] = [value]
                scenario['io']['read']['pc_sequences'][str(0x12C)] = offered
                scenario['io']['read']['address']['bank_by_pc'] = {str(0x129): 256}
                with tempfile.TemporaryDirectory() as temporary:
                    result = execute(mapping, scenario, CYCLES, mode='integrated',
                                     out=temporary, trace_limit=CYCLES)
                    trace = [json.loads(line) for line in
                             (Path(temporary) / 'trace.jsonl').read_text().splitlines()]
                if not result['clean'] or len(trace) != CYCLES:
                    raise ValueError('transformed controller run incomplete')
                first = [row for row in trace if row['pc'] == 0x127]
                first_rom = [row for row in trace if row['pc'] == 0x129]
                second = [row for row in trace if row['pc'] == 0x12C]
                second_rom = [row for row in trace if row['pc'] == 0x12E]
                if not first or any(row['external_read']['value'] != value or
                                    not row['external_read']['selected_by_alu']
                                    for row in first):
                    raise ValueError('transformed frame not selected at D127')
                if len(first) - len(first_rom) not in (0, 1):
                    raise ValueError('first loop input/ROM visits differ')
                for n, row in enumerate(first_rom, 1):
                    address = 256 + ((3 + n * value) & 255)
                    event = row['external_read']
                    if (event['address'] != address or
                            event['value'] != rom[address] or
                            not event['selected_by_alu']):
                        raise ValueError('transformed first-loop recurrence changed')
                if len(second) - len(second_rom) not in (0, 1):
                    raise ValueError('second loop input/ROM visits differ')
                phase = 1
                for n, row in enumerate(second):
                    expected = offered[min(n, len(offered) - 1)]
                    if (row['external_read']['value'] != expected or
                            not row['external_read']['selected_by_alu']):
                        raise ValueError('line bit not selected at D12C')
                for input_row, rom_row in zip(second, second_rom):
                    phase = (phase + input_row['external_read']['value']) & 255
                    event = rom_row['external_read']
                    if (event['address'] != 256 + phase or
                            event['value'] != rom[256 + phase] or
                            not event['selected_by_alu']):
                        raise ValueError('transformed second-loop recurrence changed')
                waits = [row['cycle'] for row in trace if row['pc'] == 0x084]
                cases.append(dict(selector=selector, frame=frame.hex(' ').upper(),
                                  chip_from_serial_input=chip,
                                  orientation=orientation, d127=f'{value:02X}',
                                  line_bits=len(bits), line_ones=sum(bits),
                                  first_loop_rom_reads=len(first_rom),
                                  second_loop_input_visits=len(second),
                                  full_line_stream_consumed=len(second) >= len(bits) * HOLD,
                                  final_second_phase=phase if second_rom else None,
                                  first_wait_cycle=waits[0] if waits else None,
                                  candidate_output_visits=sum(row['pc'] in (0x392, 0x39E)
                                                              for row in trace),
                                  trace_digest=result['trace_digest']))
    report = dict(fixture=dict(mapping='q3 photo-swapped', q=0,
                               cd4094='four-chip cascade, mode-0 LSB-first',
                               d127_route='one held CD4094 output byte',
                               d12c_route='real USART-01 bits LSB-first',
                               bit_hold_visits=HOLD, cycles_per_case=CYCLES,
                               rom_bank_at_129='upper'),
                  cases=cases,
                  limitations=[
                      'Chip order, Q-pin orientation, DSP bus, D127/D12C routes and sample clock are untraced.',
                      'Eight loop visits per bit is diagnostic and does not model 2400 bit/s at the board oscillator.',
                      'A reached ROM loop is not evidence of a DAC08-bound waveform or receiver behavior.'])
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    for case in report['cases']:
        print(case['selector'], case['chip_from_serial_input'],
              case['orientation'], case['d127'],
              case['second_loop_input_visits'], case['first_wait_cycle'])
