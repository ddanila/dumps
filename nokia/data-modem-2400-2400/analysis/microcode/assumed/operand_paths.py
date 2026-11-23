"""Check source-writer connectivity without merging different return stacks."""
import argparse
from collections import defaultdict, deque
from pathlib import Path
from common import HERE, decode, read, save
from analyze import graph


def ancestors(edges, targets):
    reverse=defaultdict(set)
    states=set()
    for before,after in edges:
        reverse[after].add(before);states.update((before,after))
    todo=deque(s for s in states if s[0] in targets);seen=set()
    while todo:
        state=todo.popleft()
        if state in seen:continue
        seen.add(state);todo.extend(reverse[state])
    return seen


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/operand-paths')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'operand-search.json')
    scenario=read(HERE/'results/rom-study/scenario-rom_calls.json')
    reports=[]
    for variant in config['variants']:
        mapping=read(HERE/f'results/independent-study/variant-{variant}.json');rows=decode(mapping)
        cfg=graph(rows,scenario,include_states=True)
        # A truncated graph cannot establish that no path exists.
        if cfg['exceptions']:raise ValueError(f"graph not exhaustive and clean: {cfg['exceptions']}")
        reachable=ancestors(cfg['state_edges'],set(config['sites']))
        writers=[dict(pc=r['pc'],a=r['a'],b=r['b'],instruction=r['i'],
            reset_reachable=r['pc'] in cfg['reached'],
            can_precede_call=any(state[0]==r['pc'] for state in reachable))
            for r in rows if r['b'] in range(10,14) and r['i']>>6>=2]
        report=dict(mapping=mapping['name'],states=cfg['states'],exceptions=cfg['exceptions'],
            ancestor_states=sorted(reachable),writers=writers,
            writer_count=len(writers),connected_writer_count=sum(w['can_precede_call'] for w in writers),
            targets=config['sites'])
        save(args.out/f'variant-{variant}.json',report);reports.append({k:v for k,v in report.items() if k not in ('ancestor_states','writers')})
    save(args.out/'summary.json',dict(scenario='results/rom-study/scenario-rom_calls.json',comparisons=reports,
        interpretation='Exhaustive within declared control-flow edges and four-entry stack; no claim about missing hardware edges or operand decode.'))
    print(reports)

if __name__=='__main__':main()
