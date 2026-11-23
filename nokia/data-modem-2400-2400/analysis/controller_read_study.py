"""Track an external-read value through actual controller caller instructions."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from interface_study import HERE, ROOT, CORE, ROM, SHA


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/controller-read-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=json.loads((HERE/'controller-read-scenario.json').read_text())
    interface=json.loads((HERE/config['interface_scenario']).read_text())
    rom=ROM.read_bytes()
    if hashlib.sha256(rom).hexdigest()!=SHA:raise ValueError('controller ROM hash mismatch')
    coverage={int(line.split()[2],16) for line in (HERE/config['recorded_coverage']).read_text().splitlines() if line.startswith('I ')}
    callers=[]
    for pc in sorted(coverage):
        op=rom[pc]
        target=(rom[pc+1]<<8)|rom[pc+2] if op==0x12 else (((pc+2)&0xf800)|((op&0xe0)<<3)|rom[pc+1]) if op&0x1f==0x11 else None
        if target==0x8dd:callers.append(pc)
    expected_callers=sorted(v['entry'] for k,v in config['modes'].items() if k!='port')
    if callers!=expected_callers:raise ValueError(('observed callers changed',callers))
    branch=config['poll_backedge_pc'];offset=rom[branch+1]
    branch_target=branch+2+(offset-256 if offset>=128 else offset)
    if rom[branch]!=0x80 or branch_target!=config['modes']['main']['entry']:
        raise ValueError('main polling back edge changed')
    sources=[HERE/'interface_probe.c']+[CORE/n for n in ('core.c','opcodes.c','disasm.c')]
    exe=args.out/'interface-probe'
    subprocess.run(['cc','-O2','-Wall','-DSAT_TRACE','-I',str(CORE),*[str(p) for p in sources],'-o',str(exe)],check=True)
    cases=[]
    for mode in config['modes']:
        cases += [dict(mode=mode,read=value,p2=config['p2_for_value_sweep'],sweep='value') for value in range(256)]
        cases += [dict(mode=mode,read=config['read_value_for_p2_sweep'],p2=value,sweep='p2') for value in range(256)]
    serial=[interface['discarded_byte']]+interface['base_payload'];prior=interface['base_payload']
    payload=''.join(f"{c['mode']} {bytes([c['read'],c['p2']]+serial).hex()} {bytes(prior).hex()} {interface['default_delay']} 7\n" for c in cases)
    options=[str(interface[k]) for k in ('initial_p1','initial_changed_flag','cycle_limit','return_sentinel','initial_sp')]
    run=subprocess.run([str(exe),str(ROM),*options],input=payload,text=True,capture_output=True,check=True)
    results=[json.loads(line) for line in run.stdout.splitlines()]
    if len(results)!=len(cases):raise ValueError('incomplete output')
    baseline={};saved=[];checks=0
    for case,result in zip(cases,results):
        assert result['errors']==0 and result['reached_stop'],(case,result)
        assert result['pc']==config['modes'][case['mode']]['stop'],case
        reads=[e for e in result['events'] if e['kind']=='read_address']
        values=[e for e in result['events'] if e['kind']=='read_value']
        assert len(reads)==len(values)==1 and values[0]['value']==case['read'],case
        assert reads[0]['value']==((((case['p2']&31)|128)<<8)|4),case
        assert result['p2']==(case['p2']&31),case
        if case['mode']=='port':assert result['acc']==case['read'],case
        else:
            expected_acc=(interface['base_payload'][0]^7) if case['mode']=='main' else prior[0]
            assert result['acc']==expected_acc,case
        if case['mode']!='port' and case['sweep']=='value':
            # Full modeled architectural state, not only A or a final byte.
            state={k:result[k] for k in ('cycles','pc','sp','iram','sfr')}
            baseline.setdefault(case['mode'],state)
            assert baseline[case['mode']]==state,case
            checks+=1
        if (case['sweep']=='value' and case['read'] in (0,255)) or (case['sweep']=='p2' and case['p2']==255):
            saved.append(dict(fixture=case,result=result))
    dependencies=sources+[CORE/'emu8051.h',Path(__file__),HERE/'interface_study.py',HERE/'controller-read-scenario.json',HERE/config['interface_scenario'],HERE/config['recorded_coverage']]
    report=dict(configuration=config,interface_assumptions=interface,rom_sha256=SHA,cases=len(cases),
                observed_direct_callers=callers,caller_state_equality_checks=checks,all_checks_pass=True,
                poll_backedge=dict(pc=branch,raw=list(rom[branch:branch+2]),target=branch_target),
                fixture_sha256=hashlib.sha256(payload.encode()).hexdigest(),execution_sha256=hashlib.sha256(run.stdout.encode()).hexdigest(),
                source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in dependencies},
                witnesses=saved,
                interpretation='The byte returned by 08DD is live at its return but dead at the tested caller checkpoints. External read side effects remain unmodeled and unidentified.')
    (args.out/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    exe.unlink()
    print(f'{len(cases)} external-read probes pass; {checks} caller states independent of returned byte')


if __name__=='__main__':main()
