"""Test a selected external D input in the read-valid 3ED–3FA ROM loop."""

import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent/'assumed'), str(HERE)]

from common import save
from controller_bit_dispatch import controller_stream
from execute import execute
from lower_i_prom_data_route import mapping_for
from photo_controller_path import fixture
from split_slice_probe import split_scenario

CYCLES = 1580
PULSE_VISIT = 20
INPUT_PC = 0x3F8
CONTROL_PC = 0x3FA
OTHER_PC = 0x3EB
OUTPUT_PCS = (0x3F8, 0x3F9, 0x3FA)


def run_trace(mapping, base, site, values, cycles=CYCLES):
    scenario = split_scenario(base)
    scenario['initial']['q'] = 5
    for bit in ('7', '0'):
        scenario['inputs']['instruction_bit_overrides'].pop(bit)
    for bit in ('0', '1'):
        scenario['inputs']['register_address_bit_overrides']['a'].pop(bit)
    scenario['io']['read']['pc_sequences'][str(site)] = values
    if site in scenario['io']['read']['address']['pcs']:
        scenario['io']['read']['address']['pcs'].remove(site)
    scenario['io']['read']['evidence'] += (
        f'; diagnostic D{site:03X} byte stream; physical source and clock untraced')
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, cycles, mode='integrated',
                         out=temporary, trace_limit=cycles)
        trace = [json.loads(line) for line in
                 (Path(temporary)/'trace.jsonl').read_text().splitlines()]
    if not result['clean'] or len(trace) != cycles:
        raise ValueError('D-site stream run incomplete')
    ram = scenario['initial']['ram'][:]
    boundaries = []
    for row in trace:
        for address, value in row['registers'].items():
            ram[int(address)] = value
        if row['pc'] == INPUT_PC:
            boundaries.append((tuple(ram), row['q'], row['alu'],
                               row['next_pc'], row['stack_after']))
    site_rows = [row for row in trace if row['pc'] == site]
    reads = [(row['pc'], row['external_read']['address']) for row in trace
             if row['external_read'].get('selected_by_alu') and
             'address' in row['external_read']]
    return dict(result=result, trace=trace, boundaries=boundaries, reads=reads,
                site_visits=len(site_rows),
                site_selected=sum(row['external_read']['selected_by_alu']
                                  for row in site_rows),
                outputs={f'{pc:03X}': [row['alu']['y'] for row in trace
                                      if row['pc'] == pc] for pc in OUTPUT_PCS})


def difference_indexes(left, right):
    return [index for index, (a, b) in enumerate(zip(left, right)) if a != b]


def first_pc_difference(left, right):
    return next((i for i, (a, b) in enumerate(zip(left['trace'], right['trace']))
                 if a['pc'] != b['pc']), None)


def compare(control, trial):
    common_reads = difference_indexes(control['reads'], trial['reads'])
    first_pc = first_pc_difference(control, trial)
    limit = CYCLES if first_pc is None else first_pc
    rom_address_difference_cycles_before_pc_divergence = [
        cycle for cycle, (a, b) in enumerate(zip(control['trace'][:limit],
                                                 trial['trace'][:limit]))
        if a['external_read'].get('selected_by_alu') and
        b['external_read'].get('selected_by_alu') and
        'address' in a['external_read'] and 'address' in b['external_read'] and
        a['external_read']['address'] != b['external_read']['address']]
    return dict(site_visits=trial['site_visits'],
                site_selected=trial['site_selected'],
                boundary_difference_indexes=difference_indexes(
                    control['boundaries'], trial['boundaries']),
                first_pc_divergence=first_pc,
                selected_rom_reads=len(trial['reads']),
                common_prefix_rom_address_differences=common_reads,
                rom_address_difference_cycles_before_pc_divergence=(
                    rom_address_difference_cycles_before_pc_divergence),
                output_event_counts={site: len(values) for site, values in
                                     trial['outputs'].items()},
                common_prefix_output_differences={site: difference_indexes(
                    values, trial['outputs'][site])
                    for site, values in control['outputs'].items()},
                final_pc=f"{trial['result']['final_state']['pc']:03X}",
                trace_digest=trial['result']['trace_digest'])


def run(out=HERE/'results/lower-i-d3f8-input.json'):
    _, base = fixture()
    mapping = mapping_for('!10.6', '11.2')
    _, bits = controller_stream()
    zero = run_trace(mapping, base, INPUT_PC, [1]*192)
    if zero['site_visits'] != 192 or zero['site_selected'] != 192:
        raise ValueError('selected D3F8 baseline changed')
    input_lanes = []
    for lane in (1, 2, 3):
        set_byte = 1 | (1 << lane)
        one = run_trace(mapping, base, INPUT_PC, [set_byte]*192)
        pulse_values = [1]*192
        pulse_values[PULSE_VISIT] = set_byte
        pulse = run_trace(mapping, base, INPUT_PC, pulse_values)
        actual = run_trace(mapping, base, INPUT_PC,
                           [1 | (bit << lane) for bit in bits])
        input_lanes.append(dict(lane=lane, set_byte=set_byte,
                                constant_one=compare(zero, one),
                                pulse=compare(zero, pulse),
                                controller=compare(zero, actual)))
    for row, expected_pulse, expected_stream in zip(
            input_lanes, ((31,291), (25,243), (34,315)), (28,38,53)):
        pulse = row['pulse']
        stream = row['controller']
        if (row['constant_one']['site_visits'] != 192 or
                row['constant_one']['first_pc_divergence'] is not None or
                (pulse['site_visits'], pulse['first_pc_divergence']) != expected_pulse or
                stream['site_visits'] != expected_stream or
                pulse['boundary_difference_indexes'] !=
                list(range(PULSE_VISIT, expected_pulse[0])) or
                not pulse['rom_address_difference_cycles_before_pc_divergence']):
            raise ValueError(f'D3F8 lane {row["lane"]} retention changed')
    control_base = run_trace(mapping, base, CONTROL_PC, [1]*192)
    control_actual = run_trace(mapping, base, CONTROL_PC,
                               [1 | (bit << 1) for bit in bits])
    control_case = compare(control_base, control_actual)
    if (control_case['site_visits'] != 192 or
            control_case['first_pc_divergence'] is not None or
            control_case['common_prefix_rom_address_differences'] or
            control_case['common_prefix_output_differences']['3F8'] or
            control_case['common_prefix_output_differences']['3F9'] or
            not control_case['common_prefix_output_differences']['3FA']):
        raise ValueError('D3FA control-site response changed')
    other_base = run_trace(mapping, base, OTHER_PC, [1]*192)
    other_lanes = []
    for lane in range(8):
        changed = run_trace(mapping, base, OTHER_PC, [1 ^ (1 << lane)]*192)
        equal = changed['result']['trace_digest'] == other_base['result']['trace_digest']
        other_lanes.append(dict(lane=lane, site_visits=changed['site_visits'],
                                site_selected=changed['site_selected'],
                                same_trace_digest=equal))
    if not all(row['same_trace_digest'] and row['site_selected'] == row['site_visits']
               for row in other_lanes):
        raise ValueError('D3EB control-site response changed')
    paths = [Path(__file__), HERE/'lower_i_prom_data_route.py',
             HERE/'lower_i_input_pipeline.py', HERE/'independent_slice_addresses.py',
             HERE/'independent_slice_fields.py', HERE/'split_slice_probe.py',
             HERE/'controller_bit_dispatch.py', HERE/'photo_controller_path.py',
             HERE.parent/'assumed/execute.py', HERE.parent/'model.py',
             HERE.parents[2]/'am27s31dc-prom/nokia-modem-am27s31dc.bin']
    report = dict(status='D3F8 selected-input retention and branch under PROM-data route',
                  fixture=dict(mapping='I7/A0=!10.6, I0/A1=11.2, lower I6=11.0',
                               initial_q=5, initial_ram=[0]*16,
                               cycles=CYCLES, selected_input='D3F8',
                               default_byte=1, pulse_visit=PULSE_VISIT,
                               controller_bits=128, control_site='D3FA'),
                  baseline=dict(site_visits=zero['site_visits'],
                                selected_rom_reads=len(zero['reads']),
                                output_event_counts={site:len(values) for site, values in
                                                     zero['outputs'].items()},
                                trace_digest=zero['result']['trace_digest']),
                  input_lanes=input_lanes,
                  d3fa_control=control_case,
                  d3eb_single_bit_controls=other_lanes,
                  limitations=[
                      'All D-site physical sources, bit lanes, latch timing and PROM-to-Am2901 data connections are untraced.',
                      'The 8031 stream is offered at a hypothetical D3F8 lane; its early exits do not prove a transmitter or receiver.',
                      'ALU Y is not a measured DAC input and no recovered receive bit is identified.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    for row in report['input_lanes']:
        print(row['lane'], row['pulse']['site_visits'],
              row['pulse']['first_pc_divergence'],
              row['controller']['site_visits'])
