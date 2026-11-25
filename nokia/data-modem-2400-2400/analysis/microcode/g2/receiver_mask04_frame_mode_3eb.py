"""Test the controller's 81-to-A1 frame edge as a hypothetical D3EB mode input."""

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
from joint_upper_source_screen import candidate
from lower_i_d3f8_full_adc import codes
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_four_row_condition_screen import CYCLES, PATTERNS, configured

WRAPPER_VISITS = 6001
ADC_VISITS = 1500
EDGE = 3000
MODES = {
    'held_81': [0x81] * WRAPPER_VISITS,
    'held_A1': [0xA1] * WRAPPER_VISITS,
    'rise_81_A1': [0x81] * EDGE + [0xA1] * (WRAPPER_VISITS - EDGE),
    'fall_A1_81': [0xA1] * EDGE + [0x81] * (WRAPPER_VISITS - EDGE),
}
WINDOWS = ((0, 375), (375, 750), (750, 1125), (1125, 1500))


def adc_values(pattern):
    samples = codes(pattern, 32, 'complementary')
    values = [sample for index, sample in enumerate(samples)
              for _ in range(47 if index % 8 < 7 else 46)]
    if len(values) != ADC_VISITS:
        raise ValueError('four-row ADC hold changed')
    return values


def scenario(base, values, wrapper_values):
    result = configured(base, values, 'previous', 'overflow', 1)
    result['io']['read']['pc_sequences'][str(0x3EB)] = wrapper_values
    result['io']['read']['evidence'] += (
        '; photo-compatible controller third-frame-byte to 3EB D hypothesis; '
        '81/A1 history edge, pin route and clock untraced')
    return result


def held_sweep(mapping, base):
    rows = []
    for high in range(16):
        byte = (high << 4) | 1
        result = execute(mapping,
                         scenario(base, [9] * ADC_VISITS,
                                  [byte] * WRAPPER_VISITS),
                         CYCLES, mode='integrated', trace_limit=0)
        rows.append(dict(byte=f'{byte:02X}', clean=result['clean'],
                         wrapper_visits=result['address_counts'].get(0x3EB, 0),
                         adc_visits=result['address_counts'].get(0x3F8, 0),
                         fourth_row_visits=result['address_counts'].get(0x3FE, 0),
                         final_pc=f'{result["final_state"]["pc"]:03X}',
                         trace_digest=result['trace_digest']))
    survivors = [row['byte'] for row in rows
                 if row['adc_visits'] == row['fourth_row_visits'] == ADC_VISITS]
    if survivors != [f'{(high << 4) | 1:02X}' for high in range(16)
                     if high != 3]:
        raise ValueError(('3EB high-nibble survivor set changed', survivors))
    return rows


def capture(mapping, base, pattern, mode, wrapper_values):
    offered = adc_values(pattern)
    candidate_scenario = scenario(base, offered, wrapper_values)
    ram = candidate_scenario['initial']['ram'][:]
    pc_digest = hashlib.sha256()
    states = []
    wrapper_y = []
    branch_tests = {0x3EC: [], 0x3ED: []}
    wrapper_tests = []
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, candidate_scenario, CYCLES,
                         mode='integrated', out=temporary, trace_limit=CYCLES)
        if (not result['clean'] or result['completed_cycles'] != CYCLES or
                result['address_counts'].get(0x3EB, 0) != WRAPPER_VISITS or
                result['address_counts'].get(0x3F8, 0) != ADC_VISITS or
                result['address_counts'].get(0x3FE, 0) != ADC_VISITS):
            raise ValueError(('mode-edge trace did not sustain', mode, pattern))
        for line in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(line)
            pc = row['pc']
            pc_digest.update(pc.to_bytes(2, 'little'))
            if pc == 0x3EB:
                event = row['external_read']
                if (not event.get('selected_by_alu') or
                        event['value'] != wrapper_values[len(wrapper_y)]):
                    raise ValueError(('3EB mode byte not selected', mode))
                wrapper_y.append(row['alu']['y'])
            elif pc == 0x3EA:
                wrapper_tests.append(row['test'])
            elif pc in branch_tests:
                branch_tests[pc].append((row['test'], row['next_pc']))
            for address, value in row['registers'].items():
                ram[int(address)] = value
            if pc == 0x3FE:
                states.append(bytes(ram) + bytes((row['q'],)))
    if (len(states) != ADC_VISITS or len(wrapper_y) != WRAPPER_VISITS or
            len(wrapper_tests) != WRAPPER_VISITS or
            len(branch_tests[0x3EC]) != WRAPPER_VISITS or
            len(branch_tests[0x3ED]) != WRAPPER_VISITS - 1):
        raise ValueError(('mode-edge capture count changed', mode))
    return dict(mode=mode, pattern=list(pattern),
                trace_digest=result['trace_digest'],
                pc_digest=pc_digest.hexdigest(),
                wrapper_y_sha256=hashlib.sha256(bytes(wrapper_y)).hexdigest(),
                state_sha256=hashlib.sha256(b''.join(states)).hexdigest(),
                wrapper_test_true=sum(wrapper_tests),
                states=states, wrapper_y=wrapper_y,
                wrapper_tests=wrapper_tests, branch_tests=branch_tests)


def state_differences(left, right):
    return [sum(a != b for a, b in zip(left['states'][start:end],
                                       right['states'][start:end]))
            for start, end in WINDOWS]


def branch_differences(left, right):
    return {f'{pc:03X}': dict(
        test=sum(a[0] != b[0] for a, b in zip(left['branch_tests'][pc],
                                              right['branch_tests'][pc])),
        next_pc=sum(a[1] != b[1] for a, b in zip(left['branch_tests'][pc],
                                                 right['branch_tests'][pc])))
            for pc in (0x3EC, 0x3ED)}


def run(out=HERE / 'results/receiver-mask04-frame-mode-3eb.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    held = held_sweep(mapping, base)
    cases = {}
    for name, pattern in (('waveform', PATTERNS[0]),
                          ('zero', PATTERNS[1])):
        cases[name] = {}
        for mode, wrapper_values in MODES.items():
            cases[name][mode] = capture(mapping, base, pattern,
                                        mode, wrapper_values)
            print('captured', name, mode, flush=True)
    pc_digests = {row['pc_digest'] for group in cases.values()
                  for row in group.values()}
    if len(pc_digests) != 1:
        raise ValueError('controller mode-byte edge changed four-row PC path')
    comparisons = {}
    for name, group in cases.items():
        comparisons[name] = {}
        for edge, baseline, target in (
                ('rise_81_A1', 'held_81', 'held_A1'),
                ('fall_A1_81', 'held_A1', 'held_81')):
            row = group[edge]
            comparisons[name][edge] = dict(
                state_vs_start=state_differences(row, group[baseline]),
                state_vs_target=state_differences(row, group[target]),
                wrapper_y_vs_start=sum(a != b for a, b in
                                       zip(row['wrapper_y'],
                                           group[baseline]['wrapper_y'])),
                wrapper_y_vs_target=sum(a != b for a, b in
                                        zip(row['wrapper_y'],
                                            group[target]['wrapper_y'])),
                wrapper_test_vs_start=sum(a != b for a, b in
                                          zip(row['wrapper_tests'],
                                              group[baseline]['wrapper_tests'])),
                branch_vs_start=branch_differences(row, group[baseline]))
    adc_sensitivity = {mode: state_differences(cases['waveform'][mode],
                                               cases['zero'][mode])
                       for mode in MODES}
    held_byte_differences = {
        name: [sum(a[index] != b[index] for a, b in
                   zip(group['held_81']['states'], group['held_A1']['states']))
               for index in range(17)]
        for name, group in cases.items()}
    for name, group in comparisons.items():
        for edge in ('rise_81_A1', 'fall_A1_81'):
            row = group[edge]
            if (row['state_vs_start'] != [0, 0, 375, 375] or
                    row['state_vs_target'] != [375, 375, 0, 0] or
                    any(item['test'] or item['next_pc']
                        for item in row['branch_vs_start'].values())):
                raise ValueError(('mode edge no-history comparison changed',
                                  name, edge))
    if len({tuple(value) for value in adc_sensitivity.values()}) != 1:
        raise ValueError('mode edge ADC-sensitivity count changed')
    report_cases = {name: {mode: {key: value for key, value in row.items()
                                  if key not in ('states', 'wrapper_y',
                                                 'wrapper_tests', 'branch_tests')}
                           for mode, row in group.items()}
                    for name, group in cases.items()}
    paths = [Path(__file__), HERE / 'controller_a3_a4_mode_edge.py',
             HERE / 'receiver_four_row_condition_screen.py',
             HERE / 'joint_upper_source_screen.py',
             HERE.parent / 'assumed/execute.py', HERE.parent / 'model.py',
             MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(
        experiment='controller 81-to-A1 frame byte as hypothetical D3EB mode edge',
        fixture=dict(mapping='joint upper-source mask 04',
                     dispatch='scenario [0,1,2,3]',
                     condition='inverted previous overflow at select 0',
                     adc='paired 32-sample complementary streams, 47/46 visits per sample',
                     wrapper_route='controller third CD4094 byte directly to 3EB D, untraced',
                     edge_wrapper_visit=EDGE,
                     edge_time='midpoint of shortened diagnostic receive run, not actual A3 duration',
                     modes=list(MODES)),
        held_high_nibble_sweep=held, cases=report_cases,
        comparisons=comparisons, adc_sensitivity=adc_sensitivity,
        held_mode_byte_differences=held_byte_differences,
        limitations=[
            'The CD4094-to-3EB data route and A3/A4 edge timing are photo-compatible hypotheses.',
            'A state change under the synthetic edge is not echo training or freeze.',
            'No line residual or USART receive output is identified.'],
        source_sha256={str(path.relative_to(HERE.parents[2])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    print(result['comparisons'], result['adc_sensitivity'])
