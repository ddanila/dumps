"""Test a candidate external-D to R5 to sign-table path across diagnostic restarts."""

import hashlib
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]
from common import save
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from photo_table_callers import reached_calls, scenario_for
from photo_table_controller_dibits import live_dispatch
from photo_table_exact_transform import expected
from photo_table_restart_dibits import trace_run

SEEDS = (22, 116, 184, 245)
VALUES = (0, 1, 2, 0x55, 0x80, 0xFE, 0xFF)


def run(out=HERE / 'results/photo-table-source-update.json'):
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        for name in ('q1', 'q3'):
            mapping = mapped(MAPPINGS[name])
            for seed in SEEDS:
                for value in VALUES:
                    scenario = live_dispatch(scenario_for(1, 0))
                    scenario['name'] += f'; candidate D349={value:02X}'
                    scenario['io']['read'].update(
                        mode='pc_table', value=0, status='hypothesis',
                        evidence='Candidate external data at instruction 349; physical source and timing untraced',
                        pc_values={str(0x349): value})
                    result, trace, restarts = trace_run(mapping, scenario, seed, directory)
                    writes = [row for row in trace if row['pc'] == 0x349]
                    calls = reached_calls(trace, scenario)
                    if not writes or not calls:
                        raise ValueError(f'{name} seed {seed}: missing writer or calls')
                    for row in writes:
                        if row['external_read']['value'] != value:
                            raise ValueError('candidate D349 was not consumed')
                        got = row['registers'].get('5')
                        want = 1 if name == 'q1' else (value + 1 if value != 0xFF else None)
                        if got != want:
                            raise ValueError(f'{name} seed {seed} D={value:02X}: R5={got}, expected {want}')
                    for call in calls:
                        if tuple(call['output_after']) != expected(call['source'], call['entry']):
                            raise ValueError('table output differs from exact sign transform')
                        prior = [row for row in trace[:call['cycle']]
                                 if '5' in row['registers']]
                        if prior:
                            last = prior[-1]
                            if call['source'][0] >> 8 != last['registers']['5']:
                                raise ValueError('last R5 write does not reach table source')
                    cases.append(dict(mapping=name, seed=seed, d349=value,
                                      r5_writes=[dict(cycle=row['cycle'],
                                                      value=row['registers'].get('5'))
                                                 for row in writes],
                                      calls=[dict(cycle=call['cycle'], site=call['site'],
                                                  entry=call['entry'], source=call['source'],
                                                  output=call['output_after'])
                                             for call in calls],
                                      restart_count=len(restarts),
                                      trace_digest=result['trace_digest']))
    paths = [Path(__file__), HERE / 'photo_table_restart_dibits.py',
             HERE / 'photo_table_controller_dibits.py',
             HERE / 'photo_table_callers.py',
             HERE / 'photo_table_exact_transform.py',
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             HERE.parent / 'assumed/execute.py',
             HERE.parent / 'model.py',
             *(MAPPINGS[name] for name in ('q1', 'q3'))]
    report = dict(status='conditional candidate D349-to-R5-to-sign-table path',
                  fixture=dict(mappings=['q1', 'q3'], seeds=list(SEEDS),
                               d349_values=list(VALUES), cycles=2500,
                               diagnostic_rst_pulses=15,
                               other_d=0, photo_pin_levels='E4=I7=A0=1; E2=I0=A1=0',
                               table_dispatch='previous ALU Y',
                               upstream_control='saved random rotation-study scenario'),
                  totals=dict(runs=len(cases), calls=sum(len(x['calls']) for x in cases)),
                  cases=cases,
                  limitations=[
                      'D349 source and timing are candidate wiring, not traced Nokia connections.',
                      'Diagnostic RST at 084 is an untraced AC override; upstream branches remain scenario-driven.',
                      'No Am27S31 read, demonstrated phase advance, or traced DAC sample path is in this fixture.',
                      'D=FF inhibits the R5 write at 349 in q3, so no wraparound update is claimed.'],
                  source_sha256={str(path.relative_to(HERE.parent)):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    print(report['totals'])
