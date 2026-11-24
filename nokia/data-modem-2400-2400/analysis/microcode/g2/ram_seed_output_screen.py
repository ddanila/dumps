"""Screen initial Am2901 RAM bytes against the q3 controller-fed output path.

Every mapping, ROM gate, controller input and latch site is a declared
hypothesis. This tests startup-state sensitivity, not physical DAC wiring.
"""
import copy
import hashlib
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
from common import save
from execute import execute
from controller_bit_dispatch import controller_stream
from photo_controller_path import fixture

COARSE_VALUES = (1, 2, 4, 8, 16, 32, 64, 128, 255)
CYCLES = 512


def run_case(mapping, base_scenario, register, value, directory):
    scenario = copy.deepcopy(base_scenario)
    scenario['initial']['ram'][register] = value
    result = execute(mapping, scenario, CYCLES, mode='integrated',
                     out=directory, trace_limit=CYCLES)
    trace = [json.loads(line) for line in
             (directory / 'trace.jsonl').read_text().splitlines()]
    if not result['clean'] or len(trace) != CYCLES:
        raise ValueError('incomplete startup-state run')
    codes = [row['alu']['y'] for row in trace if row['pc'] == 0x392]
    reads = [row['external_read']['value'] for row in trace if row['pc'] == 0x38E]
    writes_13 = [row['cycle'] for row in trace if '13' in row['registers']]
    return dict(register=register, seed=value, final_pc=f"{result['final_state']['pc']:03X}",
                reads_38e=len(reads), captures_392=len(codes),
                codes_392=sorted(set(codes)), writes_13=writes_13,
                selected_rom_reads=result['rom_reads']['selected_by_alu'],
                trace_digest=result['trace_digest']), trace


def run(out):
    mapping, scenario = fixture()
    _, bits = controller_stream()
    scenario['initial']['q'] = 5
    scenario['io']['read']['pc_sequences']['910'] = bits
    coarse = []
    all_13 = []
    traces = {}
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        baseline, _ = run_case(mapping, scenario, 13, 0, directory)
        for register in range(16):
            for seed in COARSE_VALUES:
                row, _ = run_case(mapping, scenario, register, seed, directory)
                coarse.append(row)
        for seed in range(256):
            row, trace = run_case(mapping, scenario, 13, seed, directory)
            all_13.append(row)
            if seed in (248, 249, 250, 251):
                traces[seed] = trace

    if baseline['codes_392'] != [11] or baseline['captures_392'] != 17:
        raise ValueError('baseline output path changed')
    if any(row['writes_13'] for row in coarse + all_13):
        raise ValueError('RAM13 was written; startup-only interpretation invalid')
    non_13 = [row for row in coarse if row['register'] != 13]
    if any(row['codes_392'] != [11] or row['captures_392'] != 17 or
           row['reads_38e'] != 39 or row['final_pc'] != '389' for row in non_13):
        raise ValueError('a coarse non-RAM13 seed changed the candidate path')
    exits = [row for row in all_13 if row['captures_392'] == 0]
    if [row['seed'] for row in exits] != [249, 250]:
        raise ValueError('RAM13 path-exit set changed')
    if any(row['codes_392'] != [(11 + row['seed']) & 255] or
           row['captures_392'] != 17 or row['reads_38e'] != 39
           for row in all_13 if row not in exits):
        raise ValueError('RAM13 candidate code formula or path changed')
    if any(row['final_pc'] != '084' or row['reads_38e'] != 1 for row in exits):
        raise ValueError('RAM13 exit route changed')

    splits = {}
    for seed in (249, 250):
        a, b = traces[248], traces[seed]
        index = next(i for i, (left, right) in enumerate(zip(a, b))
                     if left['pc'] != right['pc'])
        splits[str(seed)] = dict(first_different_cycle=index,
                                 preceding_pc=f"{a[index-1]['pc']:03X}",
                                 baseline_next=f"{a[index-1]['next_pc']:03X}",
                                 exit_next=f"{b[index-1]['next_pc']:03X}")

    sources = [Path(__file__), HERE/'photo_controller_path.py',
               HERE/'controller_bit_dispatch.py', ASSUMED/'execute.py',
               HERE/'results/swapped-sine-loop/phase-20-mapping.json',
               HERE/'results/swapped-sine-loop/phase-20-scenario.json']
    report = dict(status='scoped startup-state screen, not physical output',
                  fixture=dict(mapping=mapping['name'], q=5,
                               controller_bits_supplied=len(bits),
                               cycles_per_case=CYCLES,
                               assumed_latch_clock_pc='392',
                               assumed_latch_data='Am2901 ALU Y'),
                  baseline=baseline,
                  coarse=dict(registers=16, values=list(COARSE_VALUES),
                              cases=len(coarse),
                              non_ram13_path_metrics={
                                  f'{pc}:captures={captures}:reads={reads}': count
                                  for (pc, captures, reads), count in Counter(
                                      (row['final_pc'], row['captures_392'],
                                       row['reads_38e']) for row in non_13).items()},
                              ram13_codes={str(row['seed']): row['codes_392']
                                           for row in coarse if row['register'] == 13}),
                  ram13_full=dict(seeds=256, normal_seeds=254,
                                  code_formula='(11 + initial RAM13) mod 256',
                                  exit_seeds=[249, 250],
                                  exit_branch=splits,
                                  rows=all_13),
                  limitations=['RAM starts with exactly one varied byte; simultaneous RAM changes are not screened.',
                               'The D38E controller-bit route, ALU-Y output source and clock-at-392 are untraced hypotheses.',
                               'A fixed code under this fixture does not exclude other mappings, command paths or latch clocks.'],
                  source_sha256={str(path.relative_to(HERE.parent)): hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    out.parent.mkdir(parents=True, exist_ok=True)
    save(out, report)
    return report


if __name__ == '__main__':
    report = run(HERE/'results/ram-seed-output-screen.json')
    print(report['coarse']['cases'], report['ram13_full']['normal_seeds'],
          report['ram13_full']['exit_seeds'])
