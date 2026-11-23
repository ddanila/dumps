"""Test the D0/D1 call-table tail and audit the remaining disconnected words."""
import argparse
import copy
import json
from pathlib import Path
from common import HERE, decode, read, save, unconditional_transfer
from analyze import graph
from execute import execute
from rom_study import load_rom, rom_table, reconstruct_lookups
from terminal_study import paths, witness


def variants(base,data,config):
    result={}
    for name,changes in config['variants'].items():
        scenario=copy.deepcopy(base);scenario.update(name='rom-tail-'+name,evidence=config['evidence'])
        for site,spec in changes.items():scenario['dispatch']['tables'][site]=rom_table(data,spec,config)
        result[name]=scenario
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/rom-tail-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'rom-tail-search.json');data=load_rom(config)
    base=read(HERE/'results/rom-study/scenario-rom_calls.json');mapping=read(HERE/'sequencer.json');rows=decode(mapping)
    scenarios=variants(base,data,config);reports=[]
    original=graph(rows,base);missing={x['pc'] for x in original['unreachable']}
    catalog=[]
    for pc in sorted(missing):
        previous=rows[pc-1]
        refs=[dict(pc=r['pc'],command=r['command_name'],reachable=r['pc'] not in missing,
            overridden=str(r['pc']) in base['dispatch']['tables'] if r['command']==4 else str(r['pc']) in base.get('branch_tables',{}))
            for r in rows if r['command'] in (4,6) and r['direct'] and r['branch']==pc]
        catalog.append(dict(pc=pc,row=rows[pc],predecessor=previous,
            predecessor_unconditional=unconditional_transfer(previous,base),raw_direct_references=refs,
            status='unresolved',reason='No reset path under baseline declared edges; boundary facts are not an explained exception.'))
    save(args.out/'unresolved-catalog.json',catalog)
    for name,scenario in scenarios.items():
        cfg=graph(rows,scenario,include_states=True);parent=paths(cfg['state_edges'],(0,()))
        overflows={}
        for state in sorted(parent):
            pc,stack=state
            if len(stack)==4 and f'{pc:03x}: possible stack overflow' in cfg['exceptions']:
                path=witness(parent,state)
                if pc not in overflows or len(path)<len(overflows[pc]):overflows[pc]=path
        save(args.out/f'scenario-{name}.json',scenario)
        save(args.out/f'graph-{name}.json',{k:v for k,v in cfg.items() if k!='state_edges'})
        reports.append(dict(name=name,states=cfg['states'],reachable=len(cfg['reached']),exceptions=cfg['exceptions'],
            gained=sorted(set(cfg['reached'])-set(original['reached'])),remaining=[x['pc'] for x in cfg['unreachable']],overflow_witnesses=overflows))
    scenario=scenarios[config['dynamic_variant']]
    chosen=next(r for r in reports if r['name']==config['dynamic_variant'])
    if chosen['exceptions']:raise ValueError('dynamic variant has static exceptions')
    runs=[];reached=set();example=None
    for seed in range(config['witness_seed_limit']):
        if seed>=config['seeds'] and example is not None:break
        r=execute(mapping,scenario,config['cycles'],seed,'sequencer',trace_limit=0)
        if seed<config['seeds']:
            reached.update(r['address_counts']);runs.append(dict(seed=seed,clean=r['clean'],coverage=r['coverage'],stack=r['stack'],trace_digest=r['trace_digest']))
        if example is None and r['address_counts'].get(config['witness_pc']):example=seed
    lookups=[]
    if example is not None:
        execute(mapping,scenario,config['cycles'],example,'sequencer',args.out/'witness',config['cycles'])
        records=[json.loads(line) for line in (args.out/'witness/trace.jsonl').read_text().splitlines()]
        lookups=reconstruct_lookups(records,scenario,data)
    save(args.out/'summary.json',dict(configuration=config,variants=reports,runs=runs,reached=sorted(reached),
        dynamic_words=len(reached),all_clean=all(r['clean'] for r in runs),witness_seed=example,witness_lookups=lookups,
        interpretation='Site-scoped ROM ranges are hypotheses selected using stack constraints. Extra witness seeds are excluded from fixed-suite coverage; remaining words are unresolved, not explained exceptions.'))
    print([(r['name'],r['reachable'],r['exceptions']) for r in reports]);print('Dynamic words',len(reached),'witness seed',example)

if __name__=='__main__':main()
