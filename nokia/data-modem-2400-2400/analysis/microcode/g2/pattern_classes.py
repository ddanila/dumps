"""Classify all 256 octets in controller ROM routine 1C07 for states 83/A6."""
import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from state_transitions import HERE, ROOT, ROM, CORE, ROM_SHA


def run():
    if hashlib.sha256(ROM.read_bytes()).hexdigest()!=ROM_SHA:
        raise ValueError('controller ROM hash mismatch')
    sources=[Path(__file__),HERE/'pattern_probe.c',HERE.parents[1]/'interface_probe.c',
             *(CORE/n for n in ('core.c','opcodes.c','disasm.c','emu8051.h'))]
    groups={}
    with tempfile.TemporaryDirectory() as tmp:
        exe=Path(tmp)/'probe'
        subprocess.run(['cc','-O2','-Wall','-Wno-unused-function','-DSAT_TRACE',
                        '-I',str(CORE),str(HERE/'pattern_probe.c'),
                        *(str(CORE/n) for n in ('core.c','opcodes.c','disasm.c')),
                        '-o',str(exe)],check=True)
        for state in (0x83,0xa6):
            classes={}
            for value in range(256):
                row=json.loads(subprocess.run([str(exe),str(ROM),str(state),str(value)],
                              text=True,capture_output=True,check=True).stdout)
                assert row['returned'] and row['errors']==0 and row['octet']==value
                assert row['pending21']&0x10==0
                key=f'{row["flags24"]&0x0c:02X}'
                classes.setdefault(key,[]).append(f'{value:02X}')
            groups[f'{state:02X}']=classes
    assert {k:len(v) for k,v in groups['83'].items()}=={'00':216,'04':8,'08':24,'0C':8}
    assert {k:len(v) for k,v in groups['A6'].items()}=={'00':240,'04':8,'08':8}
    return dict(status='real 8031 ROM routine 1C07 executes for all 256 octets in each state',
        controller_rom_sha256=ROM_SHA,groups=groups,
        preconditions='Local routine entry 1C07, RAM3A=octet, RAM34=83 or A6, RAM21.4 set, other RAM zero, synthetic RET sentinel; no prior-octet history or surrounding calls.',
        interpretation='The 01h.4 pending-octet bit is consumed; output RAM24 bits 2/3 classify 40 octets in state 83 and 16 in state A6, with the remaining bytes unmarked. These are detector classes, not established V.26 ter legal-octet sets.',
        limitations=['The 08E9 dispatcher statically routes states 83 and A6 to 0A38, which calls 1C07 after other routines; this probe enters 1C07 directly.',
                     'RAM66 previous byte and RAM63 counter start at zero; repeated-octet behavior is not characterized.',
                     'No DSC2847 microcode or physical signal is executed.'],
        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in sources})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/pattern-classes.json')
    args=parser.parse_args()
    report=run();args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(report['status'],{s:{k:len(v) for k,v in classes.items()}
                             for s,classes in report['groups'].items()})


if __name__=='__main__':main()
