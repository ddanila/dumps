"""Compare four PROM-executed ALU sample sites with pulse-shaped reference data."""

import argparse
import hashlib
import json
import math
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from photo_127_liveness import ROM
from photo_controller_path import fixture
from photo_dac_bus_permutations import SELECTED, mapped_codes
from photo_frame_toggle_edge_pulse import inspect
from photo_i0_hold_screen import hold_candidate
from photo_joint_free_clock_sites import SITES, sampled_sites
from photo_joint_tone_training_data import (DATA_STEP, SEGMENT_SYMBOLS,
                                            SILENCE_SYMBOLS, TONE_STEP,
                                            TONE_SYMBOLS, TOTAL_SYMBOLS,
                                            segment2_from_txd)
from photo_main_dibit_pulse import VISITS_PER_SYMBOL, scenario_inputs
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from reference_modem import phase_positions, raised_cosine, transmit

FREE = HERE / 'results/photo-joint-free-clock-sites.json'
TXREADY = HERE / 'results/main-loop-usart-txready.json'
BUSES = HERE / 'results/photo-dac-bus-permutations.json'
FIRST_SAMPLE = 32
LAST_SAMPLE = 480
LAGS = range(-8, 9)


def reference_templates(dibits):
    phases = phase_positions(dibits)
    templates = []
    for symbol_sign in (1, -1):
        envelope = []
        for n in range(512):
            value = sum(complex(math.cos(symbol_sign * math.pi * phases[k] / 8),
                                math.sin(symbol_sign * math.pi * phases[k] / 8)) *
                        raised_cosine((n - 8 * k) / 8)
                        for k in range(max(0, n // 8 - 4), min(64, n // 8 + 5)))
            envelope.append(value)
        for carrier_sign in (1, -1):
            signal = [value * complex(math.cos(carrier_sign * 2 * math.pi * 1800 * n / 9600),
                                      math.sin(carrier_sign * 2 * math.pi * 1800 * n / 9600))
                      for n, value in enumerate(envelope)]
            templates.append((symbol_sign, carrier_sign,
                              [value.real for value in signal],
                              [value.imag for value in signal]))
    return templates


def two_basis_r2(signal, in_phase, quadrature):
    count = len(signal)
    ymean = sum(signal) / count
    amean = sum(in_phase) / count
    bmean = sum(quadrature) / count
    yy = aa = bb = ab = ya = yb = 0.0
    for y, a, b in zip(signal, in_phase, quadrature):
        y -= ymean
        a -= amean
        b -= bmean
        yy += y * y
        aa += a * a
        bb += b * b
        ab += a * b
        ya += y * a
        yb += y * b
    determinant = aa * bb - ab * ab
    return ((ya * ya * bb + yb * yb * aa - 2 * ya * yb * ab) /
            (determinant * yy) if determinant > 0 and yy > 0 else 0.0)


def best_fit(codes, templates):
    best = (-1.0, None)
    for symbol_sign, carrier_sign, in_phase, quadrature in templates:
        for lag in LAGS:
            samples = range(FIRST_SAMPLE, LAST_SAMPLE)
            r2 = two_basis_r2([codes[n] for n in samples],
                              [in_phase[n + lag] for n in samples],
                              [quadrature[n + lag] for n in samples])
            if r2 > best[0]:
                best = (r2, dict(symbol_phase_sign=symbol_sign,
                                 carrier_sign=carrier_sign, lag_samples=lag))
    return round(best[0], 6), best[1]


def replay(selector, segment2, prior, rom, buses, base):
    target = [3] * SEGMENT_SYMBOLS + segment2
    inputs = ([TONE_STEP] * (TONE_SYMBOLS * VISITS_PER_SYMBOL) +
              [DATA_STEP] * (SILENCE_SYMBOLS * VISITS_PER_SYMBOL) +
              scenario_inputs(target))
    scenario = hold_candidate(base)
    scenario['name'] += '; waveform shape screen'
    scenario['initial']['q'] = 0
    scenario['io']['read']['pc_sequences'][str(0x127)] = inputs
    scenario['io']['read']['pc_sequences'][str(0x12c)] = [0xEA]
    scenario['io']['read']['address']['bank_by_pc'] = {str(0x129): 256,
                                                       str(0x12e): 256}
    cycles = (TOTAL_SYMBOLS * VISITS_PER_SYMBOL + 64) * 4
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapped(MAPPINGS['q3']), scenario, cycles,
                         mode='integrated', out=temporary, trace_limit=cycles)
        path = Path(temporary) / 'trace.jsonl'
        streams = sampled_sites(path)
        checked = inspect(path, rom, inputs, [0] * TOTAL_SYMBOLS)
    if not result['clean'] or result['completed_cycles'] != cycles or checked['pc129_visits'] != prior['pc129_visits']:
        raise ValueError(('PROM trace stopped or changed', selector))
    for site, raw in zip(prior['sites'], streams):
        digest = hashlib.sha256(bytes(mapped_codes(raw, SELECTED))).hexdigest()
        if digest != site['sample_sha256']:
            raise ValueError(('site sample digest changed', selector, site['pc']))
    templates = reference_templates(target)
    self_fit, _ = best_fit([value + 128 for value in transmit(target)], templates)
    if self_fit < 0.999:
        raise ValueError(('reference shape self-fit changed', selector, self_fit))
    rows = []
    for site, raw in zip(SITES, streams):
        suffix = raw[(TONE_SYMBOLS + SILENCE_SYMBOLS) * 8:]
        for index, bus in enumerate(buses):
            r2, alignment = best_fit(mapped_codes(suffix, bus), templates)
            rows.append(dict(pc=f'{site:03X}', bus_index=index,
                             pulse_shaped_reference_r2=r2, **alignment))
    return dict(selector=selector, dsc_microinstructions=cycles,
                pc129_visits=checked['pc129_visits'],
                trace_digest=result['trace_digest'],
                reference_self_fit_r2=self_fit,
                fits=rows)


def run(out=HERE / 'results/photo-joint-waveform-shape-screen.json'):
    free = json.loads(FREE.read_text())
    txready = json.loads(TXREADY.read_text())
    buses = [row['input_bit_to_dac_code_bit'] for row in
             json.loads(BUSES.read_text())['zero_error_candidates']]
    if len(free['cases']) != 2 or len(buses) != 12:
        raise ValueError('site or bus coverage changed')
    rom = ROM.read_bytes()
    _, base = fixture()
    cases = []
    for prior in free['cases']:
        selector = prior['selector']
        clock_case = next(row for row in txready['cases'] if row['selector'] == selector)
        cases.append(replay(selector, segment2_from_txd(clock_case),
                            prior, rom, buses, base))
    rank = []
    for site in SITES:
        for index, bus in enumerate(buses):
            values = [next(row['pulse_shaped_reference_r2'] for row in case['fits']
                           if row['pc'] == f'{site:03X}' and row['bus_index'] == index)
                      for case in cases]
            rank.append(dict(pc=f'{site:03X}', bus_index=index,
                             input_bit_to_dac_code_bit=bus,
                             r2_by_selector=dict(zip((case['selector'] for case in cases), values)),
                             mean_r2=round(sum(values) / len(values), 6)))
    rank.sort(key=lambda row: row['mean_r2'], reverse=True)
    margins = []
    for index in range(len(buses)):
        by_site = {row['pc']: row['mean_r2'] for row in rank
                   if row['bus_index'] == index}
        margin = by_site['129'] - max(by_site['127'], by_site['128'], by_site['12A'])
        if margin <= 0:
            raise ValueError(('PC129 did not lead this bus order', index, by_site))
        margins.append(round(margin, 6))
    paths = [Path(__file__), FREE, TXREADY, BUSES, ROM,
             HERE / 'photo_joint_free_clock_sites.py',
             HERE / 'photo_joint_tone_training_data.py',
             HERE / 'photo_dac_bus_permutations.py',
             HERE / 'photo_frame_toggle_edge_pulse.py',
             HERE / 'photo_controller_path.py', HERE / 'photo_i0_hold_screen.py',
             HERE / 'photo_main_dibit_pulse.py', HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             HERE / 'reference_modem.py', HERE.parent / 'assumed/execute.py',
             MAPPINGS['q3']]
    report = dict(status='pulse-shaped reference fit ranked across four full-PROM ALU capture sites and 12 photo-B5-compatible DAC bus orders',
                  fixture=dict(input='same joined A3 FF fill and actual A4/A5 GPC/GPA segment-2 bits',
                               sample='free-running hypothetical 9600 Hz capture at 127/128/129/12A',
                               reference='100%-rolloff raised-cosine V.26 ter-class signal at 1800 Hz; initial carrier phase fitted by two quadratures',
                               fit='maximize R² over standard/conjugated symbol orientation, positive/negative carrier sign and integer lag -8..8; use central samples 32..479 of the 512-sample A3+A4 stream',
                               no_analog_filter_fitted=True,
                               dac_buses=12),
                  cases=cases, ranked_site_bus_fits=rank,
                  pc129_winning_bus_orders=len(margins),
                  pc129_margin_over_best_other_site_by_bus=margins,
                  pc129_margin_range=[min(margins), max(margins)],
                  limitations=['The reference is a separate simplified modem model, not a measured Nokia line signal or DSC receiver.',
                               'Fitting phase orientation and 17 lags can favor a candidate; compare relative ranks, not absolute proof of wiring.',
                               'No analog reconstruction filter, 74LS373/74LS273 path or physical DAC bus is established.',
                               'The data input gate, symbol timing and 9600 Hz clock remain conditional assumptions.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path,
                        default=HERE / 'results/photo-joint-waveform-shape-screen.json')
    args = parser.parse_args()
    for row in run(args.out)['ranked_site_bus_fits'][:8]:
        print(row['pc'], row['bus_index'], row['mean_r2'])
