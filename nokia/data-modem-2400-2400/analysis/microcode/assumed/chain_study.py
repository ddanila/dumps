"""Probe input sensitivity through the real 133..13D caller and its callees."""
import argparse
import itertools
from collections import Counter
from pathlib import Path
from common import HERE, decode, read, save, table_targets, unconditional_transfer
from execute import CarryInput
from model import Am2901, X8X02
from rotation_study import scenario_for


def run_chain(rows, scenario, config, entries, data, q, trace=False):
    cpu=Am2901(ram=config['initial_ram'][:],q=q);seq=X8X02(pc=config['start'])
    carry=CarryInput(scenario['inputs']['carry']);depth=0;maximum=0;records=[];stages={}
    for cycle in range(config['cycle_limit']):
        if seq.pc==config['stop']:
            if depth or seq.pushes!=seq.pops:raise ValueError('unbalanced chain')
            return dict(stages=stages,cycles=cycle,maximum_stack=maximum,trace=records)
        row=rows[seq.pc];pc=seq.pc
        d=data[pc-config['preparation']] if config['preparation']<=pc<config['preparation']+len(data) else config['external_default']
        cin=carry.resolve(row);result=cpu.step(row['i'],row['a'],row['b'],d,cin);carry.observe(result)
        test=int(unconditional_transfer(row,scenario))
        if str(pc) in config['condition_overrides']:test=config['condition_overrides'][str(pc)]
        branch=row['branch']
        if row['command']==4 and str(pc) in entries:
            branch=table_targets(scenario['dispatch']['tables'][str(pc)])[entries[str(pc)]]
        push=row['command']==5 or (row['command']==4 and test)
        pop=row['command'] in (2,3)
        depth+=int(push)-int(pop);maximum=max(maximum,depth)
        if not 0<=depth<=4:raise ValueError('chain stack violation')
        seq.step(row['command'],branch,test)
        state=dict(ram=cpu.ram[:],q=cpu.q,y=result['y'])
        if seq.pc in config['checkpoints']:stages[f'{seq.pc:03X}']=state
        if trace:records.append(dict(pc=pc,next_pc=seq.pc,d=d,carry=cin,test=test,depth=depth,**state))
    raise ValueError('chain cycle budget exhausted')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/chain-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'chain-search.json');base=read(HERE/'rotation-search.json');reports=[]
    for path in sorted((HERE/'results/preparation-study').glob('preparation-source-*.json')):
        for swap in config['swap_register_roles']:
            mapping=read(path)
            if swap:mapping['fields']['a'],mapping['fields']['b']=mapping['fields']['b'],mapping['fields']['a']
            rows=decode(mapping);scenario=scenario_for(mapping,base)
            totals={f'{stage:03X}':[dict(comparisons=0,changed_registers=Counter(),changed_q=0,changed_y=0) for _ in range(4)] for stage in config['checkpoints']}
            examples=[];cycles=set();maximum=0
            for q in config['initial_q']:
                for choices in itertools.product(range(4),repeat=len(config['dispatch_sites'])):
                    entries=dict(zip(map(str,config['dispatch_sites']),choices))
                    reference=run_chain(rows,scenario,config,entries,[0]*4,q)
                    cycles.add(reference['cycles']);maximum=max(maximum,reference['maximum_stack'])
                    for byte in range(4):
                        for value in config['perturbations']:
                            data=[0]*4;data[byte]=value
                            result=run_chain(rows,scenario,config,entries,data,q)
                            for stage,state in result['stages'].items():
                                before=reference['stages'][stage];t=totals[stage][byte];t['comparisons']+=1
                                t['changed_registers'].update(i for i,(a,b) in enumerate(zip(before['ram'],state['ram'])) if a!=b)
                                t['changed_q']+=before['q']!=state['q'];t['changed_y']+=before['y']!=state['y']
                    if q==config['initial_q'][0] and list(choices)==config['example_entries']:
                        examples.append(dict(entries=entries,zero=run_chain(rows,scenario,config,entries,[0]*4,q,True),
                            marked=run_chain(rows,scenario,config,entries,config['example_data'],q,True)))
            report=dict(mapping=mapping['name'],swap_registers=swap,checkpoints=totals,cycles=sorted(cycles),maximum_stack=maximum,examples=examples)
            save(args.out/(mapping['name']+('-swap' if swap else '')+'.json'),report)
            reports.append({k:v for k,v in report.items() if k!='examples'})
    save(args.out/'summary.json',dict(configuration=config,profiles=reports,
        interpretation='Local real-instruction caller fixtures with explicit conditions, table choices and input bytes. Sensitivity is empirical for these perturbations, not recovered I/O or reset coverage.'))
    print('Profiles:',len(reports))

if __name__=='__main__':main()
