"""Compare current Y, preceding Y, Q and scenario indexing at branch site 109."""
import argparse
import copy
import hashlib
import json
import tempfile
from collections import Counter
from pathlib import Path
from common import HERE, read, save
from defined_condition_fit import load_trace
from execute import execute


def inspect(trace):
    ram=[0]*16;q=0;previous_y=0;dispatch=[];seen={};repeat=None
    for t in trace:
        if t['pc']==0x109:
            dispatch.append(dict(cycle=t['cycle'],ram_before=ram[:],q_before=q,previous_y=previous_y,
                                 current_y=t['alu']['y'],carry_in=t['carry_in'],index=t['dispatch_input'],entry=t['dispatch_entry'],target=t['next_pc']))
        for i,v in t['registers'].items():ram[int(i)]=v
        q=t['q'];previous_y=t['alu']['y']
        key=json.dumps([t['next_pc'],ram,q,t['alu'],t['stack_after']],sort_keys=True)
        if key in seen and repeat is None:
            first=seen[key];repeat=dict(first_cycle=first,second_cycle=t['cycle'],period=t['cycle']-first,
                                       next_pc=t['next_pc'],ram=ram[:],q=q,stack=t['stack_after'])
        seen[key]=t['cycle']
    return dict(dispatch=dispatch,repeat=repeat)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/dispatch109-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'dispatch109-study.json');root=HERE/config['base']
    mapping=read(root/'mapping.json');base=read(root/'scenario.json');comparisons=[]
    assert base['dispatch']['mode']=='constant'
    with tempfile.TemporaryDirectory() as temporary:
        for source in config['sources']:
            runs=[];reached=set();targets=Counter();outcomes=Counter()
            for d in range(256):
                s=copy.deepcopy(base);s['initial']=dict(pc=0,ram=[0]*16,q=0)
                s['branch_tables'][str(config['site'])]['index_source']=source
                s['branch_tables'][str(config['site'])]['evidence']=config['evidence']
                s['dispatch']['initial_y']=config['initial_y']
                s['io']['read']=dict(mode='constant',value=d,table=[0],status='stub',evidence=config['evidence'])
                out=args.out/f'{source}-d{d:02x}' if d in config['witness_values'] else Path(temporary)
                result=execute(mapping,s,config['cycles'],mode='integrated',out=out,trace_limit=config['cycles'])
                assert result['clean']
                observed=inspect(load_trace(out));first=observed['dispatch'][0]
                assert first['ram_before'][0]==255-d and first['q_before']==first['previous_y']==0
                assert first['current_y']==(d+1)&255 and first['carry_in']==1
                index={'y':(d+1)&255,'q':0,'previous_y':0,'scenario':base['dispatch']['value']}[source]
                assert first['index']==index and first['entry']==index%8 and first['target']==0x10a+index%8
                reached.update(result['visited']);targets[first['entry']]+=1
                repeat=observed['repeat'];outcomes[f"{repeat['next_pc']:03x}/{repeat['period']}" if repeat else 'no-repeat-observed']+=1
                runs.append(dict(d=d,clean=result['clean'],observed=observed,final_pc=result['final_state']['pc'],
                                 visited=result['visited'],trace_digest=result['trace_digest']))
            comparisons.append(dict(source=source,runs=runs,visited=sorted(reached),first_entry_counts=dict(targets),repeat_counts=dict(outcomes)))
    sources=[Path(__file__),HERE/'dispatch109-study.json',HERE/'execute.py',HERE/'common.py',HERE.parent/'model.py',root/'mapping.json',root/'scenario.json']
    save(args.out/'report.json',dict(configuration=config,comparisons=comparisons,
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='At first reset encounter of 109, current Y=D+1 modulo 256 while Q and previous Y are zero. Y indexing exercises all eight branch entries. All sources remain hypotheses; coverage or termination does not identify physical wiring.'))
    for r in comparisons:print(r['source'],len(r['visited']),r['first_entry_counts'],r['repeat_counts'])


if __name__=='__main__':main()
