"""Follow the alternate loops opened by single lower-instruction pin choices."""

import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent/'assumed'), str(HERE)]

from common import save
from controller_bit_dispatch import controller_stream
from execute import execute
from lower_i_input_pipeline import mapping_with_source
from photo_controller_path import fixture
from split_slice_probe import split_scenario

CYCLES = 1580
PULSE_VISIT = 20


def run_trace(mapping, base, bits, site=None, byte=0, boundary=0x38E):
    scenario = split_scenario(base)
    scenario['initial']['q'] = 5
    scenario['io']['read']['pc_sequences']['910'] = [16*b for b in bits]
    if site is not None:
        scenario['io']['read']['pc_sequences'][str(site)] = (
            [0]*PULSE_VISIT + [byte] + [0]*127)
        if site in scenario['io']['read']['address']['pcs']:
            scenario['io']['read']['address']['pcs'].remove(site)
        scenario['io']['read']['evidence'] += (
            f'; diagnostic byte at {site:03X}; ADC route and phase untraced')
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, CYCLES, mode='integrated',
                         out=temporary, trace_limit=CYCLES)
        trace = [json.loads(line) for line in
                 (Path(temporary)/'trace.jsonl').read_text().splitlines()]
    if not result['clean'] or len(trace) != CYCLES:
        raise ValueError('alternate-loop run incomplete')
    ram = scenario['initial']['ram'][:]
    boundaries = []
    for row in trace:
        for address, value in row['registers'].items():
            ram[int(address)] = value
        if row['pc'] == boundary:
            boundaries.append((tuple(ram), row['q'], row['alu'],
                               row['next_pc'], row['stack_after']))
    outputs = {pc: [row['alu']['y'] for row in trace if row['pc'] == pc]
               for pc in range(0x392, 0x3A0) if any(row['pc'] == pc for row in trace)}
    reads = [(row['pc'], row['external_read']['address'], row['external_read']['value'])
             for row in trace if row['external_read'].get('selected_by_alu')
             and 'address' in row['external_read']]
    return dict(result=result, trace=trace, boundaries=boundaries,
                outputs=outputs, reads=reads)


def bit_rule(values, bits):
    if len(values) != len(bits):
        return None
    rules = []
    for lag in range(4):
        groups = [{values[index] for index in range(8, len(values))
                   if bits[index-lag] == bit} for bit in (0, 1)]
        if all(len(group) == 1 for group in groups) and groups[0] != groups[1]:
            rules.append(dict(lag=lag, zero=next(iter(groups[0])),
                              one=next(iter(groups[1]))))
    return rules[0] if len(rules) == 1 else None


def differences(left, right):
    if len(left) != len(right):
        raise ValueError('paired event counts differ')
    return [index for index, (a, b) in enumerate(zip(left, right)) if a != b]


def run(out=HERE/'results/lower-i-branch-followup.json'):
    _, base = fixture()
    _, bits = controller_stream()
    prior = HERE/'results/lower-i-adc-retention-screen.json'
    incomplete = [(row['lower_i_bit'], row['u11_bit']) for row in
                  json.loads(prior.read_text())['candidates']
                  if row['status'] == 'zero run incomplete']
    if len(incomplete) != 30:
        raise ValueError('divergent-path set changed')
    short_paths = []
    for target, source in incomplete:
        scenario = split_scenario(base)
        scenario['initial']['q'] = 5
        scenario['io']['read']['pc_sequences']['910'] = [16*b for b in bits]
        result = execute(mapping_with_source(target, source), scenario, 512,
                         mode='integrated', trace_limit=0)
        short_paths.append(dict(lower_i_bit=target, u11_bit=source,
                                clean=result['clean'],
                                visits_3a1=result['address_counts'].get(0x3A1, 0),
                                visits_38e=result['address_counts'].get(0x38E, 0),
                                selected_rom_reads=result['rom_reads']['selected_by_alu'],
                                final_pc=f"{result['final_state']['pc']:03X}",
                                trace_digest=result['trace_digest']))
    if any(not row['clean'] or row['visits_3a1'] for row in short_paths):
        raise ValueError('divergent-path audit changed')
    cases = []
    for target, source, site, boundary in (
            (3, 1, 0x38D, 0x38E),
            (4, 0, 0x38D, 0x38E),
            (6, 0, 0x3F8, 0x3F9)):
        mapping = mapping_with_source(target, source)
        zero = run_trace(mapping, base, bits, site, 0, boundary)
        pulse = run_trace(mapping, base, bits, site, 0xFF, boundary)
        zero_bits = run_trace(mapping, base, [0]*128, site, 0, boundary)
        one_bits = run_trace(mapping, base, [1]*128, site, 0, boundary)
        site_rows = [row for row in zero['trace'] if row['pc'] == site]
        controller_rows = [row for row in zero['trace'] if row['pc'] == 0x38E]
        rules = {f'{pc:03X}': bit_rule(values, bits)
                 for pc, values in zero['outputs'].items()}
        output_differences = {f'{pc:03X}': differences(
            values, pulse['outputs'][pc]) for pc, values in zero['outputs'].items()}
        rom_addresses = [row['external_read']['address'] for row in zero['trace']
                         if row['cycle'] >= 100 and row['pc'] == 0x3F7 and
                         row['external_read'].get('selected_by_alu') and
                         'address' in row['external_read']]
        cases.append(dict(lower_i_bit=target, u11_bit=source,
                          input_site=f'{site:03X}', boundary=f'{boundary:03X}',
                          site_visits=len(site_rows),
                          site_selected=sum(row['external_read']['selected_by_alu']
                                            for row in site_rows),
                          controller_visits=len(controller_rows),
                          controller_selected=sum(
                              row['external_read']['selected_by_alu']
                              for row in controller_rows),
                          output_sites=[f'{pc:03X}' for pc in zero['outputs']],
                          output_bit_rules=rules,
                          zero_vs_one_bit_output_differences={f'{pc:03X}':
                              differences(zero_bits['outputs'][pc], one_bits['outputs'][pc])
                              for pc, values in zero['outputs'].items()},
                          zero_vs_one_bit_rom_address_differences=differences(
                              [(pc, address) for pc, address, _ in zero_bits['reads']],
                              [(pc, address) for pc, address, _ in one_bits['reads']]),
                          adc_pulse_boundary_differences=differences(
                              zero['boundaries'], pulse['boundaries']),
                          adc_pulse_output_differences=output_differences,
                          adc_pulse_rom_address_differences=differences(
                              [(pc, address) for pc, address, _ in zero['reads']],
                              [(pc, address) for pc, address, _ in pulse['reads']]),
                          selected_rom_address_3f7_first_24=rom_addresses[:24],
                          selected_rom_address_3f7_unique=sorted(set(rom_addresses)),
                          digests={name: row['result']['trace_digest'] for name, row in
                                   (('controller', zero), ('adc_pulse', pulse),
                                    ('zero_bits', zero_bits), ('one_bits', one_bits))}))
    by_pair = {(row['lower_i_bit'], row['u11_bit']): row for row in cases}
    if any(row['site_selected'] != row['site_visits'] or
           row['site_visits'] < PULSE_VISIT+3 or
           row['adc_pulse_boundary_differences'] != [20] or
           any(row['adc_pulse_output_differences'].values()) or
           row['adc_pulse_rom_address_differences'] or
           row['zero_vs_one_bit_rom_address_differences']
           for row in cases):
        raise ValueError('alternate-loop ADC effect changed')
    if (by_pair[(3,1)]['output_bit_rules']['396'] !=
            dict(lag=1, zero=17, one=49) or
            by_pair[(4,0)]['output_bit_rules']['39A'] !=
            dict(lag=1, zero=17, one=49) or
            any(by_pair[pair]['zero_vs_one_bit_output_differences'][site] !=
                list(range(1, 128)) for pair, site in
                (((3,1), '396'), ((3,1), '398'),
                 ((4,0), '39A'), ((4,0), '39C'))) or
            len(by_pair[(6,0)]['selected_rom_address_3f7_unique']) != 8 or
            by_pair[(6,0)]['selected_rom_address_3f7_first_24'] !=
            [283,257,279,285,275,281,287,261]*3):
        raise ValueError('alternate-loop bit relay or ROM cycle changed')
    paths = [Path(__file__), HERE/'lower_i_input_pipeline.py',
             HERE/'independent_slice_addresses.py', HERE/'independent_slice_fields.py',
             HERE/'split_slice_probe.py', HERE/'controller_bit_dispatch.py',
             HERE/'photo_controller_path.py', HERE.parent/'assumed/execute.py',
             HERE.parent/'model.py', prior,
             HERE.parents[2]/'am27s31dc-prom/nokia-modem-am27s31dc.bin']
    report = dict(status='alternate lower-instruction branch and input screen',
                  fixture=dict(cycles=CYCLES, q=5, initial_ram=[0]*16,
                               controller='128 scrambler bits at D38E',
                               adc='FF pulse at visit 20 of candidate D site'),
                  divergent_path_audit=dict(cycles=512, cases=short_paths),
                  cases=cases,
                  limitations=[
                      'U11-to-U2 pin substitutions and both external D sources are untraced.',
                      'ALU Y events are not a traced DAC latch or physical line output.',
                      'An eight-address quarter-sine ROM cycle is not by itself a carrier waveform.',
                      'Only one Q/RAM seed and one controller stream are tested.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    for row in run()['cases']:
        print(row['lower_i_bit'], row['u11_bit'], row['output_bit_rules'],
              row['adc_pulse_boundary_differences'],
              row['selected_rom_address_3f7_unique'])
