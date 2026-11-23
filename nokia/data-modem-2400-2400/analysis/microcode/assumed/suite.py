"""Fixed reproducible validation and evidence-based routine catalog."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from common import HERE, decode, digest, read, save
from execute import execute


def job(item):
    name,mapping,scenario,cycles,seed,mode,out=item
    result=execute(mapping,scenario,cycles,seed,mode,out/name,64)
    return name,result


def write_dynamic(out,results):
    save(out/'dynamic-ranking.json',dict(policy='Model-error veto; register activity and coverage are reported, not treated as proof of correctness',variants=[dict(variant=i,static_score=read(out/f'datapath-{i}.json')['ranking']['score'],runs={n:dict(clean=s['clean'],coverage=s['coverage'],register_changes=s['register_changes'],unknown_flags={k:v for k,v in s['assumption_counts'].items() if k.startswith('unknown')}) for n,s in results.items() if n.startswith(f'integrated-{i}-') or n==f'flags-{i}'}) for i in range(1,4)]))


def run_suite(out, scale=1, workers=4):
    base=read(HERE/'baseline.json');seq=read(HERE/'sequencer.json');tasks=[]
    for mode in ('constant-false','constant-true','per-select'):
        s=read(HERE/'baseline.json');s['name']=mode
        s['condition']['mode']='per-select' if mode=='per-select' else 'constant'
        s['condition']['value']=int(mode=='constant-true')
        tasks.append((mode,seq,s,max(1,int(1000000*scale)),0,'sequencer',out))
    for seed in range(16):
        tasks.append((f'sequencer-seed-{seed}',seq,base,max(1,int(1000000*scale)),seed,'sequencer',out))
    for variant in range(1,4):
        m=read(out/f'datapath-{variant}.json')
        for seed in range(4):
            cycles=10000000 if seed==0 else 1000000
            tasks.append((f'integrated-{variant}-seed-{seed}',m,base,max(1,int(cycles*scale)),seed,'integrated',out))
        # Actual modeled flags are separately exercised, not claimed as wiring.
        s=read(HERE/'baseline.json');s['name']='hypothesized-flags';s['condition']['mode']='flags'
        tasks.append((f'flags-{variant}',m,s,max(1,int(1000000*scale)),0,'integrated',out))
    results={}
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for name,result in pool.map(job,tasks):
            results[name]=result
            print(name,result['completed_cycles'],round(result['coverage']*100,2),result['stop'],flush=True)
    # Replay full seed-0 experiments to verify full-run summary and trace digests.
    replay=[]
    for task in [tasks[3]]+[t for t in tasks if t[0].startswith('integrated-') and t[0].endswith('seed-0')]:
        name,mapping,scenario,cycles,seed,mode,_=task
        actual=execute(mapping,scenario,cycles,seed,mode,trace_limit=64)
        replay.append(dict(name=name,summary_equal=actual==results[name],trace_equal=actual['trace_digest']==results[name]['trace_digest']))
    sequencer=[s for n,s in results.items() if s['mode']=='sequencer']
    used={r['pc'] for r in decode(seq) if not r['unused']}
    covered=set().union(*(set(s['visited']) for s in sequencer))&used
    suite=dict(scale=scale,runs={n:{k:s[k] for k in ('completed_cycles','requested_cycles','coverage','clean','stop','trace_digest','register_changes','assumption_counts')} for n,s in results.items()},
        aggregate_sequencer_coverage=len(covered)/len(used),uncovered=sorted(used-covered),
        coverage_target_met=len(covered)/len(used)>=.9,all_runs_clean=all(s['clean'] for s in results.values()),replay=replay)
    suite['acceptance_met']=scale==1 and suite['coverage_target_met'] and suite['all_runs_clean'] and all(x['summary_equal'] for x in replay)
    save(out/'suite.json',suite)
    catalog=[]
    analysis=read(out/'analysis.json')
    for target,shape in analysis['subroutines'].items():
        pc=int(target)
        hits={n:s['address_counts'].get(pc,0) for n,s in results.items() if s['address_counts'].get(pc,0)}
        catalog.append(dict(entry=pc,end=shape['end'],label='PLP/BLT/POP loop helper' if pc==0x1e9 else ('loop-entry trampoline' if pc==0x1e else f'routine_{pc:03x}'),
            status='structural interpretation; algorithm unknown',shape=shape,execution_counts=hits,
            trace_reference='Per-run summary.json routine_samples contains first execution at each direct-call entry',
            trace_excerpts={n:s['routine_samples'][pc] for n,s in results.items() if pc in s['routine_samples'] and n in ('integrated-1-seed-0','integrated-2-seed-0','integrated-3-seed-0')},
            unresolved='No evidence yet distinguishes multiply/filter semantics or external I/O wiring'))
    save(out/'routines.json',catalog)
    write_dynamic(out,results)
    diagnostics=[]
    for seed in range(4):
        s=read(HERE/'baseline.json');s['name']='relaxed-select-zero';s['condition']['unconditional_select']=None
        r=execute(seq,s,100000,seed,out=out/f'diagnostic-select-zero-{seed}',trace_limit=16)
        diagnostics.append({k:r[k] for k in ('seed','completed_cycles','stop','stack','coverage')})
    save(out/'diagnostics.json',dict(hypothesis='Make select zero conditional everywhere; rejected by unknown-stack failures',runs=diagnostics))
    return suite


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,default=HERE/'results')
    p.add_argument('--scale',type=float,default=1);p.add_argument('--workers',type=int,default=4);p.add_argument('--report-only',action='store_true')
    a=p.parse_args()
    if a.scale<=0 or a.workers<1: p.error('positive scale and workers required')
    if a.report_only:
        write_dynamic(a.out,{p.parent.name:read(p) for p in a.out.glob('*/summary.json')})
    else:
        s=run_suite(a.out,a.scale,a.workers);print('acceptance_met:',s['acceptance_met'])
