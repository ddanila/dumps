"""Extend fitted flag policies across starts, inputs and dispatch hypotheses."""
import argparse
import itertools
import json
import tempfile
from collections import Counter
from pathlib import Path
from common import HERE, decode, read, save, unconditional_transfer
from execute import execute


def scenario_for(name, control, start, q, data, entry):
    scenario=read(HERE/f'results/condition-fit/{name}-marked/scenario.json')
    if control=='rom_calls':
        latest=read(HERE/'results/rom-study/scenario-rom_calls.json')
        scenario['dispatch']['tables']=latest['dispatch']['tables']
        scenario['branch_tables']=latest['branch_tables']
    scenario['initial'].update(pc=start,q=q)
    scenario['dispatch'].update(mode='constant',value=entry)
    scenario['io']['read']['pc_values']={str(0x341+i):value for i,value in enumerate(data)}
    return scenario


def unknown_decisions(records, rows, scenario):
    if scenario['condition']['mode']!='flags' or scenario['condition']['flag_timing']!='previous':
        raise ValueError('decision audit requires previous-flag policy')
    counts=Counter();previous={k:None for k in ('zero','sign','carry','overflow')}
    for record in records:
        row=rows[record['pc']];source=scenario['condition']['sources'][row['select']]
        if row['command'] in (0,2,4,6) and not unconditional_transfer(row,scenario):
            if source in previous and previous[source] is None:counts[record['pc']]+=1
        previous=record['alu']
    return dict(counts)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/condition-extension')
    parser.add_argument('--integrated-cycles',type=int,default=0)
    args=parser.parse_args()
    if args.integrated_cycles<0:parser.error('negative integration length')
    args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'condition-extension.json');reports=[]
    for name,control,start in itertools.product(config['mappings'],config['controls'],config['starts']):
        mapping=read(HERE/f'results/condition-fit/{name}-marked/mapping.json');rows=decode(mapping)
        runs=[];reached=set();unknown=Counter();stops=Counter()
        with tempfile.TemporaryDirectory() as tmp:
            for q,(input_name,data),entry in itertools.product(config['q_values'],config['inputs'].items(),config['entries']):
                scenario=scenario_for(name,control,start,q,data,entry)
                result=execute(mapping,scenario,config['cycles'],0,'integrated',tmp,config['cycles'])
                records=[json.loads(line) for line in (Path(tmp)/'trace.jsonl').read_text().splitlines()]
                decisions=unknown_decisions(records,rows,scenario);unknown.update(decisions)
                reached.update(result['address_counts']);stops[result['final_state']['pc']]+=1
                runs.append(dict(q=q,input=input_name,entry=entry,clean=result['clean'],stop=result['stop'],
                    completed_cycles=result['completed_cycles'],coverage=result['coverage'],stack=result['stack'],
                    final_pc=result['final_state']['pc'],first_084=next((r['cycle'] for r in records if r['pc']==0x84),None),
                    cycles_at_084=result['address_counts'].get(0x84,0),
                    visits_18b=result['address_counts'].get(0x18b,0),visits_341=result['address_counts'].get(0x341,0),
                    unknown_decisions=decisions,trace_digest=result['trace_digest']))
        report=dict(mapping=name,control=control,start=start,runs=runs,reached=sorted(reached),
            unknown_decisions=dict(unknown),terminal_pc_counts=dict(stops),all_clean=all(r['clean'] for r in runs))
        save(args.out/f'{name}-{control}-{start:03x}.json',report)
        reports.append({k:v for k,v in report.items() if k!='runs'})
    save(args.out/'summary.json',dict(configuration=config,profiles=reports,
        interpretation='Fitted local policies extended without retuning. Reset and local-entry coverage kept separate; clean cycles do not establish useful algorithm execution.'))
    if args.integrated_cycles:
        for name in config['mappings']:
            mapping=read(HERE/f'results/condition-fit/{name}-marked/mapping.json')
            spec=config['integration'];scenario=scenario_for(name,spec['control'],0,spec['q'],config['inputs'][spec['input']],spec['entry'])
            r=execute(mapping,scenario,args.integrated_cycles,0,'integrated',args.out/f'integrated-{name}',1000)
            print(name,'long run clean',r['clean'])
    print([(r['mapping'],r['control'],r['start'],len(r['reached']),r['all_clean'],r['unknown_decisions']) for r in reports])

if __name__=='__main__':main()
