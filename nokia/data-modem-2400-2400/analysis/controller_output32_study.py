"""Verify the third outgoing byte and its counter updates against controller ROM."""
import argparse
import random
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
from interface_study import HERE, ROOT, CORE, ROM, SHA
from controller_output import output32


def fixtures(config):
    rng=random.Random(config['seed'])
    for state in range(256):
        for index in range(config['cases_per_state']):
            yield dict(state=state,flags=[rng.randrange(256) for _ in range(6)],
                       input_c=rng.randrange(256),previous=rng.randrange(256),
                       counters=[rng.randrange(256) for _ in range(3)])
    for count49 in range(256):
        for count4a in range(256):
            yield dict(state=0xc2,flags=[0]*6,input_c=0,previous=(count49&1)<<6,
                       counters=[count49,count4a,0])
    for state in config['counter65_states']:
        for flags23 in (0,32):
            for flags24 in (0,32):
                for counter in range(256):
                    yield dict(state=state,flags=[0,flags23,flags24,0,0,0],input_c=0,
                               previous=0,counters=[0,0,counter])
    for state in config['prior_sweep_states']:
        for value in range(256):
            yield dict(state=state,flags=[0]*6,input_c=0,previous=value,counters=[0,0,0])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/controller-output32-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=json.loads((HERE/'controller-output32-scenario.json').read_text());rom=ROM.read_bytes()
    if hashlib.sha256(rom).hexdigest()!=SHA:raise ValueError('ROM mismatch')
    exe=args.out/'interface-probe';sources=[HERE/'interface_probe.c']+[CORE/n for n in ('core.c','opcodes.c','disasm.c')]
    subprocess.run(['cc','-O2','-Wall','-DSAT_TRACE','-I',str(CORE),*[str(p) for p in sources],'-o',str(exe)],check=True)
    fixture_hash=hashlib.sha256();execution_hash=hashlib.sha256();visited=set();saved=[];seen=set();count=0
    with tempfile.TemporaryFile(mode='w+t') as inputs:
        for case in fixtures(config):
            code=output32(rom,case['state'],case['previous'],case['flags'],case['input_c'],*case['counters'])['code']
            line=f"out32 {bytes([case['state'],case['previous'],*case['counters'],case['input_c'],code]).hex()} {bytes(case['flags']).hex()} 8 0\n"
            inputs.write(line);fixture_hash.update(line.encode())
        inputs.seek(0)
        process=subprocess.Popen([str(exe),str(ROM),str(config['initial_p1']),'0',str(config['cycle_limit']),str(config['return_sentinel']),str(config['initial_sp'])],stdin=inputs,stdout=subprocess.PIPE,text=True)
        try:
            for case in fixtures(config):
                line=process.stdout.readline()
                if not line:raise ValueError('incomplete probe output')
                execution_hash.update(line.encode());result=json.loads(line);count+=1;visited.update(result['visited'])
                expected=output32(rom,case['state'],case['previous'],case['flags'],case['input_c'],*case['counters'])
                ram=[0]*128;ram[0x22:0x28]=case['flags'];ram[0x2c]=case['input_c']
                ram[0x34]=ram[3]=case['state'];ram[2]=expected['code'];ram[0x32]=ram[0x20]=expected['value']
                ram[0x49]=expected['count49'];ram[0x4a]=expected['count4a'];ram[0x65]=expected['count65']
                ram[config['initial_sp']-1]=config['return_sentinel']&255;ram[config['initial_sp']]=config['return_sentinel']>>8
                if (result['errors'] or not result['reached_stop'] or result['pc']!=0x266
                    or result['sp']!=config['initial_sp'] or result['iram']!=ram):
                    raise ValueError((case,expected,[(i,a,b) for i,(a,b) in enumerate(zip(result['iram'],ram)) if a!=b]))
                key=(case['state']>>5,expected['action'])
                if key not in seen:seen.add(key);saved.append(dict(fixture=case,reference=expected,result=result))
            if process.stdout.readline() or process.wait()!=0:raise ValueError('unexpected probe completion')
        finally:
            if process.poll() is None:process.kill();process.wait()
            process.stdout.close()
    listing=HERE/'results/controller-linear.asm'
    pcs={int(line.split()[0],16) for line in listing.read_text().splitlines()}
    expected_pcs={p for p in pcs if 0x12f<=p<=0x263 and not 0x1be<=p<=0x1fd}
    if visited!=expected_pcs:raise ValueError(('coverage differs',sorted(expected_pcs-visited),sorted(visited-expected_pcs)))
    report=dict(configuration=config,rom_sha256=SHA,cases=count,all_checks_pass=True,instruction_coverage=sorted(visited),
        fixture_sha256=fixture_hash.hexdigest(),execution_sha256=execution_hash.hexdigest(),witnesses=saved,
        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[CORE/'emu8051.h',Path(__file__),HERE/'controller_output.py',HERE/'controller-output32-scenario.json',listing]},
        interpretation='Local RAM32 builder with counter state and raw code supplied from the validated earlier lookup. Physical timing and output destination unknown.')
    (args.out/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');exe.unlink()
    print(count,'output comparisons pass;',len(saved),'witnesses;',len(visited),'instruction starts')


if __name__=='__main__':main()
