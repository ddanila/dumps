"""Search three-literal OR clauses extending the existing optional BRT gate."""
import argparse
import hashlib
import itertools
from collections import Counter
from pathlib import Path
from common import HERE, decode, read, save, unconditional_transfer
from analyze import graph
from context_branch_study import witness
from unconditional_gate_study import bit, policy_for


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/three-bit-gate-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    scenario_path='results/constant-condition-study/gated-scenario.json'
    scenario=read(HERE/scenario_path);rows=decode(read(HERE/'sequencer.json'))
    baseline=graph(rows,scenario);base=set(baseline['reached'])
    assert len(base)==1011 and not baseline['exceptions']
    active=[r for r in rows if r['command']==6 and unconditional_transfer(r,scenario)]
    tokens=[f'{chip}.{b}' for chip in (10,11,17,18) for b in range(8)]
    masks={token:sum((not bit(row,token))<<i for i,row in enumerate(active)) for token in tokens}
    full=(1<<len(active))-1
    masks.update({'!'+token:full^mask for token,mask in list(masks.items())})
    classes={};counts=Counter();candidate_count=0
    for fields in itertools.combinations(tokens,3):
        for inversions in itertools.product(('', '!'),repeat=3):
            clause=[inv+t for inv,t in zip(inversions,fields)]
            mask=masks[clause[0]]&masks[clause[1]]&masks[clause[2]]
            if mask not in classes:
                pcs=[r['pc'] for i,r in enumerate(active) if (mask>>i)&1]
                cfg=graph(rows,scenario,unconditional_policy=policy_for(pcs))
                reached=set(cfg['reached'])
                classes[mask]=dict(clause=clause,conditional_brt=pcs,states=cfg['states'],words=len(reached),
                    gained=sorted(reached-base),exceptions=cfg['exceptions'],equivalent_clauses=0)
            result=classes[mask];result['equivalent_clauses']+=1;candidate_count+=1
            counts['exceptions' if result['exceptions'] else 'clean-gain' if result['gained'] else 'clean-no-gain']+=1
    gains=[r for r in classes.values() if r['gained'] and not r['exceptions']]
    print('candidates',candidate_count,'classes',len(classes),'counts',dict(counts),'clean gain classes',len(gains),flush=True)
    # Evaluate every pair of clean improving classes, preserving actual stack checks.
    pairs=[]
    for a,b in itertools.combinations(range(len(gains)),2):
        pcs=sorted(set(gains[a]['conditional_brt'])|set(gains[b]['conditional_brt']))
        cfg=graph(rows,scenario,unconditional_policy=policy_for(pcs))
        pairs.append(dict(indices=[a,b],conditional_brt=pcs,words=len(cfg['reached']),exceptions=cfg['exceptions']))
    options=[dict(indices=[i],conditional_brt=r['conditional_brt'],words=r['words'],exceptions=[]) for i,r in enumerate(gains)]
    options.extend(p for p in pairs if not p['exceptions'])
    best=min(options,key=lambda r:(-r['words'],len(r['indices']),len(r['conditional_brt']),r['indices']))
    selected=[gains[i]['clause'] for i in best['indices']]
    candidate=read(HERE/scenario_path)
    candidate['condition']['brt_unconditional_gate']['clauses'].extend(selected)
    candidate['condition']['brt_unconditional_gate']['evidence']='Three-bit OR extension selected by clean structural reachability. Branch-address correlations are not physical wiring evidence; no runtime default is changed.'
    cfg=graph(rows,candidate)
    assert cfg==graph(rows,scenario,unconditional_policy=policy_for(best['conditional_brt']))
    gained=sorted(set(cfg['reached'])-base)
    paths={f'{pc:03X}':witness(rows,candidate,pc) for pc in gained}
    save(args.out/'scenario.json',candidate)
    sources=[Path(__file__),HERE/scenario_path,HERE/'sequencer.json',HERE/'common.py',HERE/'analyze.py',HERE/'context_branch_study.py',HERE/'unconditional_gate_study.py',HERE.parent/'model.py']
    save(args.out/'report.json',dict(candidate_count=candidate_count,unique_masks=len(classes),counts=dict(counts),
        equivalence_classes=list(classes.values()),clean_gain_classes=gains,pairs=pairs,best=best,selected_clauses=selected,
        gained=gained,remaining=[r['pc'] for r in cfg['unreachable']],witnesses=paths,
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='Three distinct raw-bit OR clauses, appended to the prior gate; all pairwise combinations of clean improving mask classes checked. Freely chosen flags and dispatch entries. No physical wiring, integrated feasibility or runtime-default promotion claimed.'))
    print('best',best,'clauses',selected,'remaining',[f"{r['pc']:03X}" for r in cfg['unreachable']],flush=True)


if __name__=='__main__':main()
