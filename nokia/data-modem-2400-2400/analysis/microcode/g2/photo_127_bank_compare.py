"""Compare both Am27S31 banks in the D127-driven PC129 walk."""

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
from photo_127_tone_probe import spectrum
from photo_controller_path import fixture
from photo_i0_hold_screen import hold_candidate
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

ROM = HERE.parents[2] / 'am27s31dc-prom/nokia-modem-am27s31dc.bin'
CASES = ((3, 1800, 240), (48, 1800, 640), (56, 2100, 640))


def signed(value):
    return value if value < 128 else value - 256


def run(out=HERE / 'results/photo-127-bank-compare.json'):
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    rom = ROM.read_bytes()
    cases = []
    for bank in (0, 256):
        for increment, target_hz, analysis_samples in CASES:
            scenario = hold_candidate(base)
            scenario['initial']['q'] = 0
            scenario['io']['read']['address']['bank'] = bank
            scenario['io']['read']['pc_sequences'][str(0x127)] = [increment]
            with tempfile.TemporaryDirectory() as temporary:
                result = execute(mapping, scenario, 3000, mode='integrated',
                                 out=temporary, trace_limit=3000)
                trace = [json.loads(line) for line in
                         (Path(temporary) / 'trace.jsonl').read_text().splitlines()]
            reads = [row for row in trace if row['pc'] == 0x129]
            if not result['clean'] or len(reads) < analysis_samples:
                raise ValueError(f'bank {bank} increment {increment}: incomplete run')
            if {b['cycle'] - a['cycle'] for a, b in zip(reads, reads[1:])} != {4}:
                raise ValueError('PC129 cadence changed')
            addresses = [row['external_read']['address'] for row in reads]
            values = [row['external_read']['value'] for row in reads]
            y = [row['alu']['y'] for row in reads]
            expected_addresses = [bank + ((3 + (i + 1) * increment) & 255)
                                  for i in range(len(reads))]
            if (addresses != expected_addresses or
                    values != [rom[address] for address in addresses] or
                    y != [((address & 255) - value) & 255
                          for address, value in zip(addresses, values)]):
                raise ValueError('bank/index/ALU relation changed')
            target = list(range(0, 16)) if bank == 0 else list(range(256, 321))
            target_set = set(target)
            used = reads[:analysis_samples]
            cases.append(dict(bank=bank, increment=increment,
                              hypothetical_frequency_hz=target_hz,
                              analysis_samples=analysis_samples,
                              total_pc129_reads=len(reads),
                              first_16_addresses=addresses[:16],
                              first_16_rom_bytes=values[:16],
                              first_16_alu_y=y[:16],
                              target_table='sine16 000-00F' if bank == 0 else
                                           'quarter-sine 100-140',
                              target_table_hits_in_analysis=sum(
                                  address in target_set for address in addresses[:analysis_samples]),
                              distinct_target_table_addresses=len(set(addresses[:analysis_samples]) & target_set),
                              signed_rom_spectrum=spectrum([signed(row['external_read']['value'])
                                                            for row in used], target_hz),
                              signed_alu_y_spectrum=spectrum([signed(row['alu']['y'])
                                                              for row in used], target_hz),
                              trace_digest=result['trace_digest']))
    # Project additional fixed increments through the verified address rule.
    # These are ROM-only controls, not additional microcode executions.
    projected_controls = []
    for bank in (0, 256):
        for increment in (16, 24, 32, 40, 48, 56, 64, 72, 80):
            target_hz = increment * 9600 / 256
            values = [signed(rom[bank + ((3 + (n + 1) * increment) & 255)])
                      for n in range(256)]
            projected_controls.append(dict(bank=bank, increment=increment,
                                            phase_step_frequency_hz=target_hz,
                                            signed_rom_spectrum=spectrum(values, target_hz)))
    report = dict(status='fixed-bank D127/PC129 diagnostic, not carrier proof',
                  fixture=dict(mapping=mapping['name'], held_i0=1, initial_q=0,
                               initial_ram=[0] * 16, microinstructions_per_read=4,
                               assumed_sample_rate_hz=9600, cycles=3000,
                               address_rule='bank + ((3 + n*D127) mod 256), n starts at 1',
                               alu_rule='Y129=(address low byte - ROM byte) mod 256'),
                  cases=cases,
                  projected_rom_only_controls=projected_controls,
                  limitations=[
                      'ROM A8 bank select, D127 source, I0 hold, sample clock and DAC route are untraced hypotheses.',
                      'The address source uses all eight low bits; no phase folding or mask was imposed.',
                      'Spectral peaks of the byte arithmetic are not line-output waveforms.',
                      'The local fixed input does not represent the complete controller command/bit interface.'],
                  source_sha256={str(p.relative_to(HERE.parents[2])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (Path(__file__), ROM,
                                           HERE / 'photo_127_tone_probe.py',
                                           HERE / 'photo_i0_hold_screen.py',
                                           HERE / 'photo_controller_path.py',
                                           HERE / 'photo_mapping_q_sweep.py',
                                           ASSUMED / 'execute.py', HERE.parent / 'model.py',
                                           MAPPINGS['q3'])})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    for row in report['cases']:
        print(row['bank'], row['increment'], row['total_pc129_reads'],
              row['target_table_hits_in_analysis'],
              row['signed_rom_spectrum']['peak_hz'],
              row['signed_alu_y_spectrum']['peak_hz'])
