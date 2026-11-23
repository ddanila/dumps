"""Recover shift-wrapper preconditions along seeded reset dispatch paths."""
import argparse
import copy
import hashlib
import json
import tempfile
from collections import Counter
from pathlib import Path
from common import HERE, decode, read, save
from defined_condition_fit import load_trace
from drain_caller_study import expected
from execute import execute


def inspect(trace,rows):
    ram=[0]*16;q=0;writers={};events=[];dispatch=[];seen={};repeat=None;stage='first-right';returned=False
    watch={0x74,0x106,0x107,0x24f,0x150,0x157,0x248,0x249,0x24b,0x24d,0x24e}
    for t in trace:
        pc=t['pc']
        if pc in watch:
            events.append(dict(pc=pc,cycle=t['cycle'],ram_before=ram[:],q_before=q,
                               writers={str(i):writers.get(i) for i in (0,2,7,12,13)},carry_in=t['carry_in'],alu=t['alu']))
        if t['dispatch_entry'] is not None:dispatch.append(dict(pc=pc,cycle=t['cycle'],entry=t['dispatch_entry'],target=t['next_pc']))
        if pc==0x24b:stage='second-right'
        if pc==0x24d:stage='left'
        if pc==0x24e:returned=True
        for i,v in t['registers'].items():ram[int(i)]=v
        if rows[pc]['i']>>6>=2:writers[rows[pc]['b']]=dict(pc=pc,cycle=t['cycle'])
        q=t['q']
        if not returned and t['next_pc'] in (0x187,0x298):
            key=json.dumps([t['next_pc'],ram,q,t['alu'],t['stack_after']],sort_keys=True)
            if key in seen and repeat is None:
                start=seen[key]
                interval=[x for x in trace if start<x['cycle']<=t['cycle']]
                assert all(x['dispatch_entry'] is None for x in interval)
                repeat=dict(stage=stage,first_cycle=start,second_cycle=t['cycle'],period=t['cycle']-start,
                            next_pc=t['next_pc'],ram=ram[:],q=q,stack=t['stack_after'])
            seen[key]=t['cycle']
    return dict(events=events,dispatch=dispatch,returned=returned,repeat=repeat)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/drain-reset-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'drain-reset-study.json');root=HERE/config['base']
    mapping=read(root/'mapping.json');base=read(root/'scenario.json');rows=decode(mapping)
    counts=Counter();runs=[]
    with tempfile.TemporaryDirectory() as temporary:
        for seed in config['seeds']:
            for d in range(256):
                s=copy.deepcopy(base);s['dispatch']['mode']='random';s['initial']=dict(pc=0,ram=[0]*16,q=0)
                s['io']['read']=dict(mode='constant',value=d,table=[0],status='stub',evidence=config['evidence'])
                out=args.out/f'seed{seed}-d{d:02x}' if d in config['witness_values'] else Path(temporary)
                run=execute(mapping,s,config['cycles'],seed,'integrated',out,config['cycles'])
                assert run['clean']
                observed=inspect(load_trace(out),rows)
                events=observed['events'];first=lambda pc:next(e for e in events if e['pc']==pc)
                complement=first(0x74);load=first(0x107);call=first(0x150)
                assert complement['alu']['f']==255-d
                assert load['ram_before'][0]==255-d and load['alu']['f']==255
                assert load['writers']['0']['pc']==0x74
                assert call['ram_before'][7]==255 and call['writers']['7']['pc']==0x107
                assert call['q_before']==d and call['ram_before'][0]==d and call['ram_before'][12:14]==[0,0]
                assert call['writers']['0']['pc']==0x14c
                assert first(0x24f)['alu']['f']==d
                assert observed['dispatch'][0]['pc']==0x109 and observed['dispatch'][0]['entry']==1
                want=expected(d,d,255,0)
                assert observed['returned']==want['returned']
                if not want['returned']:
                    assert observed['repeat'] and observed['repeat']['stage']==want['stage']
                else:assert run['final_state']['pc']==0x84
                counts[f'{seed}:{want["stage"]}']+=1
                runs.append(dict(seed=seed,d=d,expected=want,observed=observed,final_pc=run['final_state']['pc'],trace_digest=run['trace_digest']))
    release_runs=[]
    for seed in config['seeds']:
        for d in config['release_values']:
            s=copy.deepcopy(base);s['dispatch']['mode']='random';s['initial']=dict(pc=0,ram=[0]*16,q=0)
            policy=config['release_input']
            s['io']['read']=dict(mode='pc_sequence',value=d,table=[0],pc_sequences={str(policy['right_pc']):[d,0],str(policy['left_pc']):[0]},sequence_end='hold-last',status=policy['status'],evidence=policy['evidence'])
            out=args.out/f'release-seed{seed}-d{d:02x}'
            run=execute(mapping,s,config['cycles'],seed,'integrated',out,config['cycles'])
            observed=inspect(load_trace(out),rows)
            assert run['clean'] and run['final_state']['pc']==0x84 and observed['returned'] and observed['repeat'] is None
            baseline=next(r for r in runs if r['seed']==seed and r['d']==d)
            first=lambda report:next(e for e in report['events'] if e['pc']==0x150)
            assert first(observed)==first(baseline['observed'])
            release_runs.append(dict(seed=seed,d=d,observed=observed,final_pc=run['final_state']['pc'],trace_digest=run['trace_digest']))
    sources=[Path(__file__),HERE/'drain-reset-study.json',HERE/'drain_caller_study.py',HERE/'biased_drain_study.py',HERE/'execute.py',HERE/'common.py',HERE.parent/'model.py',root/'mapping.json',root/'scenario.json']
    save(args.out/'report.json',dict(configuration=config,counts=dict(counts),runs=runs,release_runs=release_runs,
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='Seeded dispatch entry 1 at 109 reaches wrapper with R7=FF and Q=D from reset. Constant nonzero D produces an exact repeated state in one of the three loops under the selected previous-flag model. No physical dispatch index or external-D source is recovered.'))
    print(dict(counts))


if __name__=='__main__':main()
