"""Verify the output construction through actual caller and serial transmission."""
import argparse
import random
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
from interface_study import HERE, ROOT, CORE, ROM, SHA
from controller_output import output_build
from controller_program_study import reference as program_reference

def selected_mode(payload):
    d=payload[3]
    return 0xec if d&128 else {(0,0):0x6e,(0,1):0x7e,(1,0):0x6a,(1,1):0x66}[(int(bool(d&32)),int(bool(d&16)))]


def fixtures(config):
    rng=random.Random(config['seed'])
    for state in range(256):
        for index in range(config['cases_per_state']):
            case=dict(state=state,flags=[rng.randrange(256) for _ in range(6)],
                       payload=[rng.randrange(256) for _ in range(6)],
                       previous=[rng.randrange(256) for _ in range(4)],
                       counters=[rng.randrange(256) for _ in range(3)],
                       patterns=[rng.randrange(256) for _ in range(2)])
            case['prior_mode']=selected_mode(case['payload']) if index&1 else rng.randrange(256)
            yield case


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/controller-output-send-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=json.loads((HERE/'controller-output-send-scenario.json').read_text());rom=ROM.read_bytes()
    if hashlib.sha256(rom).hexdigest()!=SHA:raise ValueError('ROM mismatch')
    exe=args.out/'interface-probe';sources=[HERE/'interface_probe.c']+[CORE/n for n in ('core.c','opcodes.c','disasm.c')]
    subprocess.run(['cc','-O2','-Wall','-DSAT_TRACE','-I',str(CORE),*[str(p) for p in sources],'-o',str(exe)],check=True)
    fixture_hash=hashlib.sha256();execution_hash=hashlib.sha256();visited=set();saved=[];seen=set();count=0
    with tempfile.TemporaryFile(mode='w+t') as inputs:
        for case in fixtures(config):
            line=f"send {bytes([case['state'],*case['previous'],*case['payload'],*case['counters'],*case['patterns'],case['prior_mode']]).hex()} {bytes(case['flags']).hex()} 8 4\n"
            inputs.write(line);fixture_hash.update(line.encode())
        inputs.seek(0)
        process=subprocess.Popen([str(exe),str(ROM),str(config['initial_p1']),'0',str(config['cycle_limit']),str(config['return_sentinel']),str(config['initial_sp'])],stdin=inputs,stdout=subprocess.PIPE,text=True)
        try:
            for case in fixtures(config):
                line=process.stdout.readline()
                if not line:raise ValueError('incomplete probe output')
                execution_hash.update(line.encode());result=json.loads(line);count+=1;visited.update(result['visited'])
                expected=output_build(rom,case['state'],case['previous'],case['flags'],case['payload'],case['counters'],case['patterns'],config['initial_p1'])
                mode=selected_mode(case['payload'])
                changed=mode!=case['prior_mode']
                reset_both=not changed and bool(case['flags'][2]&32) and case['state']==0
                bus=[]
                if reset_both:bus.append(program_reference([5,0xcc,0x15,config['initial_p2']]))
                if changed or reset_both:
                    command=(0x35&~32)|((not bool(case['payload'][4]&1))<<5)
                    bus.append(program_reference([6,mode,command,config['initial_p2']]))
                expected_events=[]
                for transfer in bus:
                    for value in transfer['values']:
                        expected_events.extend([('write_address',transfer['address']),('write_value',value)])
                events=result['events']
                writes=[(e['kind'],e['value']) for e in events if e['kind'].startswith('write_')]
                wire=[v^mask for v,mask in zip(expected['values'],(0,3,0,0xf8))]
                tx=[e['value'] for e in events if e['kind']=='tx']
                completed=[e for e in events if e['kind']=='tx_complete']
                ram=result['iram'];p1=expected['p1']
                p1&=0xfa
                checks=[result['errors']==0,result['reached_stop'],result['pc']==0x1ee8,
                        result['sp']==config['initial_sp'],result['p2']==config['initial_p2'],ram[0x30:0x34]==expected['values'],
                        [ram[0x49],ram[0x4a],ram[0x65]]==expected['counters'],
                        ram[0x3d:0x3f]==expected['patterns'],ram[0x35]==mode,
                        ram[0x2a:0x30]==case['payload'],ram[0x34]==case['state'],
                        tx==wire,writes==expected_events,len(completed)==4,result['p1']==p1,
                        ram[0x20]==wire[-1]]
                if not all(checks):raise ValueError((case,checks,expected,result))
                latch=[e for e in events if e['pc'] in (0x8d7,0x8da)]
                if len(latch)!=2 or latch[0]['cycle']<=completed[-1]['cycle'] or not latch[0]['value']&4 or latch[1]['value']&4:
                    raise ValueError(('latch ordering',case,result))
                expected.update(wire=wire,bus=bus,mode=mode,final_p1=p1)
                key=(case['state']>>5,changed,reset_both,mode)
                if key not in seen:seen.add(key);saved.append(dict(fixture=case,reference=expected,result=result))
            if process.stdout.readline() or process.wait()!=0:raise ValueError('unexpected probe completion')
        finally:
            if process.poll() is None:process.kill();process.wait()
            process.stdout.close()
    listing=HERE/'results/controller-linear.asm'
    pcs={int(line.split()[0],16) for line in listing.read_text().splitlines()}
    expected_pcs={p for p in pcs if 0x6e<=p<=0x46a and not 0x95<=p<=0xd4 and not 0x1be<=p<=0x1fd and p!=0xf5}
    if not expected_pcs<=visited:raise ValueError(('prefix coverage missing',sorted(expected_pcs-visited)))
    report=dict(configuration=config,rom_sha256=SHA,cases=count,all_checks_pass=True,instruction_coverage=sorted(visited),
        unvisited_output_tail=sorted(p for p in pcs-visited if 0x433<=p<=0x4f9),
        fixture_sha256=fixture_hash.hexdigest(),execution_sha256=execution_hash.hexdigest(),witnesses=saved,
        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[CORE/'emu8051.h',Path(__file__),HERE/'controller_output.py',HERE/'controller_program_study.py',HERE/'controller-output-send-scenario.json',listing]},
        interpretation='Actual caller executes 006E and 0899 continuously; external writes logged and four synthetic TX completions supplied. Output bytes, counters, patterns, mode, P1, bus writes, and transmitted values match references. Internal initialization state is not fully compared; no DSP connection or physical timing claimed.')
    (args.out/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');exe.unlink()
    print(count,'output comparisons pass;',len(saved),'witnesses;',len(visited),'instruction starts')


if __name__=='__main__':main()
