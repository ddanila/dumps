"""Feed ROM-executed 8031 scrambled bits to candidate DSC2847 dispatch input 38E."""
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE.parents[1]
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ANALYSIS), str(ASSUMED), str(HERE)]
from common import read, save
from execute import execute
from interface_study import CORE, ROM as CONTROLLER_ROM, SHA as CONTROLLER_SHA
from controller_scrambler import transform
from sine_operand_study import scenario_for_phase
from photo_b_constraints import swapped

INPUT_PC = 0x38E
DISPATCH_PC = 0x38F
INITIAL_HISTORY = 0x654321
STREAM_BYTES = 16
CYCLES = 1580  # Includes the fourth output word after the 128th dispatch.


def controller_stream():
    if hashlib.sha256(CONTROLLER_ROM.read_bytes()).hexdigest() != CONTROLLER_SHA:
        raise ValueError('controller ROM hash mismatch')
    source = ANALYSIS / 'interface_probe.c'
    with tempfile.TemporaryDirectory() as temporary:
        executable = Path(temporary) / 'controller-probe'
        subprocess.run(['cc', '-O2', '-Wall', '-DSAT_TRACE', '-I', str(CORE),
                        str(source), *(str(CORE / name) for name in
                        ('core.c', 'opcodes.c', 'disasm.c')), '-o', str(executable)],
                       check=True, capture_output=True, text=True)
        history = INITIAL_HISTORY
        lines = []
        predictions = []
        for _ in range(STREAM_BYTES):
            frame = bytes([history >> 16, (history >> 8) & 255, history & 255,
                           0, 0, 2])
            lines.append('scram ' + frame.hex() + ' 000000000000 8 0\n')
            history, value = transform(history, 0, 18)
            predictions.append((history, value))
        result = subprocess.run([str(executable), str(CONTROLLER_ROM), '248',
                                 '0', '256', '8192', '113'], input=''.join(lines),
                                capture_output=True, text=True, check=True)
    executions = [json.loads(line) for line in result.stdout.splitlines()]
    if len(executions) != STREAM_BYTES:
        raise ValueError('missing controller byte execution')
    outputs = []
    for row, (expected_history, expected_value) in zip(executions, predictions):
        ram = row['iram']
        actual_history = (ram[0x3f] << 16) | (ram[0x40] << 8) | ram[0x41]
        if (row['errors'] or not row['returned'] or
                (actual_history, ram[0x38]) != (expected_history, expected_value)):
            raise ValueError('controller ROM scrambler differs from bit reference')
        outputs.append(expected_value)
    bits = [(value >> bit) & 1 for value in outputs for bit in range(8)]
    return outputs, bits


def groups_for(trace):
    groups = []
    for row in trace:
        if row['pc'] != DISPATCH_PC:
            continue
        first = row['next_pc']
        tail = trace[row['cycle'] + 1:row['cycle'] + 5]
        if [item['pc'] for item in tail] != list(range(first, first + 4)):
            raise ValueError('dispatch did not enter a complete four-word group')
        groups.append(dict(cycle=row['cycle'], index=row['dispatch_input'],
                           first_pc=f'{first:03X}', bytes=[item['alu']['y'] for item in tail]))
    return groups


def post_group_states(trace, initial_ram):
    ram = initial_ram[:]
    states = []
    for row in trace:
        for address, value in row['registers'].items():
            ram[int(address)] = value
        if row['pc'] == 0x390:
            states.append(dict(ram=ram[:], q=row['q'], flags=row['alu'],
                               stack=row['stack_after'], next_pc=row['next_pc']))
    return states


def execute_bits(mapping, scenario, bits, cycles, path):
    fixture = copy.deepcopy(scenario)
    fixture['name'] = f'candidate D38E controller bits, {len(bits)} values'
    fixture['io']['read']['pc_sequences'][str(INPUT_PC)] = bits
    result = execute(mapping, fixture, cycles, mode='integrated',
                     out=path, trace_limit=cycles)
    trace = [json.loads(line) for line in (path / 'trace.jsonl').read_text().splitlines()]
    selected = [row for row in trace if row['pc'] == INPUT_PC]
    groups = groups_for(trace)
    if len(groups) != len(bits) or len(selected) != len(bits):
        raise ValueError('bitstream did not drive every output dispatch')
    if [row['external_read']['value'] for row in selected] != bits:
        raise ValueError('microcode did not receive the prescribed bits')
    if [group['index'] for group in groups] != bits:
        raise ValueError('input bits did not select the matching table entries')
    return result, groups


def run(out):
    out.mkdir(parents=True, exist_ok=True)
    values, bits = controller_stream()
    mapping_path = HERE / 'results/swapped-sine-loop/phase-20-mapping.json'
    scenario_path = HERE / 'results/swapped-sine-loop/phase-20-scenario.json'
    mapping = read(mapping_path)
    scenario = read(scenario_path)
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary)
        result, groups = execute_bits(mapping, scenario, bits, CYCLES, path)
        (out / 'controller-trace.jsonl').write_bytes((path / 'trace.jsonl').read_bytes())
        (out / 'controller-scenario.json').write_bytes((path / 'scenario.json').read_bytes())
        controller_trace = [json.loads(line) for line in (path / 'trace.jsonl').read_text().splitlines()]
        controller_states = post_group_states(controller_trace, scenario['initial']['ram'])
        zero_result, zero_groups = execute_bits(mapping, scenario, [0]*len(bits), CYCLES, path)
        zero_trace = [json.loads(line) for line in (path / 'trace.jsonl').read_text().splitlines()]
        zero_states = post_group_states(zero_trace, scenario['initial']['ram'])
    controller_state_variants = {json.dumps(state, sort_keys=True) for state in controller_states}
    zero_state_variants = {json.dumps(state, sort_keys=True) for state in zero_states}
    four_way = []
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary)
        for value in range(4):
            fixture = copy.deepcopy(scenario)
            fixture['io']['read']['pc_sequences'][str(INPUT_PC)] = [value]
            check = execute(mapping, fixture, 1020, mode='integrated',
                            out=path, trace_limit=1020)
            trace = [json.loads(line) for line in (path / 'trace.jsonl').read_text().splitlines()]
            entries = groups_for(trace)
            four_way.append(dict(value=value, first_entry=entries[0],
                                 entry_count=len(entries),
                                 final_pc=f'{check["final_state"]["pc"]:03X}',
                                 trace_digest=check['trace_digest']))
    config_path = ASSUMED / 'sine-operand-study.json'
    gate_path = ASSUMED / 'results/rom-gate-study/report.json'
    source_mapping_path = ASSUMED / 'results/independent-study/variant-3.json'
    config = read(config_path)
    gate = next(fit for fit in read(gate_path)['fits']
                if fit['terms'] == [['11.4', 0], ['18.5', 0]])
    phase_comparison = []
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary)
        for phase in range(65):
            fixture = scenario_for_phase(config, 'q3', phase)
            fixture['io']['read']['address']['pcs'] = gate['pcs']
            candidate = swapped(read(source_mapping_path))
            outcomes = []
            for bit in (0, 1):
                fixture['io']['read']['pc_sequences'][str(INPUT_PC)] = [bit]
                check = execute(candidate, fixture, 128, mode='integrated',
                                out=path, trace_limit=128)
                trace = [json.loads(line) for line in (path / 'trace.jsonl').read_text().splitlines()]
                first = groups_for(trace)[0]
                if not check['clean'] or first['index'] != bit:
                    raise ValueError('phase comparison did not dispatch as requested')
                outcomes.append(first['bytes'])
            phase_comparison.append(dict(phase=phase, bit_0=outcomes[0],
                                         bit_1=outcomes[1], equal=outcomes[0] == outcomes[1]))
    sources = [Path(__file__), ANALYSIS / 'interface_probe.c',
               ANALYSIS / 'controller_scrambler.py',
               *(CORE / name for name in ('core.c', 'opcodes.c', 'disasm.c', 'emu8051.h')),
               mapping_path, scenario_path, source_mapping_path, config_path,
               gate_path, HERE / 'photo_b_constraints.py',
               ASSUMED / 'sine_operand_study.py', ASSUMED / 'execute.py',
               ASSUMED / 'common.py', HERE.parent / 'model.py']
    report = dict(status='controller-derived-candidate-dispatch-not-G2-C2',
        controller_rom_sha256=CONTROLLER_SHA, input_bytes=[0]*STREAM_BYTES,
        initial_history=INITIAL_HISTORY, scrambled_bytes=values,
        bit_order='LSB first', bit_count=len(bits), bits=bits,
        cycle_limit=CYCLES, candidate_input_pc=f'{INPUT_PC:03X}',
        controller_groups=groups, zero_control_groups=zero_groups,
        output_equal_to_zero_control=([group['bytes'] for group in groups] ==
                                      [group['bytes'] for group in zero_groups]),
        post_group_state_count=len(controller_states),
        distinct_post_group_states=len(controller_state_variants),
        first_post_group_state=controller_states[0] if controller_states else None,
        post_group_states_equal_to_zero_control=controller_state_variants == zero_state_variants,
        four_way=four_way,
        phase_comparison=phase_comparison,
        controller_trace_digest=result['trace_digest'],
        zero_trace_digest=zero_result['trace_digest'],
        microcode_rom_hashes=result['rom_hashes'],
        am27s31_sha256=result['am27s31_hash'],
        source_sha256={str(path.relative_to(HERE.parents[4])):
                       hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
        limitations=['The 8031 scrambler routine is executed locally for each byte with history passed between calls; a full USART/main-loop transmission is not modeled.',
                     'One bit per 38E visit is a hypothetical interface and timing relation, not a traced connection.',
                     'The 38E D input and four-word ALU Y groups are not traced to the physical line DAC.',
                     'ROM gate, branch conditions, dispatch table and startup state remain diagnostic hypotheses.'])
    save(out / 'report.json', report)
    return report


if __name__ == '__main__':
    report = run(HERE / 'results/controller-bit-dispatch')
    print(report['bit_count'], 'controller bits;', len(report['controller_groups']),
          'microcode dispatches;', sum(not row['equal'] for row in report['phase_comparison']),
          'phase fixtures with distinct 0/1 output')
