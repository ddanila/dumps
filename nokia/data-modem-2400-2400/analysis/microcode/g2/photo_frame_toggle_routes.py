"""Test observed controller frame-bit toggles through two existing D127 routes."""

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from photo_12c_prom_edge_latch import run_trace
from photo_127_liveness import ROM
from photo_controller_mode_decode import decode_chip1, projected_codes
from photo_controller_path import fixture
from photo_dac08_bus_order_screen import swap_bits
from photo_main_frame_carrier_swap import spectrum
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

CONTROLLER = HERE / 'results/main-loop-long.json'


def run(out=HERE / 'results/photo-frame-toggle-routes.json'):
    controller = json.loads(CONTROLLER.read_text())
    if {row['selector'] for row in controller['runs']} != {'00', '20', '40', '60'}:
        raise ValueError('controller classes changed')
    observed = {}
    for row in controller['runs']:
        for index, item in enumerate(row['iterations']):
            if item['state'] not in ('B4', 'A5'):
                continue
            frame = bytes.fromhex(item['frame'])
            if len(frame) != 4 or frame[2] not in (0xA1, 0x81, 0xC1):
                raise ValueError(('frame format changed', row['selector'], index))
            observed.setdefault(f'{frame[2]:02X}', []).append(dict(
                selector=row['selector'], iteration=index, state=item['state'],
                frame=item['frame']))
    if set(observed) != {'A1', '81', 'C1'}:
        raise ValueError('controller toggle values changed')
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    rom = ROM.read_bytes()
    routes = []
    for name in ('decoded_mode', 'direct_d0_d4_crossing'):
        cases = []
        for raw in (0xA1, 0x81, 0xC1):
            if name == 'decoded_mode':
                enabled, mode, control = decode_chip1(raw)
                if (enabled, mode) != (1, (raw >> 5) & 1):
                    raise ValueError('mode decode changed')
            else:
                control = swap_bits(raw, 0, 4)
            result, trace = run_trace(mapping, base, control, 0xEA)
            reads = [event for event in trace if event['pc'] == 0x129]
            if (not result['clean'] or len(reads) != 740 or
                    any(event['pc'] == 0x12E for event in trace)):
                raise ValueError(('DSC loop changed', name, raw))
            for n, event in enumerate(reads, 1):
                phase = (3 + n * control) & 255
                value = rom[256 + phase]
                if (event['external_read']['address'] != 256 + phase or
                        event['external_read']['value'] != value or
                        event['alu']['y'] != (phase - value) & 255):
                    raise ValueError(('PROM/Y recurrence changed', name, raw, n))
            codes = projected_codes(rom, control)
            cases.append(dict(frame_byte=f'{raw:02X}', d127=f'{control:02X}',
                              executed_pc129_reads=len(reads),
                              projected_peak_hz=spectrum(codes)['peak_hz'],
                              projected_1800_hz_variance=spectrum(codes)['target_r2'],
                              projected_codes_sha256=hashlib.sha256(bytes(codes)).hexdigest()))
        routes.append(dict(route=name, cases=cases))
    if ([case['d127'] for case in routes[0]['cases']] != ['B0', '88', '88'] or
            [case['d127'] for case in routes[1]['cases']] != ['B0', '90', 'D0']):
        raise ValueError('route decode changed')
    paths = [Path(__file__), CONTROLLER, ROM,
             HERE / 'main_loop_long.py', HERE / 'main_loop_probe.c',
             HERE / 'photo_12c_prom_edge_latch.py',
             HERE / 'photo_controller_mode_decode.py',
             HERE / 'photo_main_frame_carrier_swap.py',
             HERE / 'photo_mapping_stream_screen.py', MAPPINGS['q3'],
             HERE.parent / 'board/inventory.json',
             HERE.parent / 'board/evidence/front-annotated.jpg',
             HERE.parent / 'board/evidence/back-annotated.jpg']
    report = dict(status='existing two candidate D127 routes do not turn the observed held frame-bit toggle into a carrier-preserving reversal',
                  observed_frame_bytes=observed, routes=routes,
                  fixture=dict(controller='64-iteration unchanged 8031 ROM replay; B4/A5 frames',
                               dsc='q3 mapping, held I0, Q=0, upper ROM bank at PC129, 3000 real-PROM microinstructions per case',
                               output='project 640 DAC codes from the verified PC129 ROM/Y recurrence, one code per 375 visits',
                               sample_hz=9600),
                  limitations=['The two routes are hypotheses, not traced Nokia connections.',
                               'Each held frame-byte case is a separate DSC run; no controller timing or inter-frame transition is replayed.',
                               'The projected DAC codes extend a verified recurrence beyond the executed 740 PC129 visits.',
                               'Another route or transient strobe could use frame bit 6 without changing the held carrier step.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    for route in run()['routes']:
        print(route['route'], [(case['frame_byte'], case['d127'],
                               case['projected_peak_hz']) for case in route['cases']])
