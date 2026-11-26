"""Replay the candidate U19/U12 row-0 latch on the matched-tail ADC pulse."""

import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
import joint_mask04_receive_impulse_memory as impulse
from joint_upper_source_screen import candidate
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_four_row_condition_screen import configured
from receiver_mask04_3ed_prom_latch import gate_high
from reference_modem import transmit


def capture(mapping, base, adc):
    scenario = configured(base, adc, 'previous', 'overflow', 1)
    row0_latch = None
    every_row_latch = None
    edges = 0
    rows = []
    previous = None
    with tempfile.TemporaryDirectory() as tmp:
        result = execute(mapping, scenario, impulse.CYCLES,
                         mode='integrated', out=tmp,
                         trace_limit=impulse.CYCLES)
        if (not result['clean'] or
                result['completed_cycles'] != impulse.CYCLES or
                result['read_sequence_visits'].get(0x3F8) != impulse.ADC_VISITS):
            raise ValueError('receive loop stopped')
        for line in (Path(tmp) / 'trace.jsonl').open():
            row = json.loads(line)
            if previous is not None and gate_high(previous) and not gate_high(row):
                if previous['pc'] != 0x3ED:
                    raise ValueError('raw gate moved away from 3ED')
                phase = edges % 4
                byte = previous['alu']['y']
                if phase == 0:
                    row0_latch = byte & 15
                    row0_edge_cycle = previous['cycle']
                if phase == 3:
                    if row0_latch is None or every_row_latch is None:
                        raise ValueError('row-3 gate before row-0 capture')
                    rows.append(dict(visit=edges // 4,
                                     row0_edge_cycle=row0_edge_cycle,
                                     row3_edge_cycle=previous['cycle'],
                                     qualified_row0=row0_latch,
                                     live_row3=byte & 7,
                                     unqualified_before_row3=every_row_latch))
                every_row_latch = byte & 15
                edges += 1
            previous = row
    if edges != 4 * impulse.ADC_VISITS or len(rows) != impulse.ADC_VISITS:
        raise ValueError(('candidate latch edge count changed', edges, len(rows)))
    return rows, result


def differences(left, right, field, start, stop):
    changed = [i for i in range(start, stop) if left[i][field] != right[i][field]]
    return dict(count=len(changed), first=changed[0] if changed else None,
                last=changed[-1] if changed else None,
                first_values=([left[changed[0]][field], right[changed[0]][field]]
                              if changed else None))


def run(out=HERE / 'results/joint-mask04-carryover-latch-pulse.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    samples = [127 - value for value in transmit(impulse.VARYING_DIBITS)]
    if len(samples) != impulse.SAMPLES or samples[25] != 0x51:
        raise ValueError('reference ADC source changed')
    offered = dict(baseline=impulse.held_samples(samples, 25, None),
                   pulse=impulse.held_samples(samples, 25, 0xB1))
    cases = []
    captured = {}
    for name, adc in offered.items():
        rows, result = capture(mapping, base, adc)
        captured[name] = rows
        cases.append(dict(input=name,
                          adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                          trace_digest=result['trace_digest'],
                          cycles=result['completed_cycles'],
                          raw_edges=4 * len(rows),
                          first_rows=rows[:2],
                          unqualified_values=sorted({
                              row['unqualified_before_row3'] for row in rows}),
                          row_sha256=hashlib.sha256(bytes(
                              value for row in rows
                              for value in (row['qualified_row0'],
                                            row['live_row3'],
                                            row['unqualified_before_row3']))).hexdigest()))
        print(name, result['trace_digest'], flush=True)
    a, b = captured['baseline'], captured['pulse']
    pulse_start = sum(47 if i % 8 < 7 else 46 for i in range(25))
    restored_start = pulse_start + 47
    windows = dict(pulse=(pulse_start, restored_start),
                   first_restored_visit=(restored_start, restored_start + 1),
                   later_tail=(restored_start + 1, impulse.ADC_VISITS))
    comparisons = {field: {name: differences(a, b, field, *bounds)
                           for name, bounds in windows.items()}
                   for field in ('qualified_row0', 'live_row3',
                                 'unqualified_before_row3')}
    focus = dict(baseline=a[restored_start], pulse=b[restored_start])
    paths = (Path(__file__), Path(impulse.__file__),
             HERE / 'receiver_mask04_3ed_prom_latch.py',
             HERE / 'receiver_four_row_condition_screen.py',
             HERE.parent / 'assumed/execute.py', HERE / 'reference_modem.py',
             MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(
        experiment='candidate raw-PROM row-0 latch of a prior ADC pulse',
        fixture=dict(pulse_sample=25, base_adc=0x51, pulse_adc=0xB1,
                     adc_visits=impulse.ADC_VISITS, cycles=impulse.CYCLES,
                     windows=windows,
                     gate='three-bit U11.D7 & U17.D3 & U18.D5 decode, NAND rise after 3ED',
                     qualified_latch='assumed U12 low four Y bits on row-0 edge only',
                     control='U12 clocked on every 3ED edge'),
        cases=cases, comparisons=comparisons,
        first_restored_visit=focus,
        limitations=[
            'PROM-to-NAND, NAND-to-U12, Y-to-U12, row qualifier and U12 consumer are untraced hypotheses.',
            'A retained previous-sample nibble is not a recovered dibit or USART RxD connection.',
            'The pulse is artificial; this does not establish robustness on a natural carrier offset.'
        ],
        source_sha256={str(path.relative_to(HERE.parents[4])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
