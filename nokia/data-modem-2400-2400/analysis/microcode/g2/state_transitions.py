"""Execute the 8031 A0/A1/A2 state-step paths with explicit timer fixtures."""
import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
ROM=HERE.parents[2]/'controller-810244e/nokia-modem-other-board-2764.bin'
CORE=ROOT/'unknown/satellite-mac304-m27c2001/analysis/emulation/emu8051'
ROM_SHA='daf854c513cd427664bb345f511afc2d38441e5002e4a85389d289aedbfc0038'
STATES=(0xa0,0xa1,0xa2)
FIXTURES=(('waiting',0,0),('reload on change',0x20,0),('expired',0,0x80))
EXPECTED={
    0xa0:dict(next=0xa1,load=0x070d),
    0xa1:dict(next=0xa2,load=0x0a2d),
    0xa2:dict(next=0xb8,load=0x003c),
}


def run():
    if hashlib.sha256(ROM.read_bytes()).hexdigest()!=ROM_SHA:raise ValueError('controller ROM hash mismatch')
    sources=[Path(__file__),HERE/'state_probe.c',HERE.parents[1]/'interface_probe.c',
             *(CORE/n for n in ('core.c','opcodes.c','disasm.c','emu8051.h'))]
    with tempfile.TemporaryDirectory() as tmp:
        exe=Path(tmp)/'state-probe'
        subprocess.run(['cc','-O2','-Wall','-Wno-unused-function','-DSAT_TRACE','-I',str(CORE),
            str(HERE/'state_probe.c'),*(str(CORE/n) for n in ('core.c','opcodes.c','disasm.c')),
            '-o',str(exe)],check=True)
        cases=[]
        for state in STATES:
            for name,flag24,timer17 in FIXTURES:
                cmd=[str(exe),str(ROM),str(state),str(flag24),'0',str(timer17),'0','16']
                result=json.loads(subprocess.run(cmd,text=True,capture_output=True,check=True).stdout)
                assert result['reached_stop'] and result['errors']==0 and result['pc']==0x1755
                assert 0x1000 in result['visited'] and 0x1755 not in result['visited']
                actual_timer=result['timer16']+256*result['timer17']
                if name=='waiting':
                    assert result['state']==state and actual_timer==0
                elif name=='reload on change':
                    assert result['state']==state and actual_timer==EXPECTED[state]['load']
                else:
                    assert result['state']==EXPECTED[state]['next'] and actual_timer==0x8000
                cases.append(dict(entry=f'{state:02X}',condition=name,ram24=f'{flag24:02X}',
                    input_timer17=f'{timer17:02X}',next_state=f'{result["state"]:02X}',
                    timer=f'{actual_timer:04X}',cycles=result['cycles'],
                    visited=[f'{pc:04X}' for pc in result['visited']]))
            cmd=[str(exe),str(ROM),str(state),'32','0','0','0','0']
            control=json.loads(subprocess.run(cmd,text=True,capture_output=True,check=True).stdout)
            assert control['reached_stop'] and control['errors']==0
            assert control['state']==0 and control['timer16']==control['timer17']==0
            cases.append(dict(entry=f'{state:02X}',condition='qualification absent',ram24='20',
                input_timer17='00',next_state='00',timer='0000',cycles=control['cycles'],
                visited=[f'{pc:04X}' for pc in control['visited']]))
    return dict(status='local controller ROM state-step execution; no modem stage names inferred',
        controller_rom_sha256=ROM_SHA,entry_pc='1000',stop_pc='1755',
        preconditions='RAM22.4=1 except negative controls; RAM15=0; interrupts disabled; remaining RAM zero',
        cases=cases,interpretation='RAM24.5 (changed-input flag) reloads the state-specific countdown; when clear, RAM17 high bit selects the expiry transition.',
        limitations=['The event/timer source that sets RAM24.5 and RAM17 is not part of this local step.',
            'These state transitions have not yet been connected to a continuous controller call or DSP response.',
            'The timing values are firmware counts, not measured milliseconds or named V.26 ter stages.'],
        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/state-transitions.json')
    args=parser.parse_args();report=run();args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print([(r['entry'],r['condition'],r['next_state'],r['timer']) for r in report['cases']])

if __name__=='__main__':main()
