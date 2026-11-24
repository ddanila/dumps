"""Identify the exact reached 3C5/3DA transform under coupled photo pins."""

import hashlib
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
from common import decode, read, save
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from rotation_study import put, run_entry, scenario_for, word

TABLES = (0x3C5, 0x3DA)
SOURCES = ((0x1234, 0x5678), (0x12FF, 0x5600), (0x9234, 0xD678),
           (1, 2), (0, 0), (0xFFFF, 0x8001), (0x00FF, 0xFF00),
           (0xA5A5, 0x5A5A))
PRIOR_OUTPUTS = ((0, 0), (0xA1B2, 0xC3D4), (0xFFFF, 1))
Q_VALUES = (0, 5, 255)
CONFIG = ASSUMED / 'rotation-search.json'
REACHED = HERE / 'results/photo-table-callers.json'


def expected(source, entry):
    """High-byte replication, then two's-complement sign selection."""
    x, y = ((value >> 8) * 0x101 for value in source)
    return ((x, y), (x, -y & 0xFFFF),
            (-x & 0xFFFF, -y & 0xFFFF), (-x & 0xFFFF, y))[entry]


def coupled_rows(rows, table, entry):
    candidate = list(rows)
    for pc in range(table + 4*entry, table + 4*entry + 4):
        row = dict(candidate[pc])
        row['i'] = (row['i'] & ~129) | 128  # E4=I7=1; E2=I0=0.
        row['a'] = (row['a'] & ~3) | 1      # A0=E4=1; A1=E2=0.
        candidate[pc] = row
    return candidate


def run(out=HERE / 'results/photo-table-exact-transform.json'):
    config = read(CONFIG)
    reached = read(REACHED)
    cases = []
    for name, path in MAPPINGS.items():
        mapping = mapped(path)
        rows = decode(mapping)
        carry = scenario_for(mapping, config)['inputs']['carry']
        local_checks = 0
        local_failures = []
        witness = None
        for table in TABLES:
            for entry in range(4):
                candidate = coupled_rows(rows, table, entry)
                for source in SOURCES:
                    for prior in PRIOR_OUTPUTS:
                        for q in Q_VALUES:
                            ram = [0] * 16
                            put(ram, 4, source[0]); put(ram, 8, source[1])
                            put(ram, 10, prior[0]); put(ram, 12, prior[1])
                            cpu, trace = run_entry(candidate, table, entry,
                                                   ram, q, carry)
                            got = (word(cpu.ram, 10), word(cpu.ram, 12))
                            want = expected(source, entry)
                            local_checks += 1
                            if got != want:
                                local_failures.append(dict(table=f'{table:03X}',
                                    entry=entry, source=list(source), prior=list(prior),
                                    q=q, actual=list(got), expected=list(want)))
                            if (name == 'q3' and table == 0x3C5 and entry == 1
                                    and source == SOURCES[0] and prior == PRIOR_OUTPUTS[1]
                                    and q == 5):
                                witness = dict(source=list(source), prior=list(prior),
                                               q=q, output=list(got),
                                               words=[dict(pc=f'{row["pc"]:03X}',
                                                           a=row['a'], b=row['b'],
                                                           i=row['i'], y=row['y'])
                                                      for row in trace])
        old = next(case for case in reached['cases']
                   if case['mapping'] == name and case['e4'] == 1)
        reached_failures = []
        for observation in old['observations']:
            want = expected(observation['source'], observation['entry'])
            if tuple(observation['output_after']) != want:
                reached_failures.append(dict(seed=observation['seed'],
                    d=observation['d'], site=observation['site'],
                    entry=observation['entry'], actual=observation['output_after'],
                    expected=list(want)))
        if local_failures or reached_failures:
            raise ValueError(f'{name}: local or reached formula mismatch')
        cases.append(dict(mapping=name, local_checks=local_checks,
                          local_failures=0, reached_calls=len(old['observations']),
                          reached_matches=len(old['observations']),
                          reached_by_site=dict(Counter(x['site'] for x in old['observations'])),
                          witness=witness))
    paths = [Path(__file__), CONFIG, REACHED,
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             ASSUMED / 'rotation_study.py', ASSUMED / 'execute.py',
             HERE.parent / 'model.py', *MAPPINGS.values()]
    report = dict(status='exact transform under held photo-pin hypothesis, not recovered board wiring',
                  formula='H(v)=0x0101*(v>>8); entry 0:(Hx,Hy), 1:(Hx,-Hy), 2:(-Hx,-Hy), 3:(-Hx,Hy), modulo 65536',
                  fixture=dict(table_bases=[f'{x:03X}' for x in TABLES],
                               source_register_bases=[4, 8],
                               output_register_bases=[10, 12],
                               e4_i7_a0=1, e2_i0_a1=0,
                               source_pairs=[list(x) for x in SOURCES],
                               prior_outputs=[list(x) for x in PRIOR_OUTPUTS],
                               q_values=list(Q_VALUES),
                               local_checks_per_mapping=576),
                  cases=cases,
                  total_local_checks=sum(x['local_checks'] for x in cases),
                  total_reached_matches=sum(x['reached_matches'] for x in cases),
                  limitations=[
                      'The E4-to-I7/A0 and E2-to-I0/A1 routes are photo candidates with untraced pin continuations and held levels.',
                      'The local sweep executes four real-PROM words per entry with the G1 carry policy; it is not a controller call.',
                      'The reached-call match uses the saved rotation-study branch and dispatch scenario, not recovered physical conditions.',
                      'The model still shares instruction controls across both Am2901 slices; split-slice wiring could change this formula.',
                      'The output register pairs are not traced to the DAC08 or a line waveform.'],
                  source_sha256={str(p.relative_to(HERE.parent)):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    print(report['total_local_checks'], 'local checks;',
          report['total_reached_matches'], 'reached calls matched')
