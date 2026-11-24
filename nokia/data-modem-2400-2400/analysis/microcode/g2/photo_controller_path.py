"""Test a photo-informed A/I mapping against controller bits and byte values.

All added connections, latch levels, dispatch timing and startup state are
diagnostic hypotheses. The output examined here is Am2901 ALU Y, not the DAC.
"""
import copy
import hashlib
import json
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
from common import read, save
from execute import execute
from controller_bit_dispatch import controller_stream, groups_for, post_group_states

BASE_MAPPING = HERE / 'results/swapped-sine-loop/phase-20-mapping.json'
BASE_SCENARIO = HERE / 'results/swapped-sine-loop/phase-20-scenario.json'
PHOTO_RECORD = HERE / 'photo-i7-constraint.json'
PHOTO_A_RECORD = HERE / 'photo-a-input-constraint.json'
GATE_FITS = ASSUMED / 'results/rom-gate-study/report.json'
INPUT_PC = 0x38E
DISPATCH_PC = 0x38F
SEED_CYCLES = 512
STREAM_CYCLES = 1580


def fixture():
    mapping = read(BASE_MAPPING)
    scenario = read(BASE_SCENARIO)
    if mapping['fields']['a']['bits'] != ['18.1', '18.0', '17.7', '17.6']:
        raise ValueError('base A field changed')
    mapping['name'] += '-photo-a2-a3'
    mapping['fields']['a']['bits'][2:] = ['10.7', '10.6']
    mapping['fields']['a']['status'] = 'hypothesis'
    mapping['fields']['a']['evidence'] = (
        'Photo candidate U10 D7/D6 through U5 Q1/Q2 to U2 A2/A3; '
        'A3 continuation is not measured continuity')
    scenario['name'] += '; photo candidate I7/A0=E4 high, I0/A1=E2 low'
    e4 = ('photo-i7-constraint.json U11/U10 E4 -> U6 D0/Q0 -> U2 I7/A0; '
          'constant high is a diagnostic latch-level assumption')
    e2 = ('photo candidate U10 E2 -> U5 D0/Q0 -> U2 I0; U2 A1 shares '
          'E2-side net; constant low is a diagnostic latch-level assumption')
    def level(value, evidence):
        return dict(value=value, status='hypothesis', evidence=evidence)
    scenario['inputs']['instruction_bit_overrides'] = {
        '7': level(1, e4), '0': level(0, e2)}
    scenario['inputs']['register_address_bit_overrides'] = {
        'a': {'0': level(1, e4), '1': level(0, e2)}}
    return mapping, scenario


def run(out):
    out.mkdir(parents=True, exist_ok=True)
    mapping, scenario = fixture()
    sweep = []
    for q in range(256):
        candidate = copy.deepcopy(scenario)
        candidate['initial']['q'] = q
        result = execute(mapping, candidate, SEED_CYCLES, mode='integrated',
                         trace_limit=0)
        sweep.append(dict(q=q, clean=result['clean'],
                          visits_38e=result['address_counts'].get(INPUT_PC, 0),
                          final_pc=result['final_state']['pc']))
    if any(not row['clean'] for row in sweep):
        raise ValueError('startup sweep contains a model stop')

    seed_outputs = []
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary)
        for q in (row['q'] for row in sweep if row['visits_38e']):
            for bit in (0, 1):
                candidate = copy.deepcopy(scenario)
                candidate['initial']['q'] = q
                candidate['io']['read']['pc_sequences'][str(INPUT_PC)] = [bit]
                result = execute(mapping, candidate, SEED_CYCLES, mode='integrated',
                                 out=path, trace_limit=SEED_CYCLES)
                trace = [json.loads(line) for line in
                         (path / 'trace.jsonl').read_text().splitlines()]
                groups = groups_for(trace)
                first_dispatch = next(row['cycle'] for row in trace
                                      if row['pc'] == DISPATCH_PC)
                rom_reads = [row for row in trace if row.get('external_read', {}).get(
                    'selected_by_alu') and 'address' in row['external_read']]
                seed_outputs.append(dict(q=q, bit=bit, clean=result['clean'],
                                         group_count=len(groups),
                                         distinct_groups=sorted({tuple(group['bytes'])
                                                                 for group in groups}),
                                         dispatch_indices=sorted({group['index']
                                                                  for group in groups}),
                                         final_q=result['final_state']['q'],
                                         rom_reads=len(rom_reads),
                                         rom_reads_after_first_dispatch=sum(
                                             row['cycle'] > first_dispatch
                                             for row in rom_reads)))
    if any(not row['clean'] or row['group_count'] < 2 for row in seed_outputs):
        raise ValueError('active startup seed lacks a repeated group')
    index_rule_holds = all(row['dispatch_indices'] == [(row['bit'] - row['q']) & 255]
                           for row in seed_outputs)
    constant_per_seed_bit = all(len(row['distinct_groups']) == 1 and
                                row['final_q'] == row['q'] for row in seed_outputs)

    shift_inputs = []
    for q_in in (0, 1):
        for ram_in in (0, 1):
            candidate = copy.deepcopy(scenario)
            candidate['inputs']['q_in'] = q_in
            candidate['inputs']['ram_in'] = ram_in
            result = execute(mapping, candidate, SEED_CYCLES, mode='integrated',
                             trace_limit=0)
            shift_inputs.append(dict(q_in=q_in, ram_in=ram_in,
                                     visits_38e=result['address_counts'].get(INPUT_PC, 0),
                                     final_pc=f'{result["final_state"]["pc"]:03X}',
                                     final_q=result['final_state']['q']))

    _, bits = controller_stream()
    scenario['initial']['q'] = 5
    scenario['io']['read']['pc_sequences'][str(INPUT_PC)] = bits
    result = execute(mapping, scenario, STREAM_CYCLES, mode='integrated',
                     out=out, trace_limit=STREAM_CYCLES)
    trace = [json.loads(line) for line in (out / 'trace.jsonl').read_text().splitlines()]
    reads = [row['external_read']['value'] for row in trace
             if row['pc'] == INPUT_PC]
    groups = groups_for(trace)
    states = post_group_states(trace, scenario['initial']['ram'])
    if not result['clean'] or reads != bits or len(groups) != len(bits) or len(states) != len(bits):
        raise ValueError('controller stream did not produce one complete group per bit')
    outputs = defaultdict(set)
    indexes = defaultdict(set)
    state_variants = defaultdict(set)
    for bit, group, state in zip(bits, groups, states):
        outputs[bit].add(tuple(group['bytes']))
        indexes[bit].add(group['index'])
        state_variants[bit].add(json.dumps(state, sort_keys=True))
    if set(bits) != {0, 1}:
        raise ValueError('controller stimulus lacks both bit values')

    byte_values = list(range(256)) + list(range(255, -1, -1))
    byte_scenario = copy.deepcopy(scenario)
    byte_scenario['name'] += '; ascending and descending byte-valued D sweep'
    byte_scenario['io']['read']['pc_sequences'][str(INPUT_PC)] = byte_values
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary)
        byte_result = execute(mapping, byte_scenario, 6192, mode='integrated',
                              out=path, trace_limit=6192)
        byte_trace = [json.loads(line) for line in
                      (path / 'trace.jsonl').read_text().splitlines()]
    byte_reads = [row['external_read']['value'] for row in byte_trace
                  if row['pc'] == INPUT_PC]
    byte_groups = groups_for(byte_trace)
    byte_states = post_group_states(byte_trace, byte_scenario['initial']['ram'])
    if (not byte_result['clean'] or byte_reads != byte_values or
            len(byte_groups) != 512 or len(byte_states) != 512):
        raise ValueError('byte D sweep did not complete all dispatch groups')
    byte_group_by_mod4 = {
        str(mod): sorted({tuple(group['bytes']) for value, group in
                          zip(byte_values, byte_groups) if value % 4 == mod})
        for mod in range(4)}
    byte_state_repeats = all(byte_states[i] == byte_states[511-i]
                             for i in range(256))

    gate_cases = []
    gate_scenario = copy.deepcopy(scenario)
    gate_scenario['io']['read']['pc_sequences'].pop(str(INPUT_PC), None)
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary)
        for gate in read(GATE_FITS)['fits']:
            gate_scenario['io']['read']['address']['pcs'] = gate['pcs']
            gate_result = execute(mapping, gate_scenario, SEED_CYCLES,
                                  mode='integrated', out=path,
                                  trace_limit=SEED_CYCLES)
            gate_trace = [json.loads(line) for line in
                          (path / 'trace.jsonl').read_text().splitlines()]
            gate_groups = groups_for(gate_trace)
            first_dispatch = next(row['cycle'] for row in gate_trace
                                  if row['pc'] == DISPATCH_PC)
            gate_rom_reads = [row for row in gate_trace if
                              row.get('external_read', {}).get('selected_by_alu')
                              and 'address' in row['external_read']]
            gate_cases.append(dict(terms=gate['terms'], clean=gate_result['clean'],
                                   groups=len(gate_groups),
                                   distinct_groups=len({tuple(group['bytes'])
                                                        for group in gate_groups}),
                                   rom_reads_after_first_dispatch=sum(
                                       row['cycle'] > first_dispatch
                                       for row in gate_rom_reads),
                                   trace_digest=gate_result['trace_digest']))
    if len(gate_cases) != 137 or any(not case['clean'] for case in gate_cases):
        raise ValueError('diagnostic ROM gate screen incomplete')

    source_paths = [Path(__file__), BASE_MAPPING, BASE_SCENARIO, PHOTO_RECORD,
                    PHOTO_A_RECORD, GATE_FITS,
                    HERE / 'controller_bit_dispatch.py', ASSUMED / 'execute.py']
    report = dict(status='photo-informed-diagnostic-not-transmitter-proof',
                  seed_sweep=dict(cycles=SEED_CYCLES, initial_ram=[0]*16,
                                  q_values=256, active_q=[row['q'] for row in sweep
                                                        if row['visits_38e']],
                                  active_q_modulo_8=sorted({row['q'] % 8 for row in sweep
                                                            if row['visits_38e']}),
                                  counts_by_final_pc=dict(Counter(f'{row["final_pc"]:03X}'
                                                                  for row in sweep)),
                                  rows=sweep, shift_input_cases=shift_inputs,
                                  repeated_bit_output_cases=seed_outputs,
                                  index_is_bit_minus_initial_q_mod_256=index_rule_holds,
                                  each_seed_bit_has_fixed_output_and_q=constant_per_seed_bit,
                                  no_repeated_rom_read_after_first_dispatch=all(
                                      row['rom_reads_after_first_dispatch'] == 0
                                      for row in seed_outputs)),
                  controller_stream=dict(bits=len(bits), zero_bits=bits.count(0),
                                         one_bits=bits.count(1), seed_q=5,
                                         hypothetical_input_pc=f'{INPUT_PC:03X}',
                                         dispatch_pc=f'{DISPATCH_PC:03X}',
                                         reads=len(reads), groups=len(groups),
                                         index_by_bit={str(bit): sorted(indexes[bit])
                                                       for bit in (0, 1)},
                                         alu_y_by_bit={str(bit): sorted(map(list, outputs[bit]))
                                                       for bit in (0, 1)},
                                         distinct_post_group_states_by_bit={
                                             str(bit): len(state_variants[bit])
                                             for bit in (0, 1)},
                                         distinct_post_group_states=len(
                                             state_variants[0] | state_variants[1]),
                                         trace_digest=result['trace_digest'],
                                         final_pc=f'{result["final_state"]["pc"]:03X}'),
                  byte_sweep=dict(values=512, unique_values=256,
                                  ascending_then_descending=True,
                                  initial_q=5,
                                  index_is_d_minus_q_mod_256=all(
                                      group['index'] == ((value - 5) & 255)
                                      for value, group in zip(byte_values, byte_groups)),
                                  entry_counts=dict(Counter(group['first_pc']
                                                            for group in byte_groups)),
                                  alu_y_by_d_mod_4={key: list(map(list, groups))
                                                    for key, groups in
                                                    byte_group_by_mod4.items()},
                                  same_post_group_state_on_reverse_replay=
                                      byte_state_repeats,
                                  distinct_post_group_states=len({
                                      json.dumps(state, sort_keys=True)
                                      for state in byte_states}),
                                  trace_digest=byte_result['trace_digest']),
                  diagnostic_rom_gates=dict(count=len(gate_cases),
                      cycle_limit=SEED_CYCLES, initial_q=5,
                      all_reach_repeated_dispatch=all(case['groups'] > 1
                                                      for case in gate_cases),
                      none_reads_rom_after_first_dispatch=all(
                          case['rom_reads_after_first_dispatch'] == 0
                          for case in gate_cases),
                      none_has_changing_output_group=all(
                          case['distinct_groups'] == 1 for case in gate_cases),
                      cases=gate_cases),
                  source_sha256={str(path.relative_to(HERE.parent)):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in source_paths},
                  limitations=[
                      'A2/A3 and E4/E2 latch routes are photo candidates, not measured nets.',
                      'Fixed E4/E2 levels, initial Q=5, branch tables, ROM gate and '
                      'one controller bit per 38E read are diagnostic assumptions.',
                      'The four-word values are ALU Y; the physical DAC path and sample clock '
                      'remain unidentified.',
                      'The four-way byte response is compatible with several functions; '
                      'the D bus source is not identified.',
                      'The fixed response per input value is not evidence of a carrier, '
                      'phase accumulator, pulse shaping or receiver/echo processing.'])
    save(out / 'report.json', report)
    return report


if __name__ == '__main__':
    report = run(HERE / 'results/photo-controller-path')
    print('Q seeds reaching 38E:', len(report['seed_sweep']['active_q']))
    print('Per-bit ALU Y:', report['controller_stream']['alu_y_by_bit'])
