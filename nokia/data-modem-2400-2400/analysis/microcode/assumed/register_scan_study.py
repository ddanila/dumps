"""Characterize the register-difference scan reached through branch 302."""
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


def probe(rows,base,ram,q):
    cpu=Am2901(ram=ram[:],q=q,logic_flags=True)
    seq=X8X02(pc=0x319)
    carry=CarryInput(base['inputs']['carry'])
    previous=dict(zero=0,carry=0,sign=0,overflow=0)
    trace=[];seen={}
    while len(trace)<32:
        if seq.pc==0x07b:
            return dict(returned=True,pc=seq.pc,ram=cpu.ram,q=cpu.q,cycles=len(trace),period=None,trace=trace)
        if seq.pc==0x32c:
            key=json.dumps([seq.pc,seq.sp,seq.stack,cpu.ram,cpu.q,previous,carry.previous],sort_keys=True)
            if key in seen:
                return dict(returned=False,pc=seq.pc,ram=cpu.ram,q=cpu.q,cycles=len(trace),period=len(trace)-seen[key],trace=trace)
            seen[key]=len(trace)
        pc=seq.pc;row=rows[pc]
        result=cpu.step(row['i'],row['a'],row['b'],0x5a,carry.resolve(row),0,0)
        carry.observe(result)
        select=row['select'];source=base['condition']['sources'][select]
        value=base['condition']['value'] if source=='constant' else previous[source]
        test=1 if unconditional_transfer(row,base) else int(bool(value))^base['condition']['polarity'][select]
        if pc in range(0x31a,0x325) or pc in range(0x326,0x32a) or pc in range(0x32c,0x32f):
            assert result['f']==(ram[row['b']]-ram[0])&255
            assert result['carry']==int(ram[row['b']]>=ram[0])
        seq.step(row['command'],row['branch'],test)
        trace.append(dict(pc=pc,next_pc=seq.pc,alu=result,test=test))
        previous=result
    raise AssertionError('no exit or repeat')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/register-scan-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'register-scan-study.json');base=read(HERE/config['scenario'])
    assert base['condition']['flag_timing']=='previous'
    assert base['condition']['sources'][6]=='constant' and base['condition']['value']==base['condition']['polarity'][6]==0
    counts=Counter();digest=hashlib.sha256();witnesses=[];seen=set();reset_runs=[]
    for profile,path in config['mappings'].items():
        mapping=read(HERE/path);rows=decode(mapping)
        assert all(rows[p]['i']>>6==1 and rows[p]['i']&7 not in (5,6,7) for p in range(0x319,0x335))
        for a in range(256):
            for b in range(256):
                ram=config['initial_ram'][:];ram[0]=a;ram[15]=b;q=config['initial_q']
                got=probe(rows,base,ram,q);returned=b<a
                assert got['returned']==returned and got['ram']==ram and got['q']==q
                assert got['cycles']==(28 if returned else 25)
                assert got['period']==(None if returned else 3)
                counts[f'{profile}:'+('exit' if returned else 'repeat')]+=1
                digest.update(json.dumps([profile,a,b,got['cycles'],[e['alu']['y'] for e in got['trace']]],separators=(',',':')).encode())
                key=(profile,returned,a==b,a in (0,255))
                if key not in seen:
                    seen.add(key);scenario=copy.deepcopy(base);scenario['initial']=dict(pc=0x319,ram=ram,q=q)
                    out=args.out/f'local-{len(witnesses):02d}'
                    result=execute(mapping,scenario,got['cycles'],mode='integrated',out=out,trace_limit=got['cycles'])
                    assert result['clean'] and all(result['final_state'][k]==got[k] for k in ('pc','ram','q'))
                    trace=load_trace(out)
                    assert [(e['pc'],e['next_pc'],e['alu'],e['test']) for e in trace]==[(e['pc'],e['next_pc'],e['alu'],e['test']) for e in got['trace']]
                    witnesses.append(dict(profile=profile,a=a,b=b,observed=got,trace_digest=result['trace_digest']))
        with tempfile.TemporaryDirectory() as temporary:
            for d in range(256):
                scenario=copy.deepcopy(base);scenario['initial']=dict(pc=0,ram=[0]*16,q=0);scenario['dispatch']['value']=3
                scenario['io']['read']=dict(mode='pc_sequence',value=d,table=[0],pc_sequences={str(p):[d,0] for p in (0x117,0x106)},sequence_end='hold-last',status='stub',evidence=config['evidence'])
                out=args.out/f'{profile}-reset-{d:02x}' if d in config['reset_witnesses'] else Path(temporary)
                result=execute(mapping,scenario,256,mode='integrated',out=out,trace_limit=256)
                trace=load_trace(out);ram=[0]*16;entry=None;entry_q=None
                for e in trace:
                    if e['pc']==0x319 and entry is None:entry=ram[:];entry_q=e['q']
                    for register,value in e['registers'].items():ram[int(register)]=value
                    if entry is not None and 0x319<=e['pc']<=0x334:
                        assert ram==entry and e['q']==entry_q
                assert result['clean'] and entry is not None
                assert next(e for e in trace if e['pc']==0x302)['next_pc']==0x319
                assert entry[0]==(255 if profile=='q2' else 255-d) and entry[15]==0
                returned=entry[15]<entry[0]
                assert (result['final_state']['pc']==0x84)==returned
                assert not set(result['visited'])&{0x304,0x30b}
                reset_runs.append(dict(profile=profile,d=d,entry_ram=entry,entry_q=entry_q,exited=returned,final_state=result['final_state'],trace_digest=result['trace_digest']))
    sources=[Path(__file__),HERE/'register-scan-study.json',HERE/config['scenario'],HERE/'execute.py',HERE/'common.py',HERE.parent/'model.py']+[HERE/p for p in config['mappings'].values()]
    save(args.out/'report.json',dict(configuration=config,counts=dict(counts),witnesses=witnesses,reset_runs=reset_runs,execution_sha256=digest.hexdigest(),source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},interpretation='319–334 changes no RAM or Q and selects no external D. Under constant-zero select 6, its first two scans exit once; the final scan repeats iff R15>=R0 under previous carry. Reset index 3 exercises this path, including fitted_original D=FF repetition. Physical consumers of transient register differences are unknown.'))
    print(dict(counts),'witnesses',len(witnesses),'reset exits',sum(r['exited'] for r in reset_runs))


if __name__=='__main__':main()
