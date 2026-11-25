"""Locate carrier-bearing DAC data bits in the joint mask-04 PROM stream."""

import copy
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
from joint_four_row_retention_tx import (candidate, fixture, hold_candidate,
                                         mapped, mapping_with_upper_source,
                                         MAPPINGS, split_scenario)
from photo_dac_bus_permutations import mapped_codes
from photo_joint_line_filter_screen import BUSES
from photo_joint_tone_training_data import DATA_STEP, TONE_STEP, TONE_SYMBOLS
from photo_main_dibit_pulse import VISITS_PER_SYMBOL
from photo_tx_divided_prom_clock import capture

SAMPLE_HZ = 9600
SAMPLE_COUNT = TONE_SYMBOLS * 8
LATE_START = 64


def phasor(values, frequency_hz):
    angle = 2 * math.pi * frequency_hz / SAMPLE_HZ
    return complex(sum(value * math.cos(angle * i) for i, value in enumerate(values)),
                   -sum(value * math.sin(angle * i) for i, value in enumerate(values)))


def replay(mapping, base, step):
    scenario = split_scenario(hold_candidate(base))
    scenario['name'] += '; joint-map DAC-bit contribution audit'
    scenario['inputs']['register_address_bit_overrides']['a_high'] = copy.deepcopy(
        scenario['inputs']['register_address_bit_overrides']['a'])
    for policy in scenario['inputs']['register_address_bit_overrides']['a_high'].values():
        policy['evidence'] += '; untraced high-slice A pin diagnostic level'
    scenario['initial']['q'] = 0
    scenario['io']['read']['pc_sequences'][str(0x127)] = [step] * (
        TONE_SYMBOLS * VISITS_PER_SYMBOL + 1)
    scenario['io']['read']['pc_sequences'][str(0x12C)] = [0xEA]
    scenario['io']['read']['address']['bank_by_pc'] = {
        str(0x129): 256, str(0x12E): 256}
    cycles = (TONE_SYMBOLS * VISITS_PER_SYMBOL + 64) * 4
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, cycles, mode='integrated',
                         out=temporary, trace_limit=cycles)
        samples = capture(Path(temporary) / 'trace.jsonl', SAMPLE_COUNT)
    if (not result['clean'] or result['completed_cycles'] != cycles or
            samples['captured_samples'] != SAMPLE_COUNT):
        raise ValueError(('PROM run failed', step, result['stop']))
    return samples, result['trace_digest']


def measure(raw, bus, expected_hz):
    codes = mapped_codes(raw, bus)[LATE_START:]
    full = phasor([code - 128 for code in codes], expected_hz)
    bits = []
    for source_bit, code_bit in enumerate(bus):
        levels = [((code >> code_bit) & 1) for code in codes]
        component = phasor([level * (1 << code_bit) for level in levels], expected_hz)
        bits.append(dict(source_bit=source_bit, dac_code_bit=code_bit,
                         transitions=sum(a != b for a, b in zip(levels, levels[1:])),
                         expected_hz_amplitude=round(abs(component), 6),
                         expected_hz_power_fraction=round(
                             abs(component) ** 2 / abs(full) ** 2, 6),
                         in_phase_fraction=round(
                             (component * full.conjugate()).real / abs(full) ** 2, 6)))
    if abs(sum((phasor([((code >> row['dac_code_bit']) & 1) *
                        (1 << row['dac_code_bit']) for code in codes], expected_hz)
                for row in bits), 0j) - full) > 1e-6:
        raise ValueError('DAC bit phasors do not sum to full code')
    return dict(bus=bus, full_expected_hz_amplitude=round(abs(full), 6),
                bit_contributions=bits)


def run(out=HERE / 'results/joint-mask04-dac-bit-contributions.json'):
    buses = json.loads(BUSES.read_text())['zero_error_survivors']
    if len(buses) != 6 or any(bus[4] != 3 or bus[6:] != [6, 7]
                              for bus in buses):
        raise ValueError('photo-compatible DAC bus family changed')
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    cases = []
    for name, step, frequency in (('A1_2100_tone', TONE_STEP, 2100),
                                  ('unmodulated_1800_carrier', DATA_STEP, 1800)):
        samples, digest = replay(mapping, base, step)
        phases = []
        for phase in ('pre_rising', 'post_rom'):
            raw = samples[phase]
            rows = [measure(raw, bus, frequency) for bus in buses]
            for row in rows:
                if (any(bit['expected_hz_amplitude'] > 1e-6
                        for bit in row['bit_contributions'][:-1]) or
                        abs(row['bit_contributions'][-1]['expected_hz_amplitude'] -
                            row['full_expected_hz_amplitude']) > 1e-6):
                    raise ValueError('carrier-bin source-bit decomposition changed')
            phases.append(dict(phase=phase,
                               raw_y_sha256=hashlib.sha256(bytes(raw)).hexdigest(),
                               buses=rows))
        cases.append(dict(stimulus=name, input_d127=f'{step:02X}',
                          expected_hz=frequency, trace_digest=digest,
                          cycles=(TONE_SYMBOLS * VISITS_PER_SYMBOL + 64) * 4,
                          phases=phases))
        print(name, [(phase['phase'], phase['buses'][0]['full_expected_hz_amplitude'])
                     for phase in phases], flush=True)
    paths = [Path(__file__), BUSES, HERE / 'joint_mask04_photo_b5_tone.py',
             HERE / 'joint_four_row_retention_tx.py',
             HERE / 'photo_tx_divided_prom_clock.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(experiment='per-DAC-bit phasor audit of mask-04 PROM tone and carrier',
                  fixture=dict(mapping='joint upper-source lower mask 04',
                               input='held D127 tone 88 or unmodulated carrier B0',
                               latch='candidate U10 D2 edge divided by 375',
                               sample_hz=SAMPLE_HZ, sample_count=SAMPLE_COUNT,
                               spectral_window='late samples 64..255',
                               buses='six photo-compatible zero-error byte orders'),
                  cases=cases,
                  limitations=[
                      'Every Y-to-latch bit, DAC clock and analog output route remains a hypothesis except the photo-suggested Q4-to-B5 segment.',
                      'Per-bit phasors show where the assumed digital carrier is encoded; they do not measure DAC current or line output.',
                      'Held D127 words are controller-mode hypotheses, not live controller/DSC co-simulation.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
