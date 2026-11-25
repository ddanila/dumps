"""Model a four-CD4094 cascade and test its possible D127 byte lanes."""

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]
from common import save
from controller_bit_dispatch import CONTROLLER_ROM, CONTROLLER_SHA
from photo_127_liveness import ROM, run_case
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

MAIN_REPORT = HERE / 'results/main-loop-serial.json'
STATE_REPORT = HERE / 'results/controller-frames.json'
SELECTORS = ('00', '20', '40', '60')
STATES = ('A0', 'A1', 'A2')


def reverse_bits(value):
    return sum(((value >> bit) & 1) << (7 - bit) for bit in range(8))


def shift_four_bytes(frame):
    if len(frame) != 4:
        raise ValueError('expected four-byte controller frame')
    stages = [0] * 32
    for value in frame:
        for bit in range(8):
            stages = [(value >> bit) & 1] + stages[:-1]
    by_chip = []
    for chip in range(4):
        q = stages[8 * chip:8 * (chip + 1)]
        by_chip.append(dict(q1_to_d0=sum(bit << i for i, bit in enumerate(q)),
                            q8_to_d0=sum(bit << (7 - i) for i, bit in enumerate(q))))
    if ([row['q1_to_d0'] for row in by_chip] !=
            [reverse_bits(value) for value in frame[::-1]] or
            [row['q8_to_d0'] for row in by_chip] != list(frame[::-1])):
        raise ValueError('32-stage shift order changed')
    return by_chip


def frames_from_reports():
    main = json.loads(MAIN_REPORT.read_text())
    state = json.loads(STATE_REPORT.read_text())
    digest = hashlib.sha256(CONTROLLER_ROM.read_bytes()).hexdigest()
    if (digest != CONTROLLER_SHA or
            main['controller_rom_sha256'] != digest or
            state['controller_rom_sha256'] != digest):
        raise ValueError('controller reports use a different ROM')
    rows = {row['selector']: row for row in main['rows']
            if row['selector'] in SELECTORS}
    if set(rows) != set(SELECTORS):
        raise ValueError('missing main-loop selector classes')
    frames = {}
    for selector, row in rows.items():
        frames[f'main_{selector}'] = bytes.fromhex(
            row['frames'][row['first_line_iteration'] - 1])
    state_rows = {row['state']: row for row in state['rows']
                  if row['state'] in STATES}
    if set(state_rows) != set(STATES):
        raise ValueError('missing A-state controller frames')
    for name, row in state_rows.items():
        frames[f'state_{name}'] = bytes.fromhex(row['wire'])
    return frames


def run(out=HERE / 'results/photo-cd4094-order.json'):
    frames = frames_from_reports()
    candidates = {name: shift_four_bytes(frame) for name, frame in frames.items()}
    values = sorted({row[orientation] for chips in candidates.values()
                     for row in chips for orientation in ('q1_to_d0', 'q8_to_d0')})
    _, base = fixture()
    mapping = mapped(MAPPINGS['q3'])
    rom = ROM.read_bytes()
    executions = {}
    for value in values:
        _, result, trace = run_case(mapping, base, value, 256)
        reads = [row for row in trace if row['pc'] == 0x129]
        if not result['clean'] or not reads:
            raise ValueError('CD4094-derived byte did not execute')
        for n, row in enumerate(reads, 1):
            phase = (3 + n * value) & 255
            event = row['external_read']
            if (event['address'] != 256 + phase or
                    event['value'] != rom[256 + phase] or
                    not event['selected_by_alu']):
                raise ValueError('CD4094-derived D127 phase recurrence changed')
        second_reads = sum(row['pc'] == 0x12E for row in trace)
        if (value & 1 and not second_reads) or (not value & 1 and second_reads):
            raise ValueError('CD4094-derived parity path changed')
        executions[f'{value:02X}'] = dict(parity='odd' if value & 1 else 'even',
                                         pc129_reads=len(reads),
                                         pc12e_reads=second_reads,
                                         trace_digest=result['trace_digest'])
    groups = []
    for name, frame in frames.items():
        groups.append(dict(frame=name, sbuf_bytes=frame.hex(' ').upper(),
                           chips_from_serial_input=[
                               {key: f'{value:02X}' for key, value in chip.items()}
                               for chip in candidates[name]]))
    report = dict(fixture=dict(controller_serial_mode='mode 0, LSB first',
                               candidate_hardware='four cascaded CD4094BE, 32 stages, one strobe after fourth byte',
                               chip_order='logical chip 0 nearest serial input; actual board order untraced',
                               q1_to_d0='Q1 is bit 0 of candidate DSP D byte',
                               q8_to_d0='Q8 is bit 0 of candidate DSP D byte',
                               mapping='q3 photo-swapped', d127_route='one held CD4094 output byte'),
                  frames=groups, executions=executions,
                  totals=dict(frames=len(groups), distinct_d127_bytes=len(values)),
                  limitations=[
                      'Four CD4094 packages are photographed, but cascade wiring, serial clock, strobe route and DSP input pins are untraced.',
                      'The two Q-pin orientations are candidate bus orders; arbitrary cross-chip wiring and inversion are not covered.',
                      'The controller frames are executed ROM outputs, but the q3 D127 route and DAC path are hypotheses.'])
    save(out, report)
    return report


if __name__ == '__main__':
    print(run()['totals'])
