"""Find and replay a raw-PROM NAND pulse after the ADC-sensitive table row."""

import hashlib
import itertools
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from joint_upper_source_screen import SELECTED_MASK, candidate
from lower_i_d3f8_full_adc import codes
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_four_row_condition_screen import configured

PATTERNS = ((0, 0, 0, 0), (1, 1, 1, 1), (2, 2, 2, 2),
            (3, 3, 3, 3), (0, 1, 3, 2))
ADC_VISITS = 1500
CYCLES = 32 * ADC_VISITS + 47
GATES = (
    ((0, 3, 1), (0, 6, 1), (2, 1, 1)),
    ((0, 3, 1), (1, 2, 1), (2, 1, 1)),
)


def level(row, literals):
    return all(((row['raw'][chip] >> bit) & 1) == value
               for chip, bit, value in literals)


def short_minimality(rows):
    target_count = sum(row['pc'] == 0x3FA for row in rows)
    literals = [(chip, bit, value) for chip in range(4)
                for bit in range(8) for value in (0, 1)]
    counts = {}
    for width in (1, 2, 3):
        found = []
        for group in itertools.combinations(literals, width):
            if len({item[:2] for item in group}) < width:
                continue
            sites = [row['pc'] for row in rows if level(row, group)]
            if len(sites) == target_count and set(sites) == {0x3FA}:
                found.append(group)
        counts[width] = found
        if found:
            break
    return counts


def capture(mapping, base, pattern, save_prefix=False):
    samples = codes(pattern, 32, 'complementary')
    values = [sample for index, sample in enumerate(samples)
              for _ in range(47 if index % 8 < 7 else 46)]
    if len(values) != ADC_VISITS:
        raise ValueError('four-row ADC hold changed')
    scenario = configured(base, values, 'previous', 'overflow', 1)
    high_sites = [Counter() for _ in GATES]
    rising_sites = [Counter() for _ in GATES]
    captured = [[] for _ in GATES]
    prefix = []
    previous = None
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, CYCLES, mode='integrated',
                         out=temporary, trace_limit=CYCLES)
        if (not result['clean'] or result['completed_cycles'] != CYCLES or
                result['address_counts'].get(0x3FA, 0) != ADC_VISITS or
                result['read_sequence_visits'].get(0x3F8, 0) != ADC_VISITS):
            raise ValueError(('four-row ADC replay did not sustain', pattern))
        for line in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(line)
            if save_prefix and len(prefix) < 200:
                prefix.append(row)
            for index, gate in enumerate(GATES):
                current = level(row, gate)
                if current:
                    high_sites[index][row['pc']] += 1
                if previous is not None and level(previous, gate) and not current:
                    rising_sites[index][(previous['pc'], row['pc'])] += 1
                    captured[index].append(previous['alu']['y'])
            previous = row
    gate_rows = []
    for index in range(len(GATES)):
        if (high_sites[index] != {0x3FA: ADC_VISITS} or
                rising_sites[index] != {(0x3FA, 0x3ED): ADC_VISITS} or
                len(captured[index]) != ADC_VISITS):
            raise ValueError(('PROM NAND edge is not isolated', pattern, index,
                              high_sites[index], rising_sites[index]))
        gate_rows.append(dict(literals=GATES[index],
                              high_sites={f'{pc:03X}': count for pc, count in
                                          high_sites[index].items()},
                              nand_rising_edges={f'{a:03X}->{b:03X}': count
                                                 for (a, b), count in
                                                 rising_sites[index].items()},
                              captured_y_sha256=hashlib.sha256(
                                  bytes(captured[index])).hexdigest(),
                              distinct_captured_y=len(set(captured[index])),
                              first_16_y=captured[index][:16]))
    if captured[0] != captured[1]:
        raise ValueError('two NAND candidates captured different bytes')
    return dict(pattern=list(pattern), first_adc_codes=samples[:8],
                trace_digest=result['trace_digest'],
                gates=gate_rows,
                captured_y=captured[0]), prefix


def run(out=HERE / 'results/receiver-prom-row-latch-gate.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), SELECTED_MASK)
    _, base = fixture()
    cases = []
    prefix = None
    for pattern in PATTERNS:
        row, maybe_prefix = capture(mapping, base, pattern,
                                    save_prefix=prefix is None)
        cases.append(row)
        if prefix is None:
            prefix = maybe_prefix
        print('captured', pattern, flush=True)
    minimal = short_minimality(prefix)
    if (minimal.get(1) != [] or minimal.get(2) != [] or
            set(minimal.get(3, [])) != set(GATES)):
        raise ValueError('minimal raw-PROM gate set changed')
    reference = cases[0]['captured_y']
    differences = [sum(a != b for a, b in zip(reference, row['captured_y']))
                   for row in cases]
    report_cases = [{key: value for key, value in row.items()
                     if key != 'captured_y'} for row in cases]
    paths = [Path(__file__), HERE / 'receiver_four_row_condition_screen.py',
             HERE / 'lower_i_d3f8_full_adc.py',
             HERE / 'joint_upper_source_screen.py',
             HERE / 'reference_modem.py', HERE.parent / 'assumed/execute.py',
             HERE.parent / 'model.py',
             HERE.parent / 'board/inventory.json',
             HERE.parents[2] / 'photos/PXL_20261123_114926601.jpg',
             MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(
        experiment='raw-PROM 3-literal NAND latch clock after ADC-sensitive row',
        fixture=dict(mapping='joint upper-source mask 08',
                     dispatch='scenario [0,1,2,3]',
                     condition='inverted previous overflow at select 0',
                     adc='complementary reference PCM, 47/46 visits per sample',
                     gate_search='all 32 raw PROM bits and complements, up to 3 literals, first 200 executed words',
                     latch='hypothetical rising NAND edge at 3ED captures previous 3FA Y'),
        minimal_gates={str(width): groups for width, groups in minimal.items()},
        cases=report_cases,
        captured_y_differences_from_zero=differences,
        limitations=[
            'The 3-input NAND, clock/data wire and output latch are topology hypotheses, not traced connections.',
            'The sampled Y bytes are not an executed bit decision or identified USART RxD input.',
            'The 200-word minimality screen is path-specific; all selected gates are then checked on five full traces.'],
        source_sha256={str(path.relative_to(HERE.parents[2])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    print('captured differences', result['captured_y_differences_from_zero'])
