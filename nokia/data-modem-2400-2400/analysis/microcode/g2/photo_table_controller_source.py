"""Offer real 8031 USART-01 bytes to candidate D349 across diagnostic restarts."""

import hashlib
import sys
import tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
from common import read, save
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from photo_table_callers import reached_calls, scenario_for
from photo_table_controller_dibits import CONTROLLER, live_dispatch
from photo_table_exact_transform import expected
from photo_table_restart_dibits import trace_run

SEEDS = (22, 116, 184, 245)
OUTPUT_CANDIDATES = (0x392, 0x39E)


def table_output_flow(trace):
    """Track reads of R10:13 after table writes until another writer replaces them."""
    tainted = set()
    reads = []
    writes = 0
    overwritten = 0
    for row in trace:
        instruction = row['instruction_i']
        source = instruction & 7
        destination = instruction >> 6 & 7
        a, b = row['register_address_a'], row['register_address_b']
        inputs = []
        if source in (0, 1, 4, 5):
            inputs.append(a)
        if source in (1, 3):
            inputs.append(b)
        if destination == 2:  # AM2901 Y selects A even when F does not.
            inputs.append(a)
        for register in set(inputs) & tainted:
            reads.append(dict(cycle=row['cycle'], pc=f"{row['pc']:03X}",
                              register=register))
        if destination in (2, 3, 4, 5, 6, 7) and b in (10, 11, 12, 13):
            pc = row['pc']
            if 0x3C5 <= pc <= 0x3D4 or 0x3DA <= pc <= 0x3E9:
                tainted.add(b)
                writes += 1
            else:
                overwritten += b in tainted
                tainted.discard(b)
    return dict(table_writes=writes, overwritten_without_read=overwritten,
                downstream_reads=reads, still_live=sorted(tainted))


def run(out=HERE / 'results/photo-table-controller-source.json'):
    groups = read(CONTROLLER)['groups']
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        for mapping_name in ('q1', 'q3'):
            mapping = mapped(MAPPINGS[mapping_name])
            for seed in SEEDS:
                for group in groups:
                    selector = group['selectors'][0]
                    line_bytes = group['line_bytes']
                    scenario = live_dispatch(scenario_for(1, 0))
                    scenario['name'] += f'; candidate USART-01 bytes at D349 selector {selector}'
                    scenario['io']['read'].update(
                        mode='pc_sequence', value=0, sequence_end='hold-last',
                        status='hypothesis',
                        evidence='Actual 8031 USART-01 bytes offered by visit order at candidate D349; bus route and timing untraced',
                        pc_sequences={str(0x349): line_bytes})
                    result, trace, restarts = trace_run(mapping, scenario, seed, directory)
                    writes = [row for row in trace if row['pc'] == 0x349]
                    calls = reached_calls(trace, scenario)
                    if not writes or not calls or len(restarts) != 15:
                        raise ValueError('candidate writer, table or restart path changed')
                    if len(writes) >= len(line_bytes):
                        raise ValueError('controller stream no longer long enough for reached D349 visits')
                    for index, row in enumerate(writes):
                        value = line_bytes[index]
                        want = 1 if mapping_name == 'q1' else (value + 1 if value != 0xFF else None)
                        if (row['external_read']['value'] != value or
                                row['registers'].get('5') != want):
                            raise ValueError('controller byte to R5 relation changed')
                    for call in calls:
                        if tuple(call['output_after']) != expected(call['source'], call['entry']):
                            raise ValueError('table sign formula changed')
                    samples = [row for row in trace if row['pc'] in OUTPUT_CANDIDATES]
                    output_flow = table_output_flow(trace)
                    if output_flow['downstream_reads']:
                        raise ValueError('table output is read downstream; update path conclusion')
                    cases.append(dict(mapping=mapping_name, seed=seed,
                                      controller_selector=selector,
                                      controller_line_bytes=line_bytes,
                                      d349_visits=[dict(cycle=row['cycle'],
                                                        byte=row['external_read']['value'],
                                                        r5_write=row['registers'].get('5'),
                                                        previous_y=trace[row['cycle']-1]['alu']['y'])
                                                   for row in writes],
                                      table_calls=[dict(cycle=call['cycle'], site=call['site'],
                                                        entry=call['entry'], source=call['source'],
                                                        output=call['output_after'])
                                                   for call in calls],
                                      output_candidate_visits=[dict(cycle=row['cycle'],
                                                                    pc=f"{row['pc']:03X}",
                                                                    alu_y=row['alu']['y'])
                                                               for row in samples],
                                      output_visits_after_last_source_update=sum(
                                          row['cycle'] > writes[-1]['cycle'] for row in samples),
                                      table_output_flow=output_flow,
                                      trace_digest=result['trace_digest']))
    q3 = [case for case in cases if case['mapping'] == 'q3']
    q1 = [case for case in cases if case['mapping'] == 'q1']
    if not any(len({call['source'][0] >> 8 for call in case['table_calls']}) > 1
               for case in q3):
        raise ValueError('controller-dependent source progression was lost')
    if any(any(visit['r5_write'] != 1 for visit in case['d349_visits'])
           for case in q1):
        raise ValueError('q1 negative control changed')
    paths = [Path(__file__), CONTROLLER,
             HERE / 'photo_table_restart_dibits.py',
             HERE / 'photo_table_controller_dibits.py',
             HERE / 'photo_table_callers.py',
             HERE / 'photo_table_exact_transform.py',
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             ASSUMED / 'results/rotation-study/scenario-3.json',
             ASSUMED / 'execute.py', HERE.parent / 'model.py',
             *(MAPPINGS[name] for name in ('q1', 'q3'))]
    report = dict(status='conditional controller-byte to source-high-byte execution',
                  fixture=dict(mappings=['q1', 'q3'], seeds=list(SEEDS),
                               controller_source='unchanged 8031 USART-01 main-loop byte streams',
                               candidate_d_site='349', cycles=2500,
                               diagnostic_rst_pulses=15,
                               other_d=0, photo_pin_levels='E4=I7=A0=1; E2=I0=A1=0',
                               table_dispatch='previous ALU Y',
                               upstream_control='saved random rotation-study scenario'),
                  cases=cases,
                  totals=dict(runs=len(cases), calls=sum(len(x['table_calls']) for x in cases),
                              d349_visits=sum(len(x['d349_visits']) for x in cases),
                              output_candidate_visits=sum(len(x['output_candidate_visits'])
                                                          for x in cases),
                              output_visits_after_last_source_update=sum(
                                  x['output_visits_after_last_source_update'] for x in cases),
                              table_output_writes=sum(
                                  x['table_output_flow']['table_writes'] for x in cases),
                              table_output_downstream_reads=sum(
                                  len(x['table_output_flow']['downstream_reads']) for x in cases),
                              source_highs_by_mapping={name: dict(Counter(
                                  str(call['source'][0] >> 8) for case in cases
                                  if case['mapping'] == name for call in case['table_calls']))
                                                       for name in ('q1', 'q3')}),
                  limitations=[
                      'USART-01 to D349, previous-Y table dispatch, photo-pin levels, upstream branches and AC=RST override are hypotheses.',
                      'Only one to three controller bytes are consumed per run; this is not a continuous bitstream receiver.',
                      'Output candidate words are not traced to DAC08, and none follows the last D349 source update.',
                      'No table-written R10:13 value is read before replacement in these 32 runs; this is a dynamic fixture result, not whole-program dead-code proof.',
                      'No Am27S31 read or phase-advancing sample loop is established.'],
                  source_sha256={str(path.relative_to(HERE.parent)):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    print(report['totals'])
