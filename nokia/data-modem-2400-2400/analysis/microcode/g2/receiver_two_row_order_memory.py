"""Test whether two-row receive state depends on ADC sample order."""

import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from joint_upper_source_screen import SELECTED_MASK, candidate
from lower_i_d3f8_full_adc import scenario_for_full_byte
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

VISITS = 3000
CYCLES = 16 * VISITS + 47
BASELINE = 0x09
FIRST = 188
HOLD = 94
LEVELS = (0x19, 0xA9)


def capture(mapping, base, levels):
    values = [BASELINE] * VISITS
    for index, level in enumerate(levels):
        values[FIRST + index * HOLD:FIRST + (index + 1) * HOLD] = [level] * HOLD
    scenario = scenario_for_full_byte(base, values, 'complementary')
    scenario['dispatch']['mode'] = 'sequence'
    scenario['dispatch']['sequence'] = [0, 2]
    ram = scenario['initial']['ram'][:]
    pc_digest = hashlib.sha256()
    rows, addresses, offered = [], [], []
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, CYCLES,
                         mode='integrated', out=temporary, trace_limit=CYCLES)
        for line in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(line)
            pc = row['pc']
            pc_digest.update(bytes((pc & 255, pc >> 8)))
            for address, value in row['registers'].items():
                ram[int(address)] = value
            if pc == 0x3F8:
                offered.append(row['external_read']['value'])
            elif pc == 0x3F9:
                addresses.append(row['external_read']['address'])
            elif pc == 0x3FA:
                rows.append((bytes(ram), row['q'], row['alu']['y']))
    if (not result['clean'] or result['completed_cycles'] != CYCLES or
            len(rows) != VISITS or len(addresses) != VISITS or offered != values or
            result['address_counts'].get(0x3EF, 0) != VISITS + 1):
        raise ValueError('two-row ordered-sample execution incomplete')
    return dict(rows=rows, addresses=addresses,
                pc_digest=pc_digest.hexdigest(), trace_digest=result['trace_digest'])


def comparison(left, right, holds):
    if left['pc_digest'] != right['pc_digest']:
        raise ValueError('sample order changed PC path')
    state_diffs = [i for i, (a, b) in enumerate(zip(left['rows'], right['rows']))
                   if a != b]
    address_diffs = [i for i, (a, b) in enumerate(zip(left['addresses'],
                                                      right['addresses'])) if a != b]
    last_a, last_b = left['rows'][-1], right['rows'][-1]
    return dict(first_state_difference=state_diffs[0] if state_diffs else None,
                last_state_difference=state_diffs[-1] if state_diffs else None,
                differences_after_return=sum(i >= FIRST + holds * HOLD
                                             for i in state_diffs),
                address_differences_after_return=sum(i >= FIRST + holds * HOLD
                                                     for i in address_diffs),
                final_q_offset=(last_b[1] - last_a[1]) & 255,
                final_register_offsets={f'R{i}': (b - a) & 255
                                        for i, (a, b) in enumerate(zip(last_a[0],
                                                                        last_b[0]))
                                        if a != b},
                final_rom_address_offset=(right['addresses'][-1] -
                                          left['addresses'][-1]) & 255,
                final_y3fa_offset=(last_b[2] - last_a[2]) & 255,
                pc_digest=left['pc_digest'])


def run(out=HERE / 'results/receiver-two-row-order-memory.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), SELECTED_MASK)
    _, base = fixture()
    forward = capture(mapping, base, LEVELS)
    reverse = capture(mapping, base, tuple(reversed(LEVELS)))
    control = capture(mapping, base, (BASELINE, BASELINE))
    matched_last_a = capture(mapping, base, (0xA9, 0x19, 0xA9))
    matched_last_b = capture(mapping, base, (0x19, 0xA9, 0xA9))
    row = comparison(forward, reverse, 2)
    report = dict(experiment='equal-histogram ADC hold orders with and without matched final level',
                  fixture=dict(dispatch='scenario [0,2] at 3EC',
                               route='hypothetical complementary ADC D3F8',
                               baseline=f'{BASELINE:02X}',
                               first_visit=FIRST, hold_visits=HOLD,
                               levels=[f'{value:02X}' for value in LEVELS],
                               total_visits=VISITS),
                  comparison=row,
                  forward_vs_baseline=comparison(control, forward, 2),
                  reverse_vs_baseline=comparison(control, reverse, 2),
                  matched_last_level=dict(
                      schedules=('A9,19,A9', '19,A9,A9'),
                      comparison=comparison(matched_last_a, matched_last_b, 3)),
                  trace_digests=dict(forward=forward['trace_digest'],
                                     reverse=reverse['trace_digest'],
                                     control=control['trace_digest'],
                                     matched_last_a=matched_last_a['trace_digest'],
                                     matched_last_b=matched_last_b['trace_digest']),
                  source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    save(out, report)
    return report


if __name__ == '__main__':
    print(run()['comparison'])
