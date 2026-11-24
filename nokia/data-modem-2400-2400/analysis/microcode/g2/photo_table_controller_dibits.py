"""Drive reached sign tables with controller-ROM dibits at predecessor words."""

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
from common import read, save
from execute import execute
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from photo_table_callers import reached_calls, scenario_for
from photo_table_exact_transform import expected

CONTROLLER = HERE / 'results/main-loop-serial.json'
PREDECESSOR = {0x3C2: 0x3C1, 0x3D7: 0x3D6}
SEEDS = (11, 14)
CYCLES = 300


def dibits_from_bytes(values):
    return [(byte >> shift) & 3 for byte in values for shift in (0, 2, 4, 6)]


def live_dispatch(scenario):
    scenario['dispatch']['initial_y'] = 0
    for site in PREDECESSOR:
        scenario['dispatch']['tables'][str(site)]['index_source'] = 'previous_y'
        scenario['dispatch']['tables'][str(site)]['evidence'] += (
            '; diagnostic predecessor-ALU-Y branch-bus hypothesis')
    return scenario


def trace_run(mapping, scenario, seed, directory):
    result = execute(mapping, scenario, CYCLES, seed=seed,
                     mode='integrated', out=directory, trace_limit=CYCLES)
    trace = [json.loads(line) for line in
             (directory / 'trace.jsonl').read_text().splitlines()]
    if not result['clean']:
        raise ValueError(f'microcode stopped for seed {seed}')
    return result, trace


def run(out=HERE / 'results/photo-table-controller-dibits.json'):
    controller = read(CONTROLLER)
    if controller['distinct_streams'] != 4:
        raise ValueError('controller stream groups changed')
    streams = [(group['selectors'][0], group['line_bytes'])
               for group in controller['groups']]
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary)
        for name, mapping_path in MAPPINGS.items():
            mapping = mapped(mapping_path)
            for seed in SEEDS:
                baseline = live_dispatch(scenario_for(1, 0))
                _, control_trace = trace_run(mapping, baseline, seed, path)
                order = [row['pc'] for row in control_trace
                         if row['pc'] in PREDECESSOR]
                if not order or set(order) != set(PREDECESSOR):
                    raise ValueError(f'{name} seed {seed}: no two-table baseline')
                for stream_name, line_bytes in streams:
                    dibits = dibits_from_bytes(line_bytes)
                    offered = dibits[:len(order)]
                    per_pc = {pc: [] for pc in PREDECESSOR.values()}
                    for site, dibit in zip(order, offered):
                        per_pc[PREDECESSOR[site]].append(dibit)
                    scenario = live_dispatch(scenario_for(1, 0))
                    scenario['name'] += f'; controller dibits {stream_name} at table predecessors'
                    scenario['io']['read'].update(
                        mode='pc_sequence', sequence_end='hold-last',
                        status='hypothesis',
                        evidence='LSB-first dibits from actual 8031 USART-01 bytes, assigned in baseline chronological table-call order to candidate D3D6/D3C1 inputs; untraced routing and timing.',
                        pc_sequences={str(pc): values for pc, values in per_pc.items()})
                    result, trace = trace_run(mapping, scenario, seed, path)
                    actual_order = [row['pc'] for row in trace
                                    if row['pc'] in PREDECESSOR]
                    if actual_order != order:
                        raise ValueError(f'{name} seed {seed}: entry changes predecessor order')
                    predecessor_rows = [row for row in trace
                                        if row['pc'] in PREDECESSOR.values()]
                    calls = [row for row in trace if row['pc'] in PREDECESSOR]
                    if len(calls) != len(offered):
                        raise ValueError('one controller dibit per computed call required')
                    observations = reached_calls(trace, scenario)
                    if len(observations) != len(offered):
                        raise ValueError('table-call reconstruction incomplete')
                    for dibit, predecessor, call, observation in zip(
                            offered, predecessor_rows, calls, observations):
                        if (predecessor['external_read']['value'] != dibit or
                                call['dispatch_input'] != predecessor['alu']['y'] or
                                call['dispatch_entry'] != (predecessor['alu']['y'] & 3) or
                                observation['entry'] != call['dispatch_entry'] or
                                tuple(observation['output_after']) !=
                                expected(observation['source'], observation['entry'])):
                            raise ValueError(
                                f'{name} seed={seed} stream={stream_name} '
                                f'dibit={dibit} predecessor={predecessor["pc"]:03X}/'
                                f'{predecessor["alu"]["y"]} '
                                f'call={call["pc"]:03X}/{call["dispatch_input"]}/'
                                f'{call["dispatch_entry"]} observation={observation}')
                    cases.append(dict(mapping=name, scenario_seed=seed,
                                      controller_stream=stream_name,
                                      line_bytes=line_bytes, dibits_offered=offered,
                                      predecessor_order=[f'{pc:03X}' for pc in order],
                                      calls=[dict(site=x['site'], input_dibit=dibit,
                                                  predecessor_y=predecessor['alu']['y'],
                                                  entry=x['entry'],
                                                  source=x['source'],
                                                  output_after=x['output_after'])
                                             for dibit, predecessor, x in zip(
                                                 offered, predecessor_rows, observations)],
                                      distinct_output_pairs=len({tuple(x['output_after'])
                                                                 for x in observations}),
                                      final_pc=f'{result["final_state"]["pc"]:03X}',
                                      trace_digest=result['trace_digest']))
    mapping_summaries = {}
    for name in MAPPINGS:
        calls = [call for case in cases if case['mapping'] == name
                 for call in case['calls']]
        mapping_summaries[name] = dict(
            calls=len(calls),
            offered_dibits=sorted({call['input_dibit'] for call in calls}),
            selected_entries=sorted({call['entry'] for call in calls}),
            direct_dibit_matches=sum(call['entry'] == call['input_dibit']
                                     for call in calls),
            input_to_entries={str(dibit): sorted({call['entry'] for call in calls
                                                  if call['input_dibit'] == dibit})
                              for dibit in range(4)})
    if (any(mapping_summaries[name]['direct_dibit_matches'] !=
            mapping_summaries[name]['calls'] for name in ('q1', 'q3')) or
            any(mapping_summaries[name]['selected_entries'] != [3]
                for name in ('q2', 'q4', 'fitted_swapped'))):
        raise ValueError('cross-mapping D-to-table-entry separation changed')
    paths = [Path(__file__), CONTROLLER, HERE / 'main_loop_serial.py',
             HERE / 'photo_table_callers.py',
             HERE / 'photo_table_exact_transform.py',
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             ASSUMED / 'results/rotation-study/scenario-3.json',
             ASSUMED / 'execute.py', ASSUMED / 'caller_study.py',
             HERE.parent / 'model.py', *MAPPINGS.values()]
    report = dict(status='conditional controller-dibit to sign-table execution, not recovered physical wiring',
                  fixture=dict(controller_source='unchanged 8031 main-loop USART-01 output',
                               controller_streams=[name for name, _ in streams],
                               bit_order='LSB first, adjacent bits form low-two-bit D value',
                               candidate_d_sites=['3D6', '3C1'],
                               candidate_dispatch_source='previous ALU Y at 3D7 and 3C2',
                               other_dispatch_and_conditions='saved random rotation-study scenario',
                               other_external_d=0, initial_ram=[0]*16,
                               e4_i7_a0=1, e2_i0_a1=0, cycles=CYCLES),
                  cases=cases,
                  mapping_summaries=mapping_summaries,
                  totals=dict(runs=len(cases), calls=sum(len(x['calls']) for x in cases),
                              entry_counts=dict(Counter(str(call['entry'])
                                  for case in cases for call in case['calls'])),
                              final_pcs=dict(Counter(x['final_pc'] for x in cases))),
                  limitations=[
                      'The USART-01-to-D3D6/D3C1 route and two bits per table call are timing and wiring hypotheses.',
                      'The previous-Y branch bus is not traced; upstream dispatches and conditions remain scenario-driven.',
                      'Only a short reset prefix is exercised; it does not continue as a modem sample loop.',
                      'The held photo pin levels and shared Am2901 controls may differ from the physical board.',
                      'RAM output pairs 10/12 are not traced to the DAC08.'],
                  source_sha256={str(p.relative_to(HERE.parent)):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    print(report['totals'])
