"""Find held frame and pin changes at the controller A3-to-A4 boundary."""

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from main_loop_timer1_segment2 import CORE, ROM, ROOT, compile_probe, generated_source


def inspect(rows, selector):
    held = None
    last_p1 = None
    transitions = []
    snapshots = []
    for index, row in enumerate(rows):
        old = held
        if row['tx']:
            if len(row['tx']) != 4:
                raise ValueError(('short frame', selector, index))
            held = tuple(row['tx'])
        if old is not None and held != old:
            transitions.append(dict(iteration=index, state=f"{row['state']:02X}",
                                    old=list(old), new=list(held),
                                    p1_before=last_p1, p1_after=row['p1']))
        if row['state'] in (0xA3, 0xA4):
            snapshots.append(dict(iteration=index, state=f"{row['state']:02X}",
                                  frame=list(held), p1=row['p1'],
                                  port01_writes=sum(address == 1
                                                    for address in row['write_addresses'])))
        last_p1 = row['p1']
    a3 = [row for row in snapshots if row['state'] == 'A3']
    a4 = [row for row in snapshots if row['state'] == 'A4']
    if (len(a3) < 23 or len(a4) != 8 or
            any(row['port01_writes'] for row in a3) or
            any(row['port01_writes'] != 1 for row in a4)):
        raise ValueError(('A3/A4 iteration or USART-write fixture changed', selector))
    separating_frame_bits = []
    for byte in range(4):
        for bit in range(8):
            left = {(row['frame'][byte] >> bit) & 1 for row in a3}
            right = {(row['frame'][byte] >> bit) & 1 for row in a4}
            if len(left) == len(right) == 1 and left != right:
                separating_frame_bits.append((byte, bit))
    separating_p1_bits = []
    for bit in range(8):
        left = {(row['p1'] >> bit) & 1 for row in a3}
        right = {(row['p1'] >> bit) & 1 for row in a4}
        if len(left) == len(right) == 1 and left != right:
            separating_p1_bits.append(bit)
    boundary = next(row for row in transitions if row['state'] == 'A4')
    exact_edge = [row for row in transitions
                  if row['old'][2] == 0x81 and row['new'][2] == 0xA1]
    bit5_rises = [row for row in transitions
                  if not (row['old'][2] & 0x20) and row['new'][2] & 0x20]
    if (boundary['old'] != [0xD0, 0x42, 0x81, 0xBA] or
            boundary['new'] != [0xD0, 0x42, 0xA1, 0xBA] or
            boundary['p1_before'] != boundary['p1_after'] or
            len(exact_edge) != 1 or exact_edge[0]['iteration'] != boundary['iteration'] or
            separating_frame_bits or separating_p1_bits):
        raise ValueError(('A3/A4 mode boundary classification changed', selector))
    return dict(selector=f'{selector:02X}',
                a3_iterations=len(a3), a4_iterations=len(a4),
                a3_held_frames=sorted({' '.join(f'{byte:02X}' for byte in row['frame'])
                                       for row in a3}),
                a4_held_frames=sorted({' '.join(f'{byte:02X}' for byte in row['frame'])
                                       for row in a4}),
                a3_p1_values=sorted({f"{row['p1']:02X}" for row in a3}),
                a4_p1_values=sorted({f"{row['p1']:02X}" for row in a4}),
                separating_held_frame_bits=separating_frame_bits,
                separating_p1_bits=separating_p1_bits,
                boundary=dict(iteration=boundary['iteration'],
                              old_frame=' '.join(f'{value:02X}' for value in boundary['old']),
                              new_frame=' '.join(f'{value:02X}' for value in boundary['new']),
                              changed_third_byte_bits=[bit for bit in range(8)
                                                       if ((boundary['old'][2] ^
                                                            boundary['new'][2]) >> bit) & 1],
                              p1_before=f"{boundary['p1_before']:02X}",
                              p1_after=f"{boundary['p1_after']:02X}"),
                exact_81_to_a1_edges=len(exact_edge),
                third_byte_bit5_rises=[dict(iteration=row['iteration'],
                                            state=row['state'],
                                            old=f"{row['old'][2]:02X}",
                                            new=f"{row['new'][2]:02X}")
                                       for row in bit5_rises])


def run(out=HERE / 'results/controller-a3-a4-mode-edge.json'):
    source, _ = generated_source()
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        exe = compile_probe(source, Path(temporary), True)
        for selector in (0x40, 0x60):
            execution = json.loads(subprocess.run(
                [str(exe), str(ROM), str(selector), '10000', '1'],
                capture_output=True, text=True, check=True).stdout)
            if execution['errors'] or execution['completed'] != len(execution['iterations']):
                raise ValueError(('controller execution failed', selector))
            cases.append(inspect(execution['iterations'], selector))
    paths = [Path(__file__), HERE / 'main_loop_timer1_segment2.py',
             HERE / 'main_loop_probe.c', ROM,
             *(CORE / name for name in ('core.c', 'opcodes.c', 'disasm.c', 'emu8051.h'))]
    report = dict(status='executed A3-to-A4 controller boundary has a unique held-frame byte edge but no separating static frame/P1 bit',
                  fixture=dict(controller='unchanged 8031 ROM under interrupt-paced Timer1 harness',
                               selectors=['40', '60'],
                               ram15='held positive at PC1000 to preserve A3/A4 path; source untraced',
                               external_receive_and_status='synthetic harness events',
                               held_frame='last completed four-byte CD4094 send persists across no-send iterations'),
                  cases=cases,
                  limitations=[
                      'A3-to-A4 is a symbol-training-to-data boundary in this fixture, not proven echo train/freeze timing.',
                      'The exact 81-to-A1 byte edge needs a decoder and physical route before it can be called a DSC mode input.',
                      'The third-byte bit-5 rise also occurs earlier; its level or rise alone does not uniquely label A4.',
                      'The controller harness fixes RAM15 and synthetic receive/status events, so this is conditional execution.'],
                  source_sha256={str(path.relative_to(ROOT)):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    print([(row['selector'], row['boundary'],
            row['separating_held_frame_bits'], row['third_byte_bit5_rises'])
           for row in result['cases']])
