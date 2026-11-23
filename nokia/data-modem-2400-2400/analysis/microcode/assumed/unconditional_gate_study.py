"""Search raw-bit gates on assumed unconditional BRT, preserving calls and targets."""
import argparse
import hashlib
import itertools
from collections import Counter
from pathlib import Path
from common import HERE, decode, read, save, unconditional_transfer
from analyze import graph
from context_branch_study import witness


def bit(row,token):
    chip,position=token.lstrip('!').split('.')
    return ((row['raw'][['10','11','17','18'].index(chip)]>>int(position))&1)^token.startswith('!')


def relaxed_pcs(rows,scenario,tokens,operator):
    result=[]
    for row in rows:
        if row['command']!=6 or not unconditional_transfer(row,scenario):continue
        values=[bit(row,t) for t in tokens]
        gate=all(values) if operator=='and' else any(values)
        if not gate:result.append(row['pc'])
    return result


def policy_for(pcs):
    conditional=frozenset(pcs)
    return lambda row,scenario: unconditional_transfer(row,scenario) and row['pc'] not in conditional


def candidates():
    tokens=[f'{inv}{chip}.{position}' for chip in ('10','11','17','18') for position in range(8) for inv in ('','!')]
    for token in tokens:yield [token],'and'
    for a,b in itertools.combinations(tokens,2):
        if a.lstrip('!')==b.lstrip('!'):continue
        for operator in ('and','or'):yield [a,b],operator


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/unconditional-gate-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'unconditional-gate-study.json');scenario=read(HERE/config['scenario']);rows=decode(read(HERE/'sequencer.json'))
    baseline=graph(rows,scenario);base=set(baseline['reached']);used={r['pc'] for r in rows if not r['unused']}
    assert len(base)==999 and not baseline['exceptions']
    classes=[];by_mask={};reports=[];counts=Counter()
    for tokens,operator in candidates():
        pcs=relaxed_pcs(rows,scenario,tokens,operator);key=tuple(pcs)
        if key not in by_mask:
            g=graph(rows,scenario,unconditional_policy=policy_for(pcs));reached=set(g['reached'])
            assert base<=reached
            by_mask[key]=len(classes)
            classes.append(dict(conditional_brt=pcs,states=g['states'],used_words=len(reached&used),all_words=len(reached),gained_used=sorted((reached-base)&used),unused_reached=sorted(reached-used),exceptions=g['exceptions']))
        index=by_mask[key];item=classes[index]
        clean=not item['exceptions'];gain=bool(item['gained_used'])
        counts[f"{len(tokens)}-bit:"+('clean-gain' if clean and gain else 'clean-no-gain' if clean else 'exceptions')]+=1
        reports.append(dict(tokens=tokens,operator=operator,equivalence_class=index))
    gains=[]
    for r in reports:
        item=classes[r['equivalence_class']]
        if not item['exceptions'] and item['gained_used']:
            policy=policy_for(item['conditional_brt'])
            gains.append(dict(candidate=r,result=item,witnesses=[dict(target=p,steps=witness(rows,scenario,p,policy)) for p in item['gained_used']]))
    combinations=[]
    for size in range(2,len(gains)+1):
        for indices in itertools.combinations(range(len(gains)),size):
            pcs=sorted({p for i in indices for p in gains[i]['result']['conditional_brt']})
            cfg=graph(rows,scenario,unconditional_policy=policy_for(pcs))
            reached=set(cfg['reached'])
            combinations.append(dict(candidate_indices=list(indices),conditional_brt=pcs,used_words=len(reached&used),gained_used=sorted((reached-base)&used),unresolved=sorted(used-reached),exceptions=cfg['exceptions']))
    best=max((c for c in combinations if not c['exceptions']),key=lambda c:c['used_words'])
    combined_witnesses=[dict(target=p,steps=witness(rows,scenario,p,policy_for(best['conditional_brt']))) for p in best['gained_used']]
    all_brt=[r['pc'] for r in rows if r['command']==6 and unconditional_transfer(r,scenario)]
    diagnostic=graph(rows,scenario,unconditional_policy=policy_for(all_brt))
    sources=[Path(__file__),HERE/'unconditional-gate-study.json',HERE/'sequencer.json',HERE/config['scenario'],HERE/'analyze.py',HERE/'common.py',HERE/'context_branch_study.py',HERE.parent/'model.py']
    save(args.out/'report.json',dict(configuration=config,baseline=dict(used_words=len(base),unresolved=sorted(used-base)),counts=dict(counts),candidates=reports,equivalence_classes=classes,clean_gain_candidates=gains,combined_candidates=combinations,best_combined=best,combined_witnesses=combined_witnesses,all_brt_conditional=dict(used_words=len(set(diagnostic['reached'])&used),unused_reached=sorted(set(diagnostic['reached'])-used),exceptions=diagnostic['exceptions']),source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},interpretation='Raw-bit gates relax only the assumed unconditional BRT class. Four two-bit gates add clean static paths, up to 1009 used words individually and 1011 when composed. Conditions remain scenario choices; no physical gate, datapath flag relation, or runtime default is selected.'))
    print(dict(counts),'classes',len(classes),'clean gains',len(gains),'best single',max(g['result']['used_words'] for g in gains),'best combined',best['used_words'])


if __name__=='__main__':main()
