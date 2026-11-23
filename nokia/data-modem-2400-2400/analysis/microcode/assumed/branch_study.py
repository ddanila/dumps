"""Test local jump-table evidence without replacing historical baseline results."""
import argparse
import copy
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from common import HERE, decode, read, save
from analyze import graph, listing
from execute import execute


def run_task(task):
    name,mapping,scenario,cycles,seed,mode,out=task
    result=execute(mapping,scenario,cycles,seed,mode,out/name,64)
    return name,result


def write_table_annotations(out,rows,scenario,results):
    annotations={};tables=[]
    for site,spec in scenario['branch_tables'].items():
        pc=int(site);label=f'table_dispatch_{pc:03x}'
        annotations[pc]=label+'; hypothesis; index supplied by scenario'
        cases=[]
        for index in range(spec['count']):
            entry=spec['base']+index*spec['stride'];target=rows[entry]['branch']
            annotations[entry]=f'{label} case {index}: jump to {target:03X}'
            annotations[target]=f'{label} case {index} handler entry; algorithm unknown'
            counts={name:r['address_counts'].get(str(entry),r['address_counts'].get(entry,0)) for name,r in results.items()}
            cases.append(dict(index=index,entry=entry,target=target,execution_counts=counts))
        tables.append(dict(site=pc,label=label,status=spec['status'],evidence=spec['evidence'],cases=cases))
    save(out/'dispatch-analysis.json',tables)
    listing([dict(row,annotation=annotations.get(row['pc'],'')) for row in rows],out/'annotated-listing.csv')


def ablation_results(mapping,scenario):
    rows=decode(mapping);ablations={}
    for name, sites, requires_direct in [('baseline',[],True),('table-109-only',[0x109],True),
            ('table-109-select-zero',[0x109],False),('both-tables-select-zero',[0x109,0x34c],False)]:
        trial=copy.deepcopy(scenario)
        trial['branch_tables']={str(site):scenario['branch_tables'][str(site)] for site in sites}
        trial['condition']['unconditional_requires_direct']=requires_direct
        cfg=graph(rows,trial)
        ablations[name]=dict(reachable=len(cfg['reached']),states=cfg['states'],exceptions=cfg['exceptions'],scenario=trial)
    return ablations


def run(out, cycles=1000000, integrated_cycles=10000000, workers=4):
    out.mkdir(parents=True,exist_ok=True)
    mapping=read(HERE/'sequencer.json');scenario=read(HERE/'branch-tables.json')
    rows=decode(mapping);ablations=ablation_results(mapping,scenario)
    cfg=graph(rows,scenario);save(out/'control-flow.json',cfg)
    tasks=[(f'seed-{seed}',mapping,scenario,cycles,seed,'sequencer',out) for seed in range(16)]
    for variant in range(1,4):
        m=read(HERE/f'results/datapath-{variant}.json')
        tasks.append((f'integrated-{variant}',m,scenario,integrated_cycles,0,'integrated',out))
    results={}
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for name,result in pool.map(run_task,tasks):
            results[name]=result
            print(name,result['completed_cycles'],len(result['visited']),result['clean'],flush=True)
    covered=set().union(*(set(r['visited']) for n,r in results.items() if n.startswith('seed-')))
    replay=execute(mapping,scenario,cycles,0,trace_limit=64)
    summary=dict(scenario=scenario['name'],ablations=ablations,
        aggregate_visited=len(covered),aggregate_coverage=len(covered)/1021,
        coverage_target_met=len(covered)/1021>=.9,
        all_clean=all(r['clean'] for r in results.values()),seed_zero_replay_equal=replay==results['seed-0'],
        runs={name:{k:r[k] for k in ('completed_cycles','requested_cycles','coverage','clean','stop','trace_digest','stack','dispatch_counts','register_changes')} for name,r in results.items()},
        interpretation='Local jump-table hypothesis with scenario-supplied indices. Does not establish the datapath or physical address source.')
    baseline_uncovered=set(read(HERE/'results/suite.json')['uncovered'])
    summary['newly_visited']=sorted(covered & baseline_uncovered)
    summary['uncovered']=sorted(set(range(1024))-covered-{0x1df,0x29f,0x3ff})
    save(out/'summary.json',summary)
    write_table_annotations(out,rows,scenario,results)
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,default=HERE/'results/branch-study')
    p.add_argument('--cycles',type=int,default=1000000)
    p.add_argument('--integrated-cycles',type=int,default=10000000)
    p.add_argument('--workers',type=int,default=4)
    args=p.parse_args()
    if min(args.cycles,args.integrated_cycles,args.workers)<1:p.error('positive limits required')
    result=run(args.out,args.cycles,args.integrated_cycles,args.workers)
    print('aggregate coverage:',result['aggregate_coverage'])
