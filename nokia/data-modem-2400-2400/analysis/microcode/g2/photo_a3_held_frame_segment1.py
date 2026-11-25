"""Test direct held A3 frame-byte D127 routes against the segment-1 phase target."""

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from photo_127_liveness import ROM
from photo_controller_path import fixture
from photo_frame_toggle_edge_pulse import inspect
from photo_i0_hold_screen import hold_candidate
from photo_main_dibit_pulse import BASE, VISITS_PER_SAMPLE, VISITS_PER_SYMBOL
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

CONTROLLER = HERE / 'results/main-loop-timer1-segment2.json'
PARITY = HERE / 'results/photo-127-parity-exit.json'
SYMBOLS = 32


def a3_bytes():
    controller = json.loads(CONTROLLER.read_text())
    values = {int(byte, 16) for case in controller['cases']
              for frame in case['a3_unique_frames'] if frame
              for byte in frame.split()}
    if values != {0xD0, 0x42, 0x81, 0xA1, 0xC1, 0xBA}:
        raise ValueError(('A3 frame byte set changed', values))
    return sorted(values)


def run_even(value, rom, base, mapping):
    visits = SYMBOLS * VISITS_PER_SYMBOL
    inputs = [value] * (visits + 1)
    scenario = hold_candidate(base)
    scenario['name'] += f'; A3 frame byte {value:02X} held at D127 without port-01 data'
    scenario['initial']['q'] = 0
    scenario['io']['read']['pc_sequences'][str(0x127)] = inputs
    scenario['io']['read']['pc_sequences'][str(0x12c)] = [0xEA]
    scenario['io']['read']['address']['bank_by_pc'] = {str(0x129): 256,
                                                       str(0x12e): 256}
    cycles = (visits + 64) * 4
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, cycles, mode='integrated',
                         out=temporary, trace_limit=cycles)
        trace = inspect(Path(temporary) / 'trace.jsonl', rom, inputs, [0] * SYMBOLS)
    if (not result['clean'] or result['completed_cycles'] != cycles or
            result['address_counts'].get(0x129) != trace['pc129_visits'] or
            result['address_counts'].get(0x12e, 0)):
        raise ValueError(('held-byte PROM replay stopped', value))
    phases = [(3 + (index + 1) * VISITS_PER_SYMBOL * value) & 255
              for index in range(SYMBOLS)]
    if phases != trace['symbol_end_phases']:
        raise ValueError(('held-byte phase recurrence changed', value))
    symbol_offsets = [((index + 1) * VISITS_PER_SYMBOL * (value - BASE)) & 255
                      for index in range(SYMBOLS)]
    first_symbol_sample_offsets = [((1 + sample * VISITS_PER_SAMPLE) *
                                    (value - BASE)) & 255
                                   for sample in range(8)]
    target = [128 if index % 2 == 0 else 0 for index in range(SYMBOLS)]
    if symbol_offsets == target or len(set(first_symbol_sample_offsets[1:])) == 1:
        raise ValueError(('constant held input unexpectedly matches segment 1', value))
    return dict(d127=f'{value:02X}', regime='even held byte sustains PC127 loop',
                microinstructions=cycles, pc129_visits=trace['pc129_visits'],
                trace_digest=result['trace_digest'],
                candidate_dac_sample_sha256=trace['sample_sha256'],
                first_16_candidate_dac_codes=[f'{v:02X}' for v in trace['samples'][:16]],
                symbol_phase_offsets_vs_B0=symbol_offsets,
                first_symbol_sample_offsets_vs_B0=first_symbol_sample_offsets,
                segment1_symbol_offsets_match=False,
                stable_phase_within_first_symbol=False)


def run(out=HERE / 'results/photo-a3-held-frame-segment1.json'):
    values = a3_bytes()
    parity = {int(row['d127'], 16): row
              for row in json.loads(PARITY.read_text())['rows']}
    rom = ROM.read_bytes()
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    cases = []
    for value in values:
        if value & 1:
            earlier = parity[value]
            if (earlier['parity'] != 'odd' or
                    not (0 < earlier['pc129_reads'] < 256) or
                    earlier['pc12a_exit_cycle'] is None):
                raise ValueError(('prior odd-byte exit changed', value))
            cases.append(dict(d127=f'{value:02X}',
                              regime='odd held byte exits PC127 loop',
                              pc129_visits_before_exit=earlier['pc129_reads'],
                              first_wait_cycle_under_prior_D12C_01_fixture=earlier['first_wait_cycle'],
                              prior_trace_digest=earlier['trace_digest']))
        else:
            cases.append(run_even(value, rom, base, mapping))
    if len(cases) != 6:
        raise ValueError('A3 lane coverage changed')
    paths = [Path(__file__), CONTROLLER, PARITY, ROM,
             HERE / 'photo_frame_toggle_edge_pulse.py',
             HERE / 'photo_main_dibit_pulse.py',
             HERE / 'photo_controller_path.py',
             HERE / 'photo_i0_hold_screen.py',
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3']]
    report = dict(
        status='no A3 frame byte held directly at D127 gives a 32-symbol carrier-preserving segment-1 reversal in the tested q3 path',
        fixture=dict(controller='six unique byte values in interrupt-paced A3 four-byte frames',
                     d127='one literal held frame byte, no port-01 dibit pulses',
                     rom='upper bank at PC129 under q3 photo-compatible mapping',
                     phase_target='128,0 alternating relative to B0 unmodulated carrier at successive 3000-visit symbols, then steady offset within each symbol'),
        cases=cases,
        limitations=['The CD4094 frame lane, direct D127 route, 3000 visits/symbol and candidate DAC capture are hypotheses, not traced connections.',
                     'Odd-byte loop exits reuse the separately executed all-byte parity report; downstream PC12C behavior depends on its own untraced input.',
                     'Even-byte replays verify the PROM recurrence but cannot exclude a decoded frame command, an autonomous different loop, or another board input path.',
                     'No analog line output or receive/echo-canceller behavior is demonstrated.'],
        source_sha256={str(path.relative_to(HERE.parents[2])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path,
                        default=HERE / 'results/photo-a3-held-frame-segment1.json')
    args = parser.parse_args()
    report = run(args.out)
    for case in report['cases']:
        print(case['d127'], case['regime'],
              case.get('pc129_visits', case.get('pc129_visits_before_exit')))
