"""Explain q3 reset helpers 06F and 112 with actual call/return execution."""
import argparse
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path
from common import HERE,read,save,decode,unconditional_transfer
from execute import execute,CarryInput
from defined_condition_fit import load_trace
from model import Am2901,X8X02


def prediction(entry,ram,q,d):
    result=ram[:]
    if entry==0x06f:
        r=ram[9]
        result[0]=255-(r>>1) if r<128 else (r+1)>>1 if r<255 else 0
        result[2]=ram[8]
        return dict(ram=result,q=(q+d)&255,cycles=9 if 128<=r<=254 else 10)
    assert entry==0x112
    result[2]=(-ram[0])&255;result[4]=(q+d)&255
    return dict(ram=result,q=q,cycles=6)


def scenario_for(base,config,entry,ram,q,d):
    scenario=copy.deepcopy(base);helper=config['helpers'][str(entry)]
    scenario.update(name=f'local q3 helper {entry:03x} via actual caller',evidence=config['evidence'])
    scenario['initial']=dict(pc=helper['caller'],ram=ram[:],q=q)
    scenario['io']['read']=dict(mode='pc_sequence',value=1,table=[0],pc_sequences={str(helper['input_pc']):[d]},
        sequence_end='hold-last',status='stub',evidence=config['evidence'])
    return scenario


def probe(rows,scenario,helper,record=False):
    initial=scenario['initial'];cpu=Am2901(ram=initial['ram'][:],q=initial['q'],logic_flags=True)
    seq=X8X02(pc=initial['pc']);carry=CarryInput(scenario['inputs']['carry'])
    previous=None;trace=[];depth=0
    for cycle in range(12):
        if cycle and seq.pc==helper['caller']+1:
            assert depth==0
            return dict(ram=cpu.ram,q=cpu.q,cycles=cycle,trace=trace,sp=seq.sp,stack=seq.stack)
        pc=seq.pc;row=rows[pc]
        assert pc==helper['caller'] or helper['entry']<=pc<=helper['end']
        assert row['command'] in (0,1,3,4)
        assert (row['command']==4)==(pc==helper['caller'])
        before=cpu.ram[:];d=scenario['io']['read']['pc_sequences'].get(str(pc),[1])[0]
        ci=carry.resolve(row);result=cpu.step(row['i'],row['a'],row['b'],d,ci,0,0);carry.observe(result)
        condition=scenario['condition'];source=condition['sources'][row['select']]
        test=1 if unconditional_transfer(row,scenario) else int(bool(condition['value'] if source=='constant' else previous[source]))^condition['polarity'][row['select']]
        before_stack=dict(sp=seq.sp,depth=depth)
        if row['command']==4 and test:depth+=1
        if row['command']==3:depth-=1
        assert 0<=depth<=1
        seq.step(row['command'],row['branch'],test)
        if record:trace.append(dict(cycle=cycle,pc=pc,next_pc=seq.pc,alu=result,q=cpu.q,test=test,carry_in=ci,
            registers={str(i):v for i,v in enumerate(cpu.ram) if v!=before[i]},stack_before=before_stack,
            stack_after=dict(sp=seq.sp,depth=depth,values=seq.stack[:])))
        previous=result
    raise AssertionError('helper failed to return')


def verify_core(mapping,scenario,helper,got,out):
    result=execute(mapping,scenario,got['cycles'],mode='integrated',out=out,trace_limit=got['cycles'])
    assert result['clean'] and result['stack']['max_depth']==1 and result['stack']['final_depth']==0
    for key in ('ram','q','sp','stack'):assert result['final_state'][key]==got[key]
    assert result['final_state']['pc']==helper['caller']+1
    for actual,local in zip(load_trace(out),got['trace']):
        for key,value in local.items():assert actual[key]==value,(key,actual,local)
    return result['trace_digest']


def inspect_reset(trace,scenario):
    ram=scenario['initial']['ram'][:];q=scenario['initial']['q'];pending=None;calls=[]
    for row in trace:
        pc=row['pc']
        if pc in (0x06f,0x112):
            assert pending is None
            pending=dict(entry=pc,ram=ram[:],q=q,cycle=row['cycle'],d=None)
        if pending and pc in (0x076,0x115):pending['d']=row['external_read']['value']
        for k,v in row['registers'].items():ram[int(k)]=v
        q=row['q']
        if pending and pc in (0x077,0x116):
            want=prediction(pending['entry'],pending['ram'],pending['q'],pending['d'])
            assert (ram,q)==(want['ram'],want['q'])
            assert row['cycle']-pending['cycle']+1==want['cycles']-1
            calls.append(dict(entry=pending['entry'],entry_cycle=pending['cycle'],return_cycle=row['cycle'],
                              input=pending['d'],ram=ram[:],q=q))
            pending=None
    assert pending is None and [c['entry'] for c in calls]==[0x06f,0x112,0x112]
    return calls


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/reset-helpers-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'reset-helpers-study.json');base_path=HERE/config['base']
    mapping,base=read(base_path/'mapping.json'),read(base_path/'scenario.json');rows=decode(mapping)
    counts=Counter();digest=hashlib.sha256();witnesses=[]
    for entry,helper in ((int(k),v) for k,v in config['helpers'].items()):
        for plane in ('register_q','input_q'):
            for a in range(256):
                for q in range(256):
                    ram=[(37*i+19)&255 for i in range(16)];ram[8]=a^85
                    ram[9 if entry==0x06f else 0]=a if plane=='register_q' else 255
                    d=1 if plane=='register_q' else a
                    scenario=scenario_for(base,config,entry,ram,q,d)
                    selected=[entry,plane,a,q] in config['witnesses']
                    got=probe(rows,scenario,helper,record=selected);want=prediction(entry,ram,q,d)
                    assert all(got[k]==want[k] for k in ('ram','q','cycles'))
                    counts[f'{entry:03x}:{plane}']+=1
                    digest.update(json.dumps([entry,plane,a,q,got['ram'],got['q'],got['cycles']],separators=(',',':')).encode())
                    if selected:
                        name=f'{entry:03x}-{plane}-{a:02x}-{q:02x}'
                        trace_digest=verify_core(mapping,scenario,helper,got,args.out/name)
                        witnesses.append(dict(path=name,entry=entry,plane=plane,a=a,q=q,prediction=want,trace_digest=trace_digest))
            print(f'{entry:03x} {plane} verified',flush=True)
    result=execute(mapping,base,512,mode='integrated',out=args.out/'reset',trace_limit=512)
    assert result['clean']
    for name in ('mapping.json','scenario.json','summary.json','trace.jsonl','io.jsonl'):
        assert (args.out/'reset'/name).read_bytes()==(base_path/name).read_bytes(),name
    reset_calls=inspect_reset(load_trace(args.out/'reset'),base)
    sources=[Path(__file__),HERE/'reset-helpers-study.json',HERE/'execute.py',HERE/'common.py',
        HERE/'defined_condition_fit.py',HERE.parent/'model.py',*(base_path/n for n in ('mapping.json','scenario.json','summary.json','trace.jsonl'))]
    save(args.out/'report.json',dict(configuration=config,counts=dict(counts),execution_sha256=digest.hexdigest(),
        witnesses=witnesses,reset_calls=reset_calls,
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='q3 06F combines carry-selected half/difference preparation with Q+=D and R8 copy. 112 replaces R2 with -R0 and R4 with D+Q. Local calls use actual BSR/POP and arbitrary declared initial RAM; unchanged zero-reset replay verifies both helpers in context. Physical meanings of R8/R9 and external reads remain unresolved.'))


if __name__=='__main__':main()
