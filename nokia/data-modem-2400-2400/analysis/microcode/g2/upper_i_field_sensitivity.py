"""Test source and polarity sensitivity of upper-slice instruction fields."""

import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
from common import save
from execute import execute
from controller_bit_dispatch import controller_stream
from independent_slice_addresses import mapping_for
from photo_controller_path import fixture
from photo_mapping_stream_screen import MAPPINGS
from split_slice_probe import split_scenario

INPUT_PC = 0x38E
OUTPUT_PC = 0x39E
CYCLES = 1580
PULSE_VISIT = 20
FREE_BITS = (0, 1, 2, 3, 5, 7, 8)  # I4 and I6 follow the candidate slice links.


def run_trace(mapping, base, values):
    scenario = copy.deepcopy(base)
    scenario['initial']['q'] = 5
    scenario['io']['read']['pc_sequences'][str(INPUT_PC)] = values
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, CYCLES, mode='integrated',
                         out=temporary, trace_limit=CYCLES)
        trace = [json.loads(line) for line in
                 (Path(temporary)/'trace.jsonl').read_text().splitlines()]
    if not result['clean'] or len(trace) != CYCLES:
        raise ValueError('incomplete split-slice execution')
    return scenario, result, trace


def summary(trace, initial_ram):
    ram = initial_ram[:]
    boundaries = []
    outputs = []
    reads = []
    selected_inputs = 0
    for row in trace:
        for address, value in row['registers'].items():
            ram[int(address)] = value
        if row['pc'] == INPUT_PC:
            boundaries.append((tuple(ram), row['q'], row['alu'],
                               row['next_pc'], row['stack_after']))
            selected_inputs += bool(row['external_read']['selected_by_alu'])
        if row['pc'] == OUTPUT_PC:
            outputs.append(row['alu']['y'])
        event = row['external_read']
        if event.get('selected_by_alu') and 'address' in event:
            reads.append((row['cycle'], row['pc'], event['address'],
                          event['value'], row['alu']['y']))
    return boundaries, outputs, reads, selected_inputs


def changed_indexes(a, b):
    if len(a) != len(b):
        raise ValueError('paired sequence lengths differ')
    return [i for i, (left, right) in enumerate(zip(a, b)) if left != right]


def evaluate(mapping, scenario, bits):
    streams = {}
    for name, values in (('zero', [0]*128),
                         ('pulse', [16 if i == PULSE_VISIT else 0
                                    for i in range(128)]),
                         ('controller', [16*bit for bit in bits])):
        state, result, trace = run_trace(mapping, scenario, values)
        boundaries, outputs, reads, selected_inputs = summary(
            trace, state['initial']['ram'])
        streams[name] = dict(boundaries=boundaries, outputs=outputs,
                             reads=reads, selected_inputs=selected_inputs,
                             trace_digest=result['trace_digest'])
    zero, pulse, controller = (streams[name] for name in
                               ('zero', 'pulse', 'controller'))
    return dict(input_visits=len(zero['boundaries']),
                selected_input_visits=zero['selected_inputs'],
                selected_rom_reads=len(zero['reads']),
                distinct_rom_addresses=len({row[2] for row in zero['reads']}),
                output_visits=len(zero['outputs']),
                output_zero_tail=zero['outputs'][-3:],
                output_controller_distinct_after_8=sorted(
                    set(controller['outputs'][8:])),
                pulse_boundary_difference_indexes=changed_indexes(
                    zero['boundaries'], pulse['boundaries']),
                pulse_rom_difference_indexes=changed_indexes(
                    zero['reads'], pulse['reads']),
                pulse_rom_address_difference_indexes=[
                    i for i, (left, right) in enumerate(zip(
                        zero['reads'], pulse['reads']))
                    if left[2] != right[2]],
                pulse_output_difference_indexes=changed_indexes(
                    zero['outputs'], pulse['outputs']),
                trace_digests={name: row['trace_digest']
                               for name, row in streams.items()})


def run(out=HERE/'results/upper-i-field-sensitivity.json'):
    _, base = fixture()
    scenario = split_scenario(base)
    _, bits = controller_stream()
    polarity_cases = []
    for flip in (None, *FREE_BITS):
        mapping = mapping_for('b')
        before = None
        if flip is not None:
            before = mapping['fields']['i_high']['bits'][flip]
            after = before[1:] if before.startswith('!') else '!' + before
            mapping['fields']['i_high']['bits'][flip] = after
            mapping['fields']['i_high']['evidence'] += (
                f'; diagnostic polarity flip I{flip} {before}->{after}; '
                'an inverter on this net is not traced')
        polarity_cases.append(dict(flipped_upper_i_bit=flip,
                                   original_token=before,
                                   new_token=(mapping['fields']['i_high']['bits'][flip]
                                              if flip is not None else None),
                                   **evaluate(mapping, scenario, bits)))
    baseline = polarity_cases[0]
    first_flip = polarity_cases[1]
    if (baseline['pulse_output_difference_indexes'] != [PULSE_VISIT+1] or
            first_flip['pulse_boundary_difference_indexes'] != [PULSE_VISIT, PULSE_VISIT+1] or
            first_flip['pulse_output_difference_indexes'] or
            len(first_flip['pulse_rom_difference_indexes']) != 5 or
            first_flip['pulse_rom_address_difference_indexes'] != [70, 72, 73] or
            any(len(row['pulse_boundary_difference_indexes']) > 2
                for row in polarity_cases)):
        raise ValueError('upper-I polarity sensitivity changed')
    source_cases = []
    for target in (2, 7):
        for bit in range(8):
            mapping = mapping_for('b')
            original = mapping['fields']['i_high']['bits'][target]
            source = f'18.{bit}'
            mapping['fields']['i_high']['bits'][target] = source
            mapping['fields']['i_high']['evidence'] += (
                f'; diagnostic U8 I{target} source {original}->{source}; '
                'PROM-to-latch-to-U8 pin route untraced')
            source_cases.append(dict(target_upper_i_bit=target,
                                     original_token=original, source_token=source,
                                     duplicated_source=(bit == 6),
                                     **evaluate(mapping, scenario, bits)))
    if ([row['source_token'] for row in source_cases
         if row['pulse_output_difference_indexes']] != ['18.6', '18.6'] or
            any(len(row['pulse_boundary_difference_indexes']) > 2
                for row in source_cases)):
        raise ValueError('upper-I source sensitivity changed')
    paths = [Path(__file__), HERE/'independent_slice_addresses.py',
             HERE/'independent_slice_fields.py', HERE/'split_slice_probe.py',
             HERE/'controller_bit_dispatch.py', HERE/'photo_controller_path.py',
             ASSUMED/'execute.py', HERE.parent/'model.py',
             MAPPINGS['q3'],
             HERE.parents[2]/'am27s31dc-prom/nokia-modem-am27s31dc.bin']
    report = dict(status='upper instruction field sensitivity, not recovered wiring',
                  fixture=dict(mapping='separated instruction, upper B variant',
                               initial_q=5, initial_ram=[0]*16,
                               input_pc='38E', input_bit_lane='D4',
                               pulse_visit=PULSE_VISIT, cycles=CYCLES,
                               controller_bits=128,
                               high_slice_crosslinks='I4<-low I1; I6<-low I2'),
                  baseline_duplicate='U18.6 drives both U8 I2 and U8 I7 in the translated mapping',
                  polarity_cases=polarity_cases, source_cases=source_cases,
                  limitations=[
                      'Each polarity flip is a diagnostic alternative; no inverter on that specific U8 input net is traced.',
                      'U18 source substitutions are diagnostic alternatives; a fan-out from U18.6 is possible but unverified.',
                      'Only one upper bit at a time, Q=5, zero RAM and the upper-B mapping are tested.',
                      '39E is a candidate ALU output, not a traced DAC latch or line signal.',
                      'Controller bits use an assumed D4 source at 38E, not a measured board route.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    for row in report['polarity_cases']:
        print(row['flipped_upper_i_bit'], row['input_visits'],
              row['selected_rom_reads'],
              row['pulse_boundary_difference_indexes'],
              row['pulse_output_difference_indexes'])
    print('source cases with pulse output:',
          [(row['target_upper_i_bit'], row['source_token'])
           for row in report['source_cases']
           if row['pulse_output_difference_indexes']])
