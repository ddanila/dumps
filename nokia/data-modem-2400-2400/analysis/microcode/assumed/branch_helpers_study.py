"""Explain q3 conditional helper paths and distinguish retained state from Y."""
import argparse
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path
from common import HERE,read,save,decode,unconditional_transfer
from execute import CarryInput
from model import Am2901,X8X02
from reset_helpers_study import verify_core


def scenario_for(base,config,entry,ram,q,inputs,s5,s6):
    scenario=copy.deepcopy(base);helper=config['helpers'][str(entry)]
    scenario.update(name=f'q3 conditional helper {entry:03x}',evidence=config['evidence'])
    scenario['initial']=dict(pc=helper['caller'],ram=ram[:],q=q)
    for select,value in ((5,s5),(6,s6)):
        scenario['condition']['sources'][select]='constant'
        scenario['condition']['polarity'][select]=value
    assert scenario['condition']['value']==0
    scenario['condition']['evidence']=config['evidence']
    scenario['io']['read']=dict(mode='pc_sequence',value=1,table=[0],pc_sequences={str(k):[v] for k,v in inputs.items()},
        sequence_end='hold-last',status='stub',evidence=config['evidence'])
    return scenario


def prediction(entry,ram,q,inputs,s5,s6):
    result=ram[:];next_q=q;pcs=[];ys=[];a=ram[0]
    def d(pc):return inputs.get(pc,1)
    def emit(pc,y):pcs.append(pc);ys.append(y&255)
    if entry==0x270:
        v=d(0x271);result[2]=ram[1];next_q=v
        for pc,y in [(0x270,d(0x270)+q),(0x271,v),(0x272,0),(0x274,a),
            (0x275,(~d(0x275))&v),(0x276,d(0x276)+v),(0x277,ram[1]),
            (0x278,~(a^ram[7])),(0x27b,d(0x27b)+v),(0x27c,a+ram[3]),(0x27d,0)]:emit(pc,y)
        if a+ram[3]>=256:result[0]=v;emit(0x27e,v)
        emit(0x27f,ram[1]+ram[3])
    elif entry==0x335:
        result[4]=d(0x336)
        for pc,y in [(0x335,a),(0x336,result[4]),(0x337,a-q)]:emit(pc,y)
        if not s5:
            result[12]=(d(0x338)+q)&255;result[0]=d(0x339)&q
            emit(0x338,result[12]);emit(0x339,result[0])
        emit(0x33a,q);emit(0x33b,0);emit(0x33c,ram[15]-result[0]-1)
        if s6:emit(0x340,0)
        else:
            next_q=q^255;emit(0x33d,0);emit(0x33e,next_q);emit(0x33f,result[0])
    else:
        assert entry==0x357
        result[0]=ram[1];total=d(0x359)+q;result[4]=total&255
        high=d(0x35a)+q+int(total>=256)
        for pc,y in [(0x357,ram[1]),(0x358,ram[15]),(0x359,total),(0x35a,high),
            (0x35b,d(0x35b)+int(high>=256)),(0x35c,ram[1]|q)]:emit(pc,y)
        if s5:emit(0x360,ram[12]+ram[2])
        else:
            emit(0x35d,0)
            if ram[1]|q==255:emit(0x35f,ram[12]+ram[1])
            else:emit(0x35e,ram[12]+ram[3])
    return dict(ram=result,q=next_q,pcs=pcs,y=ys,cycles=len(pcs)+1)


def fixture(entry,a,b):
    ram=[(37*i+19)&255 for i in range(16)];q=b
    if entry==0x270:
        ram[0]=a;ram[3]=b;q=a^165
        inputs={0x270:b^127,0x271:a^b,0x275:a,0x276:b,0x27b:a^85}
    elif entry==0x335:
        ram[0]=a^55
        inputs={0x336:b^127,0x338:a,0x339:a^85}
    else:
        ram[1]=a
        inputs={0x359:a^85,0x35a:a^127,0x35b:a^255}
    return ram,q,inputs


def probe(rows,scenario,helper,record=False):
    initial=scenario['initial'];cpu=Am2901(ram=initial['ram'][:],q=initial['q'],logic_flags=True)
    seq=X8X02(pc=initial['pc']);carry=CarryInput(scenario['inputs']['carry'])
    previous=None;trace=[];depth=0
    for cycle in range(24):
        if cycle and seq.pc==helper['caller']+1:
            assert depth==0
            return dict(ram=cpu.ram,q=cpu.q,cycles=cycle,trace=trace,sp=seq.sp,stack=seq.stack)
        pc=seq.pc;row=rows[pc]
        assert pc==helper['caller'] or helper['entry']<=pc<=helper['end']
        assert row['command'] in (0,1,3,4,6)
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



def check(got,want):
    assert all(got[k]==want[k] for k in ('ram','q','cycles'))
    assert [r['pc'] for r in got['trace'][1:]]==want['pcs']
    assert [r['alu']['y'] for r in got['trace'][1:]]==want['y']


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/branch-helpers-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'branch-helpers-study.json');base_path=HERE/config['base']
    mapping,base=read(base_path/'mapping.json'),read(base_path/'scenario.json');rows=decode(mapping)
    counts=Counter();paths=Counter();digest=hashlib.sha256();witnesses=[]
    for key,helper in config['helpers'].items():
        entry=int(key)
        policies=[(1,0)] if entry==0x270 else [(s5,s6) for s5 in (0,1) for s6 in ((0,1) if entry==0x335 else (0,))]
        for s5,s6 in policies:
            for a in range(256):
                for b in range(256):
                    ram,q,inputs=fixture(entry,a,b);scenario=scenario_for(base,config,entry,ram,q,inputs,s5,s6)
                    got=probe(rows,scenario,helper,record=True);want=prediction(entry,ram,q,inputs,s5,s6);check(got,want)
                    counts[f'{entry:03x}-{s5}{s6}']+=1
                    path=','.join(f'{pc:03x}' for pc in want['pcs']);paths[path]+=1
                    digest.update(json.dumps([entry,s5,s6,a,b,want],sort_keys=True,separators=(',',':')).encode())
                    if (a,b) in ((0,0),(0,255),(255,0),(255,255)):
                        name=f'{entry:03x}-{s5}{s6}-{a:02x}-{b:02x}'
                        trace_digest=verify_core(mapping,scenario,helper,got,args.out/name)
                        witnesses.append(dict(path=name,entry=entry,a=a,b=b,s5=s5,s6=s6,prediction=want,trace_digest=trace_digest))
            print(f'{entry:03x} selectors {s5}/{s6}: 65536 complete path and state checks',flush=True)
    sources=[Path(__file__),HERE/'branch-helpers-study.json',HERE/'reset_helpers_study.py',HERE/'execute.py',HERE/'common.py',
        HERE/'defined_condition_fit.py',HERE.parent/'model.py',base_path/'mapping.json',base_path/'scenario.json']
    save(args.out/'report.json',dict(configuration=config,counts=dict(counts),paths=dict(paths),execution_sha256=digest.hexdigest(),
        witnesses=witnesses,source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='Local actual-call q3 contracts across input/register planes and explicit constant selector policies. No reset reachability or physical bus consumer is claimed.'))


if __name__=='__main__':main()
