"""Compare datapath-derived indices at the two ROM-backed branch sites."""
import argparse
import copy
from pathlib import Path
from common import HERE,read,save,table_targets
from execute import execute


def scenario_for(config,variant,source,value):
    scenario=read(HERE/f'results/independent-study/scenario-{variant}.json')
    control=read(HERE/'results/rom-study/scenario-rom_calls.json')
    scenario.update(name=f'rom-branch-index-{source}',evidence=config['evidence'],
        dispatch=copy.deepcopy(control['dispatch']),branch_tables=copy.deepcopy(control['branch_tables']))
    scenario['io']['read']['value']=value
    if source=='previous_y':scenario['dispatch']['initial_y']=config['initial_y']
    for site in config['sites']:scenario['branch_tables'][str(site)]['index_source']=source
    return scenario


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/index-study')
    parser.add_argument('--integrated-cycles',type=int,default=0)
    args=parser.parse_args()
    if args.integrated_cycles<0:parser.error('negative integration length')
    args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'index-sources.json');reports=[]
    for variant in config['variants']:
        mapping=read(HERE/f'results/independent-study/variant-{variant}.json')
        for source in config['sources']:
            reached=set();runs=[];targets={str(site):set() for site in config['sites']}
            for value in config['external_values']:
                scenario=scenario_for(config,variant,source,value)
                for seed in config['seeds']:
                    r=execute(mapping,scenario,config['cycles'],seed,'integrated',trace_limit=0)
                    reached.update(r['address_counts'])
                    for site in config['sites']:
                        allowed=set(table_targets(scenario['branch_tables'][str(site)]))
                        targets[str(site)].update(int(edge.split('->')[1],16) for edge in r['edge_counts']
                            if edge.startswith(f'{site:03x}->') and int(edge.split('->')[1],16) in allowed)
                    runs.append(dict(external_read=value,seed=seed,clean=r['clean'],coverage=r['coverage'],
                        stack=r['stack'],trace_digest=r['trace_digest'],dispatch_counts=r['dispatch_counts']))
            report=dict(mapping=mapping['name'],source=source,reached=sorted(reached),coverage=len(reached)/1021,
                observed_targets={site:sorted(values) for site,values in targets.items()},runs=runs,
                all_clean=all(r['clean'] for r in runs))
            save(args.out/f'variant-{variant}-{source}.json',report)
            reports.append({k:v for k,v in report.items() if k!='runs'})
    save(args.out/'summary.json',dict(configuration=config,comparisons=reports,
        interpretation='Index-source sensitivity under constant external D; no source selected by coverage ranking.'))
    if args.integrated_cycles:
        spec=config['integration'];mapping=read(HERE/f"results/independent-study/variant-{spec['variant']}.json")
        scenario=scenario_for(config,spec['variant'],spec['source'],spec['external_read'])
        r=execute(mapping,scenario,args.integrated_cycles,spec['seed'],'integrated',args.out/'integrated',1000)
        print('Integrated clean:',r['clean'])
    print([(r['mapping'],r['source'],len(r['reached']),r['observed_targets'],r['all_clean']) for r in reports])

if __name__=='__main__':main()
