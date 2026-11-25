"""Isolate whether the 3F7 quarter-sine ROM read affects downstream state."""

import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent/'assumed'), str(HERE)]

from common import save
from execute import execute
from lower_i_input_pipeline import mapping_with_source
from photo_controller_path import fixture
from split_slice_probe import split_scenario

ROM_PC = 0x3F7
CYCLES = 1580
PULSE_VISIT = 20


def run_trace(mapping, base, bank=None, replay=None):
    scenario = split_scenario(base)
    scenario['initial']['q'] = 5
    if bank is not None:
        scenario['io']['read']['address']['bank_by_pc'] = {str(ROM_PC): bank}
        scenario['io']['read']['address']['evidence'] += (
            '; diagnostic A8 bank override at 3F7; physical bank driver untraced')
    if replay is not None:
        scenario['io']['read']['address']['pcs'].remove(ROM_PC)
        scenario['io']['read']['pc_sequences'][str(ROM_PC)] = replay
        scenario['io']['read']['evidence'] += (
            '; diagnostic replay of selected ROM bytes at 3F7; source and timing untraced')
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, CYCLES, mode='integrated',
                         out=temporary, trace_limit=CYCLES)
        trace = [json.loads(line) for line in
                 (Path(temporary)/'trace.jsonl').read_text().splitlines()]
    if not result['clean'] or len(trace) != CYCLES:
        raise ValueError('3F7 ROM run incomplete')
    ram = scenario['initial']['ram'][:]
    states = []
    for row in trace:
        for address, value in row['registers'].items():
            ram[int(address)] = value
        states.append(dict(ram=ram[:], q=row['q'], alu=row['alu'],
                           next_pc=row['next_pc'], stack=row['stack_after']))
    return dict(result=result, trace=trace, states=states)


def difference_indexes(left, right):
    if len(left) != len(right):
        raise ValueError('paired event counts differ')
    return [index for index, (a, b) in enumerate(zip(left, right)) if a != b]


def run(out=HERE/'results/lower-i-rom-dataflow.json'):
    _, base = fixture()
    mapping = mapping_with_source(6, 0)
    high = run_trace(mapping, base)
    low = run_trace(mapping, base, bank=0)
    high_rows = [row for row in high['trace'] if row['pc'] == ROM_PC]
    low_rows = [row for row in low['trace'] if row['pc'] == ROM_PC]
    if len(high_rows) != 192 or len(low_rows) != 192 or not all(
            row['external_read']['selected_by_alu'] for row in high_rows+low_rows):
        raise ValueError('3F7 selected ROM visit set changed')
    bytes_high = [row['external_read']['value'] for row in high_rows]
    bytes_low = [row['external_read']['value'] for row in low_rows]
    replay = run_trace(mapping, base, replay=bytes_high)
    if (replay['result']['trace_digest'] != high['result']['trace_digest'] or
            replay['states'] != high['states']):
        raise ValueError('explicit byte replay diverged from ROM read')
    changed = bytes_high[:]
    changed[PULSE_VISIT] = bytes_low[PULSE_VISIT]
    one_change = run_trace(mapping, base, replay=changed)
    site_indexes = [i for i, row in enumerate(high['trace']) if row['pc'] == ROM_PC]
    boundary_differences = difference_indexes(
        [replay['states'][i] for i in site_indexes],
        [one_change['states'][i] for i in site_indexes])
    changed_ram_indexes = sorted({address
        for original, alternative in zip(high['states'], low['states'])
        for address, (a, b) in enumerate(zip(original['ram'], alternative['ram']))
        if a != b})
    all_y_differences = difference_indexes(
        [row['alu']['y'] for row in high['trace']],
        [row['alu']['y'] for row in low['trace']])
    all_pc_differences = difference_indexes(
        [row['pc'] for row in high['trace']],
        [row['pc'] for row in low['trace']])
    alu_field_difference_counts = {field: sum(
        a['alu'][field] != b['alu'][field]
        for a, b in zip(high['trace'], low['trace']))
        for field in high['trace'][0]['alu']}
    one_byte_y_differences = difference_indexes(
        [row['alu']['y'] for row in replay['trace']],
        [row['alu']['y'] for row in one_change['trace']])
    one_byte_pc_differences = difference_indexes(
        [row['pc'] for row in replay['trace']],
        [row['pc'] for row in one_change['trace']])
    if (boundary_differences != [PULSE_VISIT] or
            changed_ram_indexes != [10] or all_y_differences or all_pc_differences or
            one_byte_y_differences or one_byte_pc_differences or
            any(count for field, count in alu_field_difference_counts.items()
                if field != 'f') or
            any(a['q'] != b['q'] for a, b in zip(high['states'], low['states'])) or
            any(a['stack'] != b['stack'] for a, b in zip(high['states'], low['states'])) or
            high['result']['final_state']['ram'][10] ==
            low['result']['final_state']['ram'][10]):
        raise ValueError('3F7 dataflow classification changed')
    paths = [Path(__file__), HERE/'lower_i_input_pipeline.py',
             HERE/'independent_slice_addresses.py', HERE/'independent_slice_fields.py',
             HERE/'split_slice_probe.py', HERE/'photo_controller_path.py',
             HERE.parent/'assumed/execute.py', HERE.parent/'model.py',
             HERE.parents[2]/'am27s31dc-prom/nokia-modem-am27s31dc.bin']
    report = dict(status='3F7 quarter-sine ROM byte dataflow under lower-I6 candidate',
                  fixture=dict(lower_i6_source='11.0', cycles=CYCLES,
                               initial_q=5, initial_ram=[0]*16,
                               high_bank=256, low_bank_override_at='3F7',
                               isolated_byte_change_visit=PULSE_VISIT),
                  observations=dict(selected_3f7_visits=len(high_rows),
                                    high_addresses_first_24=[row['external_read']['address']
                                                             for row in high_rows[:24]],
                                    high_values_first_24=bytes_high[:24],
                                    low_values_first_24=bytes_low[:24],
                                    explicit_replay_matches=True,
                                    isolated_byte_before=bytes_high[PULSE_VISIT],
                                    isolated_byte_after=bytes_low[PULSE_VISIT],
                                    isolated_byte_boundary_differences=boundary_differences,
                                    bank_comparison_ram_indexes=changed_ram_indexes,
                                    bank_comparison_y_differences=all_y_differences,
                                    bank_comparison_pc_differences=all_pc_differences,
                                    bank_comparison_alu_field_difference_counts=(
                                        alu_field_difference_counts),
                                    isolated_byte_y_differences=one_byte_y_differences,
                                    isolated_byte_pc_differences=one_byte_pc_differences,
                                    high_final_r10=high['result']['final_state']['ram'][10],
                                    low_final_r10=low['result']['final_state']['ram'][10],
                                    trace_digests={
                                        'high_bank': high['result']['trace_digest'],
                                        'low_bank_at_3f7': low['result']['trace_digest'],
                                        'high_byte_replay': replay['result']['trace_digest'],
                                        'one_byte_change': one_change['result']['trace_digest']}),
                  limitations=[
                      'A8 bank selection, lower-I6 pin assignment, startup state and clock are hypotheses.',
                      'This run does not trace a DAC output or establish quarter-sine values as line samples.',
                      'One-byte independence is tested at visit 20 of this one loop and startup fixture.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    print(run()['observations'])
