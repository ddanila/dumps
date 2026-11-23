"""Follow preparation sensitivity through the alternate 18B caller."""
import argparse
import copy
import itertools
from collections import Counter
from pathlib import Path
from common import HERE, decode, read, save
from chain_study import run_chain
from rotation_study import scenario_for


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/single-caller-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'single-caller-search.json');base=read(HERE/'rotation-search.json');reports=[]
    for name in config['mappings']:
        for swap in (False,True):
            mapping=read(HERE/f'results/preparation-study/{name}.json')
            if swap:mapping['fields']['a'],mapping['fields']['b']=mapping['fields']['b'],mapping['fields']['a']
            rows=decode(mapping);scenario=scenario_for(mapping,base)
            for mask in range(1<<len(config['condition_sites'])):
                fixture=copy.deepcopy(config['fixture'])
                fixture['condition_overrides'].update({str(pc):(mask>>i)&1 for i,pc in enumerate(config['condition_sites'])})
                totals={f'{stage:03X}':[dict(comparisons=0,changed_registers=Counter(),changed_q=0,changed_y=0) for _ in range(4)] for stage in fixture['checkpoints']}
                cycles=set();maximum=0;examples=[]
                for q,entry in itertools.product(config['initial_q'],range(4)):
                    entries={str(config['dispatch_site']):entry}
                    reference=run_chain(rows,scenario,fixture,entries,[0]*4,q)
                    cycles.add(reference['cycles']);maximum=max(maximum,reference['maximum_stack'])
                    for byte,value in itertools.product(range(4),config['perturbations']):
                        data=[0]*4;data[byte]=value
                        result=run_chain(rows,scenario,fixture,entries,data,q)
                        for stage,state in result['stages'].items():
                            before=reference['stages'][stage];t=totals[stage][byte];t['comparisons']+=1
                            t['changed_registers'].update(i for i,(a,b) in enumerate(zip(before['ram'],state['ram'])) if a!=b)
                            t['changed_q']+=before['q']!=state['q'];t['changed_y']+=before['y']!=state['y']
                    if name in config['example_mappings'] and q==0 and entry==0 and mask in config['example_masks']:
                        examples.append(dict(zero=run_chain(rows,scenario,fixture,entries,[0]*4,q,True),
                            marked=run_chain(rows,scenario,fixture,entries,config['example_data'],q,True)))
                report=dict(mapping=name,swap_registers=swap,condition_mask=mask,conditions=fixture['condition_overrides'],
                    checkpoints=totals,cycles=sorted(cycles),maximum_stack=maximum)
                reports.append(report)
                if examples:save(args.out/f'example-{name}-swap-{int(swap)}-mask-{mask}.json',dict(**report,examples=examples))
    save(args.out/'summary.json',dict(configuration=config,profiles=reports,
        interpretation='Local 18B caller sensitivity with explicit one-pass loops and branch choices; no physical I/O interpretation or reset coverage.'))
    print('Profiles:',len(reports))

if __name__=='__main__':main()
