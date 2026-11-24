"""Test whether fixed D127 increments yield modem tones or ramp harmonics."""

import hashlib
import json
import math
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
from common import save
from execute import execute
from photo_controller_path import fixture
from photo_i0_hold_screen import hold_candidate
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

SAMPLE_RATE_HYPOTHESIS = 9600
SAMPLES = 640
CYCLES = 3000
CASES = ((48, 1800), (56, 2100))
ROM = HERE.parents[2] / 'am27s31dc-prom/nokia-modem-am27s31dc.bin'


def spectrum(values, expected_hz):
    count = len(values)
    mean = sum(values) / count
    centered = [value - mean for value in values]
    variance = sum(value * value for value in centered)
    powers = {}
    for bin_index in range(1, count // 2):
        angle = 2 * math.pi * bin_index / count
        real = sum(value * math.cos(angle * index)
                   for index, value in enumerate(centered))
        imag = sum(value * math.sin(angle * index)
                   for index, value in enumerate(centered))
        powers[bin_index] = real * real + imag * imag
    expected_bin = round(expected_hz * count / SAMPLE_RATE_HYPOTHESIS)
    if expected_bin * SAMPLE_RATE_HYPOTHESIS != expected_hz * count:
        raise ValueError('expected tone is not on an exact DFT bin')
    peak = max(powers, key=powers.get)
    return dict(peak_hz=peak * SAMPLE_RATE_HYPOTHESIS / count,
                expected_hz=expected_hz,
                sinusoid_r2=round(2 * powers[expected_bin] / (count * variance), 6),
                bin_hz=SAMPLE_RATE_HYPOTHESIS / count)


def run(out):
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    rom_bytes = ROM.read_bytes()
    cases = []
    for increment, expected_hz in CASES:
        scenario = hold_candidate(base)
        scenario['initial']['q'] = 0
        scenario['io']['read']['pc_sequences'][str(0x127)] = [increment]
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            result = execute(mapping, scenario, CYCLES, mode='integrated',
                             out=path, trace_limit=CYCLES)
            trace = [json.loads(line) for line in
                     (path/'trace.jsonl').read_text().splitlines()]
        reads = [row for row in trace if row['pc'] == 0x129][:SAMPLES]
        if not result['clean'] or len(reads) != SAMPLES:
            raise ValueError(f'D127={increment}: incomplete ROM-output run')
        if {b['cycle'] - a['cycle'] for a, b in zip(reads, reads[1:])} != {4}:
            raise ValueError('PC129 read cadence changed')
        addresses = [row['external_read']['address'] for row in reads]
        indexes = [address & 255 for address in addresses]
        actual_rom = [row['external_read']['value'] for row in reads]
        y = [row['alu']['y'] for row in reads]
        expected_indexes = [(3 + (index + 1) * increment) & 255
                            for index in range(SAMPLES)]
        if (indexes != expected_indexes or
                any(not row['external_read']['selected_by_alu'] for row in reads) or
                actual_rom != [rom_bytes[address] for address in addresses] or
                y != [(index - value) & 255
                      for index, value in zip(indexes, actual_rom)]):
            raise ValueError(f'D127={increment}: ROM or ALU relation changed')
        cases.append(dict(d127=increment, hypothetical_tone_hz=expected_hz,
                          samples=SAMPLES, microinstructions_per_read=4,
                          first_addresses=addresses[:16],
                          distinct_addresses=len(set(addresses)),
                          series=dict(rom_addresses=addresses,
                                      phase_index=indexes,
                                      selected_rom_byte=actual_rom,
                                      alu_y=y),
                          phase_ramp=spectrum(indexes, expected_hz),
                          rom_byte=spectrum(actual_rom, expected_hz),
                          alu_y=spectrum(y, expected_hz),
                          trace_digest=result['trace_digest']))
    paths = [Path(__file__), ROM, HERE/'photo_i0_hold_screen.py',
             HERE/'photo_controller_path.py', HERE/'photo_mapping_q_sweep.py',
             HERE/'photo_mapping_stream_screen.py', ASSUMED/'execute.py',
             HERE.parent/'model.py', MAPPINGS['q3']]
    report = dict(status='fixed-D127 tone diagnostic, not physical line-output proof',
                  fixture=dict(mapping='q3 photo-swapped', initial_q=0,
                               initial_ram=[0]*16, held_i0=1,
                               assumed_d127_source='held byte',
                               assumed_output_site='PC129 ALU Y',
                               assumed_one_read_per_sample_hz=SAMPLE_RATE_HYPOTHESIS,
                               cycles=CYCLES),
                  alu_identity='At PC129, Y = (ROM address low byte - selected ROM byte) mod 256',
                  cases=cases,
                  limitations=[
                      'The 9,600 Hz sample rate, one-PC129-read-per-sample latch and held D127 values are imposed, not recovered clock or board signals.',
                      'A spectral peak can arise from the phase-index sawtooth alone; it does not identify a sine carrier or DAC output.',
                      'The ROM enable, D127 input source, I0 hold circuit and physical output route remain untraced.',
                      'No controller command, dibit-dependent phase step, pulse shaping, receiver or echo-canceller path is demonstrated.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.parent.mkdir(parents=True, exist_ok=True)
    save(out, report)
    return report


if __name__ == '__main__':
    report = run(HERE/'results/photo-127-tone-probe.json')
    for row in report['cases']:
        print(row['d127'], row['phase_ramp'], row['rom_byte'], row['alu_y'])
