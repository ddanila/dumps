"""Read the whole q3 366 helper, including its wait and final Q mask."""
import argparse
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path
from common import HERE,read,save,decode,unconditional_transfer
from execute import CarryInput,execute
from model import Am2901,X8X02
from defined_condition_fit import load_trace


def scenario_for(base,config,ram,q,inputs,s5):
    scenario=copy.deepcopy(base)
    scenario.update(name='q3 full 366 helper',evidence=config['evidence'])
    scenario['initial']=dict(pc=config['caller'],ram=ram[:],q=q)
    scenario['condition']['sources'][5]='constant';scenario['condition']['polarity'][5]=s5
    assert scenario['condition']['value']==0
    scenario['condition']['evidence']=config['evidence']
    scenario['io']['read']=dict(mode='pc_sequence',value=1,table=[0],pc_sequences={str(k):[v] for k,v in inputs.items()},
        sequence_end='hold-last',status='stub',evidence=config['evidence'])
    return scenario


def prediction(ram,q,inputs,s5):
    def d(pc):return inputs.get(pc,1)
    result=ram[:];a=ram[0];s=a+d(0x36c);r1=s&255
    t=r1+d(0x36d)+int(s>=256);r2=t&255;r3=(r2+d(0x36e))&255
    repeat=t>=256
    pcs=[0x366,0x367,0x368,0x369,0x36a]
    y=[(d(0x366)+q)&255,(d(0x367)+q)&255,a,a,0]
    if not s5:pcs.append(0x36b);y.append((d(0x36b)+q)&255)
    for _ in range(2 if repeat else 1):
        pcs.extend([0x36c,0x36d,0x36e]);y.extend([a,r1,r2])
    result[1:4]=[r1,r2,r3]
    if not repeat:
        result[0]=d(0x36f)&q;pcs.append(0x36f);y.append(result[0])
    return dict(ram=result,q=q,pcs=pcs,y=y,cycles=len(pcs)+1,outcome='repeat' if repeat else 'return',
        period=3 if repeat else None,first_sum=s,second_sum=t)


def probe(rows,scenario,record=False):
    initial=scenario['initial'];caller=initial['pc']
    cpu=Am2901(ram=initial['ram'][:],q=initial['q'],logic_flags=True)
    seq=X8X02(pc=caller);carry=CarryInput(scenario['inputs']['carry'])
    previous=None;trace=[];depth=0;seen={};pcs=[];ys=[]
    for cycle in range(24):
        outcome=None;period=None
        if cycle and seq.pc==caller+1:
            assert depth==0;outcome='return'
        if seq.pc==0x36c:
            state=(tuple(cpu.ram),cpu.q,seq.pc,seq.sp,tuple(seq.stack),depth,tuple(sorted(previous.items())),carry.previous)
            if state in seen:outcome='repeat';period=cycle-seen[state]
            else:seen[state]=cycle
        if outcome:
            return dict(ram=cpu.ram,q=cpu.q,cycles=cycle,trace=trace,sp=seq.sp,stack=seq.stack,depth=depth,
                pcs=pcs,y=ys,outcome=outcome,period=period,pc=seq.pc)
        pc=seq.pc;row=rows[pc]
        assert pc==caller or 0x366<=pc<=0x36f
        assert row['command'] in (0,1,2,3,4,5)
        assert (row['command']==4)==(pc==caller)
        before=cpu.ram[:];d=scenario['io']['read']['pc_sequences'].get(str(pc),[1])[0]
        ci=carry.resolve(row);result=cpu.step(row['i'],row['a'],row['b'],d,ci,0,0);carry.observe(result)
        condition=scenario['condition'];source=condition['sources'][row['select']]
        test=1 if unconditional_transfer(row,scenario) else int(bool(condition['value'] if source=='constant' else previous[source]))^condition['polarity'][row['select']]
        before_stack=dict(sp=seq.sp,depth=depth)
        if (row['command']==4 and test) or row['command']==5:depth+=1
        if row['command'] in (2,3):depth-=1
        assert 0<=depth<=2
        seq.step(row['command'],row['branch'],test)
        if pc!=caller:pcs.append(pc);ys.append(result['y'])
        if record:trace.append(dict(cycle=cycle,pc=pc,next_pc=seq.pc,alu=result,q=cpu.q,test=test,carry_in=ci,
            registers={str(i):v for i,v in enumerate(cpu.ram) if v!=before[i]},stack_before=before_stack,
            stack_after=dict(sp=seq.sp,depth=depth,values=seq.stack[:])))
        previous=result
    raise AssertionError('helper neither returned nor repeated')


def check(got,want):
    for key in ('ram','q','cycles','pcs','y','outcome','period'):assert got[key]==want[key],(key,got,want)


def verify_core(mapping,scenario,got,out):
    summary=execute(mapping,scenario,got['cycles'],mode='integrated',out=out,trace_limit=got['cycles'])
    assert summary['clean'] and summary['stack']['max_depth']==2 and summary['stack']['final_depth']==got['depth']
    for key in ('ram','q','sp','stack','pc'):assert summary['final_state'][key]==got[key]
    trace=load_trace(out);assert len(trace)==len(got['trace'])==got['cycles']
    for actual,local in zip(trace,got['trace']):
        for key,value in local.items():assert actual[key]==value,(key,actual,local)
    return summary['trace_digest']


def fixture(plane,a,b):
    ram=[(37*i+19)&255 for i in range(16)]
    if plane=='r0_c':ram[0]=a;c=b;d=127
    else:assert plane=='c_d';ram[0]=255;c=a;d=b
    q=a^b
    inputs={0x366:a^85,0x367:b^127,0x36b:a^255,0x36c:c,0x36d:d,0x36e:b^165,0x36f:a^51}
    return ram,q,inputs


def inspect_reset(trace,scenario):
    ram=scenario['initial']['ram'][:];q=scenario['initial']['q'];start=None;calls=[]
    for index,row in enumerate(trace):
        if row['pc']==0x366:start=(index,ram[:],q)
        for k,v in row['registers'].items():ram[int(k)]=v
        q=row['q']
        if row['pc']==0x36f:
            assert start is not None
            begin,old_ram,old_q=start;part=trace[begin:index+1]
            inputs={r['pc']:r['external_read']['value'] for r in part}
            s5=next(r['test'] for r in part if r['pc']==0x36a)
            want=prediction(old_ram,old_q,inputs,s5)
            assert want['outcome']=='return' and [r['pc'] for r in part]==want['pcs']
            assert [r['alu']['y'] for r in part]==want['y'] and (ram,q)==(want['ram'],want['q'])
            calls.append(dict(entry_cycle=part[0]['cycle'],return_cycle=part[-1]['cycle'],inputs=inputs,prediction=want));start=None
    assert start is None and len(calls)==1
    return calls


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/carry-helper-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'carry-helper-study.json');base_path=HERE/config['base']
    mapping,base=read(base_path/'mapping.json'),read(base_path/'scenario.json');rows=decode(mapping)
    counts=Counter();digest=hashlib.sha256();witnesses=[]
    for plane in ('r0_c','c_d'):
        for s5 in (0,1):
            for a in range(256):
                for b in range(256):
                    ram,q,inputs=fixture(plane,a,b);scenario=scenario_for(base,config,ram,q,inputs,s5)
                    selected=(a,b) in ((0,0),(0,255),(255,0),(255,255),(128,128))
                    got=probe(rows,scenario,record=selected);want=prediction(ram,q,inputs,s5);check(got,want)
                    counts[f'{plane}-{s5}-{got["outcome"]}']+=1
                    digest.update(json.dumps([plane,s5,a,b,want],sort_keys=True,separators=(',',':')).encode())
                    if selected:
                        name=f'{plane}-{s5}-{a:02x}-{b:02x}'
                        trace_digest=verify_core(mapping,scenario,got,args.out/name)
                        witnesses.append(dict(path=name,prediction=want,trace_digest=trace_digest))
            print(plane,s5,dict(counts),flush=True)
    reset_path=HERE/config['reset'];reset_mapping,reset=read(reset_path/'mapping.json'),read(reset_path/'scenario.json')
    result=execute(reset_mapping,reset,512,mode='integrated',out=args.out/'reset',trace_limit=512)
    assert result['clean']
    for name in ('mapping.json','scenario.json','summary.json','trace.jsonl','io.jsonl'):
        assert (reset_path/name).read_bytes()==(args.out/'reset'/name).read_bytes(),name
    calls=inspect_reset(load_trace(args.out/'reset'),reset)
    sources=[Path(__file__),HERE/'carry-helper-study.json',HERE/'execute.py',HERE/'common.py',HERE/'defined_condition_fit.py',
        HERE.parent/'model.py',base_path/'mapping.json',base_path/'scenario.json',
        *(reset_path/n for n in ('mapping.json','scenario.json','summary.json','trace.jsonl'))]
    save(args.out/'report.json',dict(configuration=config,counts=dict(counts),execution_sha256=digest.hexdigest(),witnesses=witnesses,
        reset_calls=calls,source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='q3 366 preparation writes are overwritten by the carry loop; returning 36F masks Q into R0. Constant local reads give either immediate return or exact period-three recurrence. Saved ROM zero-reply reset validates one complete real call; feedback ROM cycles remain a distinct study.'))


if __name__=='__main__':main()
