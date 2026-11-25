"""Run all PC12C input bytes after a held D127=81 loop exit."""

import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from photo_127_liveness import ROM, CYCLES
from photo_controller_path import fixture
from photo_i0_hold_screen import hold_candidate
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS


def run(out=HERE / 'results/photo-12c-phase-scan.json'):
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    rom = ROM.read_bytes()
    rows = []
    for value in range(256):
        scenario = hold_candidate(base)
        scenario['initial']['q'] = 0
        scenario['io']['read']['pc_sequences'][str(0x127)] = [0x81]
        scenario['io']['read']['pc_sequences'][str(0x12C)] = [value]
        scenario['io']['read']['address']['bank_by_pc'] = {str(0x129): 256}
        with tempfile.TemporaryDirectory() as temporary:
            result = execute(mapping, scenario, CYCLES, mode='integrated',
                             out=temporary, trace_limit=CYCLES)
            trace = [json.loads(line) for line in
                     (Path(temporary) / 'trace.jsonl').read_text().splitlines()]
        if not result['clean'] or len(trace) != CYCLES:
            raise ValueError(f'PC12C={value:02X} execution incomplete')
        first = next(row['cycle'] for row in trace if row['pc'] == 0x12C)
        if first != 547:
            raise ValueError(f'PC12C={value:02X} entry changed')
        addresses = []
        for n, row in enumerate((row for row in trace if row['pc'] == 0x12E), 1):
            address = 256 + ((1 + n * value) & 255)
            event = row['external_read']
            if (event.get('address') != address or event.get('value') != rom[address]
                    or not event['selected_by_alu']):
                raise ValueError(f'PC12C={value:02X} ROM recurrence changed at {n}')
            addresses.append(address)
        second_rows = [row for row in trace if row['pc'] == 0x12C]
        second_visits = len(second_rows)
        if any(row['external_read']['value'] != value or
               row['external_read'].get('source') != 'scenario_pc_sequence' or
               not row['external_read']['selected_by_alu'] for row in second_rows):
            raise ValueError(f'PC12C={value:02X} input selection changed')
        wait = next((row['cycle'] for row in trace if row['pc'] == 0x084), None)
        outputs = sum(row['pc'] in (0x392, 0x39E) for row in trace)
        if value & 1:
            expected = (-pow(value, -1, 256)) % 256
            if (len(addresses) != expected or second_visits != expected or
                    len(set(addresses)) != expected or addresses[-1] != 256 or
                    wait is None or outputs):
                raise ValueError(f'PC12C={value:02X} odd scan changed')
        elif (len(addresses) != 613 or second_visits != 614 or
              wait is not None or outputs):
            raise ValueError(f'PC12C={value:02X} even scan changed')
        rows.append(dict(d12c=f'{value:02X}', parity='odd' if value & 1 else 'even',
                         pc12e_rom_reads=len(addresses),
                         distinct_rom_addresses=len(set(addresses)),
                         first_rom_addresses=[f'{address:03X}' for address in addresses[:8]],
                         last_rom_address=f'{addresses[-1]:03X}',
                         first_wait_cycle=wait, candidate_output_visits=outputs,
                         trace_digest=result['trace_digest']))

    paths = [Path(__file__), ROM, HERE / 'photo_127_liveness.py',
             HERE / 'photo_controller_path.py', HERE / 'photo_i0_hold_screen.py',
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             HERE.parent / 'assumed/execute.py', HERE.parent / 'model.py',
             MAPPINGS['q3']]
    report = dict(status='all 256 PC12C held inputs executed after D127=81 exit',
                  fixture=dict(mapping='q3', initial_q=0, d127='81 held',
                               d12c_source='held scenario byte',
                               d12f_source='scenario constant 1',
                               pc12e_rom_bank=256, cycles_per_case=CYCLES),
                  relation='PC12E address=100+((1+n*D12C) mod 256); n starts at 1',
                  odd=dict(count=128, reads='odd n in 1..255 solving 1+n*D12C=0 mod 256',
                           exits_to_wait=True),
                  even=dict(count=128, reads_per_run=613, exits_to_wait=False),
                  rows=rows,
                  limitations=[
                      'D127=81 and D12C are imposed scenario bytes; no controller-frame or physical input route is traced.',
                      'The q3 mapping, held-I0 level, Q=0, ROM gate and PC12F constant-one input remain hypotheses.',
                      'The 3000-instruction even-byte runs do not exclude later external input changes.',
                      'No candidate DAC output word 392 or 39E is reached; transient ALU outputs are not physical DAC samples.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    print('odd scans', result['odd']['count'], 'even continuing', result['even']['count'])
    for value in ('01', '03', 'FF', '02'):
        row = next(row for row in result['rows'] if row['d12c'] == value)
        print(value, row['pc12e_rom_reads'], row['first_wait_cycle'])
