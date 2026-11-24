"""Execute the real controller output path across all state bytes under one fixture."""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE.parent.parent
sys.path.insert(0,str(ANALYSIS))
from interface_study import CORE, ROM, SHA
from controller_output import output_build

FIXTURE = dict(previous=[0,0,0,0],flags=[0]*6,payload=[0]*6,
               counters=[0,0,0],patterns=[255,255],prior_mode=0x6e)
INITIAL_P1=0xf8
INITIAL_SP=113
STOP=0x2000
CYCLE_LIMIT=4000


def command_line(state):
    f=FIXTURE
    payload=bytes([state,*f['previous'],*f['payload'],*f['counters'],*f['patterns'],f['prior_mode']]).hex()
    return f"send {payload} {bytes(f['flags']).hex()} 8 4\n"


def run():
    if hashlib.sha256(ROM.read_bytes()).hexdigest()!=SHA:
        raise ValueError('controller ROM mismatch')
    source=[ANALYSIS/'interface_probe.c',*(CORE/n for n in ('core.c','opcodes.c','disasm.c'))]
    with tempfile.TemporaryDirectory() as tmp:
        exe=Path(tmp)/'probe'
        subprocess.run(['cc','-O2','-Wall','-DSAT_TRACE','-I',str(CORE),
                        *map(str,source),'-o',str(exe)],check=True)
        input_lines=''.join(command_line(state) for state in range(256))
        proc=subprocess.run([str(exe),str(ROM),str(INITIAL_P1),'0',str(CYCLE_LIMIT),
            str(STOP),str(INITIAL_SP)],input=input_lines,text=True,capture_output=True,check=True)
    results=[json.loads(line) for line in proc.stdout.splitlines()]
    if len(results)!=256:raise ValueError('controller did not return 256 results')
    rows=[]
    for state,result in enumerate(results):
        f=FIXTURE
        expected=output_build(ROM.read_bytes(),state,f['previous'],f['flags'],
            f['payload'],f['counters'],f['patterns'],INITIAL_P1)
        events=result['events']
        wire=[e['value'] for e in events if e['kind']=='tx']
        complete=[e for e in events if e['kind']=='tx_complete']
        latch=[e for e in events if e['kind']=='p1' and e['value']&4]
        if not (result['errors']==0 and result['reached_stop'] and result['pc']==0x1ee8
                and result['sp']==INITIAL_SP and len(wire)==4 and len(complete)==4
                and len(latch)==1 and latch[0]['cycle']>complete[-1]['cycle']):
            raise ValueError(('invalid controller execution',state,result))
        if wire != [v^mask for v,mask in zip(expected['values'],(0,3,0,0xf8))]:
            raise ValueError(('reference mismatch',state,wire,expected))
        rows.append(dict(state=f'{state:02X}',wire=' '.join(f'{v:02X}' for v in wire),
                         code=f'{expected["code"]:02X}',source=('zero' if state<0x80 else
                           'rom-00b5' if state<0xa0 else 'rom-0095' if state<0xc0 else 'constant-5c'),
                         latch_tick=latch[0]['cycle']))
    groups=defaultdict(list)
    for row in rows:groups[row['wire']].append(row['state'])
    return dict(status='actual 8031 ROM output execution under fixed diagnostic state',
        controller_rom_sha256=SHA,fixture=FIXTURE,rows=rows,
        distinct_frames=len(groups),collisions={wire:states for wire,states in groups.items() if len(states)>1},
        sources={kind:sum(r['source']==kind for r in rows) for kind in sorted({r['source'] for r in rows})},
        interpretation='State alone does not encode all frame semantics: the bytes also depend on flags, payload, counters and prior output. This fixed fixture isolates state sensitivity.',
        limitations=['No operating-sequence state names assigned.',
            'The output serial chain destination is not physically traced.',
            'The fixture does not represent a real call, data, tone or training state.'],
        source_sha256={str(p.relative_to(ANALYSIS.parents[2])):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [Path(__file__),ANALYSIS/'interface_probe.c',ANALYSIS/'controller_output.py',
                *(CORE/n for n in ('core.c','opcodes.c','disasm.c','emu8051.h'))]})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/controller-frames.json')
    args=parser.parse_args()
    report=run();args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('states',len(report['rows']),'distinct frames',report['distinct_frames'],
          'colliding groups',len(report['collisions']))


if __name__=='__main__':main()
