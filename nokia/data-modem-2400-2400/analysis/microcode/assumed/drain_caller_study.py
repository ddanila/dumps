"""Test the complete 248 wrapper's two right drains and following left drain."""
import argparse
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path
from common import HERE, decode, read, save, unconditional_transfer
from execute import CarryInput, execute
from model import Am2901, X8X02
from biased_drain_study import prediction


def expected(q,d,mask,bias):
    for stage in ('first-right','second-right'):
        p=prediction(q,d,mask,bias)
        if not p['returned']:return dict(stage=stage,returned=False)
        q=p['q']
    seen=set()
    while q not in seen:
        seen.add(q)
        if (d+q)&255==0:return dict(stage='returned',returned=True)
        q=(q<<1)&255
    return dict(stage='left',returned=False)


def probe(rows,scenario,q,d,mask,bias):
    ram=scenario['initial']['ram'][:];ram[7]=mask;ram[13]=bias;ram[2]=0x35
    cpu=Am2901(ram=ram,q=q,logic_flags=True);seq=X8X02(pc=0x150)
    carry=CarryInput(scenario['inputs']['carry']);previous=dict(zero=0,carry=0,sign=0,overflow=0)
    seen={};trace=[];stage='first-right';condition=scenario['condition']
    for cycle in range(256):
        key=(seq.pc,seq.sp,tuple(seq.stack),tuple(cpu.ram),cpu.q,carry.previous,tuple(sorted(previous.items())))
        if seq.pc in (0x298,0x187):
            if key in seen:return dict(returned=False,stage=stage,cycles=cycle,pc=seq.pc,repeat_from=seen[key],period=cycle-seen[key],ram=cpu.ram,q=cpu.q,trace=trace)
            seen[key]=cycle
        row=rows[seq.pc];pc=seq.pc
        if pc==0x24b:stage='second-right'
        if pc==0x24d:stage='left'
        result=cpu.step(row['i'],row['a'],row['b'],d,carry.resolve(row),0,0);carry.observe(result)
        if unconditional_transfer(row,scenario):test=1
        else:
            source=condition['sources'][row['select']]
            value=condition['per_select'][row['select']] if source=='constant' else previous[source]
            test=int(bool(value))^condition['polarity'][row['select']]
        trace.append(dict(pc=pc,q=cpu.q,ram0=cpu.ram[0],ram3=cpu.ram[3],alu=result,test=test))
        seq.step(row['command'],row['branch'],test);previous=result
        if seq.pc==0x151:return dict(returned=True,stage='returned',cycles=cycle+1,pc=seq.pc,ram=cpu.ram,q=cpu.q,trace=trace)
    raise ValueError('no return or repeated state')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/drain-caller-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'drain-caller-study.json');root=HERE/config['base']
    mapping=read(root/'mapping.json');scenario=read(root/'scenario.json');rows=decode(mapping)
    assert scenario['condition']['flag_timing']=='previous'
    counts=Counter();periods=Counter();witnesses=[];seen=set();digest=hashlib.sha256();returning={}
    for mask in config['masks']:
        for d in range(256):
            for q in range(256):
                want=expected(q,d,mask,config['bias']);got=probe(rows,scenario,q,d,mask,config['bias'])
                assert got['stage']==want['stage'] and got['returned']==want['returned'],(q,d,mask,want,got)
                for i,value in enumerate(got['ram']):
                    if i not in (0,3):assert value==({2:0x35,7:mask,13:config['bias']}.get(i,scenario['initial']['ram'][i]))
                if got['returned']:
                    assert got['q']==0 and got['ram'][0]==(d+1)&255 and got['ram'][3]==0x35
                    returning.setdefault(f'{mask:02x}:{d:02x}',[]).append(q)
                else:periods[f"{got['stage']}:{got['period']}"]+=1
                counts[f"{mask:02x}:{got['stage']}"]+=1
                digest.update(json.dumps([mask,d,q,got['stage'],got['cycles'],got['pc'],got['ram'],got['q']],separators=(',',':')).encode())
                key=(mask,got['stage'])
                if key not in seen:
                    seen.add(key);s=copy.deepcopy(scenario)
                    ram=scenario['initial']['ram'][:];ram[7]=mask;ram[13]=config['bias'];ram[2]=0x35
                    s['initial']=dict(pc=0x150,ram=ram,q=q)
                    s['io']['read']=dict(mode='constant',value=d,table=[0],status='stub',evidence=config['evidence'])
                    out=args.out/f'mask{mask:02x}-{got["stage"]}'
                    run=execute(mapping,s,got['cycles'],mode='integrated',out=out,trace_limit=got['cycles'])
                    assert run['clean'] and run['final_state']['pc']==got['pc'] and run['final_state']['ram']==got['ram'] and run['final_state']['q']==got['q']
                    witnesses.append(dict(mask=mask,d=d,q=q,expected=want,observed=got,integrated_trace_digest=run['trace_digest']))
    reset_runs=[]
    for profile in config['reset_profiles']:
        for d in range(256):
            s=copy.deepcopy(scenario)
            s['initial']=dict(pc=0,ram=[0]*16,q=0)
            if profile=='constant':
                s['io']['read']=dict(mode='constant',value=d,table=[0],status='stub',evidence=config['evidence'])
            else:
                s['io']['read']=dict(mode='pc_sequence',value=0,table=[0],pc_sequences={str(0x18d):[d],str(0x1ec):[(d+1)&255]},sequence_end='hold-last',status='stub',evidence=config['evidence'])
            run=execute(mapping,s,config['reset_cycles'],mode='integrated',trace_limit=0)
            assert run['clean']
            reset_runs.append(dict(profile=profile,d=d,visited_callers=[pc for pc in (0x150,0x157,0x248,0x249,0x24b,0x24d) if pc in run['visited']],
                                   final_pc=run['final_state']['pc'],trace_digest=run['trace_digest']))
    sources=[Path(__file__),HERE/'drain-caller-study.json',HERE/'biased_drain_study.py',HERE/'execute.py',HERE/'common.py',HERE.parent/'model.py',root/'mapping.json',root/'scenario.json']
    save(args.out/'report.json',dict(configuration=config,counts=dict(counts),repeat_periods=dict(periods),reset_runs=reset_runs,returning_inputs=returning,execution_sha256=digest.hexdigest(),witnesses=witnesses,
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='Actual 150->248 wrapper does not establish R7; first drain success does not ensure second drain or left drain returns. Constant external D is a local stub, not recovered caller behavior.'))
    print(dict(counts));print('repeat periods',dict(periods))


if __name__=='__main__':main()
