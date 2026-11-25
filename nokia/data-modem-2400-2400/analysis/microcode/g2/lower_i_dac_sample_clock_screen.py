"""Screen divided DAC latch clocks against held-symbol ROM-loop bytes."""

import hashlib
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
from common import save
from dac08_latch_probe import LS273DAC08
from lower_i_prom_data_route import mapping_for
from lower_i_timed_d0_stream import run_case
from photo_controller_path import fixture
from split_slice_probe import split_scenario

INPUT_VISITS = 6750
WARMUP_VISIT = 750
SAMPLES = 32
PHASES = 188
SAMPLE_RATE = 9600
CARRIER_BIN = 6  # 32-sample DFT: 6 * 9600/32 = 1800 Hz.
SOURCES = ('3F8_Y', '3F9_Y', '3FA_Y', '3F7_R10')
PHOTO = HERE.parents[2] / 'photos/PXL_20261123_114854803.jpg'


def dft_powers(values):
    if len(set(values)) < 2:
        return [0.0] * (SAMPLES // 2)
    return [sum(value * math.cos(2 * math.pi * k * n / SAMPLES)
                for n, value in enumerate(values)) ** 2 +
            sum(value * math.sin(2 * math.pi * k * n / SAMPLES)
                for n, value in enumerate(values)) ** 2
            for k in range(1, SAMPLES // 2 + 1)]


def spectrum(values):
    powers = dft_powers(values)
    total = sum(powers)
    peak = (max(range(1, len(powers) + 1), key=lambda k: powers[k - 1])
            if total > 1e-8 else None)
    period = next((size for size in (1, 2, 4, 8, 16, 32)
                   if all(values[i] == values[i - size]
                          for i in range(size, SAMPLES))), SAMPLES)
    return dict(peak_bin=peak,
                peak_hz=peak * SAMPLE_RATE // SAMPLES if peak else None,
                carrier_fraction=(powers[CARRIER_BIN - 1] / total
                                  if total > 1e-8 else 0.0),
                sample_period=period,
                distinct_codes=len(set(values)))


def capture(codes):
    latch = LS273DAC08()
    result = []
    for code in codes:
        latch.drive(code, 0)
        result.append(latch.drive(code, 1))
        latch.drive(code, 0)
    return result


def sequences(trace, initial_r10):
    by_source = {name: [] for name in SOURCES}
    r10 = initial_r10
    for row in trace:
        if '10' in row['registers']:
            r10 = row['registers']['10']
        pc = row['pc']
        if pc in (0x3F8, 0x3F9, 0x3FA):
            by_source[f'{pc:03X}_Y'].append(row['alu']['y'])
        if pc == 0x3F7:
            by_source['3F7_R10'].append(r10)
    if any(len(values) < INPUT_VISITS for values in by_source.values()):
        raise ValueError('held-symbol source did not repeat through sample window')
    return by_source


def sample_indices(phase):
    return [WARMUP_VISIT + phase + (375 * n) // 2
            for n in range(SAMPLES)]


def run(out=HERE / 'results/lower-i-dac-sample-clock-screen.json'):
    _, unmodified = fixture()
    base = split_scenario(unmodified)
    base['initial']['q'] = 5
    for bit in ('7', '0'):
        base['inputs']['instruction_bit_overrides'].pop(bit)
    for bit in ('0', '1'):
        base['inputs']['register_address_bit_overrides']['a'].pop(bit)
    mapping = mapping_for('!10.6', '11.2')
    controls = {}
    for label, value in (('zero', 8), ('one', 9)):
        result, trace = run_case(mapping, base, [value] * INPUT_VISITS,
                                 f'held D3F8 {value:02X}', True)
        controls[label] = dict(source=sequences(trace, base['initial']['ram'][10]),
                               trace_digest=result['trace_digest'])
    source_cases = []
    for source in SOURCES:
        phases = []
        for phase in range(PHASES):
            indices = sample_indices(phase)
            per_symbol = {}
            for label in ('zero', 'one'):
                codes = capture([controls[label]['source'][source][i]
                                 for i in indices])
                per_symbol[label] = dict(code=spectrum(codes),
                                         b5_by_y_bit={str(bit): spectrum([
                                             (code >> bit) & 1 for code in codes])
                                             for bit in range(8)},
                                         first_16_codes=codes[:16] if phase == 0 else None)
            phases.append(dict(phase=phase, symbols=per_symbol))
        both_carrier = [entry['phase'] for entry in phases
                        if all(entry['symbols'][label]['code']['peak_hz'] == 1800
                               for label in ('zero', 'one'))]
        b5_both = {str(bit): [entry['phase'] for entry in phases
                              if all(entry['symbols'][label]['b5_by_y_bit'][str(bit)]['peak_hz'] == 1800
                                     for label in ('zero', 'one'))]
                   for bit in range(8)}
        source_cases.append(dict(source=source,
                                 both_symbol_full_byte_carrier_phases=both_carrier,
                                 both_symbol_b5_carrier_phases=b5_both,
                                 phase_zero=phases[0]['symbols'],
                                 peak_hz_counts={label: {
                                     str(freq): sum(entry['symbols'][label]['code']['peak_hz'] == freq
                                                    for entry in phases)
                                     for freq in (None, 1800, 2100, 2400, 4800)}
                                     for label in ('zero', 'one')},
                                 sample_period_counts={label: {
                                     str(period): sum(entry['symbols'][label]['code']['sample_period'] == period
                                                      for entry in phases)
                                     for period in (1, 2, 4, 8, 16, 32)}
                                     for label in ('zero', 'one')},
                                 best_carrier_fraction={label: max(
                                     entry['symbols'][label]['code']['carrier_fraction']
                                     for entry in phases)
                                     for label in ('zero', 'one')}))
    if any(case['both_symbol_full_byte_carrier_phases'] or
           any(case['both_symbol_b5_carrier_phases'].values()) or
           case['sample_period_counts']['zero']['4'] != PHASES or
           case['sample_period_counts']['one']['8'] != PHASES or
           any(case['best_carrier_fraction'][label] > 1e-10
               for label in ('zero', 'one'))
           for case in source_cases):
        raise ValueError('divided direct-latch carrier screen changed')
    paths = [Path(__file__), HERE / 'lower_i_timed_d0_stream.py',
             HERE / 'lower_i_prom_data_route.py',
             HERE / 'dac08_latch_probe.py',
             HERE / 'photo_controller_path.py', HERE / 'split_slice_probe.py',
             HERE / 'DAC08-OUTPUT.md', PHOTO,
             ASSUMED / 'execute.py', HERE.parent / 'model.py',
             HERE.parents[2] / 'am27s31dc-prom/nokia-modem-am27s31dc.bin']
    report = dict(status='conditional divided-LS273 clock screen, not traced DAC output',
                  fixture=dict(mapping=mapping['name'], q=5,
                               held_d3f8_zero_one=[8, 9],
                               offered_visits_per_control=INPUT_VISITS,
                               sample_rate_hz=SAMPLE_RATE,
                               sample_interval_loop_visits='187/188 alternating',
                               sample_count=SAMPLES,
                               sample_window_start_visit=WARMUP_VISIT,
                               sampled_phase_offsets=PHASES,
                               full_byte_route='candidate source byte to LS273 D1..D8; Q-to-DAC order untraced',
                               b5_route='photo candidate DAC08 B5 from LS273 Q4; all eight source bits tested for D4'),
                  totals=dict(source_candidates=len(SOURCES),
                              full_byte_carrier_source_phases=sum(
                                  len(case['both_symbol_full_byte_carrier_phases'])
                                  for case in source_cases),
                              b5_carrier_source_bit_phases=sum(
                                  len(phases)
                                  for case in source_cases
                                  for phases in case['both_symbol_b5_carrier_phases'].values())),
                  controls={label: dict(trace_digest=data['trace_digest'])
                            for label, data in controls.items()},
                  source_cases=source_cases,
                  limitations=[
                      'The Y/R10-to-LS273 data route, latch clock, DAC byte order and controller-to-D3F8 connection are untraced hypotheses.',
                      'The photo supports only a candidate B5<-Q4 segment; no D4 source or complete DAC byte bus is verified.',
                      'A 32-sample digital code spectrum is a short carrier screen, not a measured analog line spectrum.',
                      'Only held D3F8 08/09 controls and the 14.4 MHz undivided microcycle case are tested.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    print(run()['totals'])
