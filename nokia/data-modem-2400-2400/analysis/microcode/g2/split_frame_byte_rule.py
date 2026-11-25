"""Derive the recurring D38E→39E byte rule from real-PROM execution."""

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
from split_slice_probe import split_scenario

CONTROLLER = HERE / 'results/main-loop-serial.json'
SELECTORS = ('00', '20', '40', '60')


def expected(byte):
    return (0x1B + 2 * (byte & 0x70)) & 255


def one_run(mapping, base, values, label):
    scenario = copy.deepcopy(base)
    scenario['initial']['q'] = 5
    scenario['io']['read']['pc_sequences']['910'] = values
    cycles = 12 * len(values) + 44
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, cycles, mode='integrated',
                         out=temporary, trace_limit=cycles)
        trace = [json.loads(line) for line in
                 (Path(temporary) / 'trace.jsonl').read_text().splitlines()]
    inputs = [row for row in trace if row['pc'] == 0x38E]
    outputs = [row['alu']['y'] for row in trace if row['pc'] == 0x39E]
    if (not result['clean'] or len(inputs) != len(values) or
            [row['external_read']['value'] for row in inputs] != values or
            any(not row['external_read']['selected_by_alu'] for row in inputs) or
            len(outputs) != len(values)):
        raise ValueError(f'{label}: expected recurring input/output loop changed')
    predicted = [0xFB] + [expected(value) for value in values[:-1]]
    mismatches = [index for index, (got, want) in enumerate(zip(outputs, predicted))
                  if got != want]
    first_input_cycle = inputs[0]['cycle']
    rom_after_input = sorted({row['external_read']['address'] for row in trace
                              if row['cycle'] > first_input_cycle and
                              'address' in row.get('external_read', {}) and
                              row['external_read']['selected_by_alu']})
    return dict(label=label, clean=True, input_bytes=len(values),
                output_visits=len(outputs), first_16_input=values[:16],
                first_16_output=outputs[:16], distinct_output=sorted(set(outputs)),
                mismatches=mismatches, rom_addresses_after_input=rom_after_input,
                photo_candidate_b5_after_startup=sorted({(v >> 4) & 1
                                                        for v in outputs[1:]}),
                trace_digest=result['trace_digest']), outputs


def run(out=HERE / 'results/split-frame-byte-rule.json'):
    controller = json.loads(CONTROLLER.read_text())
    if len(controller['rows']) != 256 or controller['distinct_streams'] != 4:
        raise ValueError('controller frame source changed')
    frames = {}
    for selector in SELECTORS:
        row = next(row for row in controller['rows'] if row['selector'] == selector)
        frames[selector] = [int(value, 16) for frame in row['frames']
                            for value in frame.split()]
        if len(frames[selector]) != 48:
            raise ValueError(f'{selector}: expected 12 four-byte frames')
    _, base = fixture()
    scenario = split_scenario(base)
    mapping = mapping_for('b')
    all_streams = dict(ascending=list(range(256)),
                       descending=list(range(255, -1, -1)),
                       **{f'controller_{selector}': values
                          for selector, values in frames.items()})
    cases = []
    by_byte = {value: set() for value in range(256)}
    for label, values in all_streams.items():
        row, outputs = one_run(mapping, scenario, values, label)
        if row['mismatches']:
            raise ValueError(f"{label}: byte rule failed at {row['mismatches'][:8]}")
        cases.append(row)
        for byte, output in zip(values[:-1], outputs[1:]):
            by_byte[byte].add(output)
    if any(by_byte[value] != {expected(value)} for value in range(256)):
        raise ValueError('full byte-domain rule incomplete')
    report = dict(status='exact byte rule in stated split-slice fixture',
                  formula='Y39E[n]=1B+2*(D38E[n-1]&70), modulo 256, for n>=1; Y39E[0]=FB',
                  fixture=dict(mapping=mapping['name'],
                               high_b_bits=mapping['fields']['b_high']['bits'],
                               startup_q=5, initial_ram=[0] * 16,
                               candidate_input_pc='38E', candidate_output_pc='39E',
                               controller_selectors=list(SELECTORS),
                               total_tested_input_bytes=sum(len(v) for v in all_streams.values()),
                               distinct_byte_values_checked=len(by_byte)),
                  cases=cases,
                  byte_rule={f'{value:02X}': expected(value) for value in range(256)},
                  limitations=[
                      'The upper B bit source, independent slice instructions, branch/ROM timing and D38E route are hypotheses.',
                      'The controller frames are replayed locally, not as a complete synchronized DSP connection.',
                      'Y at 39E is an ALU value, not a traced DAC latch input or line-output sample.',
                      'The rule proves this fixture, not all startup states or physical wiring.'],
                  source_sha256={str(p.relative_to(HERE.parent)):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (Path(__file__), CONTROLLER,
                                           HERE / 'independent_slice_addresses.py',
                                           HERE / 'independent_slice_fields.py',
                                           HERE / 'photo_controller_path.py',
                                           HERE / 'split_slice_probe.py',
                                           ASSUMED / 'execute.py', HERE.parent / 'model.py')})
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    print([(row['label'], row['input_bytes'], len(row['mismatches']),
            row['rom_addresses_after_input']) for row in result['cases']])
