"""Compare reversed ADC-bit streams followed by identical D3F8 input."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from adc_sample_path import DIBITS
from lower_i_d3f8_adc_decoder_screen import input_stream
from lower_i_d3f8_input import run_trace
from lower_i_prom_data_route import mapping_for
from photo_controller_path import fixture
from reference_modem import receive, transmit

SAMPLE_START = 64
PREFIX_SAMPLES = 32
TAIL_SAMPLES = 4
PREFIX_VISITS = 6000
TAIL_VISITS = 750
INPUT_PC = 0x3F8
CODE_PAIR = (3, 5)
BITS = (0, 4, 6)
CYCLES = 8 * (PREFIX_VISITS + TAIL_VISITS) + 47


def selected_bytes(run):
    return [row['external_read']['value'] for row in run['trace']
            if row['pc'] == INPUT_PC]


def tail_comparison(forward, reverse):
    a = forward['trace']
    b = reverse['trace']
    tail_start = [row['cycle'] for row in a if row['pc'] == INPUT_PC][PREFIX_VISITS]
    if tail_start != 8 * PREFIX_VISITS + 47:
        raise ValueError(('D3F8 visit cadence changed', tail_start))
    if any(left['pc'] != right['pc'] for left, right in zip(a, b)):
        raise ValueError('forward/reverse PC paths differ')
    boundary_differences = [i for i, (left, right) in enumerate(
        zip(forward['boundaries'][PREFIX_VISITS:],
            reverse['boundaries'][PREFIX_VISITS:])) if left != right]
    rom_differences = [left['cycle'] for left, right in
                       zip(a[tail_start:], b[tail_start:])
                       if (left['external_read'].get('selected_by_alu') and
                           right['external_read'].get('selected_by_alu') and
                           'address' in left['external_read'] and
                           'address' in right['external_read'] and
                           left['external_read']['address'] !=
                           right['external_read']['address'])]
    y_differences = {f'{pc:03X}': sum(
        left['pc'] == pc and left['alu']['y'] != right['alu']['y']
        for left, right in zip(a[tail_start:], b[tail_start:]))
        for pc in (0x3F8, 0x3F9, 0x3FA)}
    return dict(tail_start_cycle=tail_start,
                tail_boundary_differences=len(boundary_differences),
                first_different_tail_boundary=(boundary_differences[0]
                                               if boundary_differences else None),
                last_different_tail_boundary=(boundary_differences[-1]
                                              if boundary_differences else None),
                tail_selected_rom_address_differences=len(rom_differences),
                first_different_tail_rom_cycle=(rom_differences[0]
                                                if rom_differences else None),
                tail_alu_y_differences=y_differences)


def run(out=HERE / 'results/lower-i-d3f8-adc-history-witness.json'):
    pcm = transmit(DIBITS)
    if receive(pcm) != DIBITS[1:]:
        raise ValueError('reference waveform changed')
    adc = [127 - sample for sample in pcm[SAMPLE_START:
                                          SAMPLE_START + PREFIX_SAMPLES]]
    if len(adc) != PREFIX_SAMPLES:
        raise ValueError('ADC stimulus window changed')
    mapping = mapping_for('!10.6', '11.2')
    _, base = fixture()
    cases = []
    for bit in BITS:
        prefix = input_stream(adc, *CODE_PAIR, bit, 0)
        reversed_prefix = input_stream(adc[::-1], *CODE_PAIR, bit, 0)
        if len(prefix) != PREFIX_VISITS or len(reversed_prefix) != PREFIX_VISITS:
            raise ValueError('ADC hold schedule changed')
        tail = [CODE_PAIR[0]] * TAIL_VISITS
        forward_values = prefix + tail
        reverse_values = reversed_prefix + tail
        forward = run_trace(mapping, base, INPUT_PC, forward_values, CYCLES)
        reverse = run_trace(mapping, base, INPUT_PC, reverse_values, CYCLES)
        for label, result, values in [('forward', forward, forward_values),
                                      ('reverse', reverse, reverse_values)]:
            if (result['site_visits'] != PREFIX_VISITS + TAIL_VISITS or
                    result['site_selected'] != PREFIX_VISITS + TAIL_VISITS or
                    selected_bytes(result) != values or
                    len(result['boundaries']) != PREFIX_VISITS + TAIL_VISITS or
                    result['result']['final_state']['pc'] != INPUT_PC):
                raise ValueError(('ADC witness did not select all bytes', bit, label))
        comparison = tail_comparison(forward, reverse)
        if bit in (0, 4) and comparison['tail_boundary_differences'] != TAIL_VISITS:
            raise ValueError(('ADC history witness changed', bit, comparison))
        if bit == 6 and comparison['tail_boundary_differences'] != 0:
            raise ValueError(('ADC negative control changed', bit, comparison))
        cases.append(dict(adc_bit=bit,
                          prefix_bit_transitions=sum(
                              ((a >> bit) & 1) != ((b >> bit) & 1)
                              for a, b in zip(adc, adc[1:])),
                          forward_trace_digest=forward['result']['trace_digest'],
                          reverse_trace_digest=reverse['result']['trace_digest'],
                          forward_selected_rom_reads=len(forward['reads']),
                          reverse_selected_rom_reads=len(reverse['reads']),
                          selected_input_visits=forward['site_selected'],
                          final_pc='3F8', **comparison))
    paths = [Path(__file__), HERE / 'lower_i_d3f8_adc_decoder_screen.py',
             HERE / 'lower_i_d3f8_input.py', HERE / 'adc_sample_path.py',
             HERE / 'reference_modem.py', HERE / 'lower_i_prom_data_route.py',
             HERE / 'photo_controller_path.py', HERE / 'split_slice_probe.py',
             HERE.parent / 'assumed/execute.py', HERE.parent / 'model.py',
             HERE.parents[2] / 'am27s31dc-prom/nokia-modem-am27s31dc.bin']
    report = dict(status='conditional ADC-bit waveform-order history in real-PROM D3F8 loop',
                  fixture=dict(mapping='I7/A0=!10.6, I0/A1=11.2, lower I6=11.0',
                               initial_q=5, initial_ram=[0] * 16,
                               reference_dibits=DIBITS,
                               reference_sample_window=[SAMPLE_START,
                                                        SAMPLE_START + PREFIX_SAMPLES],
                               adc_code='127 - signed PCM sample',
                               adc_samples=adc,
                               decoder='03/05 by one complementary ADC code bit, noninverted; D0 high',
                               prefix_samples=PREFIX_SAMPLES,
                               prefix_hold_visits=[188, 187],
                               forward_and_reversed_prefix=True,
                               shared_tail='four sample periods of constant D3F8=03',
                               shared_tail_visits=TAIL_VISITS,
                               assumed_oscillator_hz=14400000,
                               cycles=CYCLES),
                  cases=cases,
                  limitations=[
                      'Only one reference waveform window and one Q/RAM seed are tested.',
                      'The ADC bit decoder, D0 bias, sample timing and physical route are hypotheses.',
                      'The shared tail is a controlled held input, not four measured continuation samples.',
                      'Different internal state and ALU Y do not identify a recovered bit or USART route; C3 remains open.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path,
                        default=HERE / 'results/lower-i-d3f8-adc-history-witness.json')
    args = parser.parse_args()
    print([(case['adc_bit'], case['tail_boundary_differences'])
           for case in run(args.out)['cases']])
