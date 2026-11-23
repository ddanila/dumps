"""Verify event accumulation and outgoing flag qualification against controller ROM."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from interface_study import HERE, ROOT, CORE, ROM, SHA
from controller_event import edge, qualify


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/controller-event-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=json.loads((HERE/'controller-event-scenario.json').read_text())
    if hashlib.sha256(ROM.read_bytes()).hexdigest()!=SHA:raise ValueError('ROM mismatch')
    cases=[]
    for mode in ('edge','qualify'):
        for high in config['high_bytes']:
            for low in range(256):
                for acc in config['accumulators']:
                    cases.append(dict(mode=mode,low=low,high=high,accumulator=acc,state34=1))
        for high in range(256):
            for low in config['boundary_lows']:
                for state34 in (0,1):
                    cases.append(dict(mode=mode,low=low,high=high,accumulator=191,state34=state34))
    for outputs in ([0,0],[255,255],[4,0],[0,16]):
        for low in config['boundary_lows']:
            for high in config['high_bytes']:
                for acc in config['accumulators']:
                    cases.append(dict(mode='qualify',low=low,high=high,accumulator=acc,state34=1,outputs=outputs))
    for mode in ('edge','qualify'):
        for initial_ie in config['additional_ie_values']:
            for low in config['boundary_lows']:
                for high in config['high_bytes']:
                    for acc in config['accumulators']:
                        cases.append(dict(mode=mode,low=low,high=high,accumulator=acc,state34=1,initial_ie=initial_ie))
    exe=args.out/'interface-probe';sources=[HERE/'interface_probe.c']+[CORE/n for n in ('core.c','opcodes.c','disasm.c')]
    subprocess.run(['cc','-O2','-Wall','-DSAT_TRACE','-I',str(CORE),*[str(p) for p in sources],'-o',str(exe)],check=True)
    payload=''.join(f"{c['mode']} {bytes([c['low'],c['high'],c['accumulator'],c['state34'],*c.get('outputs',config['outputs']),0,0,c.get('initial_ie',0)]).hex()} {bytes(config['state']).hex()} 8 0\n" for c in cases)
    run=subprocess.run([str(exe),str(ROM),str(config['initial_p1']),'0',str(config['cycle_limit']),str(config['return_sentinel']),str(config['initial_sp'])],input=payload,text=True,capture_output=True,check=True)
    results=[json.loads(line) for line in run.stdout.splitlines()]
    if len(cases)!=len(results):raise ValueError('incomplete probe output')
    visited={mode:set() for mode in ('edge','qualify')};saved=[];seen=set()
    for case,result in zip(cases,results):
        mode=case['mode'];visited[mode].update(result['visited'])
        ram=[0]*128;ram[0x22:0x28]=config['state'];ram[0x12]=case['low'];ram[0x13]=case['high']
        ram[0x6e]=case['accumulator'];ram[0x34]=case['state34'];ram[0x30:0x32]=case.get('outputs',config['outputs'])
        ram[config['initial_sp']-1]=config['return_sentinel']&255;ram[config['initial_sp']]=config['return_sentinel']>>8
        if mode=='edge':expected=edge(case['low'],case['high'],case['accumulator'],case.get('initial_ie',0));key=(mode,expected['added'])
        else:
            expected=qualify(case['low'],case['high'],case['accumulator'],case['state34'],*case.get('outputs',config['outputs']),config['state'][0],case.get('initial_ie',0))
            ram[0x30]=expected['out0'];ram[0x31]=expected['out1'];ram[0x22]=expected['state22'];key=(mode,expected['action'],expected['ie'])
        ram[0x12]=expected['low'];ram[0x13]=expected['high'];ram[0x6e]=expected['accumulator']
        if (result['errors'] or not result['returned'] or result['sp']!=config['initial_sp']-2
            or result['iram']!=ram or result['sfr'][0xa8-0x80]!=expected['ie']):
            raise ValueError((case,expected,[(i,a,b) for i,(a,b) in enumerate(zip(result['iram'],ram)) if a!=b],result['sfr'][40]))
        if key not in seen:seen.add(key);saved.append(dict(fixture=case,reference=expected,result=result))
    listing=HERE/'results/controller-linear.asm'
    pcs={int(line.split()[0],16) for line in listing.read_text().splitlines()}
    expected_pcs=dict(edge={p for p in pcs if 0x1760<=p<=0x178f}|{0x13,0x15,0x17},qualify={p for p in pcs if 0x1790<=p<=0x17f0})
    if visited!=expected_pcs:raise ValueError({mode:sorted(expected_pcs[mode]-visited[mode]) for mode in visited})
    report=dict(configuration=config,rom_sha256=SHA,cases=len(cases),all_checks_pass=True,
        instruction_coverage={k:sorted(v) for k,v in visited.items()},witnesses=saved,
        fixture_sha256=hashlib.sha256(payload.encode()).hexdigest(),execution_sha256=hashlib.sha256(run.stdout.encode()).hexdigest(),
        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[CORE/'emu8051.h',Path(__file__),HERE/'controller_event.py',HERE/'controller-event-scenario.json',listing]},
        interpretation='Countdown-derived event accumulation reaches RAM30.2/RAM31.4 output flags. Physical event and clock frequency unknown.')
    (args.out/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');exe.unlink()
    print(len(cases),'event/poll comparisons pass;',len(saved),'witnesses')


if __name__=='__main__':main()
