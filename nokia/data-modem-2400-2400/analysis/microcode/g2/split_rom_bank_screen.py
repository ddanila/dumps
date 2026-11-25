"""Test whether Am27S31 A8 choices alter the split-slice byte relay."""

import copy
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
from independent_slice_addresses import mapping_for
from photo_controller_path import fixture
from photo_mapping_stream_screen import MAPPINGS
from split_frame_byte_rule import CONTROLLER, SELECTORS, expected
from split_slice_probe import split_scenario

ROM = HERE.parents[2] / 'am27s31dc-prom/nokia-modem-am27s31dc.bin'


def run_case(mapping, base, label, values, global_bank, d38c_bank):
    scenario = copy.deepcopy(base)
    scenario['initial']['q'] = 5
    scenario['io']['read']['pc_sequences']['910'] = values
    address = scenario['io']['read']['address']
    address['bank'] = global_bank
    address['bank_by_pc'] = {str(0x38C): d38c_bank}
    cycles = 12 * len(values) + 44
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, cycles, mode='integrated',
                         out=temporary, trace_limit=cycles)
        trace = [json.loads(line) for line in
                 (Path(temporary) / 'trace.jsonl').read_text().splitlines()]
    inputs = [row for row in trace if row['pc'] == 0x38E]
    outputs = [row['alu']['y'] for row in trace if row['pc'] == 0x39E]
    reads = [row for row in trace if row['pc'] == 0x38C and
             row['external_read'].get('selected_by_alu')]
    if (not result['clean'] or len(inputs) != len(values) or
            [row['external_read']['value'] for row in inputs] != values or
            len(outputs) != len(values) or len(reads) < len(values) - 1):
        raise ValueError(f'{label} bank {global_bank}/{d38c_bank}: loop changed')
    predicted = [0xFB] + [expected(value) for value in values[:-1]]
    if outputs != predicted:
        raise ValueError(f'{label} bank {global_bank}/{d38c_bank}: byte rule changed')
    first_input_cycle = inputs[0]['cycle']
    after = [row for row in reads if row['cycle'] > first_input_cycle]
    return dict(label=label, global_bank=global_bank, d38c_bank=d38c_bank,
                input_bytes=len(inputs), output_visits=len(outputs),
                selected_d38c_reads_after_input=len(after),
                selected_d38c_address_value=sorted({
                    (row['external_read']['address'], row['external_read']['value'])
                    for row in after}),
                first_16_outputs=outputs[:16], distinct_outputs=sorted(set(outputs)),
                final_pc=result['final_state']['pc'],
                final_q=result['final_state']['q'],
                final_ram=result['final_state']['ram'],
                trace_digest=result['trace_digest']), outputs


def run(out=HERE / 'results/split-rom-bank-screen.json'):
    controller = json.loads(CONTROLLER.read_text())
    frames = {}
    for selector in SELECTORS:
        row = next(row for row in controller['rows'] if row['selector'] == selector)
        frames[f'controller_{selector}'] = [int(value, 16)
            for frame in row['frames'] for value in frame.split()]
        if len(frames[f'controller_{selector}']) != 48:
            raise ValueError('controller frame count changed')
    streams = dict(ascending=list(range(256)),
                   descending=list(range(255, -1, -1)), **frames)
    _, base = fixture()
    scenario = split_scenario(base)
    mapping = mapping_for('b')
    cases = []
    for label, values in streams.items():
        output_sequences = []
        for global_bank in (0, 256):
            for d38c_bank in (0, 256):
                row, outputs = run_case(mapping, scenario, label, values,
                                        global_bank, d38c_bank)
                cases.append(row)
                output_sequences.append(outputs)
        if any(outputs != output_sequences[0] for outputs in output_sequences[1:]):
            raise ValueError(f'{label}: A8 changed 39E outputs')
        if len({row['trace_digest'] for row in cases[-4:]}) < 2:
            raise ValueError(f'{label}: A8 alternatives did not change the trace')
        for left, right in ((cases[-4], cases[-3]), (cases[-2], cases[-1])):
            if any(left[key] != right[key]
                   for key in ('final_pc', 'final_q', 'final_ram')):
                raise ValueError(f'{label}: D38C bank changed loop-boundary state')
    sources = [Path(__file__), CONTROLLER, HERE / 'split_frame_byte_rule.py',
               HERE / 'independent_slice_addresses.py',
               HERE / 'independent_slice_fields.py',
               HERE / 'photo_controller_path.py', HERE / 'split_slice_probe.py',
               ASSUMED / 'execute.py', HERE.parent / 'model.py',
               MAPPINGS['q3'], ROM]
    report = dict(status='bounded A8 hypothesis screen, not physical output proof',
                  fixture=dict(mapping=mapping['name'], initial_q=5,
                               selected_rom_site='38C', input_site='38E',
                               candidate_output_site='39E',
                               global_a8=[0, 1], d38c_a8=[0, 1],
                               streams=list(streams), runs=len(cases)),
                  result='All four A8 choices preserve the exact 39E byte rule; '
                         'changing only D38C A8 also preserves loop-boundary state.',
                  formula='Y39E[n]=1B+2*(D38E[n-1]&70), n>=1; Y39E[0]=FB',
                  cases=cases,
                  limitations=[
                      'A8 sources and timing, upper B field, controller-to-D route and slice links are assumed.',
                      'The screen varies bank at 38C by PC, not by controller bit or intra-cycle phase.',
                      'The output is ALU Y at a candidate site, not a traced DAC input.',
                      'The ROM read changes internal state; this excludes only 39E in this loop and fixture.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    for row in report['cases'][:4]:
        print(row['label'], row['global_bank'], row['d38c_bank'],
              row['selected_d38c_address_value'], row['distinct_outputs'])
