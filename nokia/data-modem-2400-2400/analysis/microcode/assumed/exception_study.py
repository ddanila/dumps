"""Compare a non-returning direct call with an explicit local-table hypothesis."""
import argparse
import copy
import itertools
from pathlib import Path
from common import HERE,decode,read,save,table_targets
from analyze import graph
from execute import execute,CarryInput
from model import Am2901


def evidence(rows,config):
    calls=[r for r in rows if r['command']==4]
    unusual=[r['pc'] for r in calls if r['i']>>6!=1]
    targets={r['branch'] for r in rows if r['command'] in (4,6) and r['direct']}
    groups=[];group=[]
    for pc in range(config['region_start'],config['region_end']):
        if rows[pc]['command']==3 and pc not in targets:group.append(pc)
        else:
            if len(group)>1:groups.append(group)
            group=[]
    if len(group)>1:groups.append(group)
    return dict(call_count=len(calls),non_no_load_calls=unusual,isolated_pop_groups=groups,
        site=rows[config['call_site']],table_rows=[rows[p] for p in table_targets(config['table'])])


def scenarios(base,config):
    control=copy.deepcopy(base);candidate=copy.deepcopy(base)
    control['name']='exceptional-call-returning-surrogate'
    control['dispatch']['tables'][str(config['call_site'])]=dict(targets=[config['control_target']],status='stub',
        evidence='Diagnostic returning-call surrogate only; does not identify target wiring')
    candidate['name']='exceptional-call-local-pop-table';candidate['evidence']=config['evidence']
    candidate['dispatch']['tables'][str(config['call_site'])]=copy.deepcopy(config['table'])
    return dict(baseline=base,returning_control=control,local_table=candidate)


def table_examples(rows,policy,config):
    examples=[]
    fixture=config['arithmetic_fixture']
    for (av,bv),latch in itertools.product(fixture['pairs'],fixture['carry_latches']):
        outputs=[]
        for pc in table_targets(config['table']):
            row=rows[pc];cpu=Am2901(ram=[fixture['ram_fill']]*16,q=fixture['q'])
            cpu.ram[row['a']]=av;cpu.ram[row['b']]=bv
            carry=CarryInput(dict(policy,initial=latch));cin=carry.resolve(row)
            result=cpu.step(row['i'],row['a'],row['b'],fixture['external_d'],cin)
            outputs.append(dict(pc=pc,carry_in=cin,ram_b=cpu.ram[row['b']],y=result['y'],q=cpu.q))
        examples.append(dict(a=av,b=bv,carry_latch=latch,outputs=outputs))
    return examples


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/exception-study')
    parser.add_argument('--integrated-cycles',type=int,default=0)
    args=parser.parse_args()
    if args.integrated_cycles<0:parser.error('negative integration length')
    args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'exception-call.json');base=read(HERE/'results/handler-study/scenario.json')
    mapping=read(HERE/'sequencer.json');rows=decode(mapping)
    spec=config['integration'];datapath=read(HERE/f"results/independent-study/variant-{spec['variant']}.json")
    save(args.out/'evidence.json',dict(configuration=config,**evidence(decode(datapath),config)))
    alternatives=scenarios(base,config);summaries={}
    for name,scenario in alternatives.items():
        g=graph(rows,scenario);save(args.out/f'graph-{name}.json',g)
        save(args.out/f'scenario-{name}.json',scenario)
        if name=='baseline':
            previous=read(HERE/'results/handler-study/summary.json')
            if any(previous['configuration'][key]!=config[key] for key in ('seeds','cycles')):
                raise ValueError('archived baseline sampling does not match experiment')
            reached=set(previous['reached']);runs=previous['runs']
        else:
            reached=set();runs=[]
            for seed in range(config['seeds']):
                r=execute(mapping,scenario,config['cycles'],seed,trace_limit=0)
                reached.update(r['address_counts'])
                runs.append(dict(seed=seed,clean=r['clean'],coverage=r['coverage'],stack=r['stack'],trace_digest=r['trace_digest']))
        summaries[name]=dict(static_reachable=len(g['reached']),exceptions=g['exceptions'],reached=sorted(reached),
            coverage=len(reached)/1021,all_clean=all(r['clean'] for r in runs),runs=runs)
    examples={}
    for variant in range(1,5):
        m=read(HERE/f'results/independent-study/variant-{variant}.json')
        s=read(HERE/f'results/independent-study/scenario-{variant}.json')
        examples[m['name']]=table_examples(decode(m),s['inputs']['carry'],config)
    save(args.out/'table-arithmetic.json',examples)
    save(args.out/'summary.json',dict(configuration=config,comparisons=summaries,
        baseline_source='results/handler-study/summary.json; same seed range and cycle count',
        interpretation='Returning surrogate separates continuation reachability from actual target identification; local table remains a hypothesis.'))
    if args.integrated_cycles:
        s=read(HERE/f"results/independent-study/scenario-{spec['variant']}.json")
        s.update(name=alternatives['local_table']['name'],evidence=config['evidence'],dispatch=alternatives['local_table']['dispatch'],branch_tables=base['branch_tables'])
        s['io']['read']['value']=spec['external_read']
        r=execute(datapath,s,args.integrated_cycles,spec['seed'],'integrated',args.out/'integrated',128)
        print('Integrated clean:',r['clean'])
    print([(n,s['static_reachable'],len(s['reached']),s['all_clean']) for n,s in summaries.items()])

if __name__=='__main__':main()
