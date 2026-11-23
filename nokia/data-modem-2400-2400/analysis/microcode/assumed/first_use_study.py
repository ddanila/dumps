"""Find potential operand reads before replacement, preserving return context."""
import argparse
from collections import defaultdict, deque
from pathlib import Path
from common import HERE, decode, read, save
from analyze import graph


def accesses(row):
    source=row['i']&7;dest=(row['i']>>6)&7
    reads=set()
    if source in (0,1,4,5) or dest==2:reads.add(f"R{row['a']}")
    if source in (1,3):reads.add(f"R{row['b']}")
    if source in (0,2,6) or dest in (4,6):reads.add('Q')
    writes=set()
    if dest>=2:writes.add(f"R{row['b']}")
    if dest in (0,4,6):writes.add('Q')
    return reads,writes


def first_access(rows, edges, start, location):
    successors=defaultdict(set)
    for before,after in edges:successors[before].add(after)
    todo=deque([start]);parent={start:None};reads={};overwrites={}
    while todo:
        state=todo.popleft();pc,stack=state
        uses,stores=accesses(rows[pc])
        kind='read' if location in uses else 'overwrite' if location in stores else None
        if kind:
            path=[];cursor=state
            while cursor is not None:path.append(cursor);cursor=parent[cursor]
            target=reads if kind=='read' else overwrites
            target[state]=dict(pc=pc,stack=stack,path=list(reversed(path)),instruction=rows[pc])
            continue
        for after in sorted(successors[state]):
            if after not in parent:parent[after]=state;todo.append(after)
    return dict(location=location,visited_states=len(parent),reads=list(reads.values()),overwrites=list(overwrites.values()),
        interpretation='Potential operand accesses, not proven numerical dependence. Cycles without access may persist; this is not an all-path liveness proof.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/first-use-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'first-use-search.json');scenario=read(HERE/'results/rom-study/scenario-rom_calls.json');reports=[]
    for profile in config['profiles']:
        mapping=read(HERE/f"results/preparation-study/{profile['mapping']}.json")
        if profile['swap']:mapping['fields']['a'],mapping['fields']['b']=mapping['fields']['b'],mapping['fields']['a']
        rows=decode(mapping);cfg=graph(rows,scenario,start=config['start'],include_states=True)
        if cfg['exceptions']:raise ValueError(cfg['exceptions'])
        reports.append(dict(profile=profile,graph_states=cfg['states'],exceptions=cfg['exceptions'],
            locations=[first_access(rows,cfg['state_edges'],(config['start'],()),location) for location in profile['locations']]))
    save(args.out/'summary.json',dict(configuration=config,profiles=reports))
    from chain_study import run_chain
    from rotation_study import scenario_for
    for name,spec in config['witnesses'].items():
        caller=read(HERE/'single-caller-search.json');fixture=caller['fixture']
        fixture.update(stop=spec['stop'],checkpoints=spec['checkpoints'])
        fixture['condition_overrides'].update({str(pc):(spec['condition_mask']>>i)&1 for i,pc in enumerate(caller['condition_sites'])})
        fixture['condition_overrides'].update(spec['condition_overrides'])
        mapping=read(HERE/f"results/preparation-study/{spec['mapping']}.json")
        if spec['swap']:mapping['fields']['a'],mapping['fields']['b']=mapping['fields']['b'],mapping['fields']['a']
        scenario=scenario_for(mapping,read(HERE/'rotation-search.json'))
        entries={str(caller['dispatch_site']):spec['entry']}
        save(args.out/f'witness-{name}.json',dict(configuration=fixture,mapping=mapping['name'],swap=spec['swap'],
            zero=run_chain(decode(mapping),scenario,fixture,entries,[0]*4,spec['q'],True),
            marked=run_chain(decode(mapping),scenario,fixture,entries,spec['data'],spec['q'],True)))
    for report in reports:
        print(report['profile'],[(r['location'],sorted({f"{x['pc']:03X}" for x in r['reads']}),sorted({f"{x['pc']:03X}" for x in r['overwrites']})) for r in report['locations']])

if __name__=='__main__':main()
