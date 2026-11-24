"""Compose actual 8031 receive and A2 state routines for every payload byte."""
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
            assert result['received']==7 and result['stored_2e']==value
            assert result['state']==expected and result['reached_stop'] and result['errors']==0
            rows.append(dict(received_fifth_payload=f'{value:02X}',next_state=f'{expected:02X}',
                             receive_count=result['received'],state_cycles=result['state_cycles']))
    return dict(status='256 composed controller ROM executions pass',
        controller_rom_sha256=ROM_SHA,rows=rows,
        preconditions='Synthetic USART receive completions at 8 core ticks; discarded lead byte A5; all other payload bytes zero; after 0800 returns, A2 is selected with qualification set and expired timer; no interrupts.',
        interpretation='The fifth received payload byte is stored at RAM2E. Its bit 6 selects A3 on A2 expiry, or B8 when clear.',
        limitations=['The physical source and meaning of the received frame remain unknown.',
                     'The handoff to the state routine is a local harness step, not a continuous controller call.',
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
