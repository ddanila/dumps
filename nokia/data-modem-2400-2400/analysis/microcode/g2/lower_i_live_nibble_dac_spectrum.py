"""Screen all sustained D3F8 nibbles and both 187/188 DAC clock orders."""

import hashlib
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
from common import save
from lower_i_dac_sample_clock_screen import (INPUT_VISITS, PHASES, SAMPLES,
                                             SAMPLE_RATE, SOURCES, capture,
                                             sequences)
from lower_i_prom_data_route import mapping_for
from lower_i_timed_d0_stream import run_case
from photo_controller_path import fixture
from split_slice_probe import split_scenario

LIVE = (1, 2, 3, 4, 5, 7, 8, 9, 12, 15)
WARMUP = 750
CARRIER_HZ = 1800
ANSWER_HZ = 2100
TWIDDLE = tuple(tuple((math.cos(2 * math.pi * k * n / SAMPLES),
                       math.sin(2 * math.pi * k * n / SAMPLES))
                      for n in range(SAMPLES))
                for k in range(1, SAMPLES // 2 + 1))
PHOTO = HERE.parents[2] / 'photos/PXL_20261123_114854803.jpg'


def indices(phase, order):
    extra = 0 if order == 'floor' else 1
    return [WARMUP + phase + (375 * n + extra) // 2
            for n in range(SAMPLES)]


def peak(values):
    if len(set(values)) < 2:
        return dict(hz=None, carrier_fraction=0.0,
                    distinct_codes=1, sample_period=1)
    powers = []
    for wave in TWIDDLE:
        real = sum(value * wave[n][0] for n, value in enumerate(values))
        imaginary = sum(value * wave[n][1] for n, value in enumerate(values))
        powers.append(real * real + imaginary * imaginary)
    bin_number = max(range(1, len(powers) + 1), key=lambda k: powers[k - 1])
    period = next((size for size in range(1, SAMPLES // 2 + 1)
                   if all(values[i] == values[i - size]
                          for i in range(size, SAMPLES))), None)
    return dict(hz=bin_number * SAMPLE_RATE // SAMPLES,
                carrier_fraction=powers[CARRIER_HZ * SAMPLES // SAMPLE_RATE - 1] / sum(powers),
                distinct_codes=len(set(values)), sample_period=period)


def run(out=HERE / 'results/lower-i-live-nibble-dac-spectrum.json'):
    _, unmodified = fixture()
    base = split_scenario(unmodified)
    base['initial']['q'] = 5
    for bit in ('7', '0'):
        base['inputs']['instruction_bit_overrides'].pop(bit)
    for bit in ('0', '1'):
        base['inputs']['register_address_bit_overrides']['a'].pop(bit)
    mapping = mapping_for('!10.6', '11.2')
    held = {}
    for nibble in LIVE:
        result, trace = run_case(mapping, base, [nibble] * INPUT_VISITS,
                                 f'held D3F8 {nibble:X}', True)
        held[nibble] = dict(values=sequences(trace, base['initial']['ram'][10]),
                            digest=result['trace_digest'])
    cases = []
    for source in SOURCES:
        for order in ('floor', 'ceil'):
            for nibble in LIVE:
                full_carrier = []
                full_answer = []
                photo_bits = {bit: [] for bit in range(8)}
                best_fraction = 0.0
                phase_zero = None
                periods = {}
                for phase in range(PHASES):
                    sampled = capture([held[nibble]['values'][source][i]
                                       for i in indices(phase, order)])
                    full = peak(sampled)
                    best_fraction = max(best_fraction, full['carrier_fraction'])
                    key = str(full['sample_period'])
                    periods[key] = periods.get(key, 0) + 1
                    if full['hz'] == CARRIER_HZ:
                        full_carrier.append(phase)
                    if full['hz'] == ANSWER_HZ:
                        full_answer.append(phase)
                    for bit in range(8):
                        if peak([(code >> bit) & 1 for code in sampled])['hz'] == CARRIER_HZ:
                            photo_bits[bit].append(phase)
                    if phase == 0:
                        phase_zero = dict(first_16_codes=sampled[:16], spectrum=full)
                cases.append(dict(source=source, clock_order=order,
                                  held_d3f8=nibble,
                                  full_byte_1800_phases=full_carrier,
                                  full_byte_2100_phases=full_answer,
                                  b5_1800_phases_by_source_bit={str(bit): phases
                                      for bit, phases in photo_bits.items()},
                                  best_1800_power_fraction=best_fraction,
                                  sample_period_counts=periods,
                                  phase_zero=phase_zero,
                                  trace_digest=held[nibble]['digest']))
    full_hits = sum(len(row['full_byte_1800_phases']) for row in cases)
    b5_hits = sum(len(phases) for row in cases
                  for phases in row['b5_1800_phases_by_source_bit'].values())
    paths = [Path(__file__), HERE / 'lower_i_dac_sample_clock_screen.py',
             HERE / 'lower_i_timed_d0_stream.py',
             HERE / 'lower_i_prom_data_route.py',
             HERE / 'dac08_latch_probe.py',
             HERE / 'photo_controller_path.py', HERE / 'split_slice_probe.py',
             HERE / 'DAC08-OUTPUT.md', PHOTO,
             ASSUMED / 'execute.py', HERE.parent / 'model.py',
             HERE.parents[2] / 'am27s31dc-prom/nokia-modem-am27s31dc.bin']
    report = dict(status='all sustained held-nibble direct-DAC screen under two divided clock orders',
                  fixture=dict(mapping=mapping['name'], q=5,
                               held_d3f8_nibbles=list(LIVE),
                               source_bytes=list(SOURCES),
                               sample_rate_hz=SAMPLE_RATE,
                               sample_count=SAMPLES,
                               sample_clock_orders=['floor 187/188', 'ceil 188/187'],
                               integer_phase_offsets=PHASES,
                               warmup_loop_visits=WARMUP,
                               photo_b5='DAC08 B5 candidate from LS273 Q4; all source bits offered to D4'),
                  totals=dict(held_controls=len(LIVE), source_order_nibble_cases=len(cases),
                              full_byte_1800_phase_hits=full_hits,
                              b5_1800_source_bit_phase_hits=b5_hits),
                  cases=cases,
                  limitations=[
                      'Identity source-byte-to-LS273 D bus, 9600 Hz latch clock and D3F8 input route are untraced hypotheses.',
                      'Only a B5<-Q4 segment is photo-supported; Y/R10 bit-to-D4 and other DAC bit routes are untraced.',
                      'Short 32-sample DFT peaks are diagnostic and are not an analog line measurement.',
                      'The two integer-visit schedules omit within-microword subcycle latch phases and alternate state/input mappings.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    print(run()['totals'])
