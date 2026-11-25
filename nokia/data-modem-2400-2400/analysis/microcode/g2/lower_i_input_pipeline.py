"""Screen U11 sources for a short D4-to-state pipeline in the split loop."""

import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
from common import save
from controller_bit_dispatch import controller_stream
from independent_slice_addresses import mapping_for
from photo_controller_path import fixture
from split_slice_probe import split_scenario
from upper_i_field_sensitivity import evaluate, run_trace, summary, changed_indexes

PCS = (0x38E, 0x389, 0x38A, 0x38C, 0x38F, 0x39E, 0x3A0, 0x3A1)


def mapping_with_source(target, bit):
    mapping = mapping_for('b')
    previous = mapping['fields']['i']['bits'][target]
    mapping['fields']['i']['bits'][target] = f'11.{bit}'
    mapping['fields']['i']['evidence'] += (
        f'; diagnostic U2 I{target} source {previous}->11.{bit}; '
        'U11-to-U6-to-U2 pin route untraced')
    return mapping


def lag_rule(trace, bits, pc):
    values = [row['alu']['y'] for row in trace if row['pc'] == pc]
    if len(values) != len(bits):
        raise ValueError(f'{pc:03X}: expected one visit per input bit')
    matches = []
    for lag in range(5):
        by_bit = [set(), set()]
        for index in range(8, len(values)):
            by_bit[bits[index-lag]].add(values[index])
        if all(len(group) == 1 for group in by_bit) and by_bit[0] != by_bit[1]:
            matches.append(dict(lag_visits=lag, zero=next(iter(by_bit[0])),
                                one=next(iter(by_bit[1]))))
    if len(matches) > 1:
        raise ValueError(f'{pc:03X}: ambiguous one-bit lag rule')
    return matches[0] if matches else None


def run(out=HERE/'results/lower-i-input-pipeline.json'):
    _, base = fixture()
    scenario = split_scenario(base)
    _, bits = controller_stream()
    source_cases = []
    for target in (2, 7):
        for bit in range(8):
            mapping = mapping_with_source(target, bit)
            source_cases.append(dict(target_lower_i_bit=target,
                                     source_token=f'11.{bit}',
                                     duplicated_source=(bit == 6),
                                     **evaluate(mapping, scenario, bits)))
    source0 = next(row for row in source_cases
                   if row['target_lower_i_bit'] == 2 and row['source_token'] == '11.0')
    source4 = next(row for row in source_cases
                   if row['target_lower_i_bit'] == 2 and row['source_token'] == '11.4')
    baseline = next(row for row in source_cases
                    if row['target_lower_i_bit'] == 2 and row['source_token'] == '11.6')
    if (any(row['input_visits'] != 128 or row['selected_input_visits'] != 128
            or row['pulse_output_difference_indexes'] != [21]
            for row in source_cases) or
            source0['pulse_boundary_difference_indexes'] != [20, 21, 22, 23] or
            source4['pulse_boundary_difference_indexes'] != [20, 21, 22, 23] or
            baseline['pulse_boundary_difference_indexes'] != [20, 21]):
        raise ValueError('lower-I source classification changed')
    pipeline_cases = []
    for bit in (0, 4, 6):
        mapping = mapping_with_source(2, bit)
        initial, _, zero_trace = run_trace(mapping, scenario, [0]*128)
        zero_state = summary(zero_trace, initial['initial']['ram'])
        pulses = []
        for visit in (20, 40, 80):
            state, result, trace = run_trace(
                mapping, scenario,
                [16 if index == visit else 0 for index in range(128)])
            pulse_state = summary(trace, state['initial']['ram'])
            pulses.append(dict(input_visit=visit,
                               boundary_difference_indexes=changed_indexes(
                                   zero_state[0], pulse_state[0]),
                               output_39e_difference_indexes=changed_indexes(
                                   zero_state[1], pulse_state[1]),
                               rom_address_difference_indexes=[
                                   i for i, (a, b) in enumerate(zip(
                                       zero_state[2], pulse_state[2]))
                                   if a[2] != b[2]],
                               trace_digest=result['trace_digest']))
        _, result, actual_trace = run_trace(
            mapping, scenario, [16*value for value in bits])
        rules = {f'{pc:03X}': lag_rule(actual_trace, bits, pc) for pc in PCS}
        if bit in (0, 4) and any(rule is None for rule in rules.values()):
            raise ValueError('candidate pipeline lost a controller-bit lag rule')
        pipeline_cases.append(dict(lower_i2_source=f'11.{bit}',
                                   pulse_cases=pulses, controller_lag_rules=rules,
                                   controller_trace_digest=result['trace_digest']))
    for row in pipeline_cases:
        duration = 2 if row['lower_i2_source'] == '11.6' else 4
        for pulse in row['pulse_cases']:
            visit = pulse['input_visit']
            if (pulse['boundary_difference_indexes'] != list(range(visit, visit+duration))
                    or pulse['output_39e_difference_indexes'] != [visit+1]
                    or pulse['rom_address_difference_indexes']):
                raise ValueError('pulse pipeline changed')
    paths = [Path(__file__), HERE/'upper_i_field_sensitivity.py',
             HERE/'independent_slice_addresses.py',
             HERE/'independent_slice_fields.py', HERE/'split_slice_probe.py',
             HERE/'controller_bit_dispatch.py', HERE/'photo_controller_path.py',
             HERE/'results/photo-b-constraints/q3-photo-swapped.json',
             ASSUMED/'execute.py', HERE.parent/'model.py',
             HERE.parents[2]/'am27s31dc-prom/nokia-modem-am27s31dc.bin']
    report = dict(status='diagnostic lower-instruction field and short input pipeline',
                  fixture=dict(mapping='separated slices, upper B variant',
                               initial_q=5, initial_ram=[0]*16,
                               controller_bits=128, input='D4 at PC38E',
                               pulse_visits=[20, 40, 80],
                               microinstructions_per_run=1580),
                  baseline_duplicate='U11.6 drives both U2 I2 and U2 I7 in the translated mapping',
                  source_cases=source_cases, pipeline_cases=pipeline_cases,
                  limitations=[
                      'U11 source substitutions are photo-compatible hypotheses, not traced U6-to-U2 nets.',
                      'The U18.6 upper I2/I7 fan-out and U8 crosslinks remain separate unverified assumptions.',
                      'The four-checkpoint memory is a modeled transient; no bit decision or analog output is demonstrated.',
                      'The real controller bits are offered at an assumed D4 route, not a measured interface.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    for row in run()['pipeline_cases']:
        print(row['lower_i2_source'],
              [(p['input_visit'], p['boundary_difference_indexes'])
               for p in row['pulse_cases']],
              row['controller_lag_rules']['3A1'])
