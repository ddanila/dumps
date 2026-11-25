"""Screen joint lower-slice I2/I7 sources for retained D3A1 ADC history."""

import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from controller_bit_dispatch import controller_stream
from dual_input_adc_nibble import CYCLES, SAMPLE_VISIT, trace_case
from lower_i_input_pipeline import mapping_with_source
from photo_controller_path import fixture
from split_slice_probe import split_scenario

SAMPLES = (1, 0x80, 0xFF)


def screen(mapping, scenario, bits):
    try:
        zero = trace_case(mapping, scenario, bits, 0)
    except ValueError as error:
        return dict(status='baseline incomplete', reason=str(error))
    if zero['adc_selected'] <= SAMPLE_VISIT or zero['controller_selected'] <= SAMPLE_VISIT:
        return dict(status='both inputs not selected through sample',
                    adc_selected=zero['adc_selected'],
                    controller_selected=zero['controller_selected'])
    trials = []
    for sample in SAMPLES:
        try:
            row = trace_case(mapping, scenario, bits, sample)
        except ValueError as error:
            trials.append(dict(sample=f'{sample:02X}', status='trial incomplete',
                               reason=str(error)))
            continue
        differences = [index for index, (left, right) in enumerate(
            zip(zero['snapshots'], row['snapshots'])) if left != right]
        trials.append(dict(sample=f'{sample:02X}', status='complete',
                           sample_boundary_changed=SAMPLE_VISIT in differences,
                           later_boundary_differences=[index for index in differences
                                                       if index > SAMPLE_VISIT],
                           same_pc_path=zero['pcs'] == row['pcs'],
                           same_selected_rom_addresses=(
                               zero['rom_addresses'] == row['rom_addresses']),
                           same_candidate_output_events=zero['output'] == row['output'],
                           trace_digest=row['trace_digest']))
    return dict(status='both inputs selected',
                adc_selected=zero['adc_selected'],
                controller_selected=zero['controller_selected'],
                baseline_trace_digest=zero['trace_digest'], trials=trials)


def run(out=HERE / 'results/receiver-joint-i2-i7-screen.json'):
    _, base = fixture()
    scenario = split_scenario(base)
    _, bits = controller_stream()
    cases = []
    for i2 in range(8):
        for i7 in range(8):
            mapping = mapping_with_source(2, i2)
            mapping['fields']['i']['bits'][7] = f'11.{i7}'
            mapping['fields']['i']['evidence'] += (
                f'; diagnostic joint U2 I2=U11.{i2}, I7=U11.{i7}; '
                'physical pin route untraced')
            cases.append(dict(i2_u11_bit=i2, i7_u11_bit=i7,
                              **screen(mapping, scenario, bits)))
    viable = [row for row in cases if row['status'] == 'both inputs selected']
    if len(cases) != 64 or len(viable) != 40:
        raise ValueError('joint mapping coverage changed')
    if any(len(row['trials']) != 3 or any(
            trial['status'] != 'complete' or trial['later_boundary_differences'] or
            not trial['same_pc_path'] or
            not trial['same_selected_rom_addresses'] or
            not trial['same_candidate_output_events']
            for trial in row['trials']) for row in viable):
        raise ValueError('joint mapping acquired a retained or output effect')
    current = {f'{sample:02X}': sum(trial['sample_boundary_changed']
                                  for row in viable for trial in row['trials']
                                  if trial['sample'] == f'{sample:02X}')
               for sample in SAMPLES}
    if current != {'01': 40, '80': 0, 'FF': 40}:
        raise ValueError(('current-boundary effect changed', current))
    paths = [Path(__file__), HERE / 'dual_input_adc_nibble.py',
             HERE / 'lower_i_input_pipeline.py',
             HERE / 'independent_slice_addresses.py',
             HERE / 'independent_slice_fields.py',
             HERE / 'split_slice_probe.py', HERE / 'controller_bit_dispatch.py',
             HERE / 'photo_controller_path.py',
             HERE.parent / 'assumed/execute.py', HERE.parent / 'model.py']
    report = dict(status='joint lower-slice I2/I7 U11 source screen finds no retained D3A1 receive sample under the tested 389-3A1 fixture',
                  fixture=dict(mapping='separated slice, independent upper B; I2 and I7 each assigned one direct U11 bit',
                               initial_q=5, initial_ram=[0] * 16,
                               controller='real 8031 scrambler bits at D38E',
                               adc='one candidate byte at D3A1 visit 20; otherwise zero',
                               sample_bytes=[f'{sample:02X}' for sample in SAMPLES],
                               cycles_per_run=CYCLES),
                  summary=dict(mappings=64, both_inputs_selected=len(viable),
                               other_mappings=24, sample_boundary_changed_by_byte=current,
                               retained_after_next_boundary=0,
                               selected_rom_address_changes=0,
                               candidate_output_event_changes=0),
                  cases=cases,
                  limitations=['The U11-to-U2 I2/I7 routes, ADC input and controller input are labelled untraced hypotheses.',
                               'Only Q=5, zero initial RAM, one controller bitstream, three sample bytes and 320 cycles per run are tested.',
                               'The 24 mappings without both inputs selected through the sample have no receive-history conclusion.',
                               'No ADC-to-USART path or recovered receive bit is identified; C3 remains open.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    print(run()['summary'])
