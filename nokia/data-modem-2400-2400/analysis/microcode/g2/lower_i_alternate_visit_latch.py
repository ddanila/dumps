"""Test direct DAC08 latch bytes at two loop visits per 9,600 Hz sample."""

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]
from common import save
from controller_bit_dispatch import controller_stream
from lower_i_dac_sample_clock_screen import capture
from lower_i_nibble_stream_bridge import encoding, run_case
from lower_i_prom_data_route import mapping_for
from photo_controller_path import fixture
from split_slice_probe import split_scenario

SOURCES = ('3F8_Y', '3F9_Y', '3FA_Y', '3F7_R10')
SAMPLE_RATE = 9600
WINDOW = 64
WARMUP = 128
VISITS = 1024


def source_sequences(trace, initial_r10):
    result = {source: [] for source in SOURCES}
    r10 = initial_r10
    for row in trace:
        r10 = row['registers'].get('10', r10)
        pc = row['pc']
        if pc in (0x3F8, 0x3F9, 0x3FA):
            result[f'{pc:03X}_Y'].append(row['alu']['y'])
        if pc == 0x3F7:
            result['3F7_R10'].append(r10)
    if any(len(values) < VISITS for values in result.values()):
        raise ValueError('candidate source lacks 1,024 loop visits')
    return result


def spectrum(values):
    if len(values) != WINDOW:
        raise ValueError('wrong spectrum window')
    if len(set(values)) == 1:
        return dict(peak_hz=None, carrier_fraction=0.0,
                    answer_fraction=0.0, distinct_codes=1, period=1)
    powers = []
    for k in range(1, WINDOW // 2 + 1):
        real = sum(value * math.cos(2 * math.pi * k * n / WINDOW)
                   for n, value in enumerate(values))
        imaginary = sum(value * math.sin(2 * math.pi * k * n / WINDOW)
                        for n, value in enumerate(values))
        powers.append(real * real + imaginary * imaginary)
    total = sum(powers)
    peak = max(range(1, WINDOW // 2 + 1), key=lambda k: powers[k - 1])
    period = next((p for p in range(1, WINDOW // 2 + 1)
                   if all(values[i] == values[i - p]
                          for i in range(p, WINDOW))), None)
    return dict(peak_hz=peak * SAMPLE_RATE // WINDOW,
                carrier_fraction=powers[11] / total,
                answer_fraction=powers[13] / total,
                distinct_codes=len(set(values)), period=period)


def run(out=HERE / 'results/lower-i-alternate-visit-latch.json'):
    _, bits = controller_stream()
    if len(bits) != 128:
        raise ValueError('expected 128 controller bits')
    _, original = fixture()
    base = split_scenario(original)
    base['initial']['q'] = 5
    for bit in ('7', '0'):
        base['inputs']['instruction_bit_overrides'].pop(bit)
    for bit in ('0', '1'):
        base['inputs']['register_address_bit_overrides']['a'].pop(bit)
    mapping = mapping_for('!10.6', '11.2')
    controls = {}
    for label, values in (('zero', [8] * VISITS),
                          ('one', [9] * VISITS),
                          ('stream', encoding(bits, 8, 9, 8))):
        result, trace = run_case(mapping, base, values, label, trace=True)
        if result['read_sequence_visits'].get(0x3F8, 0) < VISITS:
            raise ValueError(f'{label} leaves loop before full sequence')
        controls[label] = dict(sources=source_sequences(
            trace, base['initial']['ram'][10]), digest=result['trace_digest'])
    cases = []
    for source in SOURCES:
        for phase in (0, 1):
            indices = [WARMUP + phase + 2 * n for n in range(WINDOW)]
            per_input = {}
            for label, data in controls.items():
                codes = capture([data['sources'][source][i] for i in indices])
                per_input[label] = dict(full=spectrum(codes),
                    photo_b5_by_source_bit={str(bit): spectrum(
                        [(code >> bit) & 1 for code in codes])
                        for bit in range(8)}, first_16_codes=codes[:16])
            cases.append(dict(source=source, phase=phase, inputs=per_input,
                              both_held_1800=all(
                                  per_input[label]['full']['peak_hz'] == 1800
                                  for label in ('zero', 'one'))))
    report = dict(fixture=dict(mapping=mapping['name'], q=5,
                               input_levels={'zero': 8, 'one': 9},
                               bit_hold_visits=8, sample_rate_hz=SAMPLE_RATE,
                               sample_interval_visits=2,
                               warmup_visits=WARMUP, window_samples=WINDOW,
                               assumed_microcycle_hz=153600),
                  totals=dict(source_phase_cases=len(cases),
                              both_held_1800_cases=sum(case['both_held_1800']
                                                       for case in cases)),
                  controls={label: dict(trace_digest=data['digest'])
                            for label, data in controls.items()},
                  cases=cases,
                  limitations=[
                      'The loop clock, controller D0 input, Y/R10-to-LS273 bus, LS273 clock and DAC08 bit order are untraced.',
                      'A 64-sample digital-code DFT is a diagnostic screen, not the analog line spectrum.',
                      'Held D3F8 bits are not proven steady modem dibits or the complete data2400 command.'])
    save(out, report)
    return report


if __name__ == '__main__':
    print(run()['totals'])
