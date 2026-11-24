"""Clock a diagnostic LS273/DAC08 latch at table consumers 140 and 146."""

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
from dac08_latch_probe import capture, photo_b5
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from photo_table_callers import reached_calls
from photo_table_controller_dibits import CONTROLLER
from photo_table_exact_transform import expected
from photo_table_prombit_consumer import bit_decode
from photo_table_prombit_symbols import scenario
from photo_table_restart_dibits import trace_run

SEEDS = (155, 183, 184)
CLOCK_SITES = (0x140, 0x146)


def run(out=HERE / 'results/photo-table-internal-latch.json'):
    mapping = mapped(MAPPINGS['q3'])
    groups = read(CONTROLLER)['groups']
    cases = []
    with patch.object(executor, 'decode', bit_decode):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for seed in SEEDS:
                for group in groups:
                    selector = group['selectors'][0]
                    line_bytes = group['line_bytes']
                    state = scenario({str(0x349): line_bytes})
                    result, trace, restarts = trace_run(mapping, state, seed, directory)
                    calls = reached_calls(trace, state)
                    writes = [row for row in trace if row['pc'] == 0x349]
                    outputs = [row for row in trace if row['pc'] in (0x392, 0x39E)]
                    clocks = {f'{pc:03X}': [dict(**row, dac_b5=photo_b5(row['latch_q']))
                                           for row in capture(trace, pc)]
                              for pc in CLOCK_SITES}
                    if (len(restarts) != 15 or not writes or not calls or
                            any(tuple(call['output_after']) !=
                                expected(call['source'], call['entry']) for call in calls) or
                            any(row['alu']['y'] != 0 for row in outputs) or
                            any(len(values) > 3 or not values for values in clocks.values()) or
                            [row['latch_q'] for row in clocks['140']] !=
                            [row['latch_q'] for row in clocks['146']]):
                        raise ValueError('internal-latch fixture or signal conclusion changed')
                    cases.append(dict(seed=seed, controller_selector=selector,
                                      controller_line_bytes=line_bytes,
                                      d349_bytes=[row['external_read']['value'] for row in writes],
                                      clocks=clocks,
                                      output_candidates=[dict(cycle=row['cycle'],
                                                              pc=f"{row['pc']:03X}",
                                                              alu_y=row['alu']['y'])
                                                         for row in outputs],
                                      trace_digest=result['trace_digest']))
    if len(cases) != 12 or not all(any(row['latch_q'] for row in case['clocks']['140'])
                                   for case in cases):
        raise ValueError('controller-dependent internal captures changed')
    paths = [Path(__file__), CONTROLLER,
             HERE / 'dac08_latch_probe.py',
             HERE / 'photo_table_prombit_consumer.py',
             HERE / 'photo_table_prombit_symbols.py',
             HERE / 'photo_table_restart_dibits.py',
             HERE / 'photo_table_callers.py',
             HERE / 'photo_table_exact_transform.py',
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             ASSUMED / 'results/rotation-study/scenario-3.json',
             ASSUMED / 'execute.py', HERE.parent / 'model.py', MAPPINGS['q3']]
    report = dict(status='counterfactual LS273 capture at internal table consumers',
                  fixture=dict(mapping='q3', seeds=list(SEEDS),
                               controller_source='unchanged 8031 USART-01 main-loop bytes',
                               candidate_clock_sites=['140', '146'],
                               candidate_data='Am2901 ALU Y to LS273 D1:D8 in order',
                               photo_bit='DAC08 B5 from LS273 Q4',
                               candidate_u5_d0='inverted U10 data bit 5',
                               diagnostic_rst_pulses=15, cycles=2500,
                               upstream_control='saved random rotation-study scenario'),
                  totals=dict(runs=len(cases),
                              captures_per_clock_site={site: sum(len(case['clocks'][site])
                                                                 for case in cases)
                                                       for site in ('140', '146')},
                              max_captures_per_run=max(len(case['clocks']['140'])
                                                       for case in cases),
                              reached_392_39e=sum(len(case['output_candidates'])
                                                  for case in cases)),
                  cases=cases,
                  limitations=[
                      'No physical clock net to 140 or 146 is traced; these are diagnostic rising edges.',
                      'The full Y-to-LS273 bit order is untraced; only the B5-from-Q4 DAC08 candidate has photo support.',
                      'Inverted U10-bit route, U5 capture, D349 input, branch bus and AC=RST continuation are hypotheses.',
                      'One to three captures per run do not establish a sustained carrier, sample cadence or analog line signal.'],
                  source_sha256={str(path.relative_to(HERE.parent)):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    print(report['totals'])
