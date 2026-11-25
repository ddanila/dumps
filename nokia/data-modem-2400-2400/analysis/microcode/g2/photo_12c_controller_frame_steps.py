"""Try real 8031 frame lanes as the q3 PC12C phase-step input."""

import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]
from common import save
from controller_bit_dispatch import CONTROLLER_ROM, CONTROLLER_SHA
from execute import execute
from photo_127_liveness import ROM
from photo_controller_path import fixture
from photo_i0_hold_screen import hold_candidate
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

CONTROLLER_REPORT = HERE / 'results/main-loop-serial.json'
SELECTORS = ('00', '20', '40', '60')
CYCLES = 3000


def frame_lanes():
    controller = json.loads(CONTROLLER_REPORT.read_text())
    if (controller['controller_rom_sha256'] != CONTROLLER_SHA or
            controller['controller_rom_sha256'] !=
            hashlib.sha256(CONTROLLER_ROM.read_bytes()).hexdigest()):
        raise ValueError('controller report uses a different ROM')
    rows = {row['selector']: row for row in controller['rows']
            if row['selector'] in SELECTORS}
    if set(rows) != set(SELECTORS):
        raise ValueError('missing controller selector class')
    lanes = {}
    for selector, row in rows.items():
        frame = bytes.fromhex(row['frames'][row['first_line_iteration'] - 1])
        if len(frame) != 4:
            raise ValueError('controller frame length changed')
        lanes[selector] = list(frame)
    return lanes


def run(out=HERE / 'results/photo-12c-controller-frame-steps.json'):
    lanes = frame_lanes()
    values = sorted(set(value for frame in lanes.values() for value in frame))
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    rom = ROM.read_bytes()
    cases = []
    for value in values:
        scenario = hold_candidate(base)
        scenario['initial']['q'] = 0
        scenario['io']['read']['pc_sequences'][str(0x127)] = [0x81]
        scenario['io']['read']['pc_sequences'][str(0x12C)] = [value]
        scenario['io']['read']['address']['bank_by_pc'] = {str(0x129): 256}
        with tempfile.TemporaryDirectory() as temporary:
            result = execute(mapping, scenario, CYCLES, mode='integrated',
                             out=temporary, trace_limit=CYCLES)
            trace = [json.loads(line) for line in
                     (Path(temporary) / 'trace.jsonl').read_text().splitlines()]
        if not result['clean'] or len(trace) != CYCLES:
            raise ValueError('candidate frame-byte execution incomplete')
        inputs = [row for row in trace if row['pc'] == 0x12C]
        reads = [row for row in trace if row['pc'] == 0x12E]
        if (not inputs or len(reads) < 1 or
                any(row['external_read']['value'] != value or
                    not row['external_read']['selected_by_alu'] for row in inputs)):
            raise ValueError('frame byte not selected at PC12C')
        for n, row in enumerate(reads, 1):
            address = 256 + ((1 + n * value) & 255)
            event = row['external_read']
            if (event['address'] != address or event['value'] != rom[address]
                    or not event['selected_by_alu']):
                raise ValueError(f'frame byte {value:02X} ROM walk changed')
        waits = [row['cycle'] for row in trace if row['pc'] == 0x084]
        rates = {}
        if value % 2 == 0:
            if waits:
                raise ValueError('even frame byte exited second loop')
            for divisor in (1, 3):
                step = (value * (375 // divisor)) & 255
                rates[str(divisor)] = dict(phase_step=step,
                    folded_phase_hz=min(step, 256 - step) * 9600 / 256,
                    exact_1800_or_2100=step in (48, 56, 200, 208))
        elif not waits:
            raise ValueError('odd frame byte did not exit second loop')
        cases.append(dict(byte=f'{value:02X}', parity='even' if value % 2 == 0 else 'odd',
                          pc12c_visits=len(inputs), pc12e_rom_reads=len(reads),
                          first_wait_cycle=waits[0] if waits else None,
                          fast_clock_phase_rates=rates,
                          trace_digest=result['trace_digest']))
    report = dict(fixture=dict(mapping='q3 photo-swapped', held_d127='81',
                               q=0, cycles_per_byte=CYCLES,
                               frame_lanes_by_selector={key: [f'{v:02X}' for v in frame]
                                                        for key, frame in lanes.items()},
                               assumed_d12c_route='one held controller frame lane',
                               hypothetical_sample_rate_hz=9600,
                               oscillator_hz=14400000,
                               microcycle_divisors=[1, 3]),
                  cases=cases,
                  totals=dict(unique_frame_bytes=len(cases),
                              sustained_even_bytes=sum(c['parity'] == 'even' for c in cases),
                              exact_target_steps=sum(rate['exact_1800_or_2100']
                                  for c in cases for rate in c['fast_clock_phase_rates'].values())),
                  limitations=[
                      'The controller frame lanes are ROM-executed, but their route to PC12C is untraced.',
                      'The q3 mapping, D127=81 entry, ROM bank, held I0 and clock divisors are hypotheses.',
                      'Folded phase rate is a modular arithmetic diagnostic, not a DAC sample or analog tone.',
                      'A transformed, changing or differently clocked controller input is not excluded.'])
    save(out, report)
    return report


if __name__ == '__main__':
    print(run()['totals'])
