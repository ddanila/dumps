"""Offer real controller bytes and dibits through a PROM-bit table/consumer route."""

import hashlib
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
import execute as executor
from common import read, save
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from photo_table_callers import reached_calls, scenario_for
from photo_table_controller_dibits import (CONTROLLER, PREDECESSOR,
                                           dibits_from_bytes, live_dispatch)
from photo_table_controller_source import table_output_flow
from photo_table_exact_transform import expected
from photo_table_phase_consumer import SEEDS, in_table
from photo_table_prombit_consumer import bit_decode
from photo_table_restart_dibits import trace_run


def scenario(read_sequences):
    state = live_dispatch(scenario_for(1, 0))
    state['name'] = state['name'].replace(
        'E2=0', 'I0/A1 from inverted U10 D5, U10 E2 held low')
    del state['inputs']['instruction_bit_overrides']['0']
    del state['inputs']['register_address_bit_overrides']['a']['1']
    state['io']['read'].update(
        mode='pc_sequence', value=0, sequence_end='hold-last',
        status='hypothesis',
        evidence='Actual 8031 USART-01 bytes at D349 and dibits at table predecessors by candidate visit schedules; routes untraced',
        pc_sequences=read_sequences)
    return state


def run(out=HERE / 'results/photo-table-prombit-symbols.json'):
    groups = read(CONTROLLER)['groups']
    mapping = mapped(MAPPINGS['q3'])
    cases = []
    with patch.object(executor, 'decode', bit_decode):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for seed in SEEDS:
                for group in groups:
                    selector = group['selectors'][0]
                    line_bytes = group['line_bytes']
                    _, baseline, _ = trace_run(
                        mapping, scenario({str(0x349): line_bytes}), seed, directory)
                    order = [row['pc'] for row in baseline if row['pc'] in PREDECESSOR]
                    dibits = dibits_from_bytes(line_bytes)
                    if not order or len(order) > len(dibits):
                        raise ValueError('controller stream cannot cover table calls')
                    offered = dibits[:len(order)]
                    sequences = {str(0x349): line_bytes,
                                 str(0x3C1): [], str(0x3D6): []}
                    for site, dibit in zip(order, offered):
                        sequences[str(PREDECESSOR[site])].append(dibit)
                    sequences = {pc: values for pc, values in sequences.items() if values}
                    state = scenario(sequences)
                    result, trace, restarts = trace_run(mapping, state, seed, directory)
                    calls = reached_calls(trace, state)
                    actual_order = [row['pc'] for row in trace if row['pc'] in PREDECESSOR]
                    predecessors = [row for row in trace
                                    if row['pc'] in PREDECESSOR.values()]
                    call_rows = [row for row in trace if row['pc'] in PREDECESSOR]
                    writes = [row for row in trace if row['pc'] == 0x349]
                    flow = table_output_flow(trace)
                    consumers = [dict(**event, alu_y=trace[event['cycle']]['alu']['y'])
                                 for event in flow['downstream_reads']
                                 if not in_table(int(event['pc'], 16))]
                    outputs = [row for row in trace if row['pc'] in (0x392, 0x39E)]
                    if (actual_order != order or len(calls) != len(offered) or
                            len(predecessors) != len(offered) or not consumers or
                            len(restarts) != 15 or
                            any(row['alu']['y'] != 0 for row in outputs)):
                        raise ValueError('combined controller route or candidate output changed')
                    for dibit, predecessor, call_row, call in zip(
                            offered, predecessors, call_rows, calls):
                        if (predecessor['external_read']['value'] != dibit or
                                predecessor['alu']['y'] != dibit or
                                call_row['dispatch_entry'] != dibit or
                                call['entry'] != dibit or
                                tuple(call['output_after']) !=
                                expected(call['source'], dibit)):
                            raise ValueError('dibit-to-table transform changed')
                    for index, row in enumerate(writes):
                        if (row['external_read']['value'] != line_bytes[index] or
                                row['registers'].get('5') != line_bytes[index] + 1):
                            raise ValueError('byte-to-R5 source update changed')
                    cases.append(dict(seed=seed, controller_selector=selector,
                                      controller_line_bytes=line_bytes,
                                      offered_dibits=offered,
                                      d349_visits=[dict(cycle=row['cycle'],
                                                        byte=row['external_read']['value'],
                                                        r5_write=row['registers'].get('5'))
                                                   for row in writes],
                                      table_calls=[dict(cycle=call['cycle'],
                                                        site=call['site'], entry=call['entry'],
                                                        source=call['source'],
                                                        output=call['output_after'])
                                                   for call in calls],
                                      consumers=consumers,
                                      output_candidates=[dict(cycle=row['cycle'],
                                                              pc=f"{row['pc']:03X}",
                                                              alu_y=row['alu']['y'])
                                                         for row in outputs],
                                      trace_digest=result['trace_digest']))
    entries = sorted({call['entry'] for case in cases for call in case['table_calls']})
    if entries != [0, 1, 2, 3]:
        raise ValueError('controller dibits no longer reach all table entries')
    witness = []
    for case in cases:
        if case['seed'] != 184:
            continue
        call = next(x for x in case['table_calls'] if x['cycle'] == 262)
        consumer = next(x for x in case['consumers']
                        if x['cycle'] == 271 and x['pc'] == '140')
        if consumer['alu_y'] != call['output'][0] >> 8:
            raise ValueError('post-table consumer byte differs from table output high')
        witness.append(dict(selector=case['controller_selector'],
                            first_byte=case['controller_line_bytes'][0],
                            entry=call['entry'], table_output=call['output'][0],
                            pc140_y=consumer['alu_y']))
    if len({x['pc140_y'] for x in witness}) != 4:
        raise ValueError('symbol/source consumer witness lost differentiation')
    paths = [Path(__file__), CONTROLLER,
             HERE / 'photo_table_prombit_consumer.py',
             HERE / 'photo_table_phase_consumer.py',
             HERE / 'photo_table_controller_source.py',
             HERE / 'photo_table_controller_dibits.py',
             HERE / 'photo_table_restart_dibits.py',
             HERE / 'photo_table_callers.py',
             HERE / 'photo_table_exact_transform.py',
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             ASSUMED / 'results/rotation-study/scenario-3.json',
             ASSUMED / 'execute.py', HERE.parent / 'model.py', MAPPINGS['q3']]
    report = dict(status='conditional controller bytes and dibits through U10-bit sign-table route',
                  fixture=dict(mapping='q3', seeds=list(SEEDS),
                               controller_source='unchanged 8031 USART-01 main-loop byte streams',
                               candidate_d349='one full byte per reached visit',
                               candidate_table_predecessors='successive LSB-first dibits at 3C1/3D6 by baseline call order',
                               candidate_u5_d0='inverted U10 data bit 5 with E2 held low',
                               candidate_u5_q0='Am2901 I0 and A1',
                               e4_i7_a0=1, cycles=2500,
                               diagnostic_rst_pulses=15,
                               table_dispatch='previous ALU Y',
                               upstream_control='saved random rotation-study scenario'),
                  totals=dict(runs=len(cases), calls=sum(len(x['table_calls']) for x in cases),
                              d349_visits=sum(len(x['d349_visits']) for x in cases),
                              reached_entries=entries,
                              external_table_output_reads=sum(len(x['consumers']) for x in cases),
                              output_candidate_visits=sum(len(x['output_candidates']) for x in cases)),
                  witness_seed184=witness, cases=cases,
                  limitations=[
                      'Inversion and U10-D5-to-U5-D0 wiring plus per-word latch capture are untraced hypotheses.',
                      'The same controller byte stream is offered as full bytes at D349 and as scheduled dibits at table predecessors; this timing and fan-out are untraced.',
                      'Previous-Y branch bus, upstream branches and AC=RST at 084 are untraced hypotheses.',
                      'Only one to three D349 bytes are consumed per run; no continuous transmitter or DAC-bound waveform is shown.',
                      'Reached 39E ALU bytes remain zero.'],
                  source_sha256={str(path.relative_to(HERE.parent)):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    print(report['totals'])
