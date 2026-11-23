"""Verify the composed output builders, rotating P1 patterns, and input override."""
import argparse
import random
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
from interface_study import HERE, ROOT, CORE, ROM, SHA
from controller_output import output_build


def fixtures(config):
    rng=random.Random(config['seed'])
    for state in range(256):
        for index in range(config['cases_per_state']):
            yield dict(state=state,flags=[rng.randrange(256) for _ in range(6)],
                       payload=[rng.randrange(256) for _ in range(6)],
                       previous=[rng.randrange(256) for _ in range(4)],
                       counters=[rng.randrange(256) for _ in range(3)],
                       patterns=[rng.randrange(256) for _ in range(2)])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/controller-output-build-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=json.loads((HERE/'controller-output-build-scenario.json').read_text());rom=ROM.read_bytes()
    if hashlib.sha256(rom).hexdigest()!=SHA:raise ValueError('ROM mismatch')
    exe=args.out/'interface-probe';sources=[HERE/'interface_probe.c']+[CORE/n for n in ('core.c','opcodes.c','disasm.c')]
    subprocess.run(['cc','-O2','-Wall','-DSAT_TRACE','-I',str(CORE),*[str(p) for p in sources],'-o',str(exe)],check=True)
    fixture_hash=hashlib.sha256();execution_hash=hashlib.sha256();visited=set();saved=[];seen=set();count=0
    with tempfile.TemporaryFile(mode='w+t') as inputs:
        for case in fixtures(config):
            line=f"build {bytes([case['state'],*case['previous'],*case['payload'],*case['counters'],*case['patterns']]).hex()} {bytes(case['flags']).hex()} 8 0\n"
            inputs.write(line);fixture_hash.update(line.encode())
        inputs.seek(0)
        process=subprocess.Popen([str(exe),str(ROM),str(config['initial_p1']),'0',str(config['cycle_limit']),str(config['return_sentinel']),str(config['initial_sp'])],stdin=inputs,stdout=subprocess.PIPE,text=True)
        try:
            for case in fixtures(config):
                line=process.stdout.readline()
                if not line:raise ValueError('incomplete probe output')
                execution_hash.update(line.encode());result=json.loads(line);count+=1;visited.update(result['visited'])
                expected=output_build(rom,case['state'],case['previous'],case['flags'],case['payload'],case['counters'],case['patterns'],config['initial_p1'])
                ram=[0]*128;ram[0x22:0x28]=case['flags'];ram[0x2a:0x30]=case['payload']
                ram[0x34]=ram[3]=case['state'];ram[2]=expected['code']
                ram[0x30:0x34]=expected['values'];ram[0x20]=expected['scratch']
                ram[0x49],ram[0x4a],ram[0x65]=expected['counters']
                ram[0x3d:0x3f]=expected['patterns']
                ram[config['initial_sp']-1]=config['return_sentinel']&255;ram[config['initial_sp']]=config['return_sentinel']>>8
                if (result['errors'] or not result['reached_stop'] or result['pc']!=0x46c or result['p1']!=expected['p1']
                    or result['sp']!=config['initial_sp'] or result['iram']!=ram
                    or (result['sfr'][0x50]>>5)&1!=expected['psw_f0']):
                    raise ValueError((case,expected,[(i,a,b) for i,(a,b) in enumerate(zip(result['iram'],ram)) if a!=b]))
                key=(case['state']>>5,expected['psw_f0'],case['payload'][2]&1)
                if key not in seen:seen.add(key);saved.append(dict(fixture=case,reference=expected,result=result))
            if process.stdout.readline() or process.wait()!=0:raise ValueError('unexpected probe completion')
        finally:
            if process.poll() is None:process.kill();process.wait()
            process.stdout.close()
    listing=HERE/'results/controller-linear.asm'
    pcs={int(line.split()[0],16) for line in listing.read_text().splitlines()}
    expected_pcs={p for p in pcs if 0x6e<=p<=0x46a and not 0x95<=p<=0xd4 and not 0x1be<=p<=0x1fd and p!=0xf5}
    if visited!=expected_pcs:raise ValueError(('coverage differs',sorted(expected_pcs-visited),sorted(visited-expected_pcs)))
    report=dict(configuration=config,rom_sha256=SHA,cases=count,all_checks_pass=True,instruction_coverage=sorted(visited),
        fixture_sha256=fixture_hash.hexdigest(),execution_sha256=execution_hash.hexdigest(),witnesses=saved,
        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[CORE/'emu8051.h',Path(__file__),HERE/'controller_output.py',HERE/'controller-output-build-scenario.json',listing]},
        interpretation='Uninterrupted ROM 006E–046A matches composed builders and immediate P1/byte override. Stops before helper calls at 046C; not a full polling iteration or serial transmission.')
    (args.out/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');exe.unlink()
    print(count,'output comparisons pass;',len(saved),'witnesses;',len(visited),'instruction starts')


if __name__=='__main__':main()
