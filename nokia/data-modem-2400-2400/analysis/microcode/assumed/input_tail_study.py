"""Read q3 2EC through both comparison paths and its actual nested return tail."""
import argparse
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path
from common import HERE,read,save,decode,unconditional_transfer,table_targets
from execute import CarryInput,execute
from model import Am2901,X8X02
from defined_condition_fit import load_trace


def scenario_for(base,config,ram,q,inputs,s1):
    scenario=copy.deepcopy(base)
    scenario.update(name='q3 input preparation and comparison tail',evidence=config['evidence'])
    scenario['initial']=dict(pc=config['caller'],ram=ram[:],q=q)
    scenario['condition']['sources'][1]='constant';scenario['condition']['polarity'][1]=s1
    assert scenario['condition']['value']==0
    scenario['condition']['evidence']=config['evidence']
    scenario['dispatch']['value']=config['dispatch_index']
    assert table_targets(scenario['dispatch']['tables'][str(0x21f)])[config['dispatch_index']]==0x224
    scenario['io']['read']=dict(mode='pc_sequence',value=1,table=[0],pc_sequences={str(k):[v] for k,v in inputs.items()},
        sequence_end='hold-last',status='stub',evidence=config['evidence'])
    return scenario


def prediction(ram,q,inputs,s1):
    def d(pc):return inputs.get(pc,1)
    result=ram[:];a=ram[0];z=(q+d(0x2ef))&255
    result[4]=(d(0x2ec)+1)&255;result[3]=(a+int(d(0x2f1)+z>=256))&255
    result[15]=d(0x2f0)^z;result[5]=(ram[5]-a-1)&255;result[2]=ram[1]
    next_q=d(0x225);pcs=[];ys=[]
    def emit(pc,y):pcs.append(pc);ys.append(y&255)
    for pc,y in [(0x2ec,d(0x2ec)),(0x2ed,d(0x2ed)+q+1),(0x2ee,~ram[3]),(0x2ef,z),
        (0x2f0,result[15]),(0x2f1,d(0x2f1)+z),(0x2f2,result[3]),(0x2f3,d(0x2f3)&z),
        (0x2f4,a),(0x2f5,a-ram[7]-1),(0x2f6,a-ram[7]-1+int(a>ram[7]))]:emit(pc,y)
    tail_q=d(0x2f3)&z
    if a>ram[7]:route='comparison'
    else:
        tail_q=d(0x2f7)
        for pc,y in [(0x2f7,tail_q),(0x2f8,0),(0x2f9,a),(0x2fa,a-tail_q)]:emit(pc,y)
        if s1:route='selector'
        else:
            route='reload-mask'
            emit(0x2fb,a-tail_q-1+int(a>=tail_q));emit(0x2fc,~(a^tail_q))
            tail_q=d(0x2e0)&d(0x2e1)
            for pc,y in [(0x2e0,d(0x2e0)),(0x2e1,tail_q),(0x2e2,a+ram[5]),(0x2e3,0),(0x2e4,a-tail_q-1)]:emit(pc,y)
    for pc,y in [(0x3bb,result[5]),(0x3bc,~(a^tail_q)),(0x2fd,result[3]-tail_q-1),(0x2fe,a&tail_q),
        (0x21a,result[4]),(0x21b,d(0x21b)-1),(0x21c,ram[1]),(0x21d,2*result[4]),(0x21e,tail_q),
        (0x21f,0),(0x224,result[15]-a),(0x225,next_q),(0x226,0),(0x227,next_q),(0x220,0),(0x2ff,0)]:emit(pc,y)
    return dict(ram=result,q=next_q,pcs=pcs,y=ys,cycles=len(pcs)+1,route=route,tail_q=tail_q)


def probe(rows,scenario,record=False):
    caller=scenario["initial"]["pc"]
    initial=scenario['initial'];cpu=Am2901(ram=initial['ram'][:],q=initial['q'],logic_flags=True)
    seq=X8X02(pc=initial['pc']);carry=CarryInput(scenario['inputs']['carry'])
    previous=None;trace=[];depth=0;pcs=[];ys=[]
    for cycle in range(64):
        if cycle and seq.pc==caller+1:
            assert depth==0
            return dict(ram=cpu.ram,q=cpu.q,cycles=cycle,trace=trace,sp=seq.sp,stack=seq.stack,pcs=pcs,y=ys)
        pc=seq.pc;row=rows[pc]
        assert pc==caller or 0x2e0<=pc<=0x2e4 or 0x2ec<=pc<=0x2ff or pc in (0x3bb,0x3bc) or 0x21a<=pc<=0x220 or 0x224<=pc<=0x227
        assert row['command'] in (0,1,3,4,6)
        assert (row['command']==4)==(pc in (caller,0x2fe,0x21f))
        before=cpu.ram[:];d=scenario['io']['read']['pc_sequences'].get(str(pc),[1])[0]
        ci=carry.resolve(row);result=cpu.step(row['i'],row['a'],row['b'],d,ci,0,0);carry.observe(result)
        condition=scenario['condition'];source=condition['sources'][row['select']]
        test=1 if unconditional_transfer(row,scenario) else int(bool(condition['value'] if source=='constant' else previous[source]))^condition['polarity'][row['select']]
        before_stack=dict(sp=seq.sp,depth=depth)
        if row['command']==4 and test:depth+=1
        if row['command']==3:depth-=1
        assert 0<=depth<=3
        target=table_targets(scenario['dispatch']['tables'][str(pc)])[scenario['dispatch']['value']] if pc==0x21f else row['branch']
        seq.step(row['command'],target,test)
        if pc!=caller:pcs.append(pc);ys.append(result['y'])
        if record:trace.append(dict(cycle=cycle,pc=pc,next_pc=seq.pc,alu=result,q=cpu.q,test=test,carry_in=ci,
            registers={str(i):v for i,v in enumerate(cpu.ram) if v!=before[i]},stack_before=before_stack,
            stack_after=dict(sp=seq.sp,depth=depth,values=seq.stack[:])))
        previous=result
    raise AssertionError('helper failed to return')




def check(got,want):
    for key in ('ram','q','cycles','pcs','y'):assert got[key]==want[key],(key,got,want)


def verify_core(mapping,scenario,got,out):
    summary=execute(mapping,scenario,got['cycles'],mode='integrated',out=out,trace_limit=got['cycles'])
    assert summary['clean'] and summary['stack']['max_depth']==3 and summary['stack']['final_depth']==0
    for key in ('ram','q','sp','stack'):assert summary['final_state'][key]==got[key]
    assert summary['final_state']['pc']==scenario['initial']['pc']+1
    trace=load_trace(out);assert len(trace)==len(got['trace'])==got['cycles']
    for actual,local in zip(trace,got['trace']):
        for key,value in local.items():assert actual[key]==value,(key,actual,local)
    return summary['trace_digest']


def fixture(plane,a,b):
    ram=[(37*i+19)&255 for i in range(16)]
    if plane=='comparison':ram[0]=a;ram[7]=b;q=77;entry=b^165
    else:assert plane=='input_sum';ram[0]=128;ram[7]=127+(a&1);q=a;entry=b
    inputs={0x2ec:a,0x2ef:entry,0x2f0:b^85,0x2f1:a^b,0x2f3:a^127,0x2f7:b,0x2e0:a,0x2e1:b,0x225:a^b}
    return ram,q,inputs


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/input-tail-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'input-tail-study.json');base_path=HERE/config['base']
    mapping,base=read(base_path/'mapping.json'),read(base_path/'scenario.json');rows=decode(mapping)
    counts=Counter();digest=hashlib.sha256();witnesses=[]
    for plane in ('comparison','input_sum'):
        for s1 in (0,1):
            for a in range(256):
                for b in range(256):
                    ram,q,inputs=fixture(plane,a,b);scenario=scenario_for(base,config,ram,q,inputs,s1)
                    selected=(a,b) in ((0,0),(0,255),(255,0),(255,255),(128,128))
                    got=probe(rows,scenario,record=selected);want=prediction(ram,q,inputs,s1);check(got,want)
                    counts[f'{plane}-{s1}-{want["route"]}']+=1
                    digest.update(json.dumps([plane,s1,a,b,want],sort_keys=True,separators=(',',':')).encode())
                    if selected:
                        name=f'{plane}-{s1}-{a:02x}-{b:02x}';trace_digest=verify_core(mapping,scenario,got,args.out/name)
                        witnesses.append(dict(path=name,prediction=want,trace_digest=trace_digest))
            print(plane,s1,dict(counts),flush=True)
    sources=[Path(__file__),HERE/'input-tail-study.json',HERE/'execute.py',HERE/'common.py',HERE/'defined_condition_fit.py',
        HERE.parent/'model.py',base_path/'mapping.json',base_path/'scenario.json']
    save(args.out/'report.json',dict(configuration=config,counts=dict(counts),execution_sha256=digest.hexdigest(),witnesses=witnesses,
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='q3 2EC input preparation has comparison, constant-selector and reload-mask routes to a common actual nested return. Pre-tail Q differs transiently; fixed 21F entry 224 reloads Q. Local calls do not establish reset reachability or physical input semantics.'))


if __name__=='__main__':main()
