"""Test boundary-derived sparse dispatch targets for the low-address handlers."""
import argparse
import copy
from pathlib import Path
from common import HERE,decode,read,save,table_targets,unconditional_transfer
from analyze import graph,listing
from execute import execute


def boundaries(rows,scenario,config):
    direct={r['branch'] for r in rows if r['command'] in (4,6) and r['direct']}
    candidates=[p for p in range(config['region_start'],config['region_end']) if p not in direct
        and (rows[p-1]['command']==3 or rows[p-1]['command']==6 and unconditional_transfer(rows[p-1],scenario))
        and rows[p-2]['command']!=0]
    local={p for t in config['local_tables'].values() for p in table_targets(t)}
    deferred=set(map(int,config['deferred_boundaries']))
    return dict(candidates=candidates,local_entries=sorted(local),deferred=sorted(deferred),
                handlers=[p for p in candidates if p not in local|deferred])


def scenarios(base,config,evidence):
    result={'baseline':copy.deepcopy(base)}
    scenario=copy.deepcopy(base);scenario['name']='low-address-handler-dispatch'
    scenario['evidence']=config['evidence']
    scenario['branch_tables'][str(config['dispatch_site'])]=dict(targets=evidence['handlers']+[config['retained_encoded_target']],
        status='hypothesis',evidence=config['evidence']+' Sparse order is a scenario convention.')
    result['handlers']=copy.deepcopy(scenario)
    for site,table in config['local_tables'].items():
        scenario['branch_tables'][site]=copy.deepcopy(table)
        result[f'local-{int(site):03X}']=copy.deepcopy(scenario)
    # Separate weaker alternative: the TSK after the two direct branches is entry 2.
    alternative=copy.deepcopy(scenario)
    for pc,reason in config['deferred_boundaries'].items():
        previous=next((t for t in alternative['branch_tables'].values() if table_targets(t)[-1]+1==int(pc)),None)
        if previous is not None:
            targets=table_targets(previous)+[int(pc)]
            previous.clear();previous.update(targets=targets,status='hypothesis',evidence=reason)
    result['third-entry-ablation']=alternative
    return result,scenario


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/handler-study')
    parser.add_argument('--integrated-cycles',type=int,default=0)
    args=parser.parse_args()
    if args.integrated_cycles<0:parser.error('negative integration length')
    args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'handler-search.json');base=read(HERE/'branch-tables.json')
    mapping=read(HERE/'sequencer.json');rows=decode(mapping)
    evidence=boundaries(rows,base,config);alternatives,scenario=scenarios(base,config,evidence)
    save(args.out/'boundary-evidence.json',dict(configuration=config,**evidence))
    comparisons={}
    for name,alternative in alternatives.items():
        g=graph(rows,alternative);save(args.out/f'graph-{name}.json',g)
        comparisons[name]=dict(reachable=len(g['reached']),exceptions=g['exceptions'],scenario=alternative)
    save(args.out/'scenario.json',scenario)
    control_reached=set();control_runs=[]
    reached=set();runs=[];entries={site:set() for site in scenario['branch_tables']}
    for seed in range(config['seeds']):
        control=execute(mapping,base,config['cycles'],seed,trace_limit=0)
        control_reached.update(control['address_counts'])
        control_runs.append(dict(seed=seed,clean=control['clean'],coverage=control['coverage'],stack=control['stack'],trace_digest=control['trace_digest']))
        r=execute(mapping,scenario,config['cycles'],seed,trace_limit=0)
        reached.update(r['address_counts'])
        # Observed target words, not inferred selection counts.
        for site,t in scenario['branch_tables'].items():
            entries[site].update(set(table_targets(t))&set(r['address_counts']))
        runs.append(dict(seed=seed,clean=r['clean'],coverage=r['coverage'],stack=r['stack'],trace_digest=r['trace_digest']))
    for row in rows:
        row['handler_candidate']=row['pc'] in evidence['handlers']
        row['observed']=row['pc'] in reached
        row['annotation']='boundary-derived handler hypothesis' if row['handler_candidate'] else ''
    listing(rows,args.out/'annotated-listing.csv')
    save(args.out/'summary.json',dict(configuration=config,static=comparisons,runs=runs,reached=sorted(reached),
        matched_control=dict(reached=sorted(control_reached),coverage=len(control_reached)/1021,runs=control_runs),
        added=sorted(reached-control_reached),lost=sorted(control_reached-reached),
        coverage=len(reached)/1021,all_clean=all(r['clean'] for r in runs),observed_target_words={site:sorted(v) for site,v in entries.items()},
        interpretation='Sparse handler targets are explicit hypotheses; no claim of recovered command encoding or physical I/O.'))
    if args.integrated_cycles:
        spec=config['integration'];m=read(HERE/f"results/independent-study/variant-{spec['variant']}.json")
        s=read(HERE/f"results/independent-study/scenario-{spec['variant']}.json")
        s['name']=scenario['name'];s['evidence']=scenario['evidence'];s['branch_tables']=scenario['branch_tables']
        s['io']['read']['value']=spec['external_read']
        r=execute(m,s,args.integrated_cycles,spec['seed'],'integrated',args.out/'integrated',128)
        print('Integrated clean:',r['clean'])
    print('Static:',[(name,c['reachable'],c['exceptions']) for name,c in comparisons.items()])
    print('Dynamic:',len(reached),'clean:',all(r['clean'] for r in runs))

if __name__=='__main__':main()
