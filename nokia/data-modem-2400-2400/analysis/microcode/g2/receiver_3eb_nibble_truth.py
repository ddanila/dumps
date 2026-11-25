"""Enumerate the reached 3EB D-byte transfer and first loop decision."""

import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from joint_upper_source_screen import SELECTED_MASK, candidate
from lower_i_d3f8_full_adc import codes
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_3eb_adc_route_screen import CYCLES, VISITS, scenario


def first_decision(mapping, base, value, temporary):
    execute(mapping, scenario(base, True, False, [value] * VISITS),
            55, mode='integrated', out=temporary, trace_limit=55)
    trace = [json.loads(line) for line in
             (Path(temporary) / 'trace.jsonl').open()]
    at_3eb = next(row for row in trace if row['pc'] == 0x3EB)
    at_3ed = next(row for row in trace if row['pc'] == 0x3ED)
    return dict(input=value, y_3eb=at_3eb['alu']['y'],
                test_3ed=at_3ed['test'], next_pc_3ed=at_3ed['next_pc'])


def waveform_case(mapping, base, values, name, transform):
    source = [value for sample, value in enumerate(values)
              for _ in range(94 if sample % 4 < 3 else 93)]
    candidate_scenario = scenario(base, False, True, source)
    if transform is not None:
        sequence = [item for value in source for item in transform(value)]
        sequence.append(transform(source[-1])[0])
        candidate_scenario['io']['read']['pc_sequences'][str(0x3EB)] = sequence
        candidate_scenario['io']['read']['evidence'] += (
            '; diagnostic 3EB nibble/row-phase lane route ' + name)
    result = execute(mapping, candidate_scenario, CYCLES,
                     mode='integrated', trace_limit=0)
    if not result['clean'] or result['completed_cycles'] != CYCLES:
        raise ValueError(('nibble-route run stopped', name))
    return dict(name=name,
                visits_3f8=result['address_counts'].get(0x3F8, 0),
                visits_3eb=result['address_counts'].get(0x3EB, 0),
                final_pc=f'{result["final_state"]["pc"]:03X}',
                trace_digest=result['trace_digest'])


def run(out=HERE / 'results/receiver-3eb-nibble-truth.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), SELECTED_MASK)
    _, base = fixture()
    with tempfile.TemporaryDirectory() as temporary:
        truth = [first_decision(mapping, base, value, temporary)
                 for value in range(256)]
    by_high_nibble = []
    for high in range(16):
        rows = truth[16 * high:16 * high + 16]
        outputs = {row['y_3eb'] for row in rows}
        branches = {(row['test_3ed'], row['next_pc_3ed']) for row in rows}
        if len(outputs) != 1 or len(branches) != 1:
            raise ValueError(('low nibble affected first decision', high))
        test, next_pc = next(iter(branches))
        by_high_nibble.append(dict(high_nibble=f'{high:X}',
                                   y_3eb=f'{next(iter(outputs)):02X}',
                                   test_3ed=test, next_pc_3ed=f'{next_pc:03X}'))
    samples = codes((0, 1, 3, 2), 32, 'complementary')
    policies = (
        ('default 3EB', None),
        ('both full', lambda value: (value, value)),
        ('both low nibble', lambda value: (value & 15, value & 15)),
        ('first row low nibble', lambda value: (value & 15, 1)),
        ('second row low nibble', lambda value: (1, value & 15)),
        ('first row full', lambda value: (value, 1)),
        ('second row full', lambda value: (1, value)),
    )
    waveform = [waveform_case(mapping, base, samples, name, transform)
                for name, transform in policies]
    if (any(row['y_3eb'] != f'{((int(row["high_nibble"], 16) + 1) & 15) << 4:02X}'
            for row in by_high_nibble) or
            [row['high_nibble'] for row in by_high_nibble
             if row['test_3ed'] == 0] != ['6', 'A', 'B', 'F'] or
            any(row['trace_digest'] != waveform[0]['trace_digest']
                for row in waveform[2:5]) or
            any(row['visits_3f8'] != VISITS for row in waveform[2:5])):
        raise ValueError('3EB nibble behavior changed')
    report = dict(experiment='first 3EB transfer for every D byte and ADC lane control',
                  fixture=dict(mapping='joint upper-source mask 08',
                               dispatch='scenario [0,2] at 3EC',
                               initial_q=5, initial_ram=[0] * 16,
                               condition='inverted previous sign',
                               waveform='32 complementary samples of 0,1,3,2 pattern',
                               cycles_per_waveform=CYCLES),
                  by_high_nibble=by_high_nibble, waveform=waveform,
                  source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    print([(row['name'], row['visits_3f8']) for row in result['waveform']])
