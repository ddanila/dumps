"""Compare bit-serial scrambling equations with controller ROM byte routines."""
import argparse
import hashlib
import json
import random
import subprocess
import tempfile
from pathlib import Path
from interface_study import HERE, ROOT, CORE, ROM, SHA
from controller_scrambler import transform


def fixtures(config):
    rng=random.Random(config['seed'])
    for inverse in (False,True):
        ready=8 if inverse else 2
        for delay in (5,18):
            for history in [0]+[1<<i for i in range(24)]:
                for value in range(256):
                    yield inverse,delay,history,value,ready,0xa5
            for flags in range(256):
                yield inverse,delay,rng.randrange(1<<24),rng.randrange(256),flags,rng.randrange(256)
            for _ in range(config['random_cases']):
                yield inverse,delay,rng.randrange(1<<24),rng.randrange(256),ready,rng.randrange(256)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/controller-scrambler-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=json.loads((HERE/'controller-scrambler-scenario.json').read_text())
    if hashlib.sha256(ROM.read_bytes()).hexdigest()!=SHA:raise ValueError('ROM mismatch')
    sources=[HERE/'interface_probe.c']+[CORE/n for n in ('core.c','opcodes.c','disasm.c')]
    exe=args.out/'interface-probe'
    subprocess.run(['cc','-O2','-Wall','-DSAT_TRACE','-I',str(CORE),*[str(p) for p in sources],'-o',str(exe)],check=True)
    fixture_hash=hashlib.sha256();execution_hash=hashlib.sha256();visited=set();witnesses=[];seen=set();count=0
    with tempfile.TemporaryFile(mode='w+t') as inputs:
        for inverse,delay,history,value,flags,previous in fixtures(config):
            flag24=(1<<(1 if inverse else 0)) if delay==5 else 0
            frame=[history>>16,(history>>8)&255,history&255,value,previous,flags]
            line=f"{'descram' if inverse else 'scram'} {bytes(frame).hex()} {bytes([0,0,flag24,0,0,0]).hex()} 8 0\n"
            inputs.write(line);fixture_hash.update(line.encode())
        inputs.seek(0)
        process=subprocess.Popen([str(exe),str(ROM),'248','0',str(config['cycle_limit']),str(config['return_sentinel']),str(config['initial_sp'])],stdin=inputs,stdout=subprocess.PIPE,text=True)
        try:
            for case in fixtures(config):
                inverse,delay,history,value,flags,previous=case
                line=process.stdout.readline()
                if not line:raise ValueError('missing output')
                execution_hash.update(line.encode());result=json.loads(line);visited.update(result['visited']);count+=1
                ready,busy=(8,16) if inverse else (2,4)
                active=bool(flags&ready and not flags&busy)
                h,out=transform(history,value,delay,inverse) if active else (history,previous)
                flag24=(1<<(1 if inverse else 0)) if delay==5 else 0
                ram=[0]*128;ram[0x24]=flag24;ram[0x21]=flags
                base=0x42 if inverse else 0x3f
                ram[base:base+3]=[h>>16,(h>>8)&255,h&255]
                ram[0x39 if inverse else 0x37]=value
                ram[0x3a if inverse else 0x38]=out
                if inverse:ram[0x3c]=ram[0x3e]=out
                if active:
                    ram[0x21]=(flags&~ready)|busy|(64 if inverse else 0)
                    ram[3]=history&255
                    if delay==5:
                        feedback=value if inverse else out
                        ram[2]=((history>>18)&31)|((feedback&7)<<5)
                    else:ram[2]=(history>>5)&255
                    if inverse:ram[0x20]=out
                ram[config['initial_sp']-1]=config['return_sentinel']&255
                ram[config['initial_sp']]=config['return_sentinel']>>8
                if result['errors'] or not result['returned'] or result['sp']!=config['initial_sp']-2 or result['iram']!=ram or result['events']:
                    raise ValueError((case,[(i,a,b) for i,(a,b) in enumerate(zip(result['iram'],ram)) if a!=b],result))
                key=(inverse,delay,active,bool(history&0x800000),bool(flags&busy))
                if key not in seen:seen.add(key);witnesses.append(dict(fixture=case,reference=dict(history=h,output=out,active=active),result=result))
            if process.stdout.readline() or process.wait()!=0:raise ValueError('unexpected completion')
        finally:
            if process.poll() is None:process.kill();process.wait()
            process.stdout.close()
    listing=HERE/'results/controller-linear.asm'
    pcs={int(l.split()[0],16) for l in listing.read_text().splitlines()}
    assert visited=={p for p in pcs if 0x53e<=p<=0x61f}
    rng=random.Random(config['seed']);roundtrips=0
    for delay in (5,18):
        enc=dec=rng.randrange(1<<23)
        for _ in range(config['roundtrip_bytes']):
            value=rng.randrange(256);enc,wire=transform(enc,value,delay);dec,recovered=transform(dec,wire,delay,True)
            assert recovered==value and enc==dec
            roundtrips+=1
    error_propagation={}
    for delay in (5,18):
        clean=damaged=0;differences=[]
        for index in range(8):
            clean,a=transform(clean,0,delay,True)
            damaged,b=transform(damaged,1 if index==0 else 0,delay,True)
            differences.extend(index*8+bit for bit in range(8) if (a^b)&(1<<bit))
        assert differences==[0,delay,23]
        error_propagation[str(delay)]=differences
        enc=0x654321;dec=0x123456
        for index in range(32):
            value=rng.randrange(256);enc,wire=transform(enc,value,delay);dec,recovered=transform(dec,wire,delay,True)
            if index>=3:assert recovered==value and enc==dec
    report=dict(configuration=config,rom_sha256=SHA,cases=count,all_checks_pass=True,reference_roundtrip_bytes=roundtrips,reference_single_bit_error_positions=error_propagation,
        instruction_coverage=sorted(visited),witnesses=witnesses,fixture_sha256=fixture_hash.hexdigest(),execution_sha256=execution_hash.hexdigest(),
        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[CORE/'emu8051.h',Path(__file__),HERE/'controller_scrambler.py',HERE/'controller-scrambler-scenario.json',listing]},
        interpretation='23-bit self-synchronizing scramble/descramble transforms with delays (5,23) or (18,23), LSB first. Encode shifts output into history; decode shifts input. Local entry bypasses the external status read preceding 053E; no modem-standard or DSP-link claim.')
    (args.out/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');exe.unlink()
    print(count,'ROM comparisons;',roundtrips,'reference roundtrip bytes;',len(visited),'instructions;',len(witnesses),'witnesses')


if __name__=='__main__':main()
