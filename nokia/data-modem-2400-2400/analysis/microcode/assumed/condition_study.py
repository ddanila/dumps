"""Compare zero-flag timing with random inputs on other condition selects."""
import argparse
from collections import Counter
from pathlib import Path
from common import HERE,decode,read,save
from execute import execute


def scenario_for(base,config,timing,value):
    import copy
    scenario=copy.deepcopy(base)
    scenario['name']=f'select-zero-nonzero-{timing}'
    scenario['evidence']=config['evidence']
    condition=scenario['condition']
    condition.update(mode='flags',sources=['random']*8,polarity=[0]*8,flag_timing=timing)
    condition['sources'][config['select']]=config['source']
    condition['polarity'][config['select']]=config['polarity']
    scenario['io']['read']['value']=value
    return scenario


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/condition-study')
    parser.add_argument('--integrated-cycles',type=int,default=0)
    args=parser.parse_args()
    if args.integrated_cycles<0:parser.error('negative integration length')
    args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'condition-search.json');reports=[];long_runs=[]
    for variant in range(1,5):
        mapping=read(HERE/f'results/independent-study/variant-{variant}.json')
        base=read(HERE/f'results/independent-study/scenario-{variant}.json')
        rows=decode(mapping);loop_sites=[r['pc'] for r in rows if r['command']==5]
        for timing in config['timings']:
            reached=set();runs=[];loop_counts=Counter();terminals=Counter()
            for value in config['external_read_values']:
                scenario=scenario_for(base,config,timing,value)
                for seed in config['seeds']:
                    r=execute(mapping,scenario,config['cycles'],seed,'integrated',trace_limit=0)
                    reached.update(r['address_counts']);terminals[r['final_state']['pc']]+=1
                    loop_counts.update({pc:r['address_counts'].get(pc,0) for pc in loop_sites})
                    runs.append(dict(external_read=value,seed=seed,clean=r['clean'],coverage=r['coverage'],
                        final_pc=r['final_state']['pc'],stop=r['stop'],trace_digest=r['trace_digest'],
                        stack=r['stack'],loop_counts={pc:r['address_counts'].get(pc,0) for pc in loop_sites}))
            name=f'variant-{variant}-{timing}'
            report=dict(mapping=mapping['name'],timing=timing,all_clean=all(r['clean'] for r in runs),
                coverage=len(reached)/1021,reached=sorted(reached),terminals=dict(terminals),loop_counts=dict(loop_counts),runs=runs)
            save(args.out/f'{name}.json',report)
            reports.append({k:v for k,v in report.items() if k!='runs'})
            integration=config['integration']
            if args.integrated_cycles and variant==integration['variant']:
                scenario=scenario_for(base,config,timing,integration['external_read'])
                r=execute(mapping,scenario,args.integrated_cycles,integration['seed'],'integrated',args.out/f'integrated-{timing}',128)
                long_runs.append(dict(timing=timing,**{k:r[k] for k in ('clean','coverage','completed_cycles','stack','trace_digest')}))
    save(args.out/'summary.json',dict(configuration=config,comparisons=reports,
        interpretation='Select-zero nonzero hypothesis under alternative flag timings; no timing chosen by coverage score.'))
    if long_runs:save(args.out/'integration.json',dict(configuration=config['integration'],runs=long_runs))
    print([(r['mapping'],r['timing'],len(r['reached']),r['all_clean']) for r in reports])

if __name__=='__main__':main()
