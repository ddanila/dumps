"""Test which controller D-byte lanes reach the candidate output in the split ALU."""

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
from controller_bit_dispatch import controller_stream
from independent_slice_addresses import mapping_for
from photo_controller_path import fixture
from split_slice_probe import split_scenario


def one_run(mapping, scenario, values, directory):
    candidate = copy.deepcopy(scenario)
    candidate['initial']['q'] = 5
    candidate['io']['read']['pc_sequences']['910'] = values
    result = execute(mapping, candidate, 1580, mode='integrated',
                     out=directory, trace_limit=1580)
    rows = [json.loads(line) for line in (directory / 'trace.jsonl').read_text().splitlines()]
    inputs = [row for row in rows if row['pc'] == 0x38E]
    outputs = {site: [row['alu']['y'] for row in rows if row['pc'] == int(site, 16)]
               for site in ('39E', '39F')}
    if (not result['clean'] or len(inputs) != 128 or
            any(not row['external_read']['selected_by_alu'] for row in inputs) or
            any(len(series) != 128 for series in outputs.values())):
        raise ValueError('candidate loop did not complete with 128 selected inputs/outputs')
    rom_addresses = sorted({row['external_read']['address'] for row in rows
                            if 'address' in row.get('external_read', {}) and
                            row['external_read']['selected_by_alu']})
    rom_after_input = sorted({row['external_read']['address'] for row in rows
                              if row['cycle'] > inputs[0]['cycle'] and
                              'address' in row.get('external_read', {}) and
                              row['external_read']['selected_by_alu']})
    return dict(inputs=[row['external_read']['value'] for row in inputs],
                input_cycles=[row['cycle'] for row in inputs],
                outputs=outputs, trace_digest=result['trace_digest'],
                rom_addresses=rom_addresses,
                rom_addresses_after_input=rom_after_input)


def differing(a, b):
    return [i for i, (left, right) in enumerate(zip(a, b)) if left != right]


def run(out=HERE / 'results/independent-slice-d-lanes.json'):
    _, base = fixture()
    scenario = split_scenario(base)
    mapping = mapping_for('b')
    _, bits = controller_stream()
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        for lane in range(8):
            level = 1 << lane
            waveforms = dict(zero=[0] * len(bits), one=[level] * len(bits),
                             actual=[level * bit for bit in bits],
                             pulse=[level if i == 20 else 0 for i in range(len(bits))])
            trials = {name: one_run(mapping, scenario, values,
                                    root / f'd{lane}-{name}')
                      for name, values in waveforms.items()}
            output = {}
            for site in ('39E', '39F'):
                z, o, a, p = (trials[name]['outputs'][site]
                              for name in ('zero', 'one', 'actual', 'pulse'))
                predicted = [z[0]] + [o[i] if bits[i - 1] else z[i]
                                       for i in range(1, len(bits))]
                output[site] = dict(zero_first_three=z[:3], one_first_three=o[:3],
                                    actual_first_24=a[:24],
                                    zero_one_differing_indices=differing(z, o),
                                    pulse_differing_indices=differing(z, p),
                                    actual_lag_one_prediction_mismatches=differing(a, predicted),
                                    steady_zero=sorted(set(z[1:])),
                                    steady_one=sorted(set(o[1:])),
                                    steady_actual=sorted(set(a[1:])))
            cases.append(dict(lane=lane, d_byte_for_one=f'{level:02X}',
                              output=output,
                              traces={name: trial['trace_digest']
                                      for name, trial in trials.items()},
                              rom_addresses={name: trial['rom_addresses']
                                             for name, trial in trials.items()},
                              rom_addresses_after_input={
                                  name: trial['rom_addresses_after_input']
                                  for name, trial in trials.items()}))
    report = dict(status='controller bit placement in hypothetical D byte',
                  fixture=dict(mapping=mapping['name'], controller_bits=len(bits),
                               controller_bits_sha256=hashlib.sha256(bytes(bits)).hexdigest(),
                               first_input_cycle=49, first_output_cycle=51,
                               pulse_input_index=20, cycles=1580,
                               note='39E and 39F are candidate ALU Y sites, not a traced DAC'),
                  cases=cases,
                  limitations=[
                      'The controller-to-D bus route, bit position, upper B field and DAC latch remain assumptions.',
                      'One-bit D bytes are a diagnostic bus encoding, not a proven controller interface.',
                      'The local controller stream is not a complete call or a reference line waveform.'],
                  source_sha256={str(p.relative_to(HERE.parent)):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (Path(__file__), HERE / 'independent_slice_addresses.py',
                                           HERE / 'independent_slice_fields.py',
                                           HERE / 'controller_bit_dispatch.py',
                                           HERE / 'split_slice_probe.py',
                                           ASSUMED / 'execute.py', HERE.parent / 'model.py')})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    for case in report['cases']:
        print(f"D{case['lane']}",
              {site: (row['steady_zero'], row['steady_one'],
                      len(row['pulse_differing_indices']),
                      len(row['actual_lag_one_prediction_mismatches']))
               for site, row in case['output'].items()})
