"""Run the 8031 state step for every RAM34 byte under fixed reload/expiry inputs."""
import argparse
import hashlib
import json
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path
from state_transitions import HERE, ROOT, ROM, CORE, ROM_SHA


def build():
    if hashlib.sha256(ROM.read_bytes()).hexdigest()!=ROM_SHA:
        raise ValueError('controller ROM hash mismatch')
    sources=[Path(__file__),HERE/'state_probe.c',HERE.parent.parent/'interface_probe.c',
             *(CORE/n for n in ('core.c','opcodes.c','disasm.c','emu8051.h'))]
    with tempfile.TemporaryDirectory() as tmp:
        exe=Path(tmp)/'probe'
        subprocess.run(['cc','-O2','-Wall','-Wno-unused-function','-DSAT_TRACE','-I',str(CORE),
            str(HERE/'state_probe.c'),*(str(CORE/n) for n in ('core.c','opcodes.c','disasm.c')),
            '-o',str(exe)],check=True)
        rows=[]
        for state in range(256):
            row=dict(state=f'{state:02X}')
            for key,flag24,timer17 in [('reload',32,0),('expiry',0,128)]:
                proc=subprocess.run([str(exe),str(ROM),str(state),str(flag24),'0',
                    str(timer17),'0','16'],text=True,capture_output=True,check=True)
                result=json.loads(proc.stdout)
                assert result['errors']==0 and result['reached_stop'] and result['pc']==0x1755
                assert 0x1000 in result['visited']
                row[key]=dict(next_state=f'{result["state"]:02X}',
                    countdown=result['timer16']+256*result['timer17'],
                    cycles=result['cycles'],visited=[f'{pc:04X}' for pc in result['visited']])
            rows.append(row)
    load_groups=defaultdict(list)
    for r in rows:
        if r['reload']['countdown']:
            load_groups[str(r['reload']['countdown'])].append(r['state'])
    notable=[r for r in rows if 0x80<=int(r['state'],16)<0xc0
             and (r['reload']['countdown'] or r['expiry']['next_state']!=r['state'])]
    return dict(status='local real-ROM state sensitivity under RAM22.4 qualification',
        controller_rom_sha256=ROM_SHA,
        fixtures=dict(reload=dict(ram24='20',timer17='00'),expiry=dict(ram24='00',timer17='80'),
            ram22='10',ram15='00',interrupts='disabled',other_ram='zero',entry='1000',stop='1755'),
        rows=rows,notable_80_bf=[r['state'] for r in notable],
        countdown_to_states=dict(sorted(load_groups.items(),key=lambda x:int(x[0]))),
        interpretation='Enumerates what one controller state step does for each byte; does not establish reachable operating states or physical timer duration.',
        limitations=['The two fixtures impose reload or underflow at entry rather than simulating the timer interrupt.',
            'State transitions also depend on other RAM/flag inputs, held zero here.',
            'No DSP command recipient or V.26 ter stage name is inferred.'],
        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/state-matrix.json')
    args=parser.parse_args()
    report=build();args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('states',len(report['rows']),'countdowns',list(report['countdown_to_states']),
          'notable 80-BF',len(report['notable_80_bf']))

if __name__=='__main__':main()
