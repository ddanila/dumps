"""Characterize the Q=0 ROM walk exposed by a hypothetical held I0 level."""

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
from photo_controller_path import fixture
from photo_i0_hold_screen import hold_candidate
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

PC_127 = 0x127
PC_129 = 0x129
CONSTANTS = (0, 1, 2, 3, 4, 16, 255)
CYCLES = 2048


def trace_case(mapping, base, values, cycles, d12a=None):
    scenario = hold_candidate(base)
    scenario['initial']['q'] = 0
    scenario['io']['read']['pc_sequences'][str(PC_127)] = values
    if d12a is not None:
        scenario['io']['read']['pc_sequences'][str(0x12A)] = [d12a]
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary)
        result = execute(mapping, scenario, cycles, mode='integrated',
                         out=path, trace_limit=cycles)
        trace = [json.loads(line) for line in
                 (path/'trace.jsonl').read_text().splitlines()]
    if not result['clean']:
        raise ValueError('Q=0 ROM walk stopped in the model')
    reads = [row for row in trace if row['pc'] == PC_129]
    inputs = [row for row in trace if row['pc'] == PC_127]
    if any(not row['external_read'].get('selected_by_alu') for row in reads):
        raise ValueError('PC129 ceased selecting the lookup operand')
    return result, inputs, reads


def addresses(reads):
    return [row['external_read']['address'] for row in reads]


def run(out):
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    constant_cases = []
    for value in CONSTANTS:
        result, inputs, reads = trace_case(mapping, base, [value], CYCLES)
        actual = addresses(reads)
        expected = [0x100 + ((3 + (index + 1)*value) & 255)
                    for index in range(len(reads))]
        if actual != expected:
            raise ValueError(f'D127={value}: ROM address recurrence changed')
        constant_cases.append(dict(d127=value, cycles=CYCLES,
                                   input_visits=len(inputs), rom_reads=len(reads),
                                   distinct_rom_addresses=len(set(actual)),
                                   first_addresses=actual[:8], last_addresses=actual[-8:],
                                   first_rom_values=[row['external_read']['value']
                                                     for row in reads[:8]],
                                   final_pc=f'{result["final_state"]["pc"]:03X}',
                                   trace_digest=result['trace_digest']))

    other_input_cases = []
    for d12a in (0, 1, 3):
        result, _, reads = trace_case(mapping, base, [1], 512, d12a=d12a)
        actual = addresses(reads)
        if actual != [0x100 + ((4 + index) & 255)
                      for index in range(len(reads))]:
            raise ValueError(f'D12A={d12a}: D127-driven address walk changed')
        other_input_cases.append(dict(d127=1, d12a=d12a,
                                      rom_reads=len(reads),
                                      first_addresses=actual[:8],
                                      trace_digest=result['trace_digest']))

    _, bits = controller_stream()
    controller_cases = []
    for order, offered in (('forward', bits), ('reverse', bits[::-1])):
        result, inputs, reads = trace_case(mapping, base, offered, 1024)
        actual = addresses(reads)
        if len(inputs) < len(offered) or len(reads) < len(offered):
            raise ValueError('controller bits did not drive every early ROM step')
        prefix = 3
        expected = []
        for bit in offered:
            prefix = (prefix + bit) & 255
            expected.append(0x100 + prefix)
        if actual[:len(offered)] != expected:
            raise ValueError(f'{order}: controller-driven ROM walk changed')
        controller_cases.append(dict(order=order, bits_offered=len(offered),
                                     input_visits=len(inputs), rom_reads=len(reads),
                                     first_addresses=actual[:8],
                                     address_after_128_bits=actual[127],
                                     distinct_addresses_in_128_bits=len(set(actual[:128])),
                                     final_pc=f'{result["final_state"]["pc"]:03X}',
                                     trace_digest=result['trace_digest']))
    if controller_cases[0]['trace_digest'] == controller_cases[1]['trace_digest']:
        raise ValueError('reversing controller bit order had no trace effect')

    paths = [Path(__file__), HERE/'photo_i0_hold_screen.py',
             HERE/'photo_controller_path.py', HERE/'photo_mapping_q_sweep.py',
             HERE/'photo_mapping_stream_screen.py', HERE/'controller_bit_dispatch.py',
             ASSUMED/'execute.py', HERE.parent/'model.py', MAPPINGS['q3']]
    report = dict(status='hypothetical D127 ROM-index recurrence, not modem output',
                  fixture=dict(mapping='q3-photo-swapped with candidate A2/A3',
                               initial_q=0, initial_ram=[0]*16,
                               held_i0=1, read_phase_a1=0, assumed_input_pc='127',
                               selected_rom_pc='129'),
                  derived_address_rule='ROM address at nth PC129 visit (n starts at 1) = 0x100 + ((3 + sum of first n D127 bytes) mod 256)',
                  constant_cases=constant_cases,
                  other_input_cases=other_input_cases,
                  controller_cases=controller_cases,
                  limitations=[
                      'The original D127=1 fixture drives the ascending addresses; it is a stub, not observed board data.',
                      'The D127 input route and held I0 signal are untraced hypotheses.',
                      'The ROM address walk is not a demonstrated carrier, DAC sample stream or receiver path.',
                      'Only q3 and this ROM gate, Q=0 and zero RAM are tested here.'],
                  source_sha256={str(path.relative_to(HERE.parent)):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.parent.mkdir(parents=True, exist_ok=True)
    save(out, report)
    return report


if __name__ == '__main__':
    report = run(HERE/'results/photo-127-rom-walk.json')
    print([(case['d127'], case['rom_reads'], case['distinct_rom_addresses'])
           for case in report['constant_cases']])
    print([(case['order'], case['address_after_128_bits'])
           for case in report['controller_cases']])
