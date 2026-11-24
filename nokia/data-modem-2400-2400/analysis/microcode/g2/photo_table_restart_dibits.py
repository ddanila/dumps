"""Repeat controller-fed sign-table calls through a diagnostic 8X02 RST pulse."""

import hashlib
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
from common import read, save
from execute import execute
from model import X8X02
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from photo_table_callers import reached_calls, scenario_for
from photo_table_controller_dibits import (CONTROLLER, PREDECESSOR,
                                           dibits_from_bytes, live_dispatch)
from photo_table_exact_transform import expected

MAPPING_NAMES = ('q1', 'q3')
SEEDS = (11, 14)
CYCLES = 2500
RST_PULSES = 15


def trace_run(mapping, scenario, seed, directory):
    original = X8X02.step
    restarts = []

    def step(sequencer, command, branch=0, test=False):
        if sequencer.pc == 0x084 and command == 6 and len(restarts) < RST_PULSES:
            restarts.append(dict(sp=sequencer.sp, pushes=sequencer.pushes,
                                 pops=sequencer.pops, stack=sequencer.stack[:]))
            return original(sequencer, 7, branch, test)
        return original(sequencer, command, branch, test)

    with patch.object(X8X02, 'step', step):
        result = execute(mapping, scenario, CYCLES, seed=seed,
                         mode='integrated', out=directory, trace_limit=CYCLES)
    trace = [json.loads(line) for line in
             (directory / 'trace.jsonl').read_text().splitlines()]
    if (not result['clean'] or len(restarts) != RST_PULSES or
            result['final_state']['pc'] != 0x084 or
            any(x['sp'] != 0 or x['pushes'] != x['pops'] for x in restarts)):
        raise ValueError('diagnostic restart or stack contract changed')
    return result, trace, restarts


def run(out=HERE / 'results/photo-table-restart-dibits.json'):
    controller = read(CONTROLLER)
    streams = [(group['selectors'][0], group['line_bytes'])
               for group in controller['groups']]
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary)
        for name in MAPPING_NAMES:
            mapping = mapped(MAPPINGS[name])
            for seed in SEEDS:
                baseline = live_dispatch(scenario_for(1, 0))
                _, control_trace, _ = trace_run(mapping, baseline, seed, path)
                order = [row['pc'] for row in control_trace
                         if row['pc'] in PREDECESSOR]
                if not order or set(order) != set(PREDECESSOR):
                    raise ValueError('restart baseline lacks both table calls')
                for stream_name, line_bytes in streams:
                    dibits = dibits_from_bytes(line_bytes)
                    if len(order) > len(dibits):
                        raise ValueError('controller stream too short for reached calls')
                    offered = dibits[:len(order)]
                    per_pc = {pc: [] for pc in PREDECESSOR.values()}
                    for site, dibit in zip(order, offered):
                        per_pc[PREDECESSOR[site]].append(dibit)
                    scenario = live_dispatch(scenario_for(1, 0))
                    scenario['name'] += f'; controller dibits {stream_name}; AC=RST at first 15 arrivals to 084'
                    scenario['io']['read'].update(
                        mode='pc_sequence', sequence_end='hold-last',
                        status='hypothesis',
                        evidence='Actual 8031 USART-01 dibits assigned in baseline call order to candidate D3D6/D3C1; untraced input and timing.',
                        pc_sequences={str(pc): values for pc, values in per_pc.items()})
                    result, trace, restarts = trace_run(mapping, scenario, seed, path)
                    actual_order = [row['pc'] for row in trace
                                    if row['pc'] in PREDECESSOR]
                    if actual_order != order:
                        raise ValueError('controller dibits changed call order')
                    predecessor_rows = [row for row in trace
                                        if row['pc'] in PREDECESSOR.values()]
                    calls = [row for row in trace if row['pc'] in PREDECESSOR]
                    observations = reached_calls(trace, scenario)
                    if len(observations) != len(offered):
                        raise ValueError('restart table reconstruction incomplete')
                    for dibit, predecessor, call, observation in zip(
                            offered, predecessor_rows, calls, observations):
                        if (predecessor['external_read']['value'] != dibit or
                                predecessor['alu']['y'] != dibit or
                                call['dispatch_input'] != dibit or
                                call['dispatch_entry'] != dibit or
                                observation['entry'] != dibit or
                                tuple(observation['output_after']) !=
                                expected(observation['source'], dibit)):
                            raise ValueError('restarted controller-to-table chain changed')
                    cases.append(dict(mapping=name, scenario_seed=seed,
                                      controller_stream=stream_name,
                                      line_bytes=line_bytes,
                                      offered_dibits=offered,
                                      restart_cycles=[row['cycle'] for row in trace
                                                      if row['pc'] == 0x084][:RST_PULSES],
                                      calls=[dict(cycle=x['cycle'], site=x['site'],
                                                  entry=x['entry'], source=x['source'],
                                                  output_after=x['output_after'])
                                             for x in observations],
                                      distinct_sources=len({tuple(x['source'])
                                                            for x in observations}),
                                      distinct_outputs=len({tuple(x['output_after'])
                                                            for x in observations}),
                                      final_pc='084',
                                      trace_digest=result['trace_digest']))
    paths = [Path(__file__), CONTROLLER, HERE / 'terminal_command_probe.py',
             HERE / 'photo_table_controller_dibits.py',
             HERE / 'photo_table_exact_transform.py',
             HERE / 'photo_table_callers.py',
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             ASSUMED / 'results/rotation-study/scenario-3.json',
             ASSUMED / 'execute.py', ASSUMED / 'caller_study.py',
             HERE.parent / 'model.py', *(MAPPINGS[name] for name in MAPPING_NAMES)]
    report = dict(status='bounded diagnostic restart and controller-dibit table replay, not Nokia wiring',
                  fixture=dict(mappings=list(MAPPING_NAMES), seeds=list(SEEDS),
                               controller_streams=[name for name, _ in streams],
                               cycles=CYCLES, rst_pulses=RST_PULSES,
                               rst_trigger='first 15 arrivals to internal PC 084 replace BRT with AC=111',
                               datapath_and_stack='preserved across RST',
                               candidate_d_sites=['3D6', '3C1'],
                               candidate_dispatch_source='previous ALU Y at 3D7 and 3C2',
                               other_dispatch_and_conditions='saved random rotation-study scenario',
                               e4_i7_a0=1, e2_i0_a1=0),
                  cases=cases,
                  totals=dict(runs=len(cases), calls=sum(len(x['calls']) for x in cases),
                              call_counts=dict(Counter(str(len(x['calls'])) for x in cases)),
                              source_diversity=dict(Counter(str(x['distinct_sources']) for x in cases)),
                              output_diversity=dict(Counter(str(x['distinct_outputs']) for x in cases))),
                  limitations=[
                      'No Nokia AC command override at 084 is established; 8X02 RST is an explicit counterfactual.',
                      'The USART-to-D and predecessor-Y-to-branch routes, photo-pin levels and timing are hypotheses.',
                      'Only the first 15 terminal arrivals are restarted; this is not a natural continuous modem call.',
                      'The fixture uses no Am27S31 read policy or traced DAC route; table output pairs are RAM state, not line samples.',
                      'Upstream branch and dispatch decisions remain saved scenario inputs.'],
                  source_sha256={str(p.relative_to(HERE.parent)):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    print(report['totals'])
