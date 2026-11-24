"""Test whether changing D38C bytes survive the independent-slice loop."""

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
from adc_sample_path import DIBITS
from controller_bit_dispatch import controller_stream
from independent_slice_fields import candidate_mapping
from photo_controller_path import fixture
from reference_modem import receive, transmit
from split_slice_probe import split_scenario

KINDS = ('separated', 'separated_reversed_upper')
D_PC = 0x38C
STATE_PC = 0x3A1


def state_after_loop(trace, initial_ram):
    ram = initial_ram[:]
    snapshots = []
    d_writes = []
    r6_after_3a0 = []
    r6_writes_at_3a0 = 0
    for row in trace:
        for index, value in row['registers'].items():
            ram[int(index)] = value
        if row['pc'] == D_PC:
            d_writes.append(dict(cycle=row['cycle'], d=row['external_read']['value'],
                                 r6=ram[6], alu_y=row['alu']['y']))
        if row['pc'] == 0x3A0:
            r6_after_3a0.append(ram[6])
            r6_writes_at_3a0 += '6' in row['registers']
        if row['pc'] == STATE_PC:
            snapshots.append(dict(ram=ram[:], q=row['q'], previous_y=row['alu']['y'],
                                  flags={key: row['alu'][key] for key in
                                         ('carry', 'overflow', 'zero', 'sign')},
                                  next_pc=row['next_pc'],
                                  stack=row['stack_after']))
    return snapshots, d_writes, r6_after_3a0, r6_writes_at_3a0


def run(out=HERE / 'results/independent-slice-d38c.json'):
    pcm = transmit(DIBITS)
    if receive(pcm) != DIBITS[1:]:
        raise ValueError('reference signal no longer recovers its dibits')
    adc = [127 - sample for sample in pcm[:128]]
    inverted = [128 + sample for sample in pcm[:128]]
    _, base = fixture()
    _, controller_bits = controller_stream()
    stimuli = dict(rom_constant=[19] * 128,
                   adc_complementary=adc,
                   adc_complementary_reverse=adc[::-1],
                   inverted_bus=inverted,
                   inverted_bus_reverse=inverted[::-1])
    cases = []
    rom_witnesses = []
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        for kind in KINDS:
            mapping = candidate_mapping(kind)
            rom_state = split_scenario(base)
            rom_state['initial']['q'] = 5
            rom_state['io']['read']['pc_sequences']['910'] = controller_bits
            rom_result = execute(mapping, rom_state, 1580, mode='integrated',
                                 out=directory, trace_limit=1580)
            rom_trace = [json.loads(line) for line in
                         (directory / 'trace.jsonl').read_text().splitlines()]
            first_input = next(row['cycle'] for row in rom_trace
                               if row['pc'] == 0x38E)
            selected = [row for row in rom_trace if row['cycle'] > first_input
                        and row.get('external_read', {}).get('selected_by_alu')
                        and 'address' in row['external_read']]
            if (not rom_result['clean'] or len(selected) != 127 or
                    any(row['pc'] != D_PC or
                        row['external_read']['address'] != 0x106 or
                        row['external_read']['value'] != 0x13 or
                        (row['instruction_i'] & 7) not in (5, 6, 7) or
                        (row['instruction_i_high'] & 7) in (5, 6, 7)
                        for row in selected)):
                raise ValueError('D38C lower-slice ROM witness changed')
            rom_witnesses.append(dict(mapping=kind, selected_reads=len(selected),
                                      pc='38C', rom_address='106', rom_value='13',
                                      low_instruction=selected[0]['instruction_i'],
                                      high_instruction=selected[0]['instruction_i_high'],
                                      trace_digest=rom_result['trace_digest']))
            baseline_snapshots = None
            for name, codes in stimuli.items():
                state = split_scenario(base)
                state['name'] += f'; candidate D38C input {name}'
                state['initial']['q'] = 5
                state['io']['read']['address']['pcs'].remove(D_PC)
                state['io']['read']['pc_sequences'][str(D_PC)] = codes
                state['io']['read']['pc_sequences']['910'] = controller_bits
                state['io']['read']['evidence'] = (
                    'Diagnostic ADC0800-like bytes at D38C and unchanged controller '
                    'bits at D38E; both source selection and timing are untraced')
                result = execute(mapping, state, 1580, mode='integrated',
                                 out=directory, trace_limit=1580)
                trace = [json.loads(line) for line in
                         (directory / 'trace.jsonl').read_text().splitlines()]
                snapshots, d_writes, r6_after_3a0, r6_writes_at_3a0 = state_after_loop(
                    trace, state['initial']['ram'])
                inputs = [row for row in trace if row['pc'] == 0x38E]
                outputs = sorted({row['alu']['y'] for row in trace
                                  if row['pc'] in (0x392, 0x39E)})
                if (not result['clean'] or len(trace) != 1580 or
                        len(d_writes) != 128 or len(snapshots) != 128 or
                        len(r6_after_3a0) != 128 or r6_writes_at_3a0 == 0 or
                        len(set(r6_after_3a0)) != 1 or
                        len(inputs) != 128 or
                        any(row['external_read']['held_last'] for row in inputs) or
                        outputs != [11]):
                    raise ValueError('D38C input fixture or candidate output changed')
                if baseline_snapshots is None:
                    baseline_snapshots = snapshots
                mismatches = sum(a != b for a, b in zip(baseline_snapshots, snapshots))
                if mismatches:
                    raise ValueError('D38C input now persists through loop boundary')
                cases.append(dict(mapping=kind, stimulus=name,
                                  offered_bytes=len(codes),
                                  distinct_offered_bytes=len(set(codes)),
                                  d_writes=len(d_writes),
                                  distinct_r6_at_38c=len({row['r6'] for row in d_writes}),
                                  first_d_writes=d_writes[:8],
                                  r6_after_3a0=sorted(set(r6_after_3a0)),
                                  r6_writes_at_3a0=r6_writes_at_3a0,
                                  loop_boundary_snapshots=len(snapshots),
                                  boundary_mismatches_vs_constant=mismatches,
                                  output_y_values=outputs,
                                  final_pc=f"{result['final_state']['pc']:03X}",
                                  trace_digest=result['trace_digest']))
    if len(cases) != 10 or not all(case['boundary_mismatches_vs_constant'] == 0
                                    for case in cases):
        raise ValueError('D38C comparison incomplete')
    paths = [Path(__file__), HERE / 'independent_slice_fields.py',
             HERE / 'adc_sample_path.py', HERE / 'reference_modem.py',
             HERE / 'controller_bit_dispatch.py', HERE / 'photo_controller_path.py',
             HERE / 'split_slice_probe.py',
             ASSUMED / 'execute.py', ASSUMED / 'common.py', HERE.parent / 'model.py']
    report = dict(status='diagnostic D38C input perturbation under independent slices',
                  fixture=dict(mappings=list(KINDS), cycles=1580, initial_q=5,
                               controller_bits=len(controller_bits), d_site='38C',
                               state_boundary='3A1',
                               adc_coding='diagnostic symmetric range: complementary=127-pcm, inverted=128+pcm',
                               reference_samples=len(pcm), samples_used=128),
                  rom_witnesses=rom_witnesses, cases=cases,
                  conclusion='D38C changes its R6 write, but all modeled RAM/Q/flags/stack states match the constant-byte run after each 3A1 boundary in this fixture.',
                  limitations=[
                      'ADC0800-to-D38C and USART-to-D38E routes, sample pacing, ROM gating and lane fields are hypotheses.',
                      'The reference waveform is generated independently; no physical ADC sample or USART receive bit is traced.',
                      'A zero boundary difference applies to this q3 loop and its tested input/mapping choices, not all receiver paths.'],
                  source_sha256={str(path.relative_to(HERE.parent)):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    print([(case['mapping'], case['stimulus'],
            case['distinct_r6_at_38c'], case['boundary_mismatches_vs_constant'])
           for case in report['cases']])
