"""Compare paired PC12E ROM-bank reads across the q3 second loop."""

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


def run_case(mapping, base, bank):
    scenario = hold_candidate(base)
    scenario['initial']['q'] = 0
    scenario['io']['read']['pc_sequences'][str(0x127)] = [0x81]
    scenario['io']['read']['pc_sequences'][str(0x12C)] = [1]
    scenario['io']['read']['address']['bank_by_pc'] = {
        str(0x129): 256, str(0x12E): bank}
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, CYCLES, mode='integrated',
                         out=temporary, trace_limit=CYCLES)
        trace = [json.loads(line) for line in
                 (Path(temporary) / 'trace.jsonl').read_text().splitlines()]
    if not result['clean'] or len(trace) != CYCLES:
        raise ValueError(f'PC12E bank {bank} execution incomplete')
    return scenario, result, trace


def retained(trace, initial_ram, pc):
    ram = initial_ram[:]
    rows = []
    for row in trace:
        for register, value in row['registers'].items():
            ram[int(register)] = value
        if row['pc'] == pc:
            rows.append((tuple(ram), row['q'], row['alu'],
                         row['next_pc'], row['stack_after']))
    return rows


def run(out=HERE / 'results/photo-12c-bank-liveness.json'):
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    rom = ROM.read_bytes()
    cases = [run_case(mapping, base, bank) for bank in (0, 256)]
    (low_s, low_result, low), (high_s, high_result, high) = cases
    if [row['pc'] for row in low] != [row['pc'] for row in high]:
        raise ValueError('PC12E bank changed control flow')
    selected = []
    for bank, trace in ((0, low), (256, high)):
        reads = [i for i, row in enumerate(trace) if row['pc'] == 0x12E]
        if len(reads) != 255:
            raise ValueError(f'PC12E bank {bank} read count changed')
        for n, i in enumerate(reads, 1):
            phase = (1 + n) & 255
            row = trace[i]
            if (row['external_read']['address'] != bank + phase or
                    row['external_read']['value'] != rom[bank + phase] or
                    not row['external_read']['selected_by_alu'] or
                    row['alu']['y'] != ((phase - rom[bank + phase]) & 255) or
                    row['alu']['carry'] != int(phase >= rom[bank + phase]) or
                    trace[i+1]['pc'] != 0x12F or
                    trace[i+1]['alu']['y'] != ((phase + 1 + row['alu']['carry']) & 255)):
                raise ValueError(f'PC12E bank {bank} recurrence changed at {n}')
        selected.append(reads)
    pairs = [(low[i], high[j]) for i, j in zip(*selected)]
    checkpoints = {}
    for pc in (0x12C, 0x12D, 0x12E, 0x12F, 0x084):
        a = retained(low, low_s['initial']['ram'], pc)
        b = retained(high, high_s['initial']['ram'], pc)
        if len(a) != len(b):
            raise ValueError(f'checkpoint count changed at {pc:03X}')
        checkpoints[f'{pc:03X}'] = dict(visits=len(a),
                                        differing_retained_states=sum(x != y for x, y in zip(a, b)),
                                        differing_ram_registers=sorted({i for x, y in zip(a, b)
                                            for i, (u, v) in enumerate(zip(x[0], y[0])) if u != v}))
    result = dict(selected_rom_byte_differences=sum(
                      a['external_read']['value'] != b['external_read']['value']
                      for a, b in pairs),
                  pc12e_y_differences=sum(a['alu']['y'] != b['alu']['y'] for a, b in pairs),
                  pc12f_y_differences=sum(low[i+1]['alu']['y'] != high[j+1]['alu']['y']
                                           for i, j in zip(*selected)),
                  checkpoints=checkpoints,
                  trace_digests={'lower': low_result['trace_digest'],
                                 'upper': high_result['trace_digest']})
    if (result['pc12e_y_differences'] != 251 or
            result['pc12f_y_differences'] != 69 or
            checkpoints['12C']['differing_retained_states'] != 69 or
            checkpoints['12C']['differing_ram_registers'] != [0] or
            checkpoints['12D']['differing_retained_states'] != 0 or
            checkpoints['084']['differing_retained_states'] != 0):
        raise ValueError('PC12E bank liveness result changed')

    paths = [Path(__file__), ROM, HERE / 'photo_127_liveness.py',
             HERE / 'photo_controller_path.py',
             HERE / 'photo_i0_hold_screen.py', HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             HERE.parent / 'assumed/execute.py', HERE.parent / 'model.py',
             MAPPINGS['q3']]
    report = dict(status='paired PC12E bank liveness, not physical DAC output',
                  fixture=dict(mapping='q3', initial_q=0, held_d127='81', held_d12c='01',
                               changed_input='PC12E Am27S31 A8 lower versus upper',
                               cycles_per_case=CYCLES),
                  result=result,
                  limitations=[
                      'The ROM bank select, mapping, D inputs and held-I0 route are scenario hypotheses.',
                      'PC12E ROM byte changes transient R0 and the following PC12F carry result, but the tested retained state matches after PC12D.',
                      'A latch could sample a transient value; the DAC data and clock routes are untraced.',
                      'No controller frame or physical line output is demonstrated.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()['result']
    print(result['selected_rom_byte_differences'], result['pc12e_y_differences'],
          result['pc12f_y_differences'], result['checkpoints'])
