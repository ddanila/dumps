"""Screen diagnostic branch seeds for D349 -> table -> output-candidate order."""

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
import execute as executor
from common import read, save
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from photo_table_callers import reached_calls
from photo_table_controller_dibits import CONTROLLER
from photo_table_controller_source import table_output_flow
from photo_table_prombit_consumer import bit_decode
from photo_table_prombit_symbols import scenario
from photo_table_restart_dibits import trace_run

SEEDS = range(256)
TABLE_CALLS = (0x3C2, 0x3D7)
OUTPUT_CANDIDATES = (0x392, 0x39E)
INTERNAL_CONSUMERS = (0x140, 0x146)


def events(trace):
    writes = [row for row in trace if row['pc'] == 0x349 and '5' in row['registers']]
    calls = [row for row in trace if row['pc'] in TABLE_CALLS]
    outputs = [row for row in trace if row['pc'] in OUTPUT_CANDIDATES]
    consumers = [row for row in trace if row['pc'] in INTERNAL_CONSUMERS]
    chains = [(write, call, output) for write in writes for call in calls
              for output in outputs
              if write['cycle'] < call['cycle'] < output['cycle']]
    return writes, calls, outputs, consumers, chains


def run(out=HERE / 'results/photo-table-output-order-screen.json'):
    groups = read(CONTROLLER)['groups']
    line_bytes = groups[1]['line_bytes']  # selector 20
    mapping = mapped(MAPPINGS['q3'])
    counts = Counter()
    chain_cases = []
    with patch.object(executor, 'decode', bit_decode):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for seed in SEEDS:
                state = scenario({str(0x349): line_bytes})
                try:
                    result, trace, restarts = trace_run(mapping, state, seed, directory)
                    strict_contract = True
                    digest = result['trace_digest']
                    restart_count = len(restarts)
                except ValueError:
                    strict_contract = False
                    trace_path = directory / 'trace.jsonl'
                    if not trace_path.exists():
                        raise
                    trace = [json.loads(line) for line in trace_path.read_text().splitlines()]
                    digest = None
                    restart_count = None
                writes, calls, outputs, consumers, chains = events(trace)
                counts['seeds'] += 1
                counts['strict_contract'] += strict_contract
                counts['with_d349_write'] += bool(writes)
                counts['with_table_call'] += bool(calls)
                counts['with_output_candidate'] += bool(outputs)
                counts['with_output_after_table'] += bool(calls and any(
                    output['cycle'] > calls[0]['cycle'] for output in outputs))
                counts['with_d349_before_table'] += bool(writes and calls and any(
                    write['cycle'] < call['cycle'] for write in writes for call in calls))
                counts['with_d349_table_output_order'] += bool(chains)
                counts['nonzero_output_after_table'] += any(
                    output['alu']['y'] != 0 for output in outputs
                    if calls and output['cycle'] > calls[0]['cycle'])
                if not chains:
                    continue
                observations = reached_calls(trace, state)
                table_reads = table_output_flow(trace)['downstream_reads']
                tainted_reads = {(event['cycle'], int(event['pc'], 16))
                                 for event in table_reads}
                internal = [row for row in consumers if any(
                    write['cycle'] < call['cycle'] < row['cycle'] < output['cycle']
                    for write, call, output in chains)
                    and (row['cycle'], row['pc']) in tainted_reads]
                if any(output['alu']['y'] != 0 for _, _, output in chains):
                    raise ValueError('D349/table/output chain now has nonzero candidate output')
                counts['chain_strict_contract'] += strict_contract
                counts['chain_with_nonzero_internal_consumer'] += any(
                    row['alu']['y'] != 0 for row in internal)
                chain_cases.append(dict(seed=seed, strict_contract=strict_contract,
                                        restart_count=restart_count,
                                        d349_writes=[dict(cycle=row['cycle'],
                                                          byte=row['external_read']['value'],
                                                          r5=row['registers']['5'])
                                                     for row in writes],
                                        table_calls=[dict(cycle=call['cycle'],
                                                          site=call['site'],
                                                          entry=call['entry'],
                                                          source=call['source'],
                                                          output=call['output_after'])
                                                     for call in observations],
                                        internal_consumers=[dict(cycle=row['cycle'],
                                                                 pc=f"{row['pc']:03X}",
                                                                 alu_y=row['alu']['y'])
                                                            for row in internal],
                                        output_candidates=[dict(cycle=row['cycle'],
                                                                pc=f"{row['pc']:03X}",
                                                                alu_y=row['alu']['y'])
                                                           for row in outputs],
                                        trace_digest=digest))
    if (counts['seeds'] != 256 or counts['with_d349_table_output_order'] != 8 or
            counts['nonzero_output_after_table'] != 0 or
            counts['chain_with_nonzero_internal_consumer'] != 4):
        raise ValueError('branch-seed output ordering changed')
    paths = [Path(__file__), CONTROLLER,
             HERE / 'photo_table_prombit_consumer.py',
             HERE / 'photo_table_prombit_symbols.py',
             HERE / 'photo_table_controller_source.py',
             HERE / 'photo_table_restart_dibits.py',
             HERE / 'photo_table_callers.py',
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             ASSUMED / 'results/rotation-study/scenario-3.json',
             ASSUMED / 'execute.py', HERE.parent / 'model.py', MAPPINGS['q3']]
    report = dict(status='bounded diagnostic ordering screen, not physical DAC path',
                  fixture=dict(mapping='q3', branch_seeds=[0, 255], cycles=2500,
                               controller_selector='20', line_bytes=line_bytes,
                               candidate_d349='successive controller bytes',
                               candidate_u5_d0='inverted U10 data bit 5',
                               u10_e2='held low', e4_i7_a0=1,
                               diagnostic_rst='first 15 visits to 084',
                               table_dispatch='previous ALU Y',
                               upstream_control='saved random rotation-study scenario'),
                  counts=dict(sorted(counts.items())), chain_cases=chain_cases,
                  limitations=[
                      'Random branch seeds are diagnostic inputs, not recovered controller wiring.',
                      'A failed strict contract may mean fewer than 15 restarts, nonterminal PC, unbalanced stack or model stop; its trace still supports reached-order counts.',
                      'Inverted U10 D5 route, per-word U5 capture, D349 source and AC override are hypotheses.',
                      '392/39E are candidate latch words, not traced DAC08 clocks; zero ALU bytes do not rule out another output site.'],
                  source_sha256={str(path.relative_to(HERE.parent)):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    print(report['counts'])
