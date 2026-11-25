"""Test whether A0/A1 CD4094 outputs select and drive the two phase loops."""

import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]
from common import save
from execute import execute
from photo_127_liveness import ROM
from photo_cd4094_order import frames_from_reports, shift_four_bytes
from photo_controller_path import fixture
from photo_i0_hold_screen import hold_candidate
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

CYCLES = 3000
TONE_STEPS = {1: {0x88, 0x78}, 3: {0x98, 0x68}}


def run(out=HERE / 'results/photo-cd4094-state-tone.json'):
    frames = frames_from_reports()
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    rom = ROM.read_bytes()
    cases = []
    for state in ('A0', 'A1'):
        frame = frames[f'state_{state}']
        chips = shift_four_bytes(frame)
        for orientation in ('q1_to_d0', 'q8_to_d0'):
            control = chips[1][orientation]
            for step_chip in (0, 2, 3):
                step = chips[step_chip][orientation]
                scenario = hold_candidate(base)
                scenario['initial']['q'] = 0
                scenario['io']['read']['pc_sequences'][str(0x127)] = [control]
                scenario['io']['read']['pc_sequences'][str(0x12C)] = [step]
                scenario['io']['read']['address']['bank_by_pc'] = {
                    str(0x129): 256, str(0x12E): 256}
                with tempfile.TemporaryDirectory() as temporary:
                    result = execute(mapping, scenario, CYCLES, mode='integrated',
                                     out=temporary, trace_limit=CYCLES)
                    trace = [json.loads(line) for line in
                             (Path(temporary) / 'trace.jsonl').read_text().splitlines()]
                if not result['clean'] or len(trace) != CYCLES:
                    raise ValueError('state-tone run incomplete')
                input_127 = [row for row in trace if row['pc'] == 0x127]
                rom_129 = [row for row in trace if row['pc'] == 0x129]
                input_12c = [row for row in trace if row['pc'] == 0x12C]
                rom_12e = [row for row in trace if row['pc'] == 0x12E]
                if (not input_127 or
                        any(row['external_read']['value'] != control or
                            not row['external_read']['selected_by_alu']
                            for row in input_127) or
                        len(input_127) - len(rom_129) not in (0, 1) or
                        len(input_12c) - len(rom_12e) not in (0, 1)):
                    raise ValueError('candidate input route changed')
                for n, row in enumerate(rom_129, 1):
                    address = 256 + ((3 + n * control) & 255)
                    event = row['external_read']
                    if (event['address'] != address or event['value'] != rom[address]
                            or not event['selected_by_alu']):
                        raise ValueError('first-loop phase/ROM relation changed')
                for n, row in enumerate(rom_12e, 1):
                    address = 256 + ((1 + n * step) & 255)
                    event = row['external_read']
                    if (event['address'] != address or event['value'] != rom[address]
                            or not event['selected_by_alu']):
                        raise ValueError('second-loop phase/ROM relation changed')
                if any(row['external_read']['value'] != step or
                       not row['external_read']['selected_by_alu']
                       for row in input_12c):
                    raise ValueError('second-loop input not selected')
                waits = [row['cycle'] for row in trace if row['pc'] == 0x084]
                cases.append(dict(state=state, frame=frame.hex(' ').upper(),
                                  orientation=orientation,
                                  control_chip=1, d127=f'{control:02X}',
                                  step_chip=step_chip, d12c=f'{step:02X}',
                                  pc129_rom_reads=len(rom_129),
                                  pc12e_rom_reads=len(rom_12e),
                                  effective_phase_step_9600_hz={
                                      str(divisor): (step * (375 // divisor)) & 255
                                      for divisor in (1, 3)},
                                  exact_2100_phase_step={
                                      str(divisor): step in values
                                      for divisor, values in TONE_STEPS.items()},
                                  first_wait_cycle=waits[0] if waits else None,
                                  candidate_output_visits=sum(
                                      row['pc'] in (0x392, 0x39E) for row in trace),
                                  trace_digest=result['trace_digest']))
    report = dict(fixture=dict(mapping='q3 photo-swapped', q=0,
                               controller_states=['A0', 'A1'],
                               d127_source='held logical CD4094 chip 1',
                               d12c_source='held chip 0, 2 or 3; same Q orientation',
                               rom_bank='upper', cycles_per_case=CYCLES,
                               tone_sample_rate_hz=9600,
                               assumed_microinstruction_divisors=[1, 3]),
                  cases=cases,
                  limitations=[
                      'The four-chip cascade, Q orientation, both D routes, mapping and clock are hypotheses, not traced Nokia wiring.',
                      'An exact modular phase step is only a necessary condition in this fixed-byte, fixed-gate model; it is not a DAC waveform.',
                      'Other chip wiring, a decoded phase input, a different clock and other output sites remain possible.'])
    save(out, report)
    return report


if __name__ == '__main__':
    for case in run()['cases']:
        print(case['state'], case['orientation'], case['step_chip'],
              case['d127'], case['d12c'], case['pc12e_rom_reads'],
              case['first_wait_cycle'])
