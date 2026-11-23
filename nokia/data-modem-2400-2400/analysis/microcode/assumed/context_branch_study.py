"""Test command/condition-scoped branch-bit alternatives without changing runtime decoding."""
import argparse
import copy
from collections import deque
from pathlib import Path
from common import HERE, decode, field_value, load, read, save, table_targets, unconditional_transfer
from analyze import graph
from model import X8X02


def alternative(rows,lanes,command,select,position,token):
    result=copy.deepcopy(rows)
    for row in result:
        if row['command']==command and row['select']==select and row['direct']:
            value=field_value([token],lanes,row['pc'])
            row['branch']=(row['branch'] & ~(1<<position)) | (value<<position)
    return result


def witness(rows,scenario,target_pc):
    cfg=graph(rows,scenario,include_states=True);adjacent={}
    for source,target in cfg['state_edges']:adjacent.setdefault(source,[]).append(target)
    root=(0,());parents={root:None};queue=deque([root]);end=None
    while queue:
        state=queue.popleft()
        if state[0]==target_pc:end=state;break
        for target in sorted(adjacent.get(state,[])):
            if target not in parents:parents[target]=state;queue.append(target)
    if end is None:raise ValueError('witness target not reached')
    path=[]
    while end is not None:path.append(end);end=parents[end]
    path.reverse();seq=X8X02();steps=[]
    for source,target in zip(path,path[1:]):
        row=rows[source[0]]
        table=(scenario['dispatch']['tables'].get(str(source[0])) if row['command']==4
               else scenario.get('branch_tables',{}).get(str(source[0])) if row['command']==6 else None)
        branches=table_targets(table) if table else [row['branch']]
        choices=[]
        for branch in branches:
            for test in ([True] if unconditional_transfer(row,scenario) else [False,True]):
                trial=copy.deepcopy(seq);trial.step(row['command'],branch,test)
                depth=trial.pushes-trial.pops
                stack=tuple(trial.stack[(trial.sp-depth+1+i)&3] for i in range(depth))
                if (trial.pc,stack)==target:choices.append((trial,branch,test))
        if not choices:raise ValueError('graph witness cannot replay on sequencer')
        seq,branch,test=choices[0]
        steps.append(dict(pc=source[0],stack=list(source[1]),command=row['command'],branch=branch,
                          test=test,next_pc=seq.pc,stack_after=list(target[1])))
    return steps


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/context-branch-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'context-branch-search.json');lanes=load()
    rows=decode(read(HERE/'sequencer.json'));scenario=read(HERE/config['scenario'])
    baseline=graph(rows,scenario);reached=set(baseline['reached']);reports=[]
    contexts=sorted({(r['command'],r['select']) for r in rows
                     if r['command'] in config['commands'] and r['direct'] and not r['unused']})
    for command,select in contexts:
        for position in config['positions']:
            for chip in config['chips']:
                for bit in range(8):
                    for polarity in ('','!'):
                        token=f'{polarity}{chip}.{bit}'
                        candidate=alternative(rows,lanes,command,select,position,token)
                        cfg=graph(candidate,scenario);current=set(cfg['reached'])
                        reports.append(dict(command=command,select=select,position=position,token=token,
                            states=cfg['states'],words=len(current),exceptions=cfg['exceptions'],
                            gained=sorted(current-reached),lost=sorted(reached-current),
                            changed=[dict(pc=a['pc'],before=a['branch'],after=b['branch'])
                                     for a,b in zip(rows,candidate) if a['branch']!=b['branch']]))
    clean=[r for r in reports if not r['exceptions']]
    gains=[r for r in clean if r['gained']]
    best=next(r for r in gains if not r['lost'])
    best_rows=alternative(rows,lanes,best['command'],best['select'],best['position'],best['token'])
    groups={}
    for r in gains:
        key=tuple((c['pc'],c['after']) for c in r['changed'])
        groups.setdefault(key,[]).append(dict(command=r['command'],select=r['select'],position=r['position'],token=r['token']))
    save(args.out/'report.json',dict(configuration=config,contexts=contexts,baseline_words=len(reached),
        candidates=reports,witness=dict(candidate=best,steps=witness(best_rows,scenario,best['gained'][0])),
        gain_equivalence_groups=[dict(changed=[dict(pc=p,after=a) for p,a in k],candidates=v) for k,v in groups.items()],counts=dict(candidates=len(reports),clean=len(clean),clean_with_gains=len(gains)),
        interpretation='Static counterfactuals with fixed dispatch and condition assumptions; context switches are not recovered hardware wiring.'))
    print('candidates',len(reports),'clean gains',len(gains))
    for r in sorted(gains,key=lambda a:(-a['words'],len(a['lost'])))[:20]:
        print({k:r[k] for k in ('command','select','position','token','words','gained','lost')})


if __name__=='__main__':main()
