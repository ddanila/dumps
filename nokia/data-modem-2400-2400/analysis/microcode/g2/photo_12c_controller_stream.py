"""Feed ROM-executed controller bits to PC12C under explicit hold schedules."""

import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from controller_bit_dispatch import controller_stream, CONTROLLER_ROM, CORE, ANALYSIS
from photo_127_liveness import ROM
from photo_12c_bank_liveness import retained
from photo_controller_path import fixture
from photo_i0_hold_screen import hold_candidate
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

CYCLES = 4000
HOLD_VISITS = (1, 2, 4, 8)


def run(out=HERE / 'results/photo-12c-controller-stream.json'):
    controller_bytes, bits = controller_stream()
    if len(bits) != 128 or sum(bits) != 57:
        raise ValueError('controller scrambler fixture changed')
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    rom = ROM.read_bytes()
    cases = []
    for hold in HOLD_VISITS:
        for order, stream in (('forward', bits), ('reverse-diagnostic', bits[::-1])):
            sequence = [bit for bit in stream for _ in range(hold)] + [0]
            scenario = hold_candidate(base)
            scenario['initial']['q'] = 0
            scenario['io']['read']['pc_sequences'][str(0x127)] = [0x81]
            scenario['io']['read']['pc_sequences'][str(0x12C)] = sequence
            scenario['io']['read']['address']['bank_by_pc'] = {str(0x129): 256}
            with tempfile.TemporaryDirectory() as temporary:
                result = execute(mapping, scenario, CYCLES, mode='integrated',
                                 out=temporary, trace_limit=CYCLES)
                trace = [json.loads(line) for line in
                         (Path(temporary) / 'trace.jsonl').read_text().splitlines()]
            lower_scenario = copy.deepcopy(scenario)
            lower_scenario['io']['read']['address']['bank_by_pc'][str(0x12E)] = 0
            with tempfile.TemporaryDirectory() as temporary:
                lower_result = execute(mapping, lower_scenario, CYCLES,
                                       mode='integrated', out=temporary,
                                       trace_limit=CYCLES)
                lower_trace = [json.loads(line) for line in
                               (Path(temporary) / 'trace.jsonl').read_text().splitlines()]
            if not result['clean'] or len(trace) != CYCLES:
                raise ValueError(f'{order}/{hold} run incomplete')
            if (not lower_result['clean'] or len(lower_trace) != CYCLES or
                    [row['pc'] for row in trace] != [row['pc'] for row in lower_trace] or
                    retained(trace, scenario['initial']['ram'], 0x12D) !=
                    retained(lower_trace, lower_scenario['initial']['ram'], 0x12D) or
                    retained(trace, scenario['initial']['ram'], 0x084) !=
                    retained(lower_trace, lower_scenario['initial']['ram'], 0x084)):
                raise ValueError(f'{order}/{hold} ROM bank altered retained state')
            input_rows = [row for row in trace if row['pc'] == 0x12C]
            rom_rows = [row for row in trace if row['pc'] == 0x12E]
            consumed = []
            for index, row in enumerate(input_rows):
                expected = sequence[min(index, len(sequence)-1)]
                event = row['external_read']
                if (event['value'] != expected or
                        event.get('source') != 'scenario_pc_sequence' or
                        not event['selected_by_alu']):
                    raise ValueError(f'{order}/{hold} input mismatch at {index}')
                consumed.append(expected)
            running_phase = 1
            for n, row in enumerate(rom_rows):
                running_phase = (running_phase + consumed[n]) & 255
                address = 256 + running_phase
                event = row['external_read']
                if (event.get('address') != address or event.get('value') != rom[address]
                        or not event['selected_by_alu']):
                    raise ValueError(f'{order}/{hold} ROM mismatch at {n}')
            first_wait = next((row['cycle'] for row in trace if row['pc'] == 0x084), None)
            output_visits = sum(row['pc'] in (0x392, 0x39E) for row in trace)
            lower_rom_rows = [row for row in lower_trace if row['pc'] == 0x12E]
            changed_rom_bytes = sum(a['external_read']['value'] != b['external_read']['value']
                                    for a, b in zip(rom_rows, lower_rom_rows))
            if output_visits or (first_wait is not None) != (hold == 8):
                raise ValueError(f'{order}/{hold} output or branch changed')
            cases.append(dict(order=order, hold_visits_per_bit=hold,
                              offered_bits=len(bits),
                              pc12c_visits=len(input_rows),
                              pc12e_rom_reads=len(rom_rows),
                              controller_bit_positions_touched=min(
                                  len(bits), (min(len(input_rows), len(bits)*hold)+hold-1)//hold),
                              cumulative_ones=sum(consumed),
                              final_phase=(1+sum(consumed)) & 255,
                              idle_zero_visits=max(0, len(input_rows)-len(bits)*hold),
                              first_wait_cycle=first_wait,
                              candidate_output_visits=output_visits,
                              pc12e_rom_bytes_changed_by_bank=changed_rom_bytes,
                              post_pc12d_retained_bank_differences=0,
                              first_rom_addresses=[f'{row["external_read"]["address"]:03X}'
                                                   for row in rom_rows[:12]],
                              trace_digests={'upper': result['trace_digest'],
                                             'lower': lower_result['trace_digest']}))

    expected = {(1, 'forward'): (864, 57, None),
                (1, 'reverse-diagnostic'): (864, 57, None),
                (2, 'forward'): (864, 114, None),
                (2, 'reverse-diagnostic'): (864, 114, None),
                (4, 'forward'): (864, 228, None),
                (4, 'reverse-diagnostic'): (864, 228, None),
                (8, 'forward'): (615, 255, 3074),
                (8, 'reverse-diagnostic'): (479, 255, 2530)}
    for row in cases:
        key = (row['hold_visits_per_bit'], row['order'])
        if (row['pc12c_visits'], row['cumulative_ones'], row['first_wait_cycle']) != expected[key]:
            raise ValueError(f'{key} controller stream result changed')

    paths = [Path(__file__), CONTROLLER_ROM, ROM,
             ANALYSIS / 'interface_probe.c', ANALYSIS / 'controller_scrambler.py',
             *(CORE / name for name in ('core.c', 'opcodes.c', 'disasm.c', 'emu8051.h')),
             HERE / 'controller_bit_dispatch.py', HERE / 'photo_controller_path.py',
             HERE / 'photo_i0_hold_screen.py', HERE / 'photo_127_liveness.py',
             HERE / 'photo_12c_bank_liveness.py',
             HERE / 'photo_mapping_q_sweep.py', HERE / 'photo_mapping_stream_screen.py',
             HERE.parent / 'assumed/execute.py', HERE.parent / 'model.py',
             MAPPINGS['q3']]
    report = dict(status='controller-derived bits exercised at hypothetical PC12C input',
                  fixture=dict(mapping='q3', initial_q=0, held_d127='81',
                               controller_bytes=[f'{value:02X}' for value in controller_bytes],
                               controller_bits=len(bits), input_pc='12C',
                               post_stream_idle=0, hold_visits=list(HOLD_VISITS),
                               cycles_per_case=CYCLES),
                  cases=cases,
                  limitations=[
                      'The 8031 scrambler bytes are ROM-executed, but the bitstream-to-PC12C physical route is untraced.',
                      'Holding each bit for one, two, four or eight PC12C visits is a scenario timing choice, not a recovered clock.',
                      'D127=81, q3 mapping, held-I0 level, ROM bank and Q=0 startup are hypotheses.',
                      'No candidate output word 392 or 39E is reached, and the DAC latch and analog output are unknown.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    for row in run()['cases']:
        print(row['order'], row['hold_visits_per_bit'],
              row['pc12c_visits'], row['cumulative_ones'], row['first_wait_cycle'])
