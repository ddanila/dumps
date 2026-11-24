"""Test a candidate E2 phase that lets controller-fed sign-table output be read."""

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
from photo_table_controller_dibits import CONTROLLER, live_dispatch
from photo_table_controller_source import table_output_flow
from photo_table_exact_transform import expected
from photo_table_restart_dibits import trace_run

SEEDS = (22, 116, 184, 245)
TABLE_RANGES = ((0x3C5, 0x3D4), (0x3DA, 0x3E9))


def in_table(pc):
    return any(first <= pc <= last for first, last in TABLE_RANGES)


def run(out=HERE / 'results/photo-table-phase-consumer.json'):
    groups = read(CONTROLLER)['groups']
    mapping = mapped(MAPPINGS['q3'])
    original_decode = executor.decode

    def phase_decode(candidate, lanes):
        rows = original_decode(candidate, lanes)
        for pc, row in enumerate(rows):
            e2 = 0 if in_table(pc) else 1
            row['i'] = (row['i'] & ~1) | e2
            row['a'] = (row['a'] & ~2) | (e2 << 1)
        return rows

    cases = []
    with patch.object(executor, 'decode', phase_decode):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for seed in SEEDS:
                for group in groups:
                    selector = group['selectors'][0]
                    line_bytes = group['line_bytes']
                    scenario = live_dispatch(scenario_for(1, 0))
                    scenario['name'] = scenario['name'].replace(
                        'E2=0', 'E2 phase: low in tables, high elsewhere')
                    del scenario['inputs']['instruction_bit_overrides']['0']
                    del scenario['inputs']['register_address_bit_overrides']['a']['1']
                    scenario['io']['read'].update(
                        mode='pc_sequence', value=0, sequence_end='hold-last',
                        status='hypothesis',
                        evidence='Actual 8031 USART-01 bytes offered at D349 by visit order; route and timing untraced',
                        pc_sequences={str(0x349): line_bytes})
                    result, trace, restarts = trace_run(mapping, scenario, seed, directory)
                    writes = [row for row in trace if row['pc'] == 0x349]
                    calls = reached_calls(trace, scenario)
                    flow = table_output_flow(trace)
                    consumers = [dict(**read_event,
                                      alu_y=trace[read_event['cycle']]['alu']['y'])
                                 for read_event in flow['downstream_reads']
                                 if not in_table(int(read_event['pc'], 16))]
                    outputs = [row for row in trace if row['pc'] in (0x392, 0x39E)]
                    if (not writes or not calls or not consumers or len(restarts) != 15 or
                            flow['table_writes'] != 4 * len(calls) or
                            any(tuple(call['output_after']) !=
                                expected(call['source'], call['entry']) for call in calls) or
                            any(row['alu']['y'] != 0 for row in outputs)):
                        raise ValueError('phase-consumer route or table transform changed')
                    for index, row in enumerate(writes):
                        if (row['external_read']['value'] != line_bytes[index] or
                                row['registers'].get('5') != line_bytes[index] + 1):
                            raise ValueError('controller D349-to-R5 relation changed')
                    cases.append(dict(seed=seed, controller_selector=selector,
                                      controller_line_bytes=line_bytes,
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
    witnesses = []
    for case in cases:
        if case['seed'] != 184:
            continue
        call = next(x for x in case['table_calls'] if x['cycle'] == 262)
        consumer = next(x for x in case['consumers']
                        if x['cycle'] == 271 and x['pc'] == '140')
        first = case['controller_line_bytes'][0]
        if (call['source'][0] >> 8 != first + 1 or
                call['output'][0] != (first + 1) * 0x101 or
                consumer['alu_y'] != first + 1 or consumer['register'] != 11):
            raise ValueError('controller-to-table-to-consumer witness changed')
        witnesses.append(dict(selector=case['controller_selector'],
                              controller_byte=first, table_output=call['output'][0],
                              pc140_y=consumer['alu_y']))
    if len({x['pc140_y'] for x in witnesses}) != 4:
        raise ValueError('controller-dependent consumer separation changed')
    paths = [Path(__file__), CONTROLLER,
             HERE / 'photo_table_controller_source.py',
             HERE / 'photo_table_restart_dibits.py',
             HERE / 'photo_table_controller_dibits.py',
             HERE / 'photo_table_callers.py',
             HERE / 'photo_table_exact_transform.py',
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             ASSUMED / 'results/rotation-study/scenario-3.json',
             ASSUMED / 'execute.py', HERE.parent / 'model.py', MAPPINGS['q3']]
    report = dict(status='counterfactual E2 phase opens controller-table-consumer chain',
                  fixture=dict(mapping='q3', seeds=list(SEEDS),
                               controller_source='unchanged 8031 USART-01 main-loop byte streams',
                               d349_route='candidate external input',
                               e4_i7_a0=1,
                               e2_i0_a1='0 at 3C5:3D4 and 3DA:3E9; 1 elsewhere',
                               phase_method='decode-time per-PC coupled pin substitution',
                               cycles=2500, diagnostic_rst_pulses=15,
                               table_dispatch='previous ALU Y',
                               upstream_control='saved random rotation-study scenario'),
                  totals=dict(runs=len(cases), calls=sum(len(x['table_calls']) for x in cases),
                              d349_visits=sum(len(x['d349_visits']) for x in cases),
                              external_table_output_reads=sum(len(x['consumers']) for x in cases),
                              output_candidate_visits=sum(len(x['output_candidates']) for x in cases)),
                  witness_seed184=witnesses, cases=cases,
                  limitations=[
                      'The E2 phase is assigned by PC, not derived from a traced U5 latch clock or real board timing.',
                      'USART-to-D349, previous-Y branch bus, upstream branches and AC=RST at 084 are hypotheses.',
                      'The four controller streams are short, and only one to three D349 visits occur per run.',
                      'PC140/146 reads are internal Am2901 values, not traced DAC08 sample codes; reached 39E ALU values remain zero.'],
                  source_sha256={str(path.relative_to(HERE.parent)):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    print(report['totals'])
