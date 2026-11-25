"""Test a common raw-PROM edge and its pre/post-ALU DAC latch phases."""

import hashlib
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from photo_controller_path import fixture
from photo_i0_hold_screen import hold_candidate
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from run import load

ROM_BIT = ('10', 2)
FIRST_LOOP = (0x127, 0x128, 0x129, 0x12A)
SECOND_LOOP = (0x12C, 0x12D, 0x12E, 0x12F)
CYCLES = 4000
START = 40
FREE_CLOCK = HERE / 'results/photo-joint-free-clock-sites.json'
SHAPE = HERE / 'results/photo-joint-waveform-shape-screen.json'
SURVIVORS = HERE / 'results/photo-random-dibit-validation.json'


def short_trace(mapping, base, d127):
    scenario = hold_candidate(base)
    scenario['initial']['q'] = 0
    scenario['io']['read']['pc_sequences'][str(0x127)] = [d127] * 1000
    scenario['io']['read']['pc_sequences'][str(0x12C)] = [0xEA]
    scenario['io']['read']['address']['bank_by_pc'] = {
        str(0x129): 256, str(0x12E): 256}
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, CYCLES, mode='integrated',
                         out=temporary, trace_limit=CYCLES)
        trace = [json.loads(line) for line in
                 (Path(temporary) / 'trace.jsonl').open()]
    if not result['clean'] or result['completed_cycles'] != CYCLES:
        raise ValueError('short transmitter phase trace stopped')
    edges = Counter()
    example = {}
    for before, after in zip(trace, trace[1:]):
        if after['cycle'] < START:
            continue
        left = (before['raw'][0] >> ROM_BIT[1]) & 1
        right = (after['raw'][0] >> ROM_BIT[1]) & 1
        if left == right:
            continue
        key = (before['pc'], after['pc'], left, right)
        edges[key] += 1
        if key not in example:
            example[key] = dict(cycle=after['cycle'],
                                previous_y=before['alu']['y'],
                                current_y=after['alu']['y'])
    allowed = {
        (0x128, 0x129, 0, 1), (0x129, 0x12A, 1, 0),
        (0x12D, 0x12E, 0, 1), (0x12E, 0x12F, 1, 0)}
    expected_edges = (allowed if d127 == 0x81 else
                      {(0x128, 0x129, 0, 1), (0x129, 0x12A, 1, 0)})
    if set(edges) != expected_edges:
        raise ValueError(('unexpected U10.D2 edge sites', d127, edges))
    for before_pc, after_pc, left, right in edges:
        if (edges[before_pc, after_pc, left, right] !=
                result['address_counts'].get(after_pc, 0)):
            raise ValueError('raw edge missed a reached ROM-loop word')
    return dict(d127=f'{d127:02X}', trace_digest=result['trace_digest'],
                edges=[dict(previous_pc=f'{before:03X}', pc=f'{after:03X}',
                            transition=f'{left}->{right}', count=count,
                            **example[before, after, left, right])
                       for (before, after, left, right), count in
                       sorted(edges.items())],
                loop_word_counts={f'{pc:03X}': result['address_counts'].get(pc, 0)
                                  for pc in FIRST_LOOP + SECOND_LOOP})


def prior_full_trace_comparison():
    free = json.loads(FREE_CLOCK.read_text())
    shape = json.loads(SHAPE.read_text())
    survivors = json.loads(SURVIVORS.read_text())['zero_error_survivors']
    if len(free['cases']) != 2 or len(survivors) != 6:
        raise ValueError('prior joined transmitter evidence changed')
    fits = shape['ranked_site_bus_fits']
    rows = []
    for bus in survivors:
        by_site = {row['pc']: row for row in fits
                   if row['input_bit_to_dac_code_bit'] == bus}
        if set(by_site) != {'127', '128', '129', '12A'}:
            raise ValueError('surviving bus missing a sampled site')
        rows.append(dict(input_bit_to_dac_code_bit=bus,
                         pre_rising_y128_r2=by_site['128']['mean_r2'],
                         post_rom_y129_r2=by_site['129']['mean_r2'],
                         post_falling_y12a_r2=by_site['12A']['mean_r2'],
                         post_rom_margin_over_pre_rising=round(
                             by_site['129']['mean_r2'] -
                             by_site['128']['mean_r2'], 6)))
    if not all(row['post_rom_margin_over_pre_rising'] > 0.11
               for row in rows):
        raise ValueError('phase-shape distinction changed')
    for case in free['cases']:
        if {site['pc'] for site in case['sites']} != {'127', '128', '129', '12A'}:
            raise ValueError('joined free-clock sites changed')
        if any(site['zero_error_buses'] != 12 for site in case['sites']):
            raise ValueError('joined data decisions changed')
    return dict(surviving_bus_fits=rows,
                joined_trace_digests={str(case['selector']): case['trace_digest']
                                      for case in free['cases']},
                waveform_shape_source='saved full-PROM joined site comparison',
                direct_dibit_decisions='all four ALU sites retain zero errors for the earlier 12 buses')


def run(out=HERE / 'results/photo-tx-prom-latch-phase.json'):
    lanes = load()
    patterns = {name: [(lanes[ROM_BIT[0]][pc] >> ROM_BIT[1]) & 1
                       for pc in loop]
                for name, loop in (('first', FIRST_LOOP),
                                   ('second', SECOND_LOOP))}
    if patterns != {'first': [0, 0, 1, 0],
                    'second': [0, 0, 1, 0]}:
        raise ValueError('raw U10.D2 phase pattern changed')
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    traces = [short_trace(mapping, base, d127) for d127 in (0x88, 0x81)]
    paths = [Path(__file__), FREE_CLOCK, SHAPE, SURVIVORS,
             HERE / 'photo_joint_free_clock_sites.py',
             HERE / 'photo_joint_waveform_shape_screen.py',
             HERE / 'photo_random_dibit_validation.py',
             HERE / 'photo_i0_hold_screen.py',
             HERE.parent / 'assumed/execute.py', HERE.parent / 'run.py',
             MAPPINGS['q3'],
             HERE.parents[2] / 'photos/PXL_20261123_114854803.jpg',
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(
        experiment='raw-PROM edge phase for candidate DAC-side 74LS273 clock',
        raw_signal='U10.D2', loop_levels=patterns,
        short_real_prom_traces=traces,
        prior_full_trace_comparison=prior_full_trace_comparison(),
        interpretation=('U10.D2 rises at 129/12E and falls at 12A/12F. '
                        'If its rising clock arrives before new ALU Y settles, '
                        'a latch captures the preceding word. An inverted '
                        'falling edge can capture the ROM-result Y from the '
                        'preceding word if its setup timing is met.'),
        limitations=[
            'U10.D2-to-latch wiring, inverter, divider and clock-to-data phase are untraced.',
            'The prior full-stream shape comparison covers the 127-12A loop, not the 12C-12F loop.',
            'A common PROM edge repeats once per four microinstructions and needs independent rate qualification for 9600 DAC samples/s.'],
        source_sha256={str(path.relative_to(HERE.parents[2])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    for case in result['short_real_prom_traces']:
        print(case['d127'], [(row['pc'], row['transition'], row['count'])
                             for row in case['edges']])
