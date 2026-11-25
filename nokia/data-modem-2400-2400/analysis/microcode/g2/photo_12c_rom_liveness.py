"""Check whether second-loop ROM-bank changes survive its clearing word."""

import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]
from common import save
from execute import execute
from photo_127_liveness import ROM
from photo_controller_path import fixture
from photo_i0_hold_screen import hold_candidate
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

CYCLES = 3000
STEPS = (0x7A, 0x02, 0x80, 0x88)


def run_case(mapping, base, step, bank):
    scenario = hold_candidate(base)
    scenario['initial']['q'] = 0
    scenario['io']['read']['pc_sequences'][str(0x127)] = [0x81]
    scenario['io']['read']['pc_sequences'][str(0x12C)] = [step]
    scenario['io']['read']['address']['bank_by_pc'] = {
        str(0x129): 256, str(0x12E): bank}
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, CYCLES, mode='integrated',
                         out=temporary, trace_limit=CYCLES)
        trace = [json.loads(line) for line in
                 (Path(temporary) / 'trace.jsonl').read_text().splitlines()]
    if not result['clean'] or len(trace) != CYCLES:
        raise ValueError('ROM-liveness run incomplete')
    snapshots = {site: [] for site in (0x12C, 0x12D)}
    ram = scenario['initial']['ram'][:]
    for row in trace:
        for address, value in row['registers'].items():
            ram[int(address)] = value
        if row['pc'] in snapshots:
            snapshots[row['pc']].append((row['cycle'], tuple(ram), row['q'],
                                         row['alu'], row['next_pc'],
                                         row['stack_after']))
    return result, trace, snapshots


def run(out=HERE / 'results/photo-12c-rom-liveness.json'):
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    rom = ROM.read_bytes()
    cases = []
    for step in STEPS:
        low = run_case(mapping, base, step, 0)
        high = run_case(mapping, base, step, 256)
        low_trace, high_trace = low[1], high[1]
        low_rom = [row for row in low_trace if row['pc'] == 0x12E]
        high_rom = [row for row in high_trace if row['pc'] == 0x12E]
        low_after = [row for row in low_trace if row['pc'] == 0x12F]
        high_after = [row for row in high_trace if row['pc'] == 0x12F]
        if (len(low_rom) != len(high_rom) or len(low_rom) != 613 or
                len(low_after) != len(high_after) or
                [row['pc'] for row in low_trace] !=
                [row['pc'] for row in high_trace]):
            raise ValueError('second-loop control flow changed between banks')
        for bank, rows in ((0, low_rom), (256, high_rom)):
            for n, row in enumerate(rows, 1):
                address = bank + ((1 + n * step) & 255)
                event = row['external_read']
                if (event['address'] != address or
                        event['value'] != rom[address] or
                        not event['selected_by_alu'] or
                        row['alu']['y'] != ((address & 255) - rom[address]) & 255):
                    raise ValueError('selected phase/ROM/Y recurrence changed')
        before_low, before_high = low[2][0x12C], high[2][0x12C]
        cleared_low, cleared_high = low[2][0x12D], high[2][0x12D]
        low_clear_rows = [row for row in low_trace if row['pc'] == 0x12D]
        high_clear_rows = [row for row in high_trace if row['pc'] == 0x12D]
        if any(a[:1] + (a[1][1:],) + a[2:] !=
               b[:1] + (b[1][1:],) + b[2:]
               for a, b in zip(before_low, before_high)):
            raise ValueError('preclear difference escaped R0')
        if (len(cleared_low) != len(cleared_high) or
                cleared_low != cleared_high or
                any(row['registers'].get('0') != 0 for row in low_clear_rows[1:]) or
                any(row['registers'].get('0') != 0 for row in high_clear_rows[1:])):
            raise ValueError('second-loop clear did not erase ROM difference')
        cases.append(dict(held_d12c=f'{step:02X}',
                          pc12e_reads_per_bank=len(low_rom),
                          selected_rom_byte_differences=sum(
                              a['external_read']['value'] != b['external_read']['value']
                              for a, b in zip(low_rom, high_rom)),
                          pc12e_y_differences=sum(a['alu']['y'] != b['alu']['y']
                                                  for a, b in zip(low_rom, high_rom)),
                          pc12f_y_differences=sum(a['alu']['y'] != b['alu']['y']
                                                  for a, b in zip(low_after, high_after)),
                          preclear_12c_state_differences=sum(
                              a != b for a, b in zip(before_low, before_high)),
                          postclear_12d_state_differences=0,
                          candidate_output_visits=sum(row['pc'] in (0x392, 0x39E)
                                                      for row in low_trace),
                          trace_digests_by_bank={
                              '0': low[0]['trace_digest'],
                              '256': high[0]['trace_digest']}))
    paths = [Path(__file__), ROM, HERE / 'photo_controller_path.py',
             HERE / 'photo_i0_hold_screen.py', HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3']]
    report = dict(status='second-loop ROM-bank liveness diagnostic',
                  fixture=dict(mapping='q3 photo-swapped', held_d127='81',
                               d12c_steps=[f'{step:02X}' for step in STEPS],
                               q=0, pc129_bank=256,
                               compared_pc12e_banks=[0, 256],
                               cycles_per_case=CYCLES),
                  cases=cases,
                  limitations=[
                      'The D127/D12C input routes, ROM bank control, mapping and held-I0 circuit are hypotheses.',
                      'Equality after 12D applies to these four held steps and this q3 fixture; it does not rule out an external latch sampling 12E/12F.',
                      'Neither the DAC08 data bus nor latch clock is identified.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    for case in run()['cases']:
        print(case['held_d12c'], case['selected_rom_byte_differences'],
              case['pc12f_y_differences'],
              case['postclear_12d_state_differences'])
