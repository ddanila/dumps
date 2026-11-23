"""Vary only selectors unconstrained by the saved local condition fits."""
import argparse
import copy
import itertools
import json
from pathlib import Path
from common import HERE, decode, read, save
from execute import execute
from condition_extension import scenario_for, unknown_decisions


def complete(scenario, fitted, mask):
    result=copy.deepcopy(scenario);free=sorted(set(range(8))-set(map(int,fitted)))
    if not 0<=mask<1<<len(free):raise ValueError('completion mask out of range')
    if result['condition']['value']!=0:raise ValueError('constant-zero basis required')
    for bit,select in enumerate(free):
        result['condition']['sources'][select]='constant'
        result['condition']['polarity'][select]=(mask>>bit)&1
    return result,free


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/selector-completion')
    parser.add_argument('--integrated-cycles',type=int,default=0)
    args=parser.parse_args()
    if args.integrated_cycles<0:parser.error('negative integration length')
    args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'selector-completion.json');fit=read(HERE/'condition-fit.json');reports=[]
    for name in config['mappings']:
        mapping=read(HERE/f'results/condition-fit/{name}-marked/mapping.json')
        fitted=fit['replay_policies'][name];free=sorted(set(range(8))-set(map(int,fitted)))
        runs=[]
        for control,q,entry,mask in itertools.product(config['controls'],config['q_values'],config['entries'],range(1<<len(free))):
            base=scenario_for(name,control,0,q,config['marked_data'],entry)
            scenario,_=complete(base,fitted,mask)
            r=execute(mapping,scenario,config['cycles'],0,'integrated',trace_limit=0)
            runs.append(dict(control=control,q=q,entry=entry,mask=mask,clean=r['clean'],
                visits_18b=r['address_counts'].get(0x18b,0),visits_341=r['address_counts'].get(0x341,0),
                coverage=r['coverage'],stack=r['stack'],stop=r['stop'],completed_cycles=r['completed_cycles'],
                final_pc=r['final_state']['pc'],trace_digest=r['trace_digest']))
        candidates=[r for r in runs if r['clean'] and r['visits_18b'] and r['visits_341']]
        candidates.sort(key=lambda r:(r['control']!='rom_calls',r['mask'],r['q'],r['entry']))
        chosen=candidates[0] if candidates else None
        comparison=None
        if chosen:
            for label,data in [('marked',config['marked_data']),('zero',[0]*4)]:
                scenario,_=complete(scenario_for(name,chosen['control'],0,chosen['q'],data,chosen['entry']),fitted,chosen['mask'])
                execute(mapping,scenario,config['cycles'],0,'integrated',args.out/f'{name}-{label}',config['cycles'])
            if args.integrated_cycles:
                long_scenario=read(args.out/f'{name}-marked/scenario.json')
                execute(mapping,long_scenario,args.integrated_cycles,0,'integrated',args.out/f'integrated-{name}',1000)
            traces={label:[json.loads(line) for line in (args.out/f'{name}-{label}'/'trace.jsonl').read_text().splitlines()] for label in ('zero','marked')}
            differences=[dict(cycle=a['cycle'],pc=a['pc'],zero_next=a['next_pc'],marked_next=b['next_pc'])
                for a,b in zip(traces['zero'],traces['marked']) if a['next_pc']!=b['next_pc']]
            loop_counts={}
            for label,records in traces.items():
                prefix=[];active=False
                for record in records:
                    if record['pc']==config['loop_entry']:active=True
                    if active:prefix.append(record)
                    if active and record['pc']==config['loop_exit']:break
                loop_counts[label]=sum(r['pc']==config['loop_entry'] for r in prefix)
            comparison=dict(first_control_divergence=next(iter(differences),None),first_loop_iterations=loop_counts,
                unknown_decisions={label:unknown_decisions(records,decode(mapping),scenario) for label,records in traces.items()})
        report=dict(mapping=name,free_selectors=free,runs=runs,chosen=chosen,comparison=comparison,
            clean_runs=sum(r['clean'] for r in runs),preparation_runs=sum(bool(r['visits_341']) for r in runs),
            caller_runs=sum(bool(r['visits_18b']) for r in runs),clean_caller_runs=len(candidates))
        save(args.out/f'{name}.json',report)
        reports.append({k:v for k,v in report.items() if k!='runs'})
    save(args.out/'summary.json',dict(configuration=config,profiles=reports,
        interpretation='Existence search over constant completions of unconstrained selectors; fitted sources are unchanged. Any example remains a scenario hypothesis, not recovered wiring.'))
    print(reports)

if __name__=='__main__':main()
