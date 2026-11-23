"""Check the 0620 boolean reference against unchanged 8031 instructions."""
import argparse
import hashlib
import json
import random
import subprocess
from collections import Counter
from pathlib import Path
from interface_study import HERE, ROOT, CORE, ROM, SHA
from controller_decode import decode_inputs


def fixtures(config):
    cases=[]
    def add(name,payload,state=None,byte_6e=0):
        cases.append(dict(name=name,payload=payload,state=config['base_state'][:] if state is None else state,byte_6e=byte_6e))
    for position in range(6):
        for value in range(256):
            payload=config['base_payload'][:];payload[position]=value
            add(f'byte-{position}-{value}',payload)
    # Exhaust every assignment of the seven-bit override predicate.
    locations=[(2,7),(2,6),(3,0),(1,1),(1,0),(1,3),(1,2)]
    for value in range(128):
        payload=[0,0,0,0,255,255]
        for index,(byte,bit) in enumerate(locations):payload[byte]|=((value>>index)&1)<<bit
        add(f'override-{value}',payload)
    for value in range(32):
        payload=[0,((value>>2)&1)<<4,((value>>3)&1)<<7,0,0,(value&3)<<5]
        state=[0]*6;state[0]=((value>>4)&1)<<3
        add(f'mode-{value}',payload,state)
    locations=[(2,1),(2,2),(2,3),(2,4),(1,1),(1,2),(1,3),(3,0)]
    for value in range(256):
        payload=[0]*6
        for index,(byte,bit) in enumerate(locations):payload[byte]|=((value>>index)&1)<<bit
        add(f'priority-{value}',payload,[0]*6)
    rng=random.Random(config['seed'])
    for index in range(config['random_cases']):
        add(f'random-{index}',[rng.randrange(256) for _ in range(6)],
            [rng.randrange(256) for _ in range(6)],rng.choice([0,1,254,255,rng.randrange(256)]))
    return cases


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/controller-decode-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=json.loads((HERE/'controller-decode-scenario.json').read_text())
    if hashlib.sha256(ROM.read_bytes()).hexdigest()!=SHA:raise ValueError('controller ROM hash mismatch')
    exe=args.out/'interface-probe';sources=[HERE/'interface_probe.c']+[CORE/n for n in ('core.c','opcodes.c','disasm.c')]
    subprocess.run(['cc','-O2','-Wall','-DSAT_TRACE','-I',str(CORE),*[str(p) for p in sources],'-o',str(exe)],check=True)
    cases=fixtures(config)
    payload=''.join(f"decode {bytes(c['payload']+[c['byte_6e']]).hex()} {bytes(c['state']).hex()} 8 0\n" for c in cases)
    run=subprocess.run([str(exe),str(ROM),str(config['initial_p1']),'0',str(config['cycle_limit']),
                        str(config['return_sentinel']),str(config['initial_sp'])],input=payload,text=True,capture_output=True,check=True)
    results=[json.loads(line) for line in run.stdout.splitlines()]
    if len(results)!=len(cases):raise ValueError('probe omitted cases')
    counts=Counter();saved=[];seen=set();visited=set()
    for case,result in zip(cases,results):
        visited.update(result['visited'])
        expected=decode_inputs(case['payload'],case['state'],case['byte_6e']);ram=expected['ram'][:]
        ram[config['initial_sp']-1]=config['return_sentinel']&255
        ram[config['initial_sp']]=config['return_sentinel']>>8
        if (not result['returned'] or result['errors'] or result['sp']!=config['initial_sp']-2 or result['iram']!=ram):
            differences=[(i,a,b) for i,(a,b) in enumerate(zip(result['iram'],ram)) if a!=b]
            raise ValueError((case,differences,result))
        key=(expected['override'],expected['priority'],expected['action'])
        counts[str(key)]+=1
        if key not in seen:seen.add(key);saved.append(dict(fixture=case,result=result,reference=expected))
    listing=HERE/'results/controller-linear.asm'
    expected_pcs={int(line.split()[0],16) for line in listing.read_text().splitlines() if 0x620<=int(line.split()[0],16)<=0x77b}
    if visited!=expected_pcs:raise ValueError(('instruction coverage differs',sorted(expected_pcs-visited),sorted(visited-expected_pcs)))
    report=dict(instruction_coverage=sorted(visited),configuration=config,rom_sha256=SHA,cases=len(cases),all_checks_pass=True,
        fixture_sha256=hashlib.sha256(payload.encode()).hexdigest(),execution_sha256=hashlib.sha256(run.stdout.encode()).hexdigest(),
        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+
                      [CORE/'emu8051.h',Path(__file__),HERE/'controller_decode.py',HERE/'controller-decode-scenario.json',listing]},
        semantic_cases=dict(counts),witnesses=saved,
        interpretation='Controller normalized-input decoding only; physical switch/status identities and DSP connection unknown.')
    (args.out/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');exe.unlink()
    print(len(cases),'ROM/reference comparisons pass;',len(saved),'semantic witnesses')


if __name__=='__main__':main()
