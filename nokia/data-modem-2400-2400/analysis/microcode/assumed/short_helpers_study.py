"""Read six q3 short helpers, preserving transient Y sequences as evidence."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from common import HERE,read,save,decode
from execute import execute
from defined_condition_fit import load_trace
from reset_helpers_study import scenario_for,probe,verify_core


def prediction(entry,ram,q,d):
    result=ram[:];a=ram[0];next_q=q
    if entry==0x04c:
        result[12]=ram[3];next_q=0
        y=[d,d,1&d,ram[3],0,ram[3],(2*ram[3])&255,a&ram[3]]
    elif entry==0x09a:
        result[2]=ram[1];y=[a,ram[1],(a+ram[5])&255,a]
    elif entry==0x131:
        y=[(ram[4]+ram[12])&255,a&ram[12]]
    elif entry==0x228:
        y=[(q-a-1)&255,(q-a)&255,(q-1)&255]
    else:
        assert entry in (0x238,0x240)
        result[2]=ram[4];next_q=a
        pair=[(a-1)&255,(a+int(a!=0))&255]
        y=([0,*pair,a,a,0,ram[4],a] if entry==0x238 else [0,a,a,*pair,0,ram[4],a])
    return dict(ram=result,q=next_q,y=y,cycles=len(y)+1)


def fixture(entry,a,b):
    ram=[(37*i+19)&255 for i in range(16)];ram[0]=a
    if entry==0x04c:ram[3]=a; q=a^b
    elif entry==0x09a:ram[1]=b; q=a^b
    elif entry==0x131:ram[12]=b;ram[4]=a^165;q=a^b
    elif entry==0x228:q=b
    else:ram[4]=b;q=a^b
    return ram,q,b


def inspect_reset(trace,scenario,config):
    ram=scenario['initial']['ram'][:];q=scenario['initial']['q'];pending=None;calls=[]
    helpers={int(k):v for k,v in config['helpers'].items()}
    for row in trace:
        pc=row['pc']
        if pc in helpers:
            assert pending is None
            want=prediction(pc,ram,q,row['external_read']['value'])
            pending=dict(entry=pc,cycle=row['cycle'],prediction=want,y=[])
        if pending:pending['y'].append(row['alu']['y'])
        for k,v in row['registers'].items():ram[int(k)]=v
        q=row['q']
        if pending and pc==helpers[pending['entry']]['end']:
            want=pending['prediction']
            assert (ram,q,pending['y'])==(want['ram'],want['q'],want['y'])
            calls.append(pending);pending=None
    assert pending is None
    # The unchanged zero-reset run waits before any of these helpers.
    assert not calls and {row['pc'] for row in trace[-32:]}=={0x127,0x128,0x129,0x12a}
    return calls


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/short-helpers-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'short-helpers-study.json');base_path=HERE/config['base']
    mapping,base=read(base_path/'mapping.json'),read(base_path/'scenario.json');rows=decode(mapping)
    counts=Counter();digest=hashlib.sha256();witnesses=[]
    for entry,helper in ((int(k),v) for k,v in config['helpers'].items()):
        for a in range(256):
            for b in range(256):
                ram,q,d=fixture(entry,a,b);scenario=scenario_for(base,config,entry,ram,q,d)
                got=probe(rows,scenario,helper,record=True);want=prediction(entry,ram,q,d)
                y=[t['alu']['y'] for t in got['trace'][1:]]
                assert all(got[k]==want[k] for k in ('ram','q','cycles')) and y==want['y']
                counts[f'{entry:03x}']+=1
                digest.update(json.dumps([entry,a,b,got['ram'],got['q'],y],separators=(',',':')).encode())
                if [entry,a,b] in config['witnesses']:
                    name=f'{entry:03x}-{a:02x}-{b:02x}'
                    trace_digest=verify_core(mapping,scenario,helper,got,args.out/name)
                    witnesses.append(dict(path=name,entry=entry,a=a,b=b,prediction=want,trace_digest=trace_digest))
        print(f'{entry:03x}: 65536 retained-state and Y-sequence checks',flush=True)
    result=execute(mapping,base,512,mode='integrated',out=args.out/'reset',trace_limit=512)
    assert result['clean']
    for name in ('mapping.json','scenario.json','summary.json','trace.jsonl','io.jsonl'):
        assert (args.out/'reset'/name).read_bytes()==(base_path/name).read_bytes(),name
    calls=inspect_reset(load_trace(args.out/'reset'),base,config)
    sources=[Path(__file__),HERE/'short-helpers-study.json',HERE/'reset_helpers_study.py',HERE/'execute.py',HERE/'common.py',
        HERE/'defined_condition_fit.py',HERE.parent/'model.py',*(base_path/n for n in ('mapping.json','scenario.json','summary.json','trace.jsonl'))]
    save(args.out/'report.json',dict(configuration=config,counts=dict(counts),execution_sha256=digest.hexdigest(),
        witnesses=witnesses,reset_calls=calls,
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='Six q3 short helpers have checked retained-state and transient Y contracts. 238/240 retain identical state but emit different carry-adjustment order. Local actual BSR/POP calls plus unchanged handler-0 reset replay; no physical Y consumer or output strobe is inferred.'))


if __name__=='__main__':main()
