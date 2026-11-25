"""Screen direct U11 lower-instruction alternatives for retained D3A1 input."""

import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent/'assumed'), str(HERE)]

from common import save
from controller_bit_dispatch import controller_stream
from dual_input_adc_nibble import SAMPLE_VISIT, trace_case
from lower_i_input_pipeline import mapping_with_source
from photo_controller_path import fixture
from split_slice_probe import split_scenario

SAMPLES = (1, 0x80, 0xFF)


def difference_indexes(left, right):
    return [index for index, (a, b) in enumerate(zip(left, right)) if a != b]


def screen_one(mapping, scenario, bits):
    try:
        zero = trace_case(mapping, scenario, bits, 0)
    except ValueError as error:
        return dict(status='zero run incomplete', reason=str(error))
    trials = []
    for sample in SAMPLES:
        try:
            run = trace_case(mapping, scenario, bits, sample)
        except ValueError as error:
            trials.append(dict(sample=sample, status='input run incomplete', reason=str(error)))
            continue
        boundaries = difference_indexes(zero['snapshots'], run['snapshots'])
        trials.append(dict(
            sample=sample, status='complete',
            input_selected_at_site=(run['adc_selected'] > SAMPLE_VISIT),
            controller_selected_within_window=run['controller_selected'],
            same_pc_path=(run['pcs'] == zero['pcs']),
            boundary_difference_indexes=boundaries,
            retained_after_next_boundary=any(index > SAMPLE_VISIT for index in boundaries),
            output_difference_indexes=difference_indexes(zero['output'], run['output'])
                if len(zero['output']) == len(run['output']) else None,
            rom_address_difference_indexes=difference_indexes(
                zero['rom_addresses'], run['rom_addresses'])
                if len(zero['rom_addresses']) == len(run['rom_addresses']) else None,
            trace_digest=run['trace_digest']))
    return dict(status='complete', adc_selected_within_window=zero['adc_selected'],
                controller_selected_within_window=zero['controller_selected'],
                visits_3a1=len(zero['snapshots']), output_events=len(zero['output']),
                zero_trace_digest=zero['trace_digest'], trials=trials)


def run(out=HERE/'results/lower-i-adc-retention-screen.json'):
    _, base = fixture()
    scenario = split_scenario(base)
    _, bits = controller_stream()
    rows = []
    for target in range(9):
        for source in range(8):
            mapping = mapping_with_source(target, source)
            row = screen_one(mapping, scenario, bits)
            rows.append(dict(lower_i_bit=target, u11_bit=source,
                             source_token=mapping['fields']['i']['bits'][target],
                             **row))
    viable = [row for row in rows if row['status'] == 'complete' and
              row['adc_selected_within_window'] > SAMPLE_VISIT and
              row['controller_selected_within_window'] > SAMPLE_VISIT]
    retained = [row for row in viable if any(
        trial['status'] == 'complete' and trial['retained_after_next_boundary']
        for trial in row['trials'])]
    changed_output = [row for row in viable if any(
        trial['status'] == 'complete' and trial['output_difference_indexes']
        for trial in row['trials'])]
    paths = [Path(__file__), HERE/'dual_input_adc_nibble.py',
             HERE/'lower_i_input_pipeline.py', HERE/'upper_i_field_sensitivity.py',
             HERE/'independent_slice_addresses.py', HERE/'independent_slice_fields.py',
             HERE/'split_slice_probe.py', HERE/'controller_bit_dispatch.py',
             HERE/'photo_controller_path.py', HERE.parent/'assumed/execute.py',
             HERE.parent/'model.py']
    report = dict(status='single lower-instruction source screen',
                  fixture=dict(mapping='separated slices, upper B, one U2 I pin from U11 bit',
                               initial_q=5, initial_ram=[0]*16,
                               controller='128 scrambler bits on D4 at PC38E',
                               adc_site='D3A1 visit 20; all other visits zero',
                               adc_samples=list(SAMPLES), cycles_per_run=320),
                  candidates=rows,
                  summary=dict(screened=len(rows), viable_both_inputs=len(viable),
                               retained_after_next_boundary=[
                                   [row['lower_i_bit'], row['u11_bit']] for row in retained],
                               changed_candidate_output=[
                                   [row['lower_i_bit'], row['u11_bit']] for row in changed_output]),
                  limitations=[
                      'Each single-pin U11 substitution is an untraced wiring hypothesis.',
                      'The 320-cycle fixture tests one Q/RAM seed and three ADC-like bytes.',
                      'A retained state or ALU event is not a recovered bit or physical DAC output.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    print(report['summary'])
