"""Test a controller-byte relay through the 3A6 to 3B3–3B6 candidate path."""

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent/'assumed'), str(HERE)]

from common import save
from controller_bit_dispatch import controller_stream
from lower_i_d3f8_input import run_trace
from lower_i_prom_data_route import mapping_for
from photo_controller_path import fixture

OUTPUT_PCS = (0x3B3, 0x3B4, 0x3B5, 0x3B6)
INPUT_PCS = tuple(range(0x3A3, 0x3A8))


def scenario_with_trigger(base):
    scenario = dict(base)
    scenario['condition'] = dict(base['condition'])
    scenario['condition']['sources'] = list(base['condition']['sources'])
    scenario['condition']['sources'][0] = 'carry'
    scenario['io'] = dict(base['io'])
    scenario['io']['read'] = dict(base['io']['read'])
    scenario['io']['read']['pc_sequences'] = dict(base['io']['read']['pc_sequences'])
    trigger = [1]*192
    trigger[20] = 3
    scenario['io']['read']['pc_sequences'][str(0x3F8)] = trigger
    return scenario


def output_quartets(trace):
    events = [(row['pc'], row['alu']['y']) for row in trace
              if row['pc'] in OUTPUT_PCS]
    if len(events) % 4:
        raise ValueError('incomplete output quartet')
    quartets = []
    for offset in range(0, len(events), 4):
        group = events[offset:offset+4]
        if tuple(pc for pc, _ in group) != OUTPUT_PCS:
            raise ValueError('output site order changed')
        quartets.append(tuple(y for _, y in group))
    return quartets


def expected(byte):
    nibble = byte & 15
    return (0xF0 | nibble, 0xF0 | ((nibble+1) & 15),
            nibble, 15-nibble)


def run(out=HERE/'results/lower-i-late-byte-relay.json'):
    _, base = fixture()
    mapping = mapping_for('!10.6', '11.2')
    scenario = scenario_with_trigger(base)
    _, bits = controller_stream()
    baseline = run_trace(mapping, scenario, 0x3A6, [1]*192)
    reference = output_quartets(baseline['trace'])
    if baseline['site_visits'] != 103 or len(reference) != 103 or set(reference) != {expected(1)}:
        raise ValueError('late-byte baseline changed')

    site_screen = []
    for site in INPUT_PCS:
        control = run_trace(mapping, scenario, site, [1]*192)
        control_output = output_quartets(control['trace'])
        if control_output != reference:
            raise ValueError(f'constant control changed at {site:03X}')
        lanes = []
        for lane in (1, 2, 3):
            values = [1 | (bit << lane) for bit in bits]
            trial = run_trace(mapping, scenario, site, values)
            observed = output_quartets(trial['trace'])
            if len(observed) != len(reference):
                raise ValueError(f'output quartet count changed at {site:03X}')
            differing = sum(a != b for left, right in zip(reference, observed)
                            for a, b in zip(left, right))
            lanes.append(dict(lane=lane, visits=trial['site_visits'],
                              output_quartets=len(observed),
                              differing_output_bytes=differing,
                              trace_digest=trial['result']['trace_digest']))
        site_screen.append(dict(pc=f'{site:03X}', lanes=lanes))
    expected_differences = {'3A3': 0, '3A4': 42, '3A5': 0,
                            '3A6': 168, '3A7': 0}
    for row in site_screen:
        if any(lane['differing_output_bytes'] != expected_differences[row['pc']]
               or lane['visits'] != 103 for lane in row['lanes']):
            raise ValueError(f'late-input sensitivity changed at {row["pc"]}')

    byte_signatures = []
    for byte in range(256):
        trial = run_trace(mapping, scenario, 0x3A6, [byte]*32, cycles=512)
        quartets = output_quartets(trial['trace'])
        signature = expected(byte)
        if trial['site_visits'] != 14 or len(quartets) != 14 or any(q != signature for q in quartets):
            raise ValueError(f'full-byte rule fails for {byte:02X}')
        byte_signatures.append(signature)
    if len(set(byte_signatures)) != 16:
        raise ValueError('byte rule does not collapse to sixteen low-nibble values')

    controller = []
    for lane in (1, 2, 3):
        values = [1 | (bit << lane) for bit in bits]
        trial = run_trace(mapping, scenario, 0x3A6, values, cycles=2000)
        quartets = output_quartets(trial['trace'])
        if trial['site_visits'] < 128 or len(quartets) < 128 or any(
                quartets[index] != expected(values[index]) for index in range(128)):
            raise ValueError(f'full controller relay fails on D{lane}')
        controller.append(dict(lane=lane, input_visits=trial['site_visits'],
                               checked_bits=128, output_quartets=len(quartets),
                               distinct_quartets=len(set(quartets[:128])),
                               trace_digest=trial['result']['trace_digest']))

    paths = [Path(__file__), HERE/'lower_i_d3f8_input.py',
             HERE/'lower_i_prom_data_route.py', HERE/'controller_bit_dispatch.py',
             HERE/'photo_controller_path.py', HERE.parent/'assumed/execute.py']
    report = dict(status='conditional full-byte and 8031-stream relay at 3A6',
                  fixture=dict(mapping='I7/A0=!10.6, I0/A1=11.2, lower I6=11.0',
                               condition_select_0='previous carry, inverted',
                               initial_q=5, d3f8_trigger='D1 pulse at visit 20',
                               tested_late_d_sites=[f'{pc:03X}' for pc in INPUT_PCS],
                               virtual_output_sites=[f'{pc:03X}' for pc in OUTPUT_PCS]),
                  site_screen=site_screen,
                  full_byte_check=dict(bytes_checked=256, cycles_each=512,
                                       input_visits_each=14,
                                       distinct_signatures=len(set(byte_signatures)),
                                       rule='n=D&0F; outputs=(F0|n, F0|((n+1)&0F), n, 0F-n)',
                                       signatures_sha256=hashlib.sha256(
                                           json.dumps(byte_signatures).encode()).hexdigest()),
                  controller_stream=dict(bits=len(bits), first_128_one_bits=sum(bits),
                                         lanes=controller),
                  limitations=[
                      'The D3F8 trigger, D3A6 input route, condition source, PROM data connections and output capture sites are untraced hypotheses.',
                      'The quartet is a nibble transform with no demonstrated carrier phase, DAC sample clock or analog line path.',
                      'This does not meet the transmitter or receiver/echo-canceller acceptance tests.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    print('site differences', [(row['pc'], row['lanes'][0]['differing_output_bytes'])
                               for row in result['site_screen']])
    print('byte values checked', result['full_byte_check']['bytes_checked'])
    print('controller bits checked', result['controller_stream']['bits'])
