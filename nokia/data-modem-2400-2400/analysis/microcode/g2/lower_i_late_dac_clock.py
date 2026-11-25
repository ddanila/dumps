"""Test direct LS273 clock candidates at a repeated 3B3–3B6 Y quartet."""

import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent/'assumed'), str(HERE)]

from common import save
from controller_bit_dispatch import controller_stream
from dac08_latch_probe import LS273DAC08
from lower_i_d3f8_input import run_trace
from lower_i_late_byte_relay import OUTPUT_PCS, expected, output_quartets, scenario_with_trigger
from lower_i_prom_data_route import mapping_for
from photo_controller_path import fixture

LOOP_PCS = (*range(0x3A2, 0x3A9), *OUTPUT_PCS, 0x3A9)


def period(block):
    return next(width for width in range(1, len(block)+1)
                if len(block) % width == 0 and
                all(block[index] == block[index % width]
                    for index in range(len(block))))


def captures(trace, sites, y_bit=None):
    latch = LS273DAC08()
    values = []
    for row in trace:
        y = row['alu']['y']
        data = y if y_bit is None else ((y & ~16) | (((y >> y_bit) & 1) << 4))
        if row['pc'] in sites:
            values.append(latch.drive(data, 1))
            latch.drive(data, 0)
        else:
            latch.drive(data, 0)
    return values


def repeated_loop(trace):
    start = next(index for index, row in enumerate(trace) if row['pc'] == LOOP_PCS[0])
    block = [(row['pc'], row['alu']['y']) for row in trace[start:start+12]]
    if tuple(pc for pc, _ in block) != LOOP_PCS:
        raise ValueError('late-loop PC order changed')
    complete = (len(trace)-start)//12
    for repetition in range(complete):
        observed = [(row['pc'], row['alu']['y']) for row in
                    trace[start+12*repetition:start+12*(repetition+1)]]
        if observed != block:
            raise ValueError(f'late-loop PC/Y block changed at {repetition}')
    return dict(first_cycle=start, complete_blocks=complete,
                pc_y_block=[(f'{pc:03X}', y) for pc, y in block])


def run(out=HERE/'results/lower-i-late-dac-clock.json'):
    _, base = fixture()
    mapping = mapping_for('!10.6', '11.2')
    scenario = scenario_with_trigger(base)
    _, bits = controller_stream()
    streams = {'zero': [1]*128,
               'one': [3]*128,
               'controller': [1 | (bit << 1) for bit in bits]}
    traces = {name: run_trace(mapping, scenario, 0x3A6, values, cycles=2000)
              for name, values in streams.items()}
    for name, case in traces.items():
        quartets = output_quartets(case['trace'])
        if case['site_visits'] != 138 or len(quartets) != 138:
            raise ValueError(f'late-loop duration changed for {name}')
        if name != 'controller' and set(quartets) != {expected(streams[name][0])}:
            raise ValueError(f'constant-symbol quartet changed for {name}')
        if name == 'controller' and any(quartets[i] != expected(streams[name][i])
                                        for i in range(128)):
            raise ValueError('controller quartet changed')
    fixed_loops = {name: repeated_loop(traces[name]['trace'])
                   for name in ('zero', 'one')}
    if any(row['complete_blocks'] != 137 for row in fixed_loops.values()):
        raise ValueError('constant-symbol loop repetition count changed')
    if any((1800*width) % 9600 == 0 for width in range(1, len(LOOP_PCS)+1)):
        raise ValueError('a fixed late-loop clock count could support 1800 Hz')

    rows = []
    for mask in range(1, 16):
        sites = tuple(pc for index, pc in enumerate(OUTPUT_PCS) if mask & (1 << index))
        width = len(sites)
        code_periods = {}
        b5_periods = {}
        first_codes = {}
        for name in ('zero', 'one'):
            sample = captures(traces[name]['trace'], sites)
            if len(sample) != 138*width:
                raise ValueError('direct clock count changed')
            block = sample[:width]
            if sample != block*138:
                raise ValueError('constant-symbol samples not periodic by loop')
            code_periods[name] = period(block)
            first_codes[name] = block
            b5_periods[name] = []
            for y_bit in range(8):
                b5 = [value >> 4 & 1 for value in
                      captures(traces[name]['trace'], sites, y_bit)]
                if b5 != b5[:width]*138:
                    raise ValueError('photo-candidate B5 is not periodic')
                b5_periods[name].append(period(b5[:width]))
        observed = captures(traces['controller']['trace'], sites)
        if len(observed) != 138*width:
            raise ValueError('controller direct-clock count changed')
        if any((1800*value) % 9600 == 0 for value in
               [*code_periods.values(), *b5_periods['zero'], *b5_periods['one']]):
            raise ValueError('a tested period supports 1800 Hz at 9600 samples/s')
        rows.append(dict(clock_sites=[f'{pc:03X}' for pc in sites],
                         samples_per_loop=width,
                         captured_codes_per_case=len(observed),
                         first_constant_codes=first_codes,
                         constant_code_periods=code_periods,
                         photo_candidate_b5_periods_by_y_bit=b5_periods,
                         controller_distinct_codes=len(set(observed))))

    paths = [Path(__file__), HERE/'lower_i_late_byte_relay.py',
             HERE/'lower_i_d3f8_input.py', HERE/'lower_i_prom_data_route.py',
             HERE/'controller_bit_dispatch.py', HERE/'photo_controller_path.py',
             HERE/'dac08_latch_probe.py', HERE.parent/'assumed/execute.py',
             HERE.parents[2]/'photos/PXL_20261123_114854803.jpg']
    report = dict(status='direct LS273 clock family at late-loop Y sites',
                  fixture=dict(mapping='I7/A0=!10.6, I0/A1=11.2, lower I6=11.0',
                               condition_select_0='previous carry, inverted',
                               initial_q=5, d3f8_trigger='D1 pulse at visit 20',
                               d3a6_zero_byte=1, d3a6_one_byte=3,
                               d3a6_controller_lane='D1',
                               photo_candidate='DAC08 B5 receives LS273 Q4',
                               y_to_ls273_d4='all eight source-bit choices',
                               assumed_sample_rate_hz=9600,
                               cycles=2000, loop_repetitions=138),
                  clock_cases=rows,
                  fixed_12_word_loops=fixed_loops,
                  limitations=[
                      'The photo supports only the B5←Q4 segment; Y-to-LS273 D wiring, clock decode and all other DAC bits are untraced.',
                      'The 9600 samples/s cadence is a reference hypothesis, not a measured board clock.',
                      'The 12-word invariant excludes one direct clock edge at any fixed subset of this loop at that cadence; held data, other program paths and different physical timing remain open.',
                      'No analog DAC current or line output is modeled.'],
                  trace_digests={name: case['result']['trace_digest']
                                 for name, case in traces.items()},
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    print('clock sets', len(report['clock_cases']))
    print('maximum constant code period', max(
        max(row['constant_code_periods'].values())
        for row in report['clock_cases']))
