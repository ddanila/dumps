"""Characterize the idempotent Q-mask loops and their flag-timing alternatives."""
import argparse
import copy
import hashlib
import json
import tempfile
from collections import Counter
from pathlib import Path
from common import HERE, decode, read, save, unconditional_transfer
from execute import CarryInput, execute
from defined_condition_fit import load_trace
from model import Am2901, X8X02


def prediction(mask,q,addend,wrapped,timing):
    supplied=(q+addend)&255 if wrapped else q
    masked=supplied&mask
    equal=masked==mask
    done=equal if timing=='previous' else ((masked+int(equal))&255)==0
    return dict(masked=masked,returned=done,q=(masked+addend)&255 if done and wrapped else masked)


def probe(rows,base,ram,q,wrapped,timing):
    entry=0x11b if wrapped else 0x11d;stop=entry+1
    cpu=Am2901(ram=ram[:],q=q,logic_flags=True);seq=X8X02(pc=entry)
    carry=CarryInput(base['inputs']['carry']);previous=dict(zero=0,carry=0,sign=0,overflow=0)
    seen={};trace=[]
    for cycle in range(32):
        key=json.dumps([seq.pc,seq.sp,seq.stack,cpu.ram,cpu.q,previous,carry.previous],sort_keys=True)
        if seq.pc in (0x127,0x12c):
            if key in seen:return dict(returned=False,pc=seq.pc,q=cpu.q,ram=cpu.ram,cycles=cycle,period=cycle-seen[key],trace=trace)
            seen[key]=cycle
        row=rows[seq.pc];pc=seq.pc
        result=cpu.step(row['i'],row['a'],row['b'],0x5a,carry.resolve(row),0,0);carry.observe(result)
        if unconditional_transfer(row,base):test=1
        else:
            select=row['select'];source=base['condition']['sources'][select]
            flags=previous if timing=='previous' else result
            value=base['condition']['value'] if source=='constant' else flags[source]
            test=int(bool(value))^base['condition']['polarity'][select]
        trace.append(dict(pc=pc,q=cpu.q,ram2=cpu.ram[2],alu=result,test=test))
        seq.step(row['command'],row['branch'],test);previous=result
        if seq.pc==stop:return dict(returned=True,pc=seq.pc,q=cpu.q,ram=cpu.ram,cycles=cycle+1,trace=trace)
    raise ValueError('no return or exact repetition')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/mask-loop-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'mask-loop-study.json');root=HERE/config['base']
    mapping=read(root/'mapping.json');base=read(root/'scenario.json');rows=decode(mapping)
    assert all(rows[p]['i']&7 not in (5,6,7) for p in range(0x126,0x131))
    counts=Counter();digest=hashlib.sha256();witnesses=[];seen=set()
    for wrapped in (False,True):
        for timing in ('previous','current'):
            for mask in range(256):
                for q in range(256):
                    ram=config['initial_ram'][:];ram[0]=mask
                    want=prediction(mask,q,ram[10],wrapped,timing)
                    got=probe(rows,base,ram,q,wrapped,timing)
                    final_ram=ram[:];final_ram[2]=ram[1]
                    assert got['returned']==want['returned'] and got['q']==want['q'] and got['ram']==final_ram,(mask,q,wrapped,timing,want,got)
                    if not got['returned']:assert got['period']==4
                    counts[f'{wrapped}:{timing}:'+('return' if got['returned'] else 'repeat')]+=1
                    digest.update(json.dumps([wrapped,timing,mask,q,got['pc'],got['cycles'],got['q'],got['ram']],separators=(',',':')).encode())
                    key=(wrapped,timing,got['returned'],mask in (0,255))
                    if key not in seen:
                        seen.add(key);s=copy.deepcopy(base);s['initial']=dict(pc=0x11b if wrapped else 0x11d,ram=ram,q=q)
                        s['condition']['flag_timing']=timing
                        s['io']['read']=dict(mode='constant',value=0x5a,table=[0],status='stub',evidence=config['evidence'])
                        out=args.out/f'witness-{len(witnesses):02d}'
                        run=execute(mapping,s,got['cycles'],mode='integrated',out=out,trace_limit=got['cycles'])
                        assert run['clean'] and run['final_state']['pc']==got['pc'] and run['final_state']['ram']==got['ram'] and run['final_state']['q']==got['q']
                        witnesses.append(dict(mask=mask,q=q,wrapped=wrapped,timing=timing,expected=want,observed=got,trace_digest=run['trace_digest']))
    reset_runs=[]
    with tempfile.TemporaryDirectory() as temporary:
        for d in config['reset_values']:
            s=copy.deepcopy(base);s['initial']=dict(pc=0,ram=[0]*16,q=0)
            s['branch_tables']['265']['index_source']='y'
            s['io']['read']=dict(mode='constant',value=d,table=[0],status='stub',evidence=config['evidence'])
            out=args.out/f'reset-d{d:02x}' if d in config['reset_witnesses'] else Path(temporary)
            run=execute(mapping,s,config['reset_cycles'],mode='integrated',out=out,trace_limit=config['reset_cycles'])
            trace=load_trace(out);ram=[0]*16;q=0;writer=None;entry=None;loop=[]
            for t in trace:
                if t['pc']==0x126 and entry is None:entry=dict(cycle=t['cycle'],ram=ram[:],q=q,writer=writer)
                if entry is not None and t['pc'] in (0x127,0x128,0x129,0x12a) and len(loop)<4:loop.append(t)
                for i,v in t['registers'].items():ram[int(i)]=v
                op=rows[t['pc']]
                if op['i']>>6>=2 and op['b']==0:writer=dict(pc=t['pc'],cycle=t['cycle'])
                q=t['q']
            assert run['clean'] and entry['ram'][0]==255-d and entry['ram'][10]==entry['q']==0
            assert entry['writer']['pc']==0x74 and loop[-1]['next_pc']==(0x12b if d==255 else 0x127)
            assert loop[2]['alu']['f']==(d+1)&255
            returned=any(t['pc']==0x12b for t in trace)
            assert returned==(d==255)
            reset_runs.append(dict(d=d,entry=entry,loop=loop,returned=returned,trace_digest=run['trace_digest']))
    sources=[Path(__file__),HERE/'mask-loop-study.json',HERE/'execute.py',HERE/'common.py',HERE.parent/'model.py',root/'mapping.json',root/'scenario.json']
    save(args.out/'report.json',dict(configuration=config,counts=dict(counts),reset_runs=reset_runs,witnesses=witnesses,execution_sha256=digest.hexdigest(),
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='Mask loops use no external D operand. Under previous flags they return iff masked Q equals R0; otherwise exact four-instruction repetition. Current timing selects a different predicate. Caller 126 adds R10 before and after the loop.'))
    print(dict(counts),'witnesses',len(witnesses))


if __name__=='__main__':main()
