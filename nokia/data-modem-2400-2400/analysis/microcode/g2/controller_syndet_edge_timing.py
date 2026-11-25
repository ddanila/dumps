"""Compare controller frame writes with the first A4 line-data write."""

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from main_loop_timer1_segment2 import CORE, HERE, ROM, ROOT, compile_probe, generated_source


EDGE = HERE / 'results/controller-a3-a4-mode-edge.json'


def instrument(source):
    changes = [
        ('if(address==0x99) {',
         'if(address==0x99) {\n'
         '        if(c->mLowerData[0x34]==0xA4) '
         'fprintf(stderr,"F %u %04X %02X\\n",cycle,pc,c->mSFR[REG_SBUF]);'),
        ('if(address==1 || address==2 || address==5 || address==6) {',
         'if(address==1 || address==2 || address==5 || address==6) {\n'
         '        if(address==1 && c->mLowerData[0x34]==0xA4) '
         'fprintf(stderr,"D %u %04X %02X\\n",cycle,pc,value);'),
    ]
    for old, new in changes:
        if source.count(old) != 1:
            raise ValueError(('probe callback changed', old, source.count(old)))
        source = source.replace(old, new)
    return source


def parse_events(output):
    events = []
    for line in output.splitlines():
        kind, cycle, pc, value = line.split()
        if kind not in ('F', 'D'):
            raise ValueError(('unexpected probe output', line))
        events.append(dict(kind=kind, cycle=int(cycle), pc=pc, value=int(value, 16)))
    return events


def run(out=HERE / 'results/controller-syndet-edge-timing.json'):
    edge = json.loads(EDGE.read_text())
    if [row['exact_81_to_a1_edges'] for row in edge['cases']] != [1, 1]:
        raise ValueError('saved A3/A4 frame edge changed')
    source, _ = generated_source()
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        exe = compile_probe(instrument(source), Path(temporary), True)
        for selector in (0x40, 0x60):
            result = subprocess.run([str(exe), str(ROM), str(selector), '10000', '1'],
                                    capture_output=True, text=True, check=True)
            execution = json.loads(result.stdout)
            if execution['errors']:
                raise ValueError(('controller errors', selector))
            events = parse_events(result.stderr)
            first_data = next(event for event in events if event['kind'] == 'D')
            before = [event for event in events if event['kind'] == 'F' and
                      event['cycle'] < first_data['cycle']]
            frame = before[-4:]
            if ([event['value'] for event in frame] != [0xD0, 0x42, 0xA1, 0xBA] or
                    any(frame[i]['cycle'] >= frame[i + 1]['cycle'] for i in range(3)) or
                    first_data['pc'] != '1DA8'):
                raise ValueError(('A4 frame/data order changed', selector, frame, first_data))
            cases.append(dict(selector=f'{selector:02X}',
                              frame_sbuf_writes=frame,
                              first_a4_port01_data_write=first_data,
                              ticks_last_sbuf_write_before_data=(first_data['cycle'] -
                                                                  frame[-1]['cycle']),
                              ticks_third_frame_byte_before_data=(first_data['cycle'] -
                                                                    frame[2]['cycle'])))
    paths = [Path(__file__), HERE / 'main_loop_timer1_segment2.py',
             HERE / 'main_loop_probe.c', EDGE, ROM,
             *(CORE / name for name in ('core.c', 'opcodes.c', 'disasm.c', 'emu8051.h'))]
    report = dict(
        status='The 8031 writes the first A4 CD4094 frame before its first port-01 data byte in both selectors.',
        fixture=dict(controller='unchanged 8031 ROM under Timer1 harness',
                     ram15='held positive at each PC1000 dispatch; external gate untraced',
                     uart_tx_completion='synthetically asserted eight emulator ticks after each SBUF write',
                     receive_and_status='synthetic harness events',
                     observation='instruction-level SBUF writes and MOVX port-01 data writes'),
        cases=cases,
        inference='An external decoder could use the exact 81-to-A1 frame transition as an A4 event before the controller writes its first line byte. This is a candidate SYNDET source, not an observed connection or correctly timed receive pulse.',
        limitations=[
            'SBUF write order does not measure CD4094 shift, latch, propagation, or remote receiver timing.',
            'The harness imposes eight-tick serial completion and does not co-simulate the physical USART clocks.',
            'The first port-01 write is local transmit data; it does not locate the first arriving remote receive bit.',
            'The 81-to-A1 edge is only unique with frame history; an unqualified bit-5 rise occurs earlier.',
            'RxD, RxC and SYNDET routes remain assumed, so this result does not pass C3.'],
        source_sha256={str(path.relative_to(ROOT)):
                       hashlib.sha256(path.read_bytes()).hexdigest() for path in paths})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    return report


if __name__ == '__main__':
    for case in run()['cases']:
        print(case['selector'], case['ticks_last_sbuf_write_before_data'],
              case['ticks_third_frame_byte_before_data'])
