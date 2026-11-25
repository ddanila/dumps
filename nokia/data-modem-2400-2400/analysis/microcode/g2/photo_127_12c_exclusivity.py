"""Check whether controller-fed D127 and PC12C ROM feedback coexist."""

import copy
import hashlib
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
from common import read, save
from execute import execute
from controller_bit_dispatch import controller_stream
from photo_controller_path import fixture, GATE_FITS
from photo_variant_rom_loop import MAPPINGS, ROM


def mapping_for(name):
    mapping = read(MAPPINGS[name])
    mapping['fields']['a']['bits'][2:] = ['10.7', '10.6']
    mapping['fields']['a']['status'] = 'hypothesis'
    return mapping


def scenario_for(base, gate, values):
    scenario = copy.deepcopy(base)
    scenario['name'] += '; diagnostic D127 external input, ROM at 12C'
    scenario['io']['read']['address']['pcs'] = [pc for pc in gate['pcs']
                                                  if pc != 0x127]
    scenario['io']['read']['address']['evidence'] += (
        '; removal of PC127 from gate is a diagnostic wiring alternative')
    scenario['io']['read']['pc_sequences'][str(0x127)] = values
    return scenario


def counts(result):
    address = result['address_counts']
    return dict(input_127=address.get(0x127, 0), rom_12c=address.get(0x12C, 0),
                output_392=address.get(0x392, 0),
                final_pc=f"{result['final_state']['pc']:03X}")


def run(out=HERE / 'results/photo-127-12c-exclusivity.json'):
    _, base = fixture()
    gate = next(row for row in read(GATE_FITS)['fits'] if 0x127 in row['pcs'])
    _, bits = controller_stream()
    cases = []
    for name in ('q1', 'q2'):
        mapping = mapping_for(name)
        rows = []
        for value in range(256):
            result = execute(mapping, scenario_for(base, gate, [value]),
                             512, mode='integrated', trace_limit=0)
            if not result['clean']:
                raise ValueError(f'{name} D127={value:02X} stopped')
            rows.append(dict(byte=value, **counts(result)))
        enter_table = [row['byte'] for row in rows if row['rom_12c'] > 0]
        expected = [0] if name == 'q1' else [0, 119, 183, 184, 185]
        if enter_table != expected or any(row['output_392'] for row in rows):
            raise ValueError(f'{name} D127/table classification changed')
        stream_cases = []
        for label, stream in (('forward', bits), ('reverse', bits[::-1])):
            scenario = scenario_for(base, gate, stream)
            with tempfile.TemporaryDirectory() as temporary:
                result = execute(mapping, scenario, 2048, mode='integrated',
                                 out=temporary, trace_limit=2048)
                trace = [json.loads(line) for line in
                         (Path(temporary)/'trace.jsonl').read_text().splitlines()]
            consumed = [row['external_read']['value'] for row in trace
                        if row['pc'] == 0x127]
            addresses = [row['external_read']['address'] for row in trace
                         if row['pc'] == 0x12C and
                         row['external_read'].get('selected_by_alu')]
            if not result['clean'] or consumed != stream[:len(consumed)]:
                raise ValueError(f'{name} {label} controller stream changed')
            stream_cases.append(dict(order=label, **counts(result),
                                     controller_bits_available=len(stream),
                                     controller_bits_consumed=len(consumed),
                                     first_inputs=consumed[:8],
                                     selected_rom_reads=len(addresses),
                                     distinct_rom_addresses=len(set(addresses)),
                                     first_rom_addresses=addresses[:12],
                                     trace_digest=result['trace_digest']))
        cases.append(dict(mapping=name, held_byte_sweep=dict(
            runs=len(rows), table_entry_bytes=enter_table,
            input_visit_histogram=dict(sorted(Counter(
                row['input_127'] for row in rows).items())),
            table_visit_histogram=dict(sorted(Counter(
                row['rom_12c'] for row in rows).items())),
            output_visits=sum(row['output_392'] for row in rows)),
            controller_streams=stream_cases))
    paths = [Path(__file__), HERE/'controller_bit_dispatch.py',
             HERE/'photo_variant_rom_loop.py', HERE/'photo_controller_path.py',
             GATE_FITS, ROM, ASSUMED/'execute.py', HERE.parent/'model.py',
             *MAPPINGS.values()]
    report = dict(status='diagnostic D127/table-path exclusivity; no modem output',
                  fixture=dict(mapping_names=['q1', 'q2'], initial_q=0,
                               initial_ram=[0]*16, rom_gate='first fit selecting PC127, with PC127 removed',
                               external_input_pc='127', selected_rom_pc='12C',
                               held_byte_cycles=512, controller_cycles=2048),
                  cases=cases,
                  limitations=[
                      'Removing PC127 from the fitted ROM gate is a wiring hypothesis, not a traced decoder.',
                      'The q1/q2 A2/A3 choices are photo candidates, not recovered Am2901 fields.',
                      'Only Q=0, zero RAM, one gate and two mappings are tested.',
                      'The controller source is a scrambler bitstream, not a full modem command or a traced DSC input.',
                      'ROM feedback at 12C is not a demonstrated pulse filter or DAC output.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    for row in run()['cases']:
        print(row['mapping'], row['held_byte_sweep']['table_entry_bytes'],
              [(x['order'], x['controller_bits_consumed'], x['selected_rom_reads'])
               for x in row['controller_streams']])
