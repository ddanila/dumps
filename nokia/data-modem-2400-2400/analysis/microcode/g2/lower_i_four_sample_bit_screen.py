"""Screen photo-compatible D3F8 nibble pairs at four/eight visits per bit."""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'assumed'))

from common import save
from controller_bit_dispatch import controller_stream
from lower_i_nibble_stream_bridge import (LIVE, encoding, run_case,
                                          site_values)
from lower_i_prom_data_route import mapping_for
from photo_controller_path import fixture
from split_slice_probe import split_scenario

INPUT_PC = 0x3F8
ROM_PC = 0x3F7


def run(out=HERE / 'results/lower-i-four-sample-bit-screen.json'):
    _, bits = controller_stream()
    if len(bits) != 128 or set(bits) != {0, 1}:
        raise ValueError('expected 128 controller bits with both levels')
    _, original = fixture()
    base = split_scenario(original)
    base['initial']['q'] = 5
    for bit in ('7', '0'):
        base['inputs']['instruction_bit_overrides'].pop(bit)
    for bit in ('0', '1'):
        base['inputs']['register_address_bit_overrides']['a'].pop(bit)
    mapping = mapping_for('!10.6', '11.2')

    cases = []
    for hold in (4, 8):
        for zero in LIVE:
            for one in LIVE:
                if zero == one:
                    continue
                values = encoding(bits, zero, one, hold)
                result, _ = run_case(mapping, base, values,
                                     f'{zero:X}/{one:X}, hold {hold}')
                visits = result['read_sequence_visits'].get(INPUT_PC, 0)
                cases.append(dict(hold=hold, zero=zero, one=one,
                                  offered_visits=len(values), consumed_visits=visits,
                                  complete=visits >= len(values),
                                  final_pc=result['final_state']['pc']))

    survivors = [row for row in cases if row['complete']]
    witnesses = []
    for case in survivors:
        hold, zero, one = (case[key] for key in ('hold', 'zero', 'one'))
        values = encoding(bits, zero, one, hold)
        traces = {}
        for label, supplied in (('stream', values),
                                ('zero', [zero] * len(values)),
                                ('one', [one] * len(values))):
            result, trace = run_case(mapping, base, supplied, label, trace=True)
            traces[label] = trace
            if label == 'stream':
                selected = [row['external_read'] for row in trace
                            if row['pc'] == INPUT_PC][:len(values)]
                if ([row['value'] for row in selected] != values or
                        not all(row['selected_by_alu'] for row in selected)):
                    raise ValueError('controller stream not selected at D3F8')
                case['trace_digest'] = result['trace_digest']
        sites = {}
        for pc, field in ((ROM_PC, 'rom_address'),
                          (INPUT_PC, 'alu_y'), (0x3F9, 'alu_y'),
                          (0x3FA, 'alu_y')):
            arrays = {label: site_values(trace, pc, field)[:len(values)]
                      for label, trace in traces.items()}
            if any(len(array) != len(values) for array in arrays.values()):
                raise ValueError('surviving loop lacks an output site')
            sites[f'{pc:03X}_{field}'] = dict(
                distinct_stream_values=len(set(arrays['stream'])),
                differs_from_zero=sum(a != b for a, b in
                                      zip(arrays['stream'], arrays['zero'])),
                differs_from_one=sum(a != b for a, b in
                                     zip(arrays['stream'], arrays['one'])))
        witnesses.append(dict(hold=hold, zero=zero, one=one, sites=sites))
    report = dict(fixture=dict(mapping=mapping['name'], q=5,
                               bits='128 locally ROM-executed 8031 scrambler bits',
                               input_pc='3F8', rom_pc='3F7', holds=[4, 8],
                               live_nibbles=list(LIVE)),
                  totals=dict(cases=len(cases), survivors=len(survivors)),
                  cases=cases, witnesses=witnesses,
                  limitations=[
                      'D3F8 bit source, control mapping, loop timing and DAC latch route are assumptions.',
                      'The 8031 bits are local scrambler output, not a full timed controller/DSP co-simulation.',
                      'ROM addresses and ALU Y are internal values, not proven DAC08 or line output.'])
    save(out, report)
    return report


if __name__ == '__main__':
    print(run()['totals'])
