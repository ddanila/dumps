"""Exhaust the state/flag inputs to the controller's RAM33 output builder."""
import argparse
import csv
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
from interface_study import HERE, ROOT, CORE, ROM, SHA
from controller_output import output33


def fixtures(config):
    for state in range(256):
        for bits in range(256):
            flags=config['base_state'][:]
            flags[1]=sum(((bits>>i)&1)<<b for i,b in enumerate((1,5,6,7)))
            flags[2]=((bits>>4)&1)<<6
            inp=(((bits>>5)&1)<<2)|(((bits>>6)&1)<<7)
            yield dict(state=state,flags=flags,input2d=inp,output30=((bits>>7)&1)<<5,
                       prior33=config['prior_output'])
    for state in config['prior_sweep_states']:
        for prior in range(256):
            yield dict(state=state,flags=config['base_state'][:],input2d=0,output30=0,prior33=prior)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/controller-output-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=json.loads((HERE/'controller-output-scenario.json').read_text());rom=ROM.read_bytes()
    if hashlib.sha256(rom).hexdigest()!=SHA:raise ValueError('ROM mismatch')
    exe=args.out/'interface-probe';sources=[HERE/'interface_probe.c']+[CORE/n for n in ('core.c','opcodes.c','disasm.c')]
    subprocess.run(['cc','-O2','-Wall','-DSAT_TRACE','-I',str(CORE),*[str(p) for p in sources],'-o',str(exe)],check=True)
    fixture_hash=hashlib.sha256();execution_hash=hashlib.sha256();visited=set();saved=[];seen=set();count=0
    with tempfile.TemporaryFile(mode='w+t') as inputs:
        for case in fixtures(config):
            line=f"out33 {bytes([case['state'],case['prior33'],case['output30'],case['input2d']]).hex()} {bytes(case['flags']).hex()} 8 0\n"
            inputs.write(line);fixture_hash.update(line.encode())
        inputs.seek(0)
        process=subprocess.Popen([str(exe),str(ROM),str(config['initial_p1']),'0',str(config['cycle_limit']),str(config['return_sentinel']),str(config['initial_sp'])],stdin=inputs,stdout=subprocess.PIPE,text=True)
        try:
            for case in fixtures(config):
                line=process.stdout.readline()
                if not line:raise ValueError('incomplete probe output')
                execution_hash.update(line.encode());result=json.loads(line);count+=1;visited.update(result['visited'])
                expected=output33(rom,case['state'],case['flags'][1],case['flags'][2],case['input2d'],case['output30'])
                ram=[0]*128;ram[0x22:0x28]=case['flags'];ram[0x2d]=case['input2d'];ram[0x30]=case['output30']
                ram[0x34]=case['state'];ram[3]=case['state'];ram[2]=expected['code'];ram[0x20]=ram[0x33]=expected['value']
                ram[config['initial_sp']-1]=config['return_sentinel']&255;ram[config['initial_sp']]=config['return_sentinel']>>8
                if (result['errors'] or not result['reached_stop'] or result['pc']!=0x12f
                    or result['sp']!=config['initial_sp'] or result['iram']!=ram):
                    raise ValueError((case,expected,[(i,a,b) for i,(a,b) in enumerate(zip(result['iram'],ram)) if a!=b]))
                key=(expected['source'],expected['reason'],expected['value']&7)
                if key not in seen:seen.add(key);saved.append(dict(fixture=case,reference=expected,result=result))
            if process.stdout.readline() or process.wait()!=0:raise ValueError('unexpected probe completion')
        finally:
            if process.poll() is None:process.kill();process.wait()
            process.stdout.close()
    listing=HERE/'results/controller-linear.asm'
    pcs={int(line.split()[0],16) for line in listing.read_text().splitlines()}
    expected_pcs={p for p in pcs if 0x6e<=p<=0x12c and not 0x95<=p<=0xd4}
    # The redundant E8 test at 00F2 cannot be equal after the earlier test.
    expected_pcs.discard(0xf5)
    if visited!=expected_pcs:raise ValueError(('coverage differs',sorted(expected_pcs-visited),sorted(visited-expected_pcs)))
    with (args.out/'state-codes.csv').open('w') as f:
        writer=csv.writer(f,lineterminator='\n');writer.writerow(['state','source','raw_code','ram33_high_bits','wire_high_bits'])
        for state in range(256):
            r=output33(rom,state,0,0,0,0)
            writer.writerow([f'{state:02X}',r['source'],f"{r['code']:02X}",f"{r['value']&248:02X}",f"{r['wire_value']&248:02X}"])
    report=dict(configuration=config,rom_sha256=SHA,cases=count,all_checks_pass=True,instruction_coverage=sorted(visited),
        fixture_sha256=fixture_hash.hexdigest(),execution_sha256=execution_hash.hexdigest(),witnesses=saved,
        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[CORE/'emu8051.h',Path(__file__),HERE/'controller_output.py',HERE/'controller-output-scenario.json',listing]},
        interpretation='Complete local RAM33 builder under bank-zero/disabled-interrupt assumptions. Physical destination and the other output builders remain unresolved.')
    (args.out/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');exe.unlink()
    print(count,'output comparisons pass;',len(saved),'witnesses;',len(visited),'instruction starts')


if __name__=='__main__':main()
