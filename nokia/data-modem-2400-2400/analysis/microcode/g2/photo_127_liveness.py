"""Test whether a PC129 ROM-bank change survives the four-word D127 loop."""

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
from photo_controller_path import fixture
from photo_i0_hold_screen import hold_candidate
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

ROM = HERE.parents[2] / 'am27s31dc-prom/nokia-modem-am27s31dc.bin'
CYCLES = 3000


def run_case(mapping, base, increment, bank):
    scenario = hold_candidate(base)
    scenario['initial']['q'] = 0
    scenario['io']['read']['pc_sequences'][str(0x127)] = [increment]
    # Isolate the selected operand at PC129; all other ROM reads keep the
    # baseline upper bank, so a paired run differs in exactly one input rule.
    scenario['io']['read']['address']['bank_by_pc'] = {str(0x129): bank}
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, CYCLES, mode='integrated',
                         out=temporary, trace_limit=CYCLES)
        trace = [json.loads(line) for line in
                 (Path(temporary) / 'trace.jsonl').read_text().splitlines()]
    if not result['clean'] or len(trace) != CYCLES:
        raise ValueError('incomplete execution')
    return scenario, result, trace


def snapshots(trace, initial_ram):
    ram = initial_ram[:]
    retained = []
    for row in trace:
        for address, value in row['registers'].items():
            ram[int(address)] = value
        if row['pc'] == 0x128:
            retained.append((row['cycle'], tuple(ram), row['q'], row['alu'],
                             row['next_pc'], row['stack_after']))
    return retained


def check_loop(trace, rom, increment, bank):
    reads = [i for i, row in enumerate(trace) if row['pc'] == 0x129]
    if not reads:
        raise ValueError('no selected ROM reads')
    carry_ones = 0
    for n, i in enumerate(reads, 1):
        before, row, after = trace[i-2], trace[i], trace[i+1]
        if [before['pc'], trace[i-1]['pc'], row['pc'], after['pc']] != [0x127, 0x128, 0x129, 0x12A]:
            raise ValueError('D127 loop quartet changed')
        phase = (3 + n * increment) & 255
        rom_byte = rom[bank + phase]
        carry = int(phase >= rom_byte)
        if (before['registers'].get('1') != phase or
                (trace[i-1]['registers'] and
                 trace[i-1]['registers'].get('0') != 0) or
                row['external_read']['address'] != bank + phase or
                row['external_read']['value'] != rom_byte or
                row['alu']['y'] != (phase - rom_byte) & 255 or
                row['alu']['carry'] != carry or
                (row['registers'] and
                 row['registers'].get('0') != row['alu']['y']) or
                after['alu']['y'] != (phase + 1 + carry) & 255 or
                (after['registers'] and
                 after['registers'].get('0') != after['alu']['y'])):
            raise ValueError(f'ROM/carry/write relation changed at read {n}')
        carry_ones += carry
    if any(b-a != 4 for a, b in zip(reads, reads[1:])):
        raise ValueError('PC129 visit cadence changed')
    return reads, carry_ones


def run(out=HERE / 'results/photo-127-liveness.json'):
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    rom = ROM.read_bytes()
    cases = []
    for increment in (1, 48, 56):
        variants = []
        for bank in (0, 256):
            scenario, result, trace = run_case(mapping, base, increment, bank)
            reads, carry_ones = check_loop(trace, rom, increment, bank)
            variants.append((trace, reads, snapshots(trace, scenario['initial']['ram']),
                             result['trace_digest'], carry_ones))
        low, high = variants
        if len(low[1]) != len(high[1]) or low[2] != high[2]:
            raise ValueError('bank choice altered loop count or retained PC128 state')
        pairs = [(low[0][a], high[0][b]) for a, b in zip(low[1], high[1])]
        cases.append(dict(increment=increment, cycles=CYCLES,
                          pc129_reads=len(pairs), pc128_snapshots=len(low[2]),
                          selected_rom_byte_differences=sum(
                              a['external_read']['value'] != b['external_read']['value']
                              for a, b in pairs),
                          pc129_y_differences=sum(a['alu']['y'] != b['alu']['y']
                                                  for a, b in pairs),
                          pc12a_y_differences=sum(low[0][i+1]['alu']['y'] !=
                                                  high[0][j+1]['alu']['y']
                                                  for i, j in zip(low[1], high[1])),
                          pc128_retained_state_differences=0,
                          carry_ones_by_bank={'0': low[4], '256': high[4]},
                          trace_digests_by_bank={'0': low[3], '256': high[3]}))
    paths = [Path(__file__), ROM, HERE/'photo_controller_path.py',
             HERE/'photo_i0_hold_screen.py', HERE/'photo_mapping_q_sweep.py',
             HERE/'photo_mapping_stream_screen.py', ASSUMED/'execute.py',
             HERE.parent/'model.py', MAPPINGS['q3']]
    report = dict(status='PC129 operand-liveness diagnostic, not a traced DAC path',
                  fixture=dict(mapping='q3', held_i0=1, initial_q=0,
                               d127_source='held scenario value', cycles=CYCLES,
                               changed_input='Am27S31 A8 only at PC129'),
                  verified_relations=[
                      'phase_n=(3+n*D127) mod 256; n starts at 1',
                      'Y129=(phase_n-ROM[bank+phase_n]) mod 256',
                      'carry129=1 iff phase_n >= ROM[bank+phase_n]',
                      'Y12A=(phase_n+1+carry129) mod 256',
                      'PC128, PC129 and PC12A write R0 conditionally; PC128 ALU F is zero before the selected read'],
                  cases=cases,
                  limitations=[
                      'Only q3, Q=0, zero RAM, held I0 and three D127 constants are tested.',
                      'The selected ROM byte changes transient R0/ALU values; no DAC sampling phase or latch clock is traced.',
                      'Equal PC128 snapshots rule out retained effects in this fixture, not externally sampled effects at PC129 or PC12A.',
                      'D127 source and bank driver are scenario assumptions.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    for row in run()['cases']:
        print(row['increment'], row['pc129_reads'],
              row['selected_rom_byte_differences'],
              row['pc12a_y_differences'],
              row['pc128_retained_state_differences'])
