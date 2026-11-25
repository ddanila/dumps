"""Test the executed AF/B0 frame change in two labelled DSC input routes."""

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from photo_cd4094_order import shift_four_bytes
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from photo_127_liveness import ROM, run_case
from independent_slice_addresses import mapping_for
from split_frame_byte_rule import expected, one_run
from split_slice_probe import split_scenario

SOURCE = HERE / 'results/zero-run-detector.json'
FRAMES = {'AF': bytes.fromhex('D0 42 89 9A'),
          'B0': bytes.fromhex('D0 42 81 1A')}


def run(out=HERE / 'results/photo-af-b0-frame-routes.json'):
    source = json.loads(SOURCE.read_text())
    observed = {state: {row['outgoing_frame'] for row in source['cases']
                        if row['final_state'] == state}
                for state in FRAMES}
    if observed != {state: {frame.hex(' ').upper()}
                    for state, frame in FRAMES.items()}:
        raise ValueError('executed controller frames changed')
    _, base = fixture()

    # The held-byte D38E hypothesis uses only bits 4..6 at its reached Y39E.
    d38e = []
    mapping38e = mapping_for('b')
    scenario38e = split_scenario(base)
    for lane in range(4):
        before, after = (FRAMES[state][lane] for state in ('AF', 'B0'))
        values = [before] * 16 + [after] * 16
        result, outputs = one_run(mapping38e, scenario38e, values,
                                  f'AF_to_B0_lane_{lane}')
        if (result['mismatches'] or outputs[1:] !=
                [expected(value) for value in values[:-1]]):
            raise ValueError(('D38E byte rule changed', lane))
        d38e.append(dict(lane=lane, af=f'{before:02X}', b0=f'{after:02X}',
                         af_y39e=f'{expected(before):02X}',
                         b0_y39e=f'{expected(after):02X}',
                         observed_y39e_changes=sum(a != b for a, b in
                                                   zip(outputs[1:], outputs[2:])),
                         selected_rom_addresses=result['rom_addresses_after_input'],
                         trace_digest=result['trace_digest']))
    if any(row['af_y39e'] != row['b0_y39e'] or
           row['observed_y39e_changes'] for row in d38e):
        raise ValueError('AF/B0 frame became visible at Y39E')

    # Each chip/orientation is a separate, held D127 wiring candidate.
    mapping127 = mapped(MAPPINGS['q3'])
    routes = []
    cache = {}
    for chip in range(4):
        for order in ('q1_to_d0', 'q8_to_d0'):
            values = {state: shift_four_bytes(frame)[chip][order]
                      for state, frame in FRAMES.items()}
            cases = {}
            for state, value in values.items():
                if value not in cache:
                    _, result, trace = run_case(mapping127, base, value, 256)
                    if not result['clean']:
                        raise ValueError(('D127 run stopped', value))
                    cache[value] = dict(pc129_reads=sum(r['pc'] == 0x129 for r in trace),
                                        pc12e_reads=sum(r['pc'] == 0x12E for r in trace),
                                        final_pc=f'{trace[-1]["pc"]:03X}',
                                        trace_digest=result['trace_digest'])
                cases[state] = dict(d127=f'{value:02X}', **cache[value])
            routes.append(dict(logical_chip=chip, order=order, cases=cases,
                               path_changed=cases['AF']['trace_digest'] !=
                                            cases['B0']['trace_digest']))
    if not (any(row['path_changed'] for row in routes) and
            any(not row['path_changed'] for row in routes)):
        raise ValueError('D127 route discrimination changed')

    paths = [Path(__file__), SOURCE, ROM, HERE / 'zero_run_detector.py',
             HERE / 'photo_cd4094_order.py',
             HERE / 'photo_127_liveness.py',
             HERE / 'split_frame_byte_rule.py',
             HERE / 'split_slice_probe.py',
             HERE / 'independent_slice_addresses.py',
             HERE / 'photo_controller_path.py',
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3']]
    report = dict(status='AF/B0 control-bit visibility under held-byte input hypotheses',
                  controller_frames={state: frame.hex(' ').upper()
                                     for state, frame in FRAMES.items()},
                  fixture=dict(controller='same-image AF/B0 output from zero-run detector',
                               d38e='one held frame byte at a time; split-slice mapping b, Q=5; 16 AF then 16 B0 input visits',
                               d127='one CD4094 output byte held at PC127; q3 mapping, Q=0, upper Am27S31 bank, 3000 real-PROM instructions per distinct byte',
                               cd4094='four cascaded eight-bit stages, one strobe; logical order and both bit orientations tested'),
                  d38e=d38e, d127_routes=routes,
                  interpretation='The two changed frame bits are invisible at reached Y39E in the tested D38E relay, while some held D127 lanes alter the PROM phase-loop trace. Neither result identifies the physical command route or echo-canceller action.',
                  limitations=['The CD4094 cascade, its strobe and both DSC ingress routes are photo-compatible hypotheses rather than traced nets.',
                               'Each D127 frame is held in a separate startup run; no continuous AF-to-B0 DSP transition or echo signal is modeled.',
                               'Y39E and the D127 loop trace are internal diagnostics, not DAC output or received-bit evidence.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    print([(row['logical_chip'], row['order'], row['path_changed'])
           for row in result['d127_routes']])
