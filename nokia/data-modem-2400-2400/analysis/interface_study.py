"""Verify controller transfer semantics with byte-distinct local ROM executions."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CORE=ROOT/'unknown/satellite-mac304-m27c2001/analysis/emulation/emu8051'
ROM=ROOT/'nokia/data-modem-2400-2400/controller-810244e/nokia-modem-other-board-2764.bin'
SHA='daf854c513cd427664bb345f511afc2d38441e5002e4a85389d289aedbfc0038'


def fixtures(config):
    base=config['base_payload']
    cases=[]
    def add(name,mode,frame,prior,delay=None,completions=None,save=False):
        cases.append(dict(name=name,mode=mode,frame=frame,prior=prior,delay=config['default_delay'] if delay is None else delay,
                          completions=(7 if mode=='read' else 4) if completions is None else completions,
                          save=save))
    for position in range(6):
        for value in range(256):
            payload=base[:];payload[position]=value
            expected=[payload[0]^7]+payload[1:]
            add(f'read-equal-{position}-{value}','read',[config['discarded_byte']]+payload,expected,save=position==0 and value in (0,255))
            prior=expected[:];prior[position]^=1
            add(f'read-changed-{position}-{value}','read',[config['discarded_byte']]+payload,prior,save=position==0 and value in (0,255))
    for discarded in range(256):
        add(f'discard-{discarded}','read',[discarded]+base,[base[0]^7]+base[1:],save=discarded in (0,255))
    for position in range(4):
        for value in range(256):
            payload=base[:4];payload[position]=value
            add(f'write-{position}-{value}','write',payload,base,save=position==0 and value in (0,255))
    for delay in config['completion_delays']:
        for mode in ('read','write'):
            add(f'delay-{mode}-{delay}',mode,[config['discarded_byte']]+base if mode=='read' else base[:4],base,delay=delay,save=True)
    for mode,limits in (('read',(0,6)),('write',(0,3))):
        for limit in limits:
            add(f'incomplete-{mode}-{limit}',mode,[config['discarded_byte']]+base if mode=='read' else base[:4],base,completions=limit,save=True)
    return cases


def check(case,result,config):
    assert result['errors']==0,(case['name'],result)
    events=result['events'];kind=lambda name:[e for e in events if e['kind']==name]
    complete=case['completions']==(7 if case['mode']=='read' else 4)
    assert result['returned']==complete,case['name']
    if not complete:
        assert result['cycles']==config['cycle_limit'] and result['sp']==config['initial_sp'],case['name']
        waiting={('read',0):0x807,('read',6):0x87e,('write',0):0x8b0,('write',3):0x8d4}
        assert result['pc']==waiting[(case['mode'],case['completions'])],case['name']
        if case['mode']=='write':
            assert not any(e['value']&4 for e in kind('p1')),case['name']
            assert len(kind('tx'))==case['completions']+1,case['name']
        else:
            assert len(kind('rx'))==case['completions'],case['name']
        return
    assert result['sp']==config['initial_sp']-2 and result['pc']==config['return_sentinel'],case['name']
    if case['mode']=='read':
        expected=case['frame'][1:];expected=[expected[0]^7]+expected[1:]
        assert result['ram']==expected,case['name']
        assert result['changed']==int(expected!=case['prior']),case['name']
        assert [e['value'] for e in kind('rx')]==case['frame'],case['name']
        assert [e['value'] for e in kind('p1')]==[0xfa,0xf8,0xf9,0xf8],case['name']
        assert result['scon']==0 and not kind('tx'),case['name']
        assert kind('p1')[0]['cycle'] < kind('rx')[0]['cycle'] < kind('p1')[1]['cycle'],case['name']
        assert kind('p1')[2]['cycle'] < kind('rx')[1]['cycle'],case['name']
    else:
        expected=[v^mask for v,mask in zip(case['frame'],(0,3,0,0xf8))]
        assert [e['value'] for e in kind('tx')]==expected,case['name']
        assert len(kind('tx_complete'))==4 and not kind('rx'),case['name']
        assert [e['value'] for e in kind('p1')]==[0xf8,0xfc,0xf8],case['name']
        assert kind('p1')[1]['cycle'] > kind('tx_complete')[-1]['cycle'],case['name']
        assert result['ram']==case['prior'],case['name']


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/interface-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=json.loads((HERE/'interface-scenario.json').read_text())
    if hashlib.sha256(ROM.read_bytes()).hexdigest()!=SHA:raise ValueError('controller ROM hash mismatch')
    exe=args.out/'interface-probe'
    sources=[HERE/'interface_probe.c']+[CORE/n for n in ('core.c','opcodes.c','disasm.c')]
    subprocess.run(['cc','-O2','-Wall','-DSAT_TRACE','-I',str(CORE),*[str(p) for p in sources],'-o',str(exe)],check=True)
    cases=fixtures(config)
    payload=''.join(f"{c['mode']} {bytes(c['frame']).hex()} {bytes(c['prior']).hex()} {c['delay']} {c['completions']}\n" for c in cases)
    options=[str(config[k]) for k in ('initial_p1','initial_changed_flag','cycle_limit','return_sentinel','initial_sp')]
    run=subprocess.run([str(exe),str(ROM),*options],input=payload,text=True,capture_output=True,check=True)
    results=[json.loads(line) for line in run.stdout.splitlines()]
    if len(results)!=len(cases):raise ValueError('incomplete probe output')
    saved=[]
    for case,result in zip(cases,results):
        check(case,result,config)
        if case['save']:saved.append(dict(fixture=case,result=result))
    report=dict(rom_sha256=SHA,cases=len(cases),all_checks_pass=True,
        fixture_sha256=hashlib.sha256(payload.encode()).hexdigest(),
        execution_sha256=hashlib.sha256(run.stdout.encode()).hexdigest(),
        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[CORE/'emu8051.h',Path(__file__),HERE/'interface-scenario.json']},
        assumptions=config,
        witnesses=saved,
        interpretation='Controller-side frame and handshake constraints only. No physical switch/LED mapping or DSC2847 connection is established.')
    (args.out/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    exe.unlink()
    print(f'{len(cases)} local controller fixtures pass; {len(saved)} event witnesses retained')


if __name__=='__main__':main()
