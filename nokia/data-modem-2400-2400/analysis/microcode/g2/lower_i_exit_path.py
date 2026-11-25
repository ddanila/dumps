"""Follow input-sensitive 3ED–3FA exits under two flag-timing hypotheses."""

import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent/'assumed'), str(HERE)]

from common import save
from controller_bit_dispatch import controller_stream
from lower_i_d3f8_input import run_trace
from lower_i_prom_data_route import mapping_for
from photo_controller_path import fixture


def first(trace, pc):
    return next((index for index, row in enumerate(trace) if row['pc'] == pc), None)


def summarize(result, virtual_write_pcs):
    trace = result['trace']
    exit_cycle = first(trace, 0x3EE)
    drain_cycle = first(trace, 0x1E9)
    poll_cycle = first(trace, 0x1EC)
    writes = [(row['cycle'], f"{row['pc']:03X}", row['alu']['y'])
              for row in trace if row['pc'] in virtual_write_pcs]
    answer = dict(d3f8_visits=result['site_visits'],
                  first_3ee_cycle=exit_cycle,
                  first_1e9_cycle=drain_cycle,
                  first_1ec_cycle=poll_cycle,
                  virtual_output_events=writes,
                  final_pc=f"{result['result']['final_state']['pc']:03X}",
                  trace_digest=result['result']['trace_digest'])
    if exit_cycle is not None:
        producer, test, ret = trace[exit_cycle-2:exit_cycle+1]
        if (producer['pc'], test['pc'], ret['pc']) != (0x3FA, 0x3ED, 0x3EE):
            raise ValueError('unexpected 3EE producer/test/return sequence')
        answer['exit'] = dict(producer_zero=producer['alu']['zero'],
                              producer_y=producer['alu']['y'],
                              test=test['test'],
                              test_next_pc=f"{test['next_pc']:03X}",
                              return_next_pc=f"{ret['next_pc']:03X}",
                              stack_depth_after_return=ret['stack_after']['depth'])
    if drain_cycle is not None:
        tail = trace[-256:]
        answer['tail'] = dict(pcs=sorted({f"{row['pc']:03X}" for row in tail}),
                              q_values=sorted({row['q'] for row in tail}),
                              selected_d_reads=sum(row['external_read']['selected_by_alu']
                                                   for row in tail),
                              virtual_output_events=sum(row['pc'] in virtual_write_pcs
                                                        for row in tail),
                              tests_at_1ea=sorted({row['test'] for row in tail
                                                   if row['pc'] == 0x1EA}))
    return answer


def run(out=HERE/'results/lower-i-exit-path.json'):
    _, base = fixture()
    mapping = mapping_for('!10.6', '11.2')
    _, bits = controller_stream()
    writes = {entry['pc'] for entry in base['io']['writes']}
    cases = {}
    for timing in ('previous', 'current'):
        scenario = dict(base)
        scenario['condition'] = dict(base['condition'], flag_timing=timing)
        baseline = run_trace(mapping, scenario, 0x3F8, [1]*192)
        cases[timing] = {'baseline': summarize(baseline, writes),
                         'lanes': {}}
        for lane in (1, 2, 3):
            pulse = [1]*192
            pulse[20] = 1 | (1 << lane)
            stream = [1 | (bit << lane) for bit in bits]
            cases[timing]['lanes'][str(lane)] = {
                'pulse': summarize(run_trace(mapping, scenario, 0x3F8, pulse), writes),
                'controller': summarize(run_trace(mapping, scenario, 0x3F8, stream), writes)}

    previous = cases['previous']
    current = cases['current']
    if previous['baseline']['first_3ee_cycle'] is not None:
        raise ValueError('previous-flag baseline unexpectedly exits')
    for lane, expected_pulse, expected_stream in ((1, 291, 267),
                                                   (2, 243, 347),
                                                   (3, 315, 467)):
        for kind, expected in (('pulse', expected_pulse),
                               ('controller', expected_stream)):
            case = previous['lanes'][str(lane)][kind]
            if (case['first_3ee_cycle'] != expected or
                    case['exit']['producer_zero'] != 1 or
                    case['exit']['test'] != 0 or
                    case['exit']['test_next_pc'] != '3EE' or
                    case['exit']['return_next_pc'] != '18D' or
                    case['tail'] != dict(pcs=['1E9', '1EA'], q_values=[0],
                                         selected_d_reads=0, virtual_output_events=0,
                                         tests_at_1ea=[1]) or
                    case['virtual_output_events']):
                raise ValueError(f'previous-flag exit path changed: {lane} {kind}')
    current_baseline = current['baseline']
    if (current_baseline['d3f8_visits'] != 2 or
            current_baseline['first_3ee_cycle'] != 59 or
            current_baseline['first_1ec_cycle'] != 189 or
            len(current_baseline['virtual_output_events']) != 4):
        raise ValueError('current-flag baseline changed')
    for lane in (1, 2, 3):
        case = current['lanes'][str(lane)]['controller']
        if case['trace_digest'] != current_baseline['trace_digest']:
            raise ValueError(f'controller stream unexpectedly affects current-flag lane {lane}')

    paths = [Path(__file__), HERE/'lower_i_d3f8_input.py',
             HERE/'lower_i_prom_data_route.py', HERE/'controller_bit_dispatch.py',
             HERE/'photo_controller_path.py', HERE.parent/'assumed/execute.py']
    report = dict(status='conditional 3EE exit and downstream timing comparison',
                  fixture=dict(mapping='I7/A0=!10.6, I0/A1=11.2, lower I6=11.0',
                               initial_q=5, d3f8_base_byte=1, pulse_visit=20,
                               controller_bits=len(bits), cycles=1580,
                               flag_timing=['previous', 'current'],
                               virtual_output_sites=sorted(f'{pc:03X}' for pc in writes)),
                  cases=cases,
                  limitations=[
                      'PROM-to-Am2901 and D3F8 physical routes and both flag timings remain hypotheses.',
                      'Virtual output events are ALU-Y captures at assumed sites, not DAC08 input samples.',
                      'No sustained controller-driven transmitter or decoded receive bit is demonstrated.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    for timing, cases in result['cases'].items():
        print(timing, 'baseline visits', cases['baseline']['d3f8_visits'])
        for lane, variants in cases['lanes'].items():
            print(lane, 'pulse/stream exits', variants['pulse']['first_3ee_cycle'],
                  variants['controller']['first_3ee_cycle'])
