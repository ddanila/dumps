"""Verify the external peripheral programming sequence against unchanged ROM."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from interface_study import HERE, ROOT, CORE, ROM, SHA


def fixtures(config):
    for address in config['addresses']:
        for mode in range(256):
            for command in config['commands']:
                yield [address,mode,command,0]
        for page in range(256):
            for mode in (0xcc,0xec,0x66,0x6a,0x6e,0x7e):
                yield [address,mode,0x35,page]


def reference(frame):
    address,mode,command,page=frame
    values=[0x80,0,0x40,mode]
    if mode&3==0:values.append(255)
    values.append(command)
    return dict(address=(page<<8)|address,values=values)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/controller-program-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=json.loads((HERE/'controller-program-scenario.json').read_text())
    if hashlib.sha256(ROM.read_bytes()).hexdigest()!=SHA:raise ValueError('ROM mismatch')
    sources=[HERE/'interface_probe.c']+[CORE/n for n in ('core.c','opcodes.c','disasm.c')]
    exe=args.out/'interface-probe'
    subprocess.run(['cc','-O2','-Wall','-DSAT_TRACE','-I',str(CORE),*[str(p) for p in sources],'-o',str(exe)],check=True)
    cases=list(fixtures(config))
    inputs=''.join(f'program {bytes(frame).hex()} 000000000000 8 0\n' for frame in cases)
    process=subprocess.run([str(exe),str(ROM),'248','0',str(config['cycle_limit']),str(config['return_sentinel']),str(config['initial_sp'])],input=inputs,text=True,capture_output=True,check=True)
    lines=process.stdout.splitlines()
    if len(lines)!=len(cases):raise ValueError('probe output length')
    visited=set();witnesses=[];seen=set()
    for frame,line in zip(cases,lines):
        result=json.loads(line);expected=reference(frame);visited.update(result['visited'])
        events=result['events'];pairs=[]
        for value in expected['values']:
            pairs.extend([('write_address',expected['address']),('write_value',value)])
        ram=[0]*128;ram[0],ram[3],ram[2]=frame[:3]
        ram[config['initial_sp']-1]=config['return_sentinel']&255
        ram[config['initial_sp']]=config['return_sentinel']>>8
        assert result['returned'] and result['errors']==0,(frame,result)
        assert result['sp']==config['initial_sp']-2 and result['iram']==ram,(frame,result)
        assert result['acc']==frame[2] and result['p2']==frame[3] and result['p1']==248,(frame,result)
        assert [(e['kind'],e['value']) for e in events]==pairs,(frame,result)
        key=(frame[0],frame[1]&3,frame[3] in (0,255))
        if key not in seen:seen.add(key);witnesses.append(dict(fixture=frame,reference=expected,result=result))
    listing=HERE/'results/controller-linear.asm'
    expected_pcs={int(line.split()[0],16) for line in listing.read_text().splitlines() if 0x1d05<=int(line.split()[0],16)<=0x1d30}
    assert visited==expected_pcs,(visited,expected_pcs)
    report=dict(configuration=config,rom_sha256=SHA,cases=len(cases),all_checks_pass=True,
                instruction_coverage=sorted(visited),witnesses=witnesses,
                fixture_sha256=hashlib.sha256(inputs.encode()).hexdigest(),
                execution_sha256=hashlib.sha256(process.stdout.encode()).hexdigest(),
                source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[CORE/'emu8051.h',Path(__file__),HERE/'controller-program-scenario.json',listing]},
                interpretation='Local 1D05 helper writes reset/mode/optional synchronization/command bytes. External device behavior is not simulated; P2 supplies the high address byte.')
    (args.out/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');exe.unlink()
    print(len(cases),'programming comparisons pass;',len(visited),'instruction starts;',len(witnesses),'witnesses')


if __name__=='__main__':main()
