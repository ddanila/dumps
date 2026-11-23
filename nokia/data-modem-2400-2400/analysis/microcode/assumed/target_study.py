"""Classify disconnected bank entries and test bounded, permissive target pools."""
import argparse
import copy
from pathlib import Path
from common import HERE,decode,read,save,unconditional_transfer
from analyze import graph
from execute import execute


def classify(rows,base,config):
    baseline=graph(rows,base)
    unreachable={r['pc'] for r in baseline['unreachable']}
    direct={r['branch'] for r in rows if r['command'] in (4,6) and r['direct']}
    candidates=[p for p in range(config['region_start'],config['region_end'])
        if p in unreachable and p not in direct and rows[p-2]['command']!=0
        and (rows[p-1]['command']==3 or rows[p-1]['command']==6 and unconditional_transfer(rows[p-1],base))]
    reports=[]
    for pc in candidates:
        root=graph(rows,base,start=pc)
        call=graph(rows,base,start=pc,initial_stack=(-1,),return_sentinel=-1)
        calls=[p for p in call['reached'] if rows[p]['command']==4]
        reports.append(dict(entry=pc,root_safe=not root['exceptions'],root_exceptions=root['exceptions'],
            returns=call['terminal_return_reached'],call_safe=not call['exceptions'],call_exceptions=call['exceptions'],
            calls=calls,leaf=not calls,reached_with_caller=call['reached']))
    setups=[[rows[p]['raw'] for p in pair] for pair in config['setup_pairs']]
    return dict(entries=reports,setup_words=setups,setup_equal=all(s==setups[0] for s in setups),
        interpretation='Local stack probes classify possible entry roles; their visited words do not count as reset execution coverage.')


def scenarios(base,config,classification):
    unbounded=copy.deepcopy(base)
    unbounded['name']='permissive-bank-target-pools';unbounded['evidence']=config['evidence']
    entries=classification['entries']
    unbounded['branch_tables'][str(config['branch_site'])]=dict(targets=[r['entry'] for r in entries if r['root_safe']],
        status='hypothesis',evidence='Bank boundaries safe without an initial caller; association to 26F remains tentative')
    excluded={}
    for site in config['call_sites']:
        eligible=[r for r in entries if r['returns'] and r['call_safe']]
        excluded[str(site)]=[r['entry'] for r in eligible if site in r['reached_with_caller']]
        unbounded['dispatch']['tables'][str(site)]=dict(targets=[r['entry'] for r in eligible if site not in r['reached_with_caller']],
            status='hypothesis',evidence='Returning boundaries excluding direct recursion through this call site; permissive target pool')
    selected=copy.deepcopy(unbounded);selected['name']='bounded-bank-target-pools'
    leaf={r['entry'] for r in entries if r['leaf']}
    for site in config['leaf_only_sites']:
        table=selected['dispatch']['tables'][str(site)]
        table['targets']=[p for p in table['targets'] if p in leaf]
        table['evidence']=config['leaf_evidence']
    return dict(unrestricted=unbounded,bounded=selected),excluded


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/target-study')
    parser.add_argument('--integrated-cycles',type=int,default=0)
    args=parser.parse_args()
    if args.integrated_cycles<0:parser.error('negative integration length')
    args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'target-pools.json');base=read(HERE/'results/exception-study/scenario-local_table.json')
    mapping=read(HERE/'sequencer.json');rows=decode(mapping)
    classification=classify(rows,base,config);save(args.out/'classification.json',classification)
    alternatives,excluded=scenarios(base,config,classification)
    static={}
    for name,scenario in dict(baseline=base,**alternatives).items():
        g=graph(rows,scenario);save(args.out/f'graph-{name}.json',g);save(args.out/f'scenario-{name}.json',scenario)
        static[name]=dict(reachable=len(g['reached']),exceptions=g['exceptions'])
    if static['bounded']['exceptions']:raise RuntimeError('bounded hypothesis still has static stack errors')
    selected=alternatives['bounded'];reached=set();runs=[]
    for seed in range(config['seeds']):
        r=execute(mapping,selected,config['cycles'],seed,trace_limit=0)
        reached.update(r['address_counts'])
        runs.append(dict(seed=seed,clean=r['clean'],coverage=r['coverage'],stack=r['stack'],trace_digest=r['trace_digest']))
    previous=read(HERE/'results/exception-study/summary.json')
    if any(previous['configuration'][key]!=config[key] for key in ('cycles','seeds')):
        raise ValueError('archived comparison does not match sampling effort')
    old=set(previous['comparisons']['local_table']['reached'])
    save(args.out/'summary.json',dict(configuration=config,static=static,excluded_self_recursive=excluded,
        reached=sorted(reached),coverage=len(reached)/1021,added=sorted(reached-old),lost=sorted(old-reached),
        all_clean=all(r['clean'] for r in runs),runs=runs,
        interpretation='Coverage under permissive, structurally constrained target pools; not recovered address wiring or known physical I/O.'))
    if args.integrated_cycles:
        spec=config['integration'];m=read(HERE/f"results/independent-study/variant-{spec['variant']}.json")
        s=read(HERE/f"results/independent-study/scenario-{spec['variant']}.json")
        s.update(name=selected['name'],evidence=selected['evidence'],dispatch=selected['dispatch'],branch_tables=selected['branch_tables'])
        s['io']['read']['value']=spec['external_read']
        r=execute(m,s,args.integrated_cycles,spec['seed'],'integrated',args.out/'integrated',128)
        print('Integrated clean:',r['clean'])
    print('Static',static,'dynamic',len(reached),'clean',all(r['clean'] for r in runs))

if __name__=='__main__':main()
