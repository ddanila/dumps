"""Test inverted U10 D5 as candidate U5 Q0 source for table/output access."""

import hashlib
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
import execute as executor
from common import load, read, save
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from photo_table_callers import reached_calls, scenario_for
from photo_table_controller_dibits import CONTROLLER, live_dispatch
from photo_table_controller_source import table_output_flow
from photo_table_exact_transform import expected
from photo_table_phase_consumer import SEEDS, in_table
from photo_table_restart_dibits import trace_run

PHASE_REPORT = HERE / 'results/photo-table-phase-consumer.json'
BASE_DECODE = executor.decode


def bit_decode(candidate, lanes):
    rows = BASE_DECODE(candidate, lanes)
    for pc, row in enumerate(rows):
        level = 1 - (lanes['10'][pc] >> 5 & 1)
        row['i'] = (row['i'] & ~1) | level
        row['a'] = (row['a'] & ~2) | (level << 1)
    return rows


def run(out=HERE / 'results/photo-table-prombit-consumer.json'):
    groups = read(CONTROLLER)['groups']
    phase_cases = {(x['seed'], x['controller_selector']): x
                   for x in read(PHASE_REPORT)['cases']}
    mapping = mapped(MAPPINGS['q3'])
    cases = []
    with patch.object(executor, 'decode', bit_decode):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for seed in SEEDS:
                for group in groups:
                    selector = group['selectors'][0]
                    line_bytes = group['line_bytes']
                    scenario = live_dispatch(scenario_for(1, 0))
                    scenario['name'] = scenario['name'].replace(
                        'E2=0', 'I0/A1 from inverted U10 D5, U10 E2 held low')
                    del scenario['inputs']['instruction_bit_overrides']['0']
                    del scenario['inputs']['register_address_bit_overrides']['a']['1']
                    scenario['io']['read'].update(
                        mode='pc_sequence', value=0, sequence_end='hold-last',
                        status='hypothesis',
                        evidence='Actual 8031 USART-01 bytes offered at candidate D349 by visit order; route and timing untraced',
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
                    phase = phase_cases[(seed, selector)]
                    if (not writes or not calls or not consumers or len(restarts) != 15 or
                            flow['table_writes'] != 4 * len(calls) or
                            any(tuple(call['output_after']) !=
                                expected(call['source'], call['entry']) for call in calls) or
                            any(row['alu']['y'] != 0 for row in outputs) or
                            any(row['instruction_i'] & 1 for row in trace if in_table(row['pc'])) or
                            any(not (trace[x['cycle']]['instruction_i'] & 1)
                                for x in consumers)):
                        raise ValueError('PROM-bit table/consumer chain changed')
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
                                      trace_digest=result['trace_digest'],
                                      differs_from_address_phase=(
                                          result['trace_digest'] != phase['trace_digest'])))
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
            raise ValueError('U10-bit controller-to-consumer witness changed')
        witnesses.append(dict(selector=case['controller_selector'],
                              controller_byte=first, table_output=call['output'][0],
                              pc140_y=consumer['alu_y']))
    if len({x['pc140_y'] for x in witnesses}) != 4:
        raise ValueError('consumer no longer separates controller streams')
    u10 = load()['10']
    table_pcs = set()
    consumer_pcs = set()
    for case in cases:
        for call in case['table_calls']:
            base = 0x3C5 if call['site'] == '3C2' else 0x3DA
            table_pcs.update(range(base + 4 * call['entry'],
                                   base + 4 * call['entry'] + 4))
        consumer_pcs.update(int(x['pc'], 16) for x in case['consumers'])
    if (any(1 - (u10[pc] >> 5 & 1) for pc in table_pcs) or
            any(not 1 - (u10[pc] >> 5 & 1) for pc in consumer_pcs)):
        raise ValueError('U10 bit-5 pattern no longer separates table and consumer sites')
    global_phase_differences = sum(
        (1 - (u10[pc] >> 5 & 1)) != (0 if in_table(pc) else 1)
        for pc in range(1024))
    all_table_pcs = [pc for pc in range(1024) if in_table(pc)]
    if any(1 - (u10[pc] >> 5 & 1) for pc in all_table_pcs):
        raise ValueError('U10 bit-5 level is not low throughout both sign tables')
    paths = [Path(__file__), CONTROLLER, PHASE_REPORT,
             HERE / 'photo_table_phase_consumer.py',
             HERE / 'photo_table_controller_source.py',
             HERE / 'photo_table_restart_dibits.py',
             HERE / 'photo_table_controller_dibits.py',
             HERE / 'photo_table_callers.py',
             HERE / 'photo_table_exact_transform.py',
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             ASSUMED / 'results/rotation-study/scenario-3.json',
             ASSUMED / 'execute.py', HERE.parent / 'model.py', MAPPINGS['q3']]
    report = dict(status='counterfactual inverted U10 data-bit route to table consumer',
                  fixture=dict(mapping='q3', seeds=list(SEEDS),
                               controller_source='unchanged 8031 USART-01 main-loop byte streams',
                               candidate_u5_d0='inverted U10 data bit 5',
                               u10_e2='held low for valid U10 data',
                               candidate_u5_q0='Am2901 I0 and A1, updated per decoded microaddress',
                               e4_i7_a0=1, d349_route='candidate external input',
                               cycles=2500, diagnostic_rst_pulses=15,
                               table_dispatch='previous ALU Y',
                               upstream_control='saved random rotation-study scenario'),
                  totals=dict(runs=len(cases), calls=sum(len(x['table_calls']) for x in cases),
                              d349_visits=sum(len(x['d349_visits']) for x in cases),
                              external_table_output_reads=sum(len(x['consumers']) for x in cases),
                              output_candidate_visits=sum(len(x['output_candidates']) for x in cases),
                              trace_digests_different_from_address_phase=sum(
                                  x['differs_from_address_phase'] for x in cases)),
                  raw_bit_pattern=dict(reached_table_pcs=[f'{pc:03X}' for pc in sorted(table_pcs)],
                                       reached_consumer_pcs=[f'{pc:03X}' for pc in sorted(consumer_pcs)],
                                       all_table_words_low=len(all_table_pcs),
                                       global_address_phase_differences=global_phase_differences),
                  witness_seed184=witnesses, cases=cases,
                  limitations=[
                      'No inverter or U10-D5-to-U5-D0 route has been traced; this replaces the uncertain E2-to-D0 photo continuation.',
                      'Per-microaddress U5 capture is modeled, not derived from its clock or setup/hold timing.',
                      'USART-to-D349, previous-Y branch bus, upstream branches and AC=RST at 084 remain hypotheses.',
                      'Only one to three controller bytes are consumed per run; reached 39E remains zero and no DAC-bound stream is shown.'],
                  source_sha256={str(path.relative_to(HERE.parent)):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    print(report['totals'])
