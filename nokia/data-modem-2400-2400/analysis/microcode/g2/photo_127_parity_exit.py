"""Run all held D127 bytes and classify the PC127/PC12C control-flow split."""

import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from photo_127_liveness import ROM, CYCLES, run_case
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS


def run(out=HERE / 'results/photo-127-parity-exit.json'):
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    rom = ROM.read_bytes()
    rows = []
    for value in range(256):
        _, execution, trace = run_case(mapping, base, value, 256)
        reads = [i for i, row in enumerate(trace) if row['pc'] == 0x129]
        for n, i in enumerate(reads, 1):
            row = trace[i]
            phase = (3 + n * value) & 255
            if (row['external_read']['address'] != 256 + phase or
                    row['external_read']['value'] != rom[256 + phase] or
                    row['alu']['y'] != ((phase - rom[256 + phase]) & 255) or
                    trace[i-2]['pc'] != 0x127 or trace[i-1]['pc'] != 0x128 or
                    trace[i+1]['pc'] != 0x12A):
                raise ValueError(f'D127={value:02X} recurrence changed at {n}')
        if any(b-a != 4 for a,b in zip(reads,reads[1:])):
            raise ValueError(f'D127={value:02X} PC129 cadence changed')
        if not execution['clean'] or len(trace) != CYCLES:
            raise ValueError(f'D127={value:02X} execution failed')
        exit_rows = [row for row in trace
                     if row['pc'] == 0x12A and row['next_pc'] == 0x12B]
        second_loop = [row for row in trace if row['pc'] == 0x12C]
        rom_reads = [row for row in trace if row['pc'] == 0x12E]
        first_wait = next((row['cycle'] for row in trace if row['pc'] == 0x084), None)
        output_visits = sum(row['pc'] in (0x392, 0x39E) for row in trace)
        if value & 1:
            expected = (-3 * pow(value, -1, 256)) % 256
            if (len(reads) != expected or len(exit_rows) != 1 or
                    exit_rows[0]['cycle'] != 39 + 4 * expected or
                    len(second_loop) != 255 or len(rom_reads) != 255 or
                    any(row['external_read'].get('source') != 'scenario_pc_sequence'
                        or row['external_read']['value'] != 1 for row in second_loop) or
                    [row['external_read'].get('address') for row in rom_reads] !=
                    [256 + ((n + 1) & 255) for n in range(1, 256)] or
                    any(not row['external_read']['selected_by_alu'] for row in rom_reads) or
                    first_wait != exit_rows[0]['cycle'] + 1095 or
                    output_visits):
                raise ValueError(f'D127={value:02X} odd exit changed')
        elif (len(reads) != 740 or exit_rows or second_loop or rom_reads or
              first_wait is not None or output_visits):
            raise ValueError(f'D127={value:02X} even loop changed')
        rows.append(dict(d127=f'{value:02X}', parity='odd' if value & 1 else 'even',
                         pc129_reads=len(reads),
                         pc12a_exit_cycle=exit_rows[0]['cycle'] if exit_rows else None,
                         pc12c_visits=len(second_loop),
                         pc12e_rom_reads=len(rom_reads), first_wait_cycle=first_wait,
                         candidate_output_visits=output_visits,
                         trace_digest=execution['trace_digest']))

    paths = [Path(__file__), ROM, HERE / 'photo_127_liveness.py',
             HERE / 'photo_controller_path.py', HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3']]
    report = dict(status='all 256 held D127 values executed under q3 photo-pin fixture',
                  fixture=dict(mapping='q3', initial_q=0,
                               d127_source='held byte, hypothetical',
                               pc129_rom_bank=256, cycles_per_case=CYCLES),
                  relation='phase_n=(3+n*D127) mod 256; PC12A exits to PC12B when phase_n=0',
                  odd=dict(count=128, pc129_reads='unique odd n in 1..255 solving phase_n=0',
                           pc12c_visits_each=255, pc12e_rom_reads_each=255,
                           pc12e_rom_addresses='102..1FF,100 in order',
                           wait_cycle='39+4*n+1095'),
                  even=dict(count=128, pc129_reads_each=740,
                            pc12c_visits_each=0, wait_reached=False),
                  rows=rows,
                  limitations=[
                      'This is a control-flow property of the q3 held-I0, Q=0 and upper-bank fixture, not a recovered Nokia input connection.',
                      'Only 3000 microinstructions per value are run; even values have no phase-zero solution under the checked recurrence, but longer independent control changes are untested.',
                      'PC392 and PC39E are candidate output sites; no DAC latch or analog output is traced.',
                      'The four-byte controller frame is not proven to drive D127.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    print('odd exits', result['odd']['count'], 'even retained loops', result['even']['count'])
    for value in ('81', '88'):
        row = next(row for row in result['rows'] if row['d127'] == value)
        print(value, row['pc129_reads'], row['pc12e_rom_reads'], row['first_wait_cycle'])
