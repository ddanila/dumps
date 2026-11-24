"""Explain q3 370 paired self-arithmetic, high-byte wait and input dispatch."""
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


def scenario_for(base,config,ram,q,index,d375,source='scenario'):
    scenario=copy.deepcopy(base)
    scenario.update(name='q3 paired self-arithmetic wait',evidence=config['evidence'])
    scenario['initial']=dict(pc=config['caller'],ram=ram[:],q=q)
    scenario['dispatch']['value']=index
    table=scenario['dispatch']['tables'][str(0x376)]
    table.update(config['table'],index_source=source,status='hypothesis',evidence=config['evidence'])
    scenario['io']['read']=dict(mode='pc_sequence',value=1,table=[0],pc_sequences={str(0x375):[d375]},
        sequence_end='hold-last',status='stub',evidence=config['evidence'])
    return scenario


def prediction(ram,q,index,d375):
    result=ram[:];result[1]=ram[0]
    u=ram[4]+256*ram[5];v=ram[6]+256*ram[7]
    first=(2*u)&65535 if index in (0,3) else 0
    second=(2*v)&65535 if index in (0,1) else 0
    output=[first&255,first>>8,second&255,second>>8]
    repeat=output[-1]!=0
    pcs=list(range(0x370,0x377))+list(range(0x379+4*index,0x37d+4*index))+[0x377]
    ys=[ram[0],*ram[4:8],d375,0,*output,ram[0]&q]
    if repeat:pcs*=2;ys*=2
    else:pcs.append(0x378);ys.append(0)
    return dict(ram=result,q=q,pcs=pcs,y=ys,cycles=len(pcs)+1,outcome='repeat' if repeat else 'return',
        period=12 if repeat else None,output=output)


def probe(rows,scenario,record=False):
    initial=scenario['initial'];caller=initial['pc']
    cpu=Am2901(ram=initial['ram'][:],q=initial['q'],logic_flags=True)
    seq=X8X02(pc=caller);carry=CarryInput(scenario['inputs']['carry'])
    previous=None;trace=[];depth=0;seen={};pcs=[];ys=[]
    for cycle in range(40):
        outcome=None;period=None
        if cycle and seq.pc==caller+1:
            assert depth==0;outcome='return'
        if seq.pc==0x370:
            state=(tuple(cpu.ram),cpu.q,seq.pc,seq.sp,tuple(seq.stack),depth,tuple(sorted(previous.items())),carry.previous)
            if state in seen:outcome='repeat';period=cycle-seen[state]
            else:seen[state]=cycle
        if outcome:
            return dict(ram=cpu.ram,q=cpu.q,cycles=cycle,trace=trace,sp=seq.sp,stack=seq.stack,depth=depth,
                pcs=pcs,y=ys,outcome=outcome,period=period,pc=seq.pc)
        pc=seq.pc;row=rows[pc]
        assert pc==caller or 0x370<=pc<=0x388
        assert row['command'] in (0,1,2,3,4,5)
        assert (row['command']==4)==(pc in (caller,0x376))
        before=cpu.ram[:];d=scenario['io']['read']['pc_sequences'].get(str(pc),[1])[0]
        ci=carry.resolve(row);result=cpu.step(row['i'],row['a'],row['b'],d,ci,0,0);carry.observe(result)
        condition=scenario['condition'];source=condition['sources'][row['select']]
        test=1 if unconditional_transfer(row,scenario) else int(bool(condition['value'] if source=='constant' else previous[source]))^condition['polarity'][row['select']]
        before_stack=dict(sp=seq.sp,depth=depth)
        if (row['command']==4 and test) or row['command']==5:depth+=1
        if row['command'] in (2,3):depth-=1
        assert 0<=depth<=3
        target=row['branch']
        if pc==0x376:
            table=scenario['dispatch']['tables'][str(pc)]
            index=previous['y'] if table.get('index_source')=='previous_y' else scenario['dispatch']['value']
            target=table['base']+(index%table['count'])*table['stride']
        seq.step(row['command'],target,test)
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
    assert summary['clean'] and summary['stack']['max_depth']==3 and summary['stack']['final_depth']==got['depth']
    for key in ('ram','q','sp','stack','pc'):assert summary['final_state'][key]==got[key]
    trace=load_trace(out);assert len(trace)==len(got['trace'])==got['cycles']
    for actual,local in zip(trace,got['trace']):
        for key,value in local.items():assert actual[key]==value,(key,actual,local)
    return summary['trace_digest']



def fixture(v):
    ram=[(37*i+19)&255 for i in range(16)];u=v^0xa55a
    ram[4:8]=[u&255,u>>8,v&255,v>>8]
    return ram,(v^(v>>8))&255


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/pair-wait-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'pair-wait-study.json');base_path=HERE/config['base']
    mapping,base=read(base_path/'mapping.json'),read(base_path/'scenario.json');rows=decode(mapping)
    counts=Counter();digest=hashlib.sha256();witnesses=[];input_controls=[]
    for index in range(4):
        for v in range(65536):
            ram,q=fixture(v);scenario=scenario_for(base,config,ram,q,index,0xa5)
            selected=v in (0,127,128,32768,32895,32896,65535)
            got=probe(rows,scenario,record=selected);want=prediction(ram,q,index,0xa5);check(got,want)
            counts[f'{index}-{got["outcome"]}']+=1
            digest.update(json.dumps([index,v,want],sort_keys=True,separators=(',',':')).encode())
            if selected:
                name=f'entry-{index}-{v:04x}';trace_digest=verify_core(mapping,scenario,got,args.out/name)
                witnesses.append(dict(path=name,prediction=want,trace_digest=trace_digest))
        print(index,dict(counts),flush=True)
    # Every byte at 375 selects the expected table row through preceding Y.
    for d in range(256):
        ram,q=fixture(0x1234);scenario=scenario_for(base,config,ram,q,0,d,'previous_y')
        got=probe(rows,scenario,record=True);want=prediction(ram,q,d%4,d);check(got,want)
        name=f'input-{d:02x}'
        # Keep only the four boundary input traces; all 256 use the main core.
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            out=args.out/name if d in (0,1,254,255) else Path(tmp)
            trace_digest=verify_core(mapping,scenario,got,out)
        input_controls.append(dict(input=d,index=d%4,outcome=got['outcome'],trace_digest=trace_digest,
            path=name if d in (0,1,254,255) else None))
    sources=[Path(__file__),HERE/'pair-wait-study.json',HERE/'execute.py',HERE/'common.py',HERE/'defined_condition_fit.py',
        HERE.parent/'model.py',base_path/'mapping.json',base_path/'scenario.json']
    save(args.out/'report.json',dict(configuration=config,counts=dict(counts),execution_sha256=digest.hexdigest(),witnesses=witnesses,
        input_controls=input_controls,source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='q3 370 preserves both input words and Q, copies R0 to R1, and exposes doubled or self-subtracted words. Previous final high byte controls return; unchanged inputs give exact period-12 recurrence. Preceding-Y dispatch can use D375; no physical port or reset coverage inferred.'))


if __name__=='__main__':main()
