"""Replay the D127 ROM walk through the photo-candidate DAC08 B5 latch bit."""

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
from dac08_latch_probe import LS273DAC08, photo_b5
from photo_127_tone_probe import spectrum
from photo_controller_path import fixture
from photo_i0_hold_screen import hold_candidate
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

CAPTURES = 128
CYCLES = 560


def run_trace(mapping, base, values):
    scenario = hold_candidate(base)
    scenario['initial']['q'] = 0
    scenario['io']['read']['pc_sequences'][str(0x127)] = values
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary)
        result = execute(mapping, scenario, CYCLES, mode='integrated',
                         out=path, trace_limit=CYCLES)
        trace = [json.loads(line) for line in
                 (path/'trace.jsonl').read_text().splitlines()]
    if not result['clean']:
        raise ValueError('candidate ROM-walk run stopped')
    inputs = [row['external_read']['value'] for row in trace if row['pc'] == 0x127]
    captures = [row for row in trace if row['pc'] == 0x129][:CAPTURES]
    if inputs[:CAPTURES] != values[:CAPTURES] or len(captures) != CAPTURES:
        raise ValueError('candidate ROM walk missed controller inputs or latch sites')
    return result, captures


def latch_b5(rows, y_bit):
    latch = LS273DAC08()
    captured = []
    for row in rows:
        y = row['alu']['y']
        data = (y & ~16) | (((y >> y_bit) & 1) << 4)
        code = latch.drive(data, 1)
        captured.append(photo_b5(code))
        latch.drive(data, 0)
    return captured


def bit_summary(codes):
    if len(set(codes)) == 1:
        shape = dict(peak_hz=None, sinusoid_r2=0, bin_hz=75.0)
    else:
        shape = spectrum(codes, 1800)
    return dict(ones=sum(codes), transitions=sum(a != b for a, b in zip(codes, codes[1:])),
                first_32=codes[:32], spectrum=shape)


def run(out):
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    _, bits = controller_stream()
    paced = [bit for bit in bits[:32] for _ in range(4)]
    streams = (('forward', bits), ('reverse', bits[::-1]),
               ('paced_4_samples_per_bit', paced),
               ('paced_reverse', [bit for bit in bits[:32][::-1] for _ in range(4)]),
               ('zero', [0]*len(bits)))
    cases = []
    for name, values in streams:
        result, rows = run_trace(mapping, base, values)
        bit_cases = []
        for y_bit in range(8):
            captured = latch_b5(rows, y_bit)
            bit_cases.append(dict(y_bit_to_ls273_d4=y_bit,
                                  **bit_summary(captured),
                                  full_b5_series=captured if y_bit == 4 else None))
        cases.append(dict(stream=name, controller_bits=len(values), captures=len(rows),
                          first_rom_addresses=[row['external_read']['address']
                                               for row in rows[:16]],
                          last_rom_address=rows[-1]['external_read']['address'],
                          bit_cases=bit_cases, trace_digest=result['trace_digest']))
    if any(case['captures'] != 128 for case in cases):
        raise ValueError('photo B5 capture count changed')
    if any(row['spectrum']['peak_hz'] == 1800
           for case in cases if case['stream'] != 'zero'
           for row in case['bit_cases']):
        raise ValueError('a new B5 bit mapping has an 1800 Hz peak')
    paths = [Path(__file__), HERE/'dac08_latch_probe.py',
             HERE/'photo_127_tone_probe.py', HERE/'photo_i0_hold_screen.py',
             HERE/'photo_controller_path.py', HERE/'controller_bit_dispatch.py',
             HERE/'photo_mapping_q_sweep.py', HERE/'photo_mapping_stream_screen.py',
             HERE.parents[2]/'photos/PXL_20261123_114854803.jpg',
             ASSUMED/'execute.py', HERE.parent/'model.py', MAPPINGS['q3']]
    report = dict(status='photo-B5 candidate replay, not a physical DAC waveform',
                  fixture=dict(mapping='q3 photo-swapped', initial_q=0,
                               assumed_controller_input='D127 receives 8031 scrambler bits',
                               assumed_latch_clock='one rising LS273 edge at each PC129',
                               photo_candidate='DAC08 pin 9 B5 receives LS273 pin 9 Q4',
                               y_to_ls273_d4='all eight source-bit choices tested',
                               sample_rate_hypothesis_hz=9600,
                               paced_case='four PC129 captures per controller bit, eight per dibit',
                               cycles=CYCLES, captures=CAPTURES),
                  cases=cases,
                  limitations=[
                      'The B5-to-Q4 segment is a photo interpretation, not measured continuity.',
                      'No Y-to-LS273-D4 bit route, clock edge, D127 input connection or I0 hold circuit is traced.',
                      'Only one DAC input bit is constrained by this photo; a full-byte line sample or analog filter is not reconstructed.',
                      'The controller source is the 8031 scrambler routine, not a continuous modem call or identified command state.',
                      'The 9,600 Hz sample clock is imposed; the board divider and actual output cadence remain unknown.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.parent.mkdir(parents=True, exist_ok=True)
    save(out, report)
    return report


if __name__ == '__main__':
    report = run(HERE/'results/photo-dac-b5-127.json')
    for case in report['cases']:
        print(case['stream'], [(row['y_bit_to_ls273_d4'], row['ones'],
                                row['transitions'], row['spectrum']['peak_hz'])
                               for row in case['bit_cases']])
