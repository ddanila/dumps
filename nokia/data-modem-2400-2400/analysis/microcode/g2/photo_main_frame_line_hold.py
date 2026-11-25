"""Replay real USART bits held on one D127 lane at the 2400-bit/s clock."""

import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]
from common import save
from execute import execute
from lower_i_command_data_mix import bits_from_bytes
from photo_127_liveness import ROM
from photo_controller_path import fixture
from photo_dac08_bus_order_screen import q_to_dac
from photo_i0_hold_screen import hold_candidate
from photo_main_frame_carrier_swap import MAIN_STATES, spectrum
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

CONTROLLER = HERE / 'results/main-loop-serial.json'
OSCILLATOR_HZ = 14_400_000
BIT_HZ = 2400
LOOP_WORDS = 4
BIT_VISITS = OSCILLATOR_HZ // (BIT_HZ * LOOP_WORDS)
CYCLES = 13_000
BASE = 0xB0
LANES = (4, 5)


def projected_held(rom, input_byte):
    phases = [(3 + (1 + sample * 375) * input_byte) & 255
              for sample in range(640)]
    y = [(phase - rom[256 + phase]) & 255 for phase in phases]
    dac = [q_to_dac(value, 'swap_q4_q5') for value in y]
    return spectrum(dac)


def run(out=HERE / 'results/photo-main-frame-line-hold.json'):
    if BIT_VISITS != 1500:
        raise ValueError('line-rate visit budget changed')
    controller = json.loads(CONTROLLER.read_text())
    rows = {f'main_{row["selector"]}': row for row in controller['rows']
            if f'main_{row["selector"]}' in MAIN_STATES}
    if set(rows) != set(MAIN_STATES):
        raise ValueError('controller stream classes changed')
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    rom = ROM.read_bytes()
    spectra = {str(lane): {
        'zero': projected_held(rom, BASE),
        'one': projected_held(rom, BASE & ~(1 << lane))}
        for lane in LANES}
    if (spectra['4']['zero']['peak_hz'] != 1800 or
            spectra['4']['one']['peak_hz'] != 3600 or
            spectra['5']['one']['peak_hz'] != 600):
        raise ValueError('held-level carrier frequency screen changed')
    cases = []
    for name in MAIN_STATES:
        row = rows[name]
        bits = bits_from_bytes(row['line_bytes'])
        for lane in LANES:
            values = [BASE & ~(bit << lane)
                      for bit in bits[:3] for _ in range(BIT_VISITS)]
            scenario = hold_candidate(base)
            scenario['initial']['q'] = 0
            scenario['io']['read']['pc_sequences'][str(0x127)] = values
            scenario['io']['read']['pc_sequences'][str(0x12C)] = [0]
            scenario['io']['read']['address']['bank_by_pc'] = {str(0x129): 256}
            with tempfile.TemporaryDirectory() as temporary:
                result = execute(mapping, scenario, CYCLES, mode='integrated',
                                 out=temporary, trace_limit=CYCLES)
                trace = [json.loads(line) for line in
                         (Path(temporary) / 'trace.jsonl').read_text().splitlines()]
            if not result['clean'] or len(trace) != CYCLES:
                raise ValueError('line-rate run incomplete')
            input_rows = [item for item in trace if item['pc'] == 0x127]
            rom_rows = [item for item in trace if item['pc'] == 0x129]
            if (len(input_rows) < 3001 or len(input_rows) - len(rom_rows) not in (0, 1)
                    or any(item['pc'] == 0x12E for item in trace)):
                raise ValueError('held-bit route left the carrier loop')
            phase = 3
            samples = []
            for visit, (input_row, rom_row) in enumerate(zip(input_rows, rom_rows), 1):
                d = values[visit - 1]
                phase = (phase + d) & 255
                value = rom[256 + phase]
                if (input_row['external_read']['value'] != d or
                        not input_row['external_read']['selected_by_alu'] or
                        rom_row['external_read']['address'] != 256 + phase or
                        rom_row['external_read']['value'] != value or
                        rom_row['alu']['y'] != (phase - value) & 255):
                    raise ValueError(f'line D/phase/ROM/Y mismatch at visit {visit}')
                if (visit - 1) % 375 == 0:
                    samples.append(q_to_dac(rom_row['alu']['y'], 'swap_q4_q5'))
            if len(samples) < 9:
                raise ValueError('insufficient executed DAC capture candidates')
            checkpoints = []
            for visit in (BIT_VISITS, 2 * BIT_VISITS):
                delta = (-sum(bits[:visit // BIT_VISITS]) * BIT_VISITS *
                         (1 << lane)) & 255
                actual = (3 + sum(values[:visit]) - (3 + visit * BASE)) & 255
                if actual != delta:
                    raise ValueError('bit-boundary differential phase changed')
                checkpoints.append(dict(after_bits=visit // BIT_VISITS,
                                        phase_delta=delta))
            cases.append(dict(controller_class=name,
                              first_3_line_bits=bits[:3], d_lane=lane,
                              selected_d127_visits=len(input_rows),
                              selected_pc129_reads=len(rom_rows),
                              first_9_candidate_dac_codes=[f'{value:02X}'
                                                           for value in samples[:9]],
                              bit_boundary_phase_deltas=checkpoints,
                              candidate_output_visits=sum(item['pc'] in (0x392, 0x39E)
                                                          for item in trace),
                              trace_digest=result['trace_digest']))
    paths = [Path(__file__), CONTROLLER, ROM,
             HERE / 'lower_i_command_data_mix.py',
             HERE / 'photo_127_liveness.py',
             HERE / 'photo_main_frame_carrier_swap.py',
             HERE / 'photo_dac08_bus_order_screen.py',
             HERE / 'photo_controller_path.py',
             HERE / 'photo_i0_hold_screen.py',
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3']]
    report = dict(status='line-rate held-controller-bit overlay on B0 carrier candidate',
                  fixture=dict(mapping='q3 photo-swapped', frame_d127_base='B0 from main-frame A1 via hypothetical D0/D4 crossing',
                               line_bits='real 8031 USART-01 bytes, LSB first',
                               d127_bit_rule='clear baseline D4 or D5 throughout each bit-1 hold',
                               oscillator_hz=OSCILLATOR_HZ,
                               microinstruction_divisor=1,
                               bits_per_second=BIT_HZ,
                               loop_visits_per_bit=BIT_VISITS,
                               output_sample_hz=9600,
                               candidate_dac='Y129→LS273 ordered, Q4/Q5 swapped to DAC08'),
                  held_level_spectra=spectra, cases=cases,
                  limitations=[
                      'The USART-to-D127 gate, frame crossing, DAC bus/clock and oscillator divisor are untraced hypotheses.',
                      'Only the first two complete bit holds and start of the third are executed per class/lane; full streams are not projected.',
                      'The one level yields an end-of-bit phase offset but also changes the carrier-rate frequency during the held bit.',
                      'No observed DAC output, four-way dibit decode, receiver decision or echo cancellation is demonstrated.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    for row in result['cases']:
        print(row['controller_class'], row['d_lane'], row['first_3_line_bits'],
              [item['phase_delta'] for item in row['bit_boundary_phase_deltas']])
