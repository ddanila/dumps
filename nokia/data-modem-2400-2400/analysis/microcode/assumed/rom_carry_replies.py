"""Derive and exhaust the ROM/carry feedback recurrence at 36C-36E."""
import argparse
import hashlib
import shutil
import tempfile
from collections import Counter
from pathlib import Path
from common import HERE, read, save, decode
from model import Am2901
from execute import execute, CarryInput
from defined_condition_fit import load_trace
from rom_study import load_rom
from rom_gate_handlers import scenario_for_gate, outcome


def transition(table,x,d):
    byte=table[x]
    total=255+d if byte==0 else byte+d
    return dict(rom_byte=byte,r1=(byte-1)&255,r2=total&255,r3=(total+1)&255,
                repeat=int(total>=256))


def predict(table,d,x=0):
    seen={};steps=[]
    while x not in seen:
        seen[x]=len(steps)
        step=dict(address_byte=x,**transition(table,x,d));steps.append(step)
        if not step['repeat']:return dict(outcome='exit',iterations=len(steps),steps=steps,period=None)
        x=step['r2']
    return dict(outcome='repeat',iterations=None,steps=steps,period=len(steps)-seen[x],cycle_start=seen[x])


def check_step(rows,scenario,table,x,d):
    cpu=Am2901(logic_flags=True);cpu.ram[0]=255;cpu.q=5
    carry=CarryInput(scenario['inputs']['carry']);expected=transition(table,x,d)
    results=[]
    for pc,value in ((0x36c,table[x]),(0x36d,d),(0x36e,1)):
        row=rows[pc];result=cpu.step(row['i'],row['a'],row['b'],value,carry.resolve(row),0,0)
        carry.observe(result);results.append(result)
    assert cpu.ram[0]==255 and cpu.q==5
    assert cpu.ram[1:4]==[expected[k] for k in ('r1','r2','r3')]
    assert results[0]['y']==255 and results[1]['y']==expected['r1']
    assert results[2]['y']==expected['r2']
    assert results[1]['carry']==expected['repeat']
    return expected


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/rom-carry-replies')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'rom-carry-replies.json');rom=load_rom(config);table=rom[256:]
    mapping=read(HERE/config['profiles']['q3']);rows=decode(mapping)
    gate=read(HERE/config['gates'])['fits'][0]
    assert gate['terms']==[['11.4',0],['18.5',0]]
    scenario=scenario_for_gate(config,5,gate['pcs'])
    for pc in (0x36c,0x36d,0x36e):
        row=rows[pc]
        assert row['i']==133 and row['a']==pc-0x36c and row['b']==pc-0x36b
    assert [rows[p]['command'] for p in (0x36c,0x36d,0x36e)]==[5,1,2]
    assert rows[0x36e]['select']==2 and scenario['condition']['sources'][2]=='carry'
    assert scenario['condition']['polarity'][2]==0 and scenario['condition']['flag_timing']=='previous'
    local_counts=Counter();runs=[];witnesses=[];counts=Counter()
    for d in range(256):
        for x in range(256):
            check_step(rows,scenario,table,x,d)
            p=predict(table,d,x);local_counts[p['outcome']]+=1
    with tempfile.TemporaryDirectory() as temporary:
        out=Path(temporary)/'run'
        for d in range(256):
            scenario=scenario_for_gate(config,5,gate['pcs'])
            scenario['io']['read']['pc_sequences'][str(0x36d)]=[d]
            scenario['name']=f'ROM carry recurrence reply {d:02X}'
            summary=execute(mapping,scenario,config['cycles'],mode='integrated',out=out,trace_limit=config['cycles'])
            assert summary['clean'] and not summary['unused_word_executions']
            trace=load_trace(out);finding=outcome(trace,summary,scenario);p=predict(table,d)
            loop=[row for row in trace if 0x36c<=row['pc']<=0x36e]
            assert loop[0]['cycle']==84 and len(loop)>=3*len(p['steps'])
            for i,step in enumerate(p['steps']):
                a,b,c=loop[3*i:3*i+3]
                assert [r['pc'] for r in (a,b,c)]==[0x36c,0x36d,0x36e]
                assert a['external_read']['address']==256+step['address_byte'] and a['external_read']['value']==step['rom_byte']
                assert [r['alu']['f'] for r in (a,b,c)]==[step['r1'],step['r2'],step['r3']]
                assert c['alu']['y']==step['r2'] and c['test']==step['repeat']
            if p['outcome']=='exit':
                assert finding['outcome']=='terminal' and len(loop)==3*p['iterations']
                assert finding['first_terminal']==110+3*(p['iterations']-1)
            else:
                assert finding['outcome']=='repeat' and finding['repeat']['period']==3*p['period']
            case=dict(reply=d,prediction=p,observed=finding);runs.append(case)
            counts[p['outcome']]+=1
            if d in config['witness_replies']:
                name=f'reply-{d:02x}'
                shutil.copytree(out,args.out/name,dirs_exist_ok=True)
                witnesses.append(dict(path=name,reply=d,trace_digest=summary['trace_digest']))
    sources=[Path(__file__),HERE/'rom-carry-replies.json',HERE/config['gates'],HERE/'rom_gate_handlers.py',HERE/'handler_timing_study.py',HERE/'selector_prefix_study.py',HERE/'rom_study.py',HERE/'execute.py',HERE/'common.py',HERE/'defined_condition_fit.py',HERE.parent/'model.py',HERE/config['scenario'],HERE/config['tables'],HERE/config['profiles']['q3']]
    save(args.out/'report.json',dict(configuration=config,local_transition_checks=65536,local_entry_counts=dict(local_counts),
        reset_counts=dict(counts),runs=runs,witnesses=witnesses,
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}))
    print(dict(local_entries=local_counts,reset=counts))


if __name__=='__main__':main()
