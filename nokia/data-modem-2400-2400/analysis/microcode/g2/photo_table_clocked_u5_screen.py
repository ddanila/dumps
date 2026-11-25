"""Replay plausible raw PROM edges as a stateful U5 clock, not a per-PC level."""

import hashlib
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
from common import read, save
import execute as executor
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from photo_table_callers import reached_calls, scenario_for
from photo_table_controller_dibits import CONTROLLER, live_dispatch
from photo_table_controller_source import table_output_flow
from photo_table_exact_transform import expected
from photo_table_phase_consumer import in_table
from photo_table_prombit_consumer import bit_decode
from photo_table_restart_dibits import trace_run

# Offline screen: these edges alone reproduced U10-D5 levels at all reached
# sign-table and downstream-consumer words across twelve controller-fed traces.
CLOCKS = (('10', 0, 1), ('11', 1, 1), ('11', 3, 1),
          ('17', 2, 1), ('17', 3, 1), ('17', 4, 1), ('18', 5, 0))
SEEDS = (155, 183, 184)
CONSUMERS = {0x140, 0x141, 0x143, 0x146}


def run(out=HERE / 'results/photo-table-clocked-u5-screen.json'):
    mapping = mapped(MAPPINGS['q3'])
    groups = read(CONTROLLER)['groups']
    baseline = {}
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        with patch.object(executor, 'decode', bit_decode):
            for seed in SEEDS:
                for group in groups:
                    scenario = live_dispatch(scenario_for(1, 0))
                    del scenario['inputs']['instruction_bit_overrides']['0']
                    del scenario['inputs']['register_address_bit_overrides']['a']['1']
                    scenario['io']['read'].update(
                        mode='pc_sequence', value=0, sequence_end='hold-last',
                        status='hypothesis', evidence='Controller bytes at candidate D349',
                        pc_sequences={str(0x349): group['line_bytes']})
                    result, trace, _ = trace_run(mapping, scenario, seed, directory)
                    baseline[(seed, group['selectors'][0])] = dict(
                        digest=result['trace_digest'],
                        output_y=[row['alu']['y'] for row in trace
                                  if row['pc'] in (0x392, 0x39E)])
        for chip, bit, edge_to in CLOCKS:
            for initial in (0, 1):
                for seed in SEEDS:
                    for group in groups:
                        selector = group['selectors'][0]
                        scenario = live_dispatch(scenario_for(1, 0))
                        scenario['name'] += f'; candidate clocked U5 Q0 {chip}.{bit} edge {edge_to}'
                        del scenario['inputs']['instruction_bit_overrides']['0']
                        del scenario['inputs']['register_address_bit_overrides']['a']['1']
                        scenario['inputs']['clocked_prom_bit'] = dict(
                            status='hypothesis',
                            evidence='Raw PROM edge selected by offline critical-word timing screen; U5 clock and U10-D5 data route untraced',
                            clock_chip=chip, clock_bit=bit, edge_to=edge_to,
                            data_chip='10', data_bit=5, invert_data=True,
                            initial=initial, targets=['i0', 'a1'])
                        scenario['io']['read'].update(
                            mode='pc_sequence', value=0, sequence_end='hold-last',
                            status='hypothesis',
                            evidence='Real 8031 USART-01 bytes offered at candidate D349 by visit order; route and timing untraced',
                            pc_sequences={str(0x349): group['line_bytes']})
                        contract = True
                        try:
                            result, trace, restarts = trace_run(mapping, scenario, seed, directory)
                        except ValueError as error:
                            if 'diagnostic restart or stack contract changed' not in str(error):
                                raise
                            contract = False
                            result = read(directory / 'summary.json')
                            trace = [json.loads(line) for line in
                                     (directory / 'trace.jsonl').read_text().splitlines()]
                        critical = [row for row in trace
                                    if in_table(row['pc']) or row['pc'] in CONSUMERS]
                        critical_mismatch = sum(
                            row['clocked_prom_bit']['q'] != (0 if in_table(row['pc']) else 1)
                            for row in critical)
                        table = [row for row in trace if in_table(row['pc'])]
                        consumers = [row for row in trace if row['pc'] in CONSUMERS]
                        outputs = [row['alu']['y'] for row in trace
                                   if row['pc'] in (0x392, 0x39E)]
                        calls = reached_calls(trace, scenario)
                        sign_matches = sum(
                            tuple(call['output_after']) == expected(call['source'], call['entry'])
                            for call in calls)
                        flow = table_output_flow(trace)
                        downstream_reads = sum(
                            not in_table(int(item['pc'], 16))
                            for item in flow['downstream_reads'])
                        reference = baseline[(seed, selector)]
                        cases.append(dict(clock_chip=chip, clock_bit=bit,
                                          edge_to=edge_to, initial=initial,
                                          seed=seed, controller_selector=selector,
                                          clean=result['clean'], restart_contract=contract,
                                          captures=result['clocked_prom_bit_captures'],
                                          critical_visits=len(critical),
                                          critical_mismatch=critical_mismatch,
                                          table_words=len(table), consumer_words=len(consumers),
                                          calls=len(calls), sign_matches=sign_matches,
                                          downstream_reads=downstream_reads,
                                          output_y=outputs, reference_output_y=reference['output_y'],
                                          trace_matches_per_pc_reference=(
                                              result['trace_digest'] == reference['digest']),
                                          trace_digest=result['trace_digest'], stop=result['stop']))
    survivors = [case for case in cases
                 if case['trace_matches_per_pc_reference']]
    paths = [Path(__file__), CONTROLLER,
             HERE / 'photo_table_prombit_consumer.py',
             HERE / 'photo_table_restart_dibits.py',
             HERE / 'photo_table_controller_dibits.py',
             HERE / 'photo_table_callers.py',
             ASSUMED / 'execute.py', ASSUMED / 'results/rotation-study/scenario-3.json',
             MAPPINGS['q3']]
    report = dict(status='stateful raw-PROM-edge U5 clock screen under untraced route',
                  fixture=dict(mapping='q3', controller='real 8031 USART-01 byte groups at candidate D349',
                               seeds=list(SEEDS), cycles=2500, diagnostic_rst_pulses=15,
                               data='inverted U10 D5 to candidate U5 D0',
                               output='candidate U5 Q0 to Am2901 I0 and A1',
                               clock='edge of raw PROM bit; capture at current microword'),
                  totals=dict(runs=len(cases), reference_matches=len(survivors),
                              clean=sum(x['clean'] for x in cases),
                              restart_contracts=sum(x['restart_contract'] for x in cases),
                              critical_mismatches=sum(x['critical_mismatch'] for x in cases),
                              calls=sum(x['calls'] for x in cases),
                              sign_matches=sum(x['sign_matches'] for x in cases),
                              downstream_reads=sum(x['downstream_reads'] for x in cases),
                              nonzero_output_cases=sum(any(x['output_y']) for x in cases)),
                  matching_cases=survivors, cases=cases,
                  limitations=[
                      'Clock, data, inverter and latch output routes are untraced photo-compatible hypotheses.',
                      'The raw clock bits are replayed from the dumps; their electrical availability under PROM enables is not established.',
                      'A raw PROM edge is sampled at the current microword; physical propagation and hold timing remain unknown.',
                      'The 084 AC=RST pulse and controller-to-D349 route are diagnostic assumptions.',
                      'Matching a per-PC counterfactual does not demonstrate sustained modem output.'],
                  source_sha256={str(path.relative_to(HERE.parent)):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    print(run()['totals'])
