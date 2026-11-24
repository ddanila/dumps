"""Compose actual 8031 receive, A2 state and output routines for every byte."""
import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from state_transitions import HERE, ROOT, ROM, CORE, ROM_SHA


def run():
    assert hashlib.sha256(ROM.read_bytes()).hexdigest()==ROM_SHA
    sources=[HERE/'receive_state_probe.c',HERE.parents[1]/'interface_probe.c',
             *(CORE/n for n in ('core.c','opcodes.c','disasm.c','emu8051.h'))]
    with tempfile.TemporaryDirectory() as tmp:
        exe=Path(tmp)/'probe'
        subprocess.run(['cc','-O2','-Wall','-Wno-unused-function','-DSAT_TRACE',
            '-I',str(CORE),str(HERE/'receive_state_probe.c'),
            *(str(CORE/n) for n in ('core.c','opcodes.c','disasm.c')),
            '-o',str(exe)],check=True)
        rows=[]
        for value in range(256):
            result=json.loads(subprocess.run([str(exe),str(ROM),str(value)],
                check=True,capture_output=True,text=True).stdout)
            expected=0xa3 if value&0x40 else 0xb8
            expected_wire=[0xc0 if value&1 else 0xd0,0x42,0x81,
                           0xba if value&0x40 else 0x22]
            assert result['received']==7 and result['stored_2e']==value
            assert result['state']==expected and result['output_stop'] and result['errors']==0
            assert result['writes']==result['completed']==4 and result['wire']==expected_wire
            rows.append(dict(received_fifth_payload=f'{value:02X}',next_state=f'{expected:02X}',
                             wire=' '.join(f'{b:02X}' for b in result['wire']),
                             receive_count=result['received'],state_cycles=result['state_cycles']))
    return dict(status='256 composed controller ROM receive/state/output executions pass',
        controller_rom_sha256=ROM_SHA,rows=rows,
        preconditions='Synthetic USART receive and transmit completions at 8 core ticks; discarded lead byte A5; other payload bytes zero; after 0800 returns, A2 is selected with qualification set and expired timer; after the state step, the output routine begins at 1EE2; no interrupts.',
        interpretation='The fifth received payload byte is stored at RAM2E. Bit 6 selects A3 or B8 on A2 expiry and changes the fourth output byte BA/22. Bit 0 changes the first output byte C0/D0. The other six bits do not affect state or wire frame under this fixture.',
        limitations=['The physical source and meaning of the received frame remain unknown.',
                     'The handoffs between the three local routines are harness-directed, not a continuous controller call.',
                     'No DSC2847 microcode or line output is executed in this probe.'],
        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/receive-state.json')
    args=parser.parse_args()
    report=run();args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(report['status'])


if __name__=='__main__': main()
