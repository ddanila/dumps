"""Test the 3EC computed-call source behind the candidate ADC loop."""

import copy
import hashlib
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
from lower_i_d3f8_full_adc import (
    LONG_CYCLES, LONG_SAMPLES, SHORT_CYCLES, SHORT_SAMPLES,
    codes, hold, scenario_for_full_byte,
)
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

DISPATCH_PC = 0x3EC
ADC_PC = 0x3F8
CYCLES = 16047
BYTES = (0x09, 0x59)
SOURCES = ('y', 'q', 'previous_y')


def trial(mapping, base, source, value, adc_byte):
    scenario = scenario_for_full_byte(base, [adc_byte] * 2200, 'complementary')
    scenario = copy.deepcopy(scenario)
    table = scenario['dispatch']['tables'][str(DISPATCH_PC)]
    if source == 'constant':
        scenario['dispatch']['source'] = 'scenario'
        scenario['dispatch']['mode'] = 'constant'
        scenario['dispatch']['value'] = value
    elif source == 'sequence':
        scenario['dispatch']['source'] = 'scenario'
        scenario['dispatch']['mode'] = 'sequence'
        scenario['dispatch']['sequence'] = value
    else:
        table['index_source'] = source
    table['evidence'] += (
        f'; diagnostic {source} index source at 3EC; U9 B-bus route untraced')
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, CYCLES,
                         mode='integrated', out=temporary, trace_limit=CYCLES)
        events = []
        selected_adc = 0
        for line in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(line)
            if row['pc'] == DISPATCH_PC:
                events.append(dict(cycle=row['cycle'],
                                   entry=row['dispatch_entry'],
                                   input=row.get('dispatch_input'),
                                   branch=row['branch']))
            elif row['pc'] == ADC_PC:
                selected_adc += bool(row['external_read'].get('selected_by_alu'))
    if len(events) != result['address_counts'].get(DISPATCH_PC, 0):
        raise ValueError('3EC dispatch event count changed')
    return dict(source=source, constant_index=value, adc_byte=f'{adc_byte:02X}',
                clean=result['clean'], stop=result['stop'],
                completed_cycles=result['completed_cycles'],
                final_pc=f"{result['final_state']['pc']:03X}",
                adc_visits=result['address_counts'].get(ADC_PC, 0),
                selected_adc_visits=result['read_sequence_visits'].get(ADC_PC, 0),
                alu_selected_adc_visits=selected_adc,
                dispatch_visits=len(events),
                entries=dict(sorted(Counter(event['entry'] for event in events).items())),
                first_12_dispatches=events[:12],
                selected_rom_reads=result['rom_reads']['selected_by_alu'],
                trace_digest=result['trace_digest'])


def reference_trial(mapping, base, source, pattern):
    samples = codes(pattern, LONG_SAMPLES, 'complementary')
    if source.startswith('sequence_'):
        values = [value for index, sample in enumerate(samples)
                  for value in [sample] * (94 if index % 4 < 3 else 93)]
    else:
        values = hold(samples)
    scenario = scenario_for_full_byte(base, values, 'complementary')
    scenario = copy.deepcopy(scenario)
    table = scenario['dispatch']['tables'][str(DISPATCH_PC)]
    if source == 'q':
        table['index_source'] = 'q'
        table['evidence'] += '; diagnostic Q-derived index; physical U9 B route untraced'
    elif source.startswith('sequence_'):
        scenario['dispatch']['mode'] = 'sequence'
        scenario['dispatch']['sequence'] = ([0, 2] if source == 'sequence_0_2'
                                            else [2, 0])
        table['evidence'] += '; diagnostic alternating two-row index; physical counter/buffer route untraced'
    result = execute(mapping, scenario, LONG_CYCLES,
                     mode='integrated', trace_limit=0)
    visits = result['read_sequence_visits'].get(ADC_PC, 0)
    return dict(source=source, pattern=list(pattern),
                distinct_adc_codes=len(set(samples)),
                offered_adc_visits=len(values),
                first_16_adc_codes=[f'{value:02X}' for value in samples[:16]],
                first_59_sample=next((index for index, value in enumerate(samples)
                                      if value == 0x59), None),
                clean=result['clean'], stop=result['stop'],
                completed_cycles=result['completed_cycles'],
                adc_visits=result['address_counts'].get(ADC_PC, 0),
                selected_adc_visits=visits,
                dispatch_visits=result['address_counts'].get(DISPATCH_PC, 0),
                final_pc=f"{result['final_state']['pc']:03X}",
                trace_digest=result['trace_digest'])


def two_row_detail(mapping, base, pattern):
    samples = codes(pattern, SHORT_SAMPLES, 'complementary')
    values = [value for index, sample in enumerate(samples)
              for value in [sample] * (94 if index % 4 < 3 else 93)]
    scenario = scenario_for_full_byte(base, values, 'complementary')
    scenario['dispatch']['mode'] = 'sequence'
    scenario['dispatch']['sequence'] = [0, 2]
    addresses = []
    pc_digest = hashlib.sha256()
    selected = 0
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, SHORT_CYCLES,
                         mode='integrated', out=temporary,
                         trace_limit=SHORT_CYCLES)
        for line in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(line)
            pc = row['pc']
            pc_digest.update(bytes((pc & 255, pc >> 8)))
            if pc == ADC_PC:
                selected += bool(row['external_read'].get('selected_by_alu'))
            elif pc == 0x3F9:
                addresses.append(row['external_read']['address'])
    if (not result['clean'] or selected != 3000 or
            len(addresses) != 3000):
        raise ValueError('two-row detailed ADC-to-ROM path changed')
    return dict(pattern=list(pattern), selected_adc_visits=selected,
                rom_lookup_visits=len(addresses),
                first_16_rom_addresses=[f'{value:03X}' for value in addresses[:16]],
                addresses=addresses,
                pc_digest=pc_digest.hexdigest(),
                trace_digest=result['trace_digest'])


def run(out=HERE / 'results/receiver-dispatch-source-screen.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), SELECTED_MASK)
    _, base = fixture()
    table = base['dispatch']['tables'][str(DISPATCH_PC)]
    if (base['dispatch']['source'] != 'scenario' or
            base['dispatch']['mode'] != 'constant' or
            base['dispatch']['value'] != 2 or
            table['base'] != 0x3EF or table['count'] != 4 or
            table['stride'] != 4):
        raise ValueError('base 3EC dispatch fixture changed')
    cases = [trial(mapping, base, source, value, byte)
             for source, value in ([('constant', index) for index in range(4)] +
                                   [(source, None) for source in SOURCES] +
                                   [('sequence', [(start + step * direction) % 4
                                                  for step in range(4)])
                                    for direction in (1, -1)
                                    for start in range(4)] +
                                   [('sequence', sequence)
                                    for sequence in ([0, 2], [2, 0], [1, 2],
                                                     [2, 1])])
             for byte in BYTES]
    control = [row for row in cases if row['source'] == 'constant' and
               row['constant_index'] == 2]
    if any(not row['clean'] or row['adc_visits'] != 2000 or
           row['selected_adc_visits'] != 2000 or
           row['alu_selected_adc_visits'] != 2000 or
           row['entries'] != {2: 2001}
           for row in control):
        raise ValueError('constant-index-2 ADC control changed')
    alternating = [row for row in cases if row['source'] == 'sequence' and
                   row['constant_index'] in ([0, 2], [2, 0])]
    if any(not row['clean'] or row['adc_visits'] != 1000 or
           row['alu_selected_adc_visits'] != 1000
           for row in alternating):
        raise ValueError('alternating-row ADC selection changed')
    reference = [reference_trial(mapping, base, source, pattern)
                 for source in ('constant_2', 'q', 'sequence_0_2',
                                'sequence_2_0')
                 for pattern in ((0, 1, 3, 2), (0, 0, 0, 0))]
    if any(row['adc_visits'] != 24000 or not row['clean']
           for row in reference if row['source'] == 'constant_2'):
        raise ValueError('reference ADC stream control changed')
    if any(row['adc_visits'] != 12000 or not row['clean']
           for row in reference if row['source'].startswith('sequence_')):
        raise ValueError('two-row reference ADC stream changed')
    detail = [two_row_detail(mapping, base, pattern)
              for pattern in ((0, 1, 3, 2), (0, 0, 0, 0))]
    if detail[0]['pc_digest'] != detail[1]['pc_digest']:
        raise ValueError('two-row reference PC paths diverged')
    differing_addresses = sum(left != right for left, right in zip(
        detail[0]['addresses'], detail[1]['addresses']))
    detail_summary = dict(patterns=[row['pattern'] for row in detail],
                          selected_adc_visits=[row['selected_adc_visits'] for row in detail],
                          rom_lookup_visits=[row['rom_lookup_visits'] for row in detail],
                          same_pc_path=True,
                          different_rom_addresses=differing_addresses,
                          first_16_rom_addresses=[row['first_16_rom_addresses']
                                                  for row in detail],
                          trace_digests=[row['trace_digest'] for row in detail])
    paths = [Path(__file__), HERE / 'joint_upper_source_screen.py',
             HERE / 'lower_i_d3f8_full_adc.py',
             HERE / 'lower_i_d3f8_upper_d_route.py',
             HERE / 'photo_controller_path.py',
             HERE / 'reference_modem.py',
             HERE / 'split_slice_probe.py',
             HERE.parent / 'assumed/execute.py', HERE.parent / 'model.py',
             MAPPINGS['q3'],
             HERE / 'results/joint-upper-source-mask08-mapping.json',
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(
        status='screen of forced and datapath-derived 3EC computed-call index sources under the joint map',
        fixture=dict(mapping='joint upper-source mask 08',
                     entry='same Q=5, zero-RAM, inverted-previous-sign ADC fixture',
                     dispatch_table='3EC BSR -> 3EF, 3F3, 3F7, 3FB rows',
                     base_index='constant scenario value 2, not a recovered U9 B-bus connection',
                     diagnostic_sources=['constant 0-3', *SOURCES,
                                         'four rotations each of 0-1-2-3 and 3-2-1-0',
                                         'alternating 0/2 and 1/2 in both phases'],
                     adc='held complementary byte 09 or 59 at D3F8',
                     cycles=CYCLES),
        cases=cases,
        reference_streams=reference,
        two_row_adc_to_rom_detail=detail_summary,
        limitations=[
            'U9 computed-call index source and physical ADC ingress are untraced.',
            'A short held-byte run does not demonstrate demodulation or echo cancellation.',
            'Datapath-derived y/q/previous_y are modeled candidate B-bus sources, not observed board nets.'],
        source_sha256={str(path.relative_to(HERE.parents[2])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    for row in report['cases']:
        print(row['source'], row['constant_index'], row['adc_byte'],
              row['clean'], row['adc_visits'], row['entries'])
