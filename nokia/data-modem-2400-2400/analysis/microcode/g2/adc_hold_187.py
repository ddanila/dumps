"""Test one held ADC0800 byte across fitted-swapped's 187 PLP/BLT loop."""
import copy
import hashlib
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
from common import save
from execute import execute
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS


def run_case(mapping, base, q, value, cycles):
    scenario = copy.deepcopy(base)
    scenario['initial']['q'] = q
    scenario['io']['read']['pc_sequences']['391'] = [value]
    result = execute(mapping, scenario, cycles, mode='integrated', trace_limit=0)
    if not result['clean']:
        raise ValueError('held-byte DSC2847 run did not complete')
    return dict(value=value, visits_187=result['address_counts'].get(0x187, 0),
                final_pc=f"{result['final_state']['pc']:03X}",
                trace_digest=result['trace_digest'])


def run(out):
    mapping = mapped(MAPPINGS['fitted_swapped'])
    _, base = fixture()
    sweeps = []
    for q in (1, 129):
        rows = [run_case(mapping, base, q, value, 512) for value in range(256)]
        grouped = defaultdict(list)
        for row in rows:
            grouped[(row['visits_187'], row['final_pc'])].append(row['value'])
        classes = [dict(visits_187=visits, final_pc=pc, values=values)
                   for (visits, pc), values in sorted(grouped.items())]
        sweeps.append(dict(initial_q=q, cycles=512, classes=classes,
                           exit_values=[row['value'] for row in rows
                                        if row['final_pc'] == '084']))
    if ([row['exit_values'] for row in sweeps] != [[0], [0]] or
            [(len(row['classes']), [len(c['values']) for c in row['classes']])
             for row in sweeps] != [(3, [1, 6, 249]), (3, [1, 5, 250])]):
        raise ValueError('held-byte outcome classes changed')
    long = [dict(initial_q=q, cycles=4096,
                 **run_case(mapping, base, q, value, 4096))
            for q in (1, 129) for value in (1, 128, 255)]
    if any(row['final_pc'] == '084' for row in long):
        raise ValueError('a nonzero long-run control exited unexpectedly')

    sources = [Path(__file__), HERE/'photo_controller_path.py',
               HERE/'photo_mapping_q_sweep.py', HERE/'photo_mapping_stream_screen.py',
               ASSUMED/'execute.py',
               MAPPINGS['fitted_swapped']]
    report = dict(status='held ADC-byte timing candidate, not recovered ADC wiring',
                  mapping=mapping['name'], input_pc='187',
                  stimulus='one byte held at D187 through every visit, compatible with ADC0800 latched output semantics',
                  sweeps=sweeps, long_nonzero_controls=long,
                  interpretation='Only byte 00 reaches 084 within 512 cycles. Every nonzero byte ends in the 187/188 loop in both Q fixtures; some briefly take other PCs and reenter. Representative nonzero bytes also end there after 4096 cycles.',
                  limitations=['The D187 connection, ADC output-enable, conversion schedule and startup Q are untraced hypotheses.',
                               'This is a held-byte test of one inner loop, not an end-to-end receiver or line-sample capture.',
                               'A bounded nonzero run does not prove the loop is infinite under all future external events.'],
                  source_sha256={str(path.relative_to(HERE.parent)): hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    out.parent.mkdir(parents=True, exist_ok=True)
    save(out, report)
    return report


if __name__ == '__main__':
    report = run(HERE/'results/adc-hold-187.json')
    print([(row['initial_q'], row['exit_values'],
            [(case['visits_187'], len(case['values'])) for case in row['classes']])
           for row in report['sweeps']])
