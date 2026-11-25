"""Find exact signed anti-symmetric ROM regions and test one executed reader."""

import hashlib
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from photo_127_liveness import ROM, run_case, snapshots
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

ROM_SHA = '312fa21f50203c7b84ec0a4b4aea62ca343b2a579c38687111342368b1f04d58'


def signed(value):
    return value if value < 128 else value - 256


def gain(values, frequency_hz, sample_hz=9600):
    return abs(sum(value * complex(math.cos(-2*math.pi*frequency_hz*n/sample_hz),
                                   math.sin(-2*math.pi*frequency_hz*n/sample_hz))
                   for n, value in enumerate(values)))


def run(out=HERE / 'results/rom-antisymmetric-regions.json'):
    data = ROM.read_bytes()
    if len(data) != 512 or hashlib.sha256(data).hexdigest() != ROM_SHA:
        raise ValueError('Am27S31 dump changed')
    windows = []
    for address in range(0x30, 0x80):
        for length in range(8, min(33, 0x80-address+1)):
            values = [signed(byte) for byte in data[address:address+length]]
            if any(values) and values == [-value for value in values[::-1]]:
                windows.append((address, address+length-1))
    maximal = [window for window in windows if not any(
        other != window and other[0] <= window[0] and window[1] <= other[1]
        for other in windows)]
    if maximal != [(0x5A, 0x69), (0x72, 0x7B)]:
        raise ValueError('anti-symmetric ROM windows changed')
    regions = []
    for first, last in maximal:
        values = [signed(byte) for byte in data[first:last+1]]
        sample_gains = {str(hz): round(gain(values, hz), 6)
                        for hz in (0, 1800, 2100, 4800)}
        if sample_gains['0'] != 0 or max(
                range(0, 4801, 15), key=lambda hz: gain(values, hz)) != 4800:
            raise ValueError(f'{first:02X} frequency profile changed')
        regions.append(dict(first_address=f'{first:02X}', last_address=f'{last:02X}',
                            signed_values=values, length=len(values),
                            exact_anti_symmetry=True,
                            contiguous_tap_interpretation_at_9600_hz=dict(
                                gain_by_hz=sample_gains,
                                max_grid_frequency_hz=4800,
                                bin_hz=15)))
    if not (data[0x5D] == 0xF0 and data[0x66] == 0x10 and
            0x5D + 0x66 == 0x5A + 0x69):
        raise ValueError('F0/10 symmetric positions changed')

    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    paired = [run_case(mapping, base, 1, bank) for bank in (0, 256)]
    rows = []
    for bank, (scenario, execution, trace) in zip((0, 256), paired):
        reads = [row['external_read']['address'] for row in trace
                 if row['pc'] == 0x129 and row['external_read']['selected_by_alu']]
        if not execution['clean'] or len(reads) != 253:
            raise ValueError(f'PC129 bank {bank} read count changed')
        rows.append(dict(bank=bank, pc129_selected_reads=len(reads),
                         first_region_hits=sum(0x5A <= address <= 0x69
                                               for address in reads),
                         second_region_hits=sum(0x72 <= address <= 0x7B
                                                for address in reads),
                         trace_digest=execution['trace_digest']))
    if (rows[0]['first_region_hits'], rows[0]['second_region_hits']) != (16, 10):
        raise ValueError('lower-bank q3 sweep no longer visits both regions')
    if snapshots(paired[0][2], paired[0][0]['initial']['ram']) != snapshots(
            paired[1][2], paired[1][0]['initial']['ram']):
        raise ValueError('ROM bank changed retained PC128 state')

    paths = [Path(__file__), ROM, HERE / 'photo_127_liveness.py',
             HERE / 'photo_controller_path.py', HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             HERE.parent / 'assumed/execute.py', HERE.parent / 'model.py',
             MAPPINGS['q3']]
    report = dict(status='exact ROM anti-symmetry and conditional q3 read audit',
                  region=regions,
                  fast_step_coincidence=dict(negative_tap=dict(address='5D', byte='F0',
                                                                signed=-16),
                                             positive_tap=dict(address='66', byte='10',
                                                               signed=16),
                                             interpretation='opposite positions in the same 16-byte anti-symmetric region, not independent D127-source evidence'),
                  q3_lower_bank_control=dict(held_d127='01',
                                             paired_bank_runs=rows,
                                             pc128_retained_snapshots_equal=True),
                  limitations=[
                      'Anti-symmetry is a ROM-data fact; FIR taps, byte order, sample rate and functional role are hypotheses.',
                      'The frequency response assumes contiguous signed taps at 9600 Hz; the board may read the bytes in another order or at another rate.',
                      'The q3 lower-bank run sweeps all addresses, so reaching these windows does not identify their intended consumer.',
                      'The q3 mapping, ROM gate, held-I0 level and D127 source are untraced; no transmitter or receiver path is shown.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    for region in run()['region']:
        print(region['first_address'], region['last_address'], region['signed_values'])
