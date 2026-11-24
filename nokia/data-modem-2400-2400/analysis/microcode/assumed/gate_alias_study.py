"""Bound raw-only gate extensions using identical words; target unique 257."""
import argparse
import hashlib
import itertools
from pathlib import Path
from common import HERE, decode, read, save, unconditional_transfer
from analyze import graph
from context_branch_study import witness
from unconditional_gate_study import bit, policy_for


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/gate-alias-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    scenario_path='results/three-bit-gate-study/scenario.json'
    scenario=read(HERE/scenario_path);rows=decode(read(HERE/'sequencer.json'))
    base=graph(rows,scenario);assert len(base['reached'])==1016 and not base['exceptions']
    diagnostic=graph(rows,scenario,unconditional_policy=policy_for([r['pc'] for r in rows if r['command']==6]))
    remaining_entries={pc:sorted({a for a,b,k in diagnostic['edges'] if b==pc}) for pc in (0xfd,0xfe,0xff,0x2df)}
    assert remaining_entries=={0xfd:[0xfc],0xfe:[0xfd],0xff:[0xfe],0x2df:[0x2de]}
    aliases=[]
    for pc,failure in ((0xfc,0x220),(0x2de,0x2ff)):
        group=[r['pc'] for r in rows if r['raw']==rows[pc]['raw']]
        assert all(unconditional_transfer(rows[p],scenario) for p in group)
        policy=policy_for(group);cfg=graph(rows,scenario,unconditional_policy=policy)
        path=witness(rows,scenario,failure,policy,target_stack=())
        assert path[-1]['stack_after']==[] and rows[failure]['command']==3
        assert f'{failure:03x}: possible stack underflow' in cfg['exceptions']
        aliases.append(dict(pc=pc,identical_words=group,raw=rows[pc]['raw'],exceptions=cfg['exceptions'],
            reached_words=len(cfg['reached']),failure_pc=failure,empty_stack_witness=path))
    # Any raw-only relaxation at these sites includes its entire identical-word
    # class. More relaxed tests add graph edges and cannot remove these witnesses.
    active=[r for r in rows if r['command']==6 and unconditional_transfer(r,scenario)]
    tokens=[f'{chip}.{b}' for chip in (10,11,17,18) for b in range(8)]
    false_tokens=[('!' if bit(rows[0x257],t) else '')+t for t in tokens]
    masks={t:sum((not bit(r,t))<<i for i,r in enumerate(active)) for t in false_tokens}
    classes={};candidate_count=0
    for clause in itertools.combinations(false_tokens,4):
        mask=masks[clause[0]]&masks[clause[1]]&masks[clause[2]]&masks[clause[3]]
        if mask not in classes:
            pcs=[r['pc'] for i,r in enumerate(active) if (mask>>i)&1]
            assert 0x257 in pcs
            cfg=graph(rows,scenario,unconditional_policy=policy_for(pcs))
            classes[mask]=dict(clause=list(clause),conditional_brt=pcs,words=len(cfg['reached']),
                exceptions=cfg['exceptions'],equivalent_clauses=0)
        classes[mask]['equivalent_clauses']+=1;candidate_count+=1
    clean=[r for r in classes.values() if not r['exceptions']]
    best=min(clean,key=lambda r:(-r['words'],len(r['conditional_brt']),r['clause']))
    candidate=read(HERE/scenario_path)
    candidate['condition']['brt_unconditional_gate']['clauses'].append(best['clause'])
    candidate['condition']['brt_unconditional_gate']['evidence']='Targeted four-literal OR extension for 257 after the raw-alias obstruction study. Structural hypothesis only; no physical wiring claim.'
    cfg=graph(rows,candidate)
    assert cfg==graph(rows,scenario,unconditional_policy=policy_for(best['conditional_brt']))
    gained=sorted(set(cfg['reached'])-set(base['reached']))
    paths={f'{pc:03X}':witness(rows,candidate,pc) for pc in gained}
    save(args.out/'scenario.json',candidate)
    sources=[Path(__file__),HERE/scenario_path,HERE/'sequencer.json',HERE/'common.py',HERE/'analyze.py',HERE/'context_branch_study.py',HERE/'unconditional_gate_study.py',HERE.parent/'model.py']
    save(args.out/'report.json',dict(alias_obstructions=aliases,all_brt_conditional_entries=remaining_entries,
        diagnostic_words=len(diagnostic['reached']),diagnostic_exceptions=diagnostic['exceptions'],candidates=candidate_count,unique_masks=len(classes),
        clean_clauses=sum(r['equivalent_clauses'] for r in clean),clean_masks=len(clean),classes=list(classes.values()),
        best=best,gained=gained,remaining=[r['pc'] for r in cfg['unreachable']],witnesses=paths,
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='Raw-only unconditional-to-conditional BRT relaxations with fixed targets/tables and free tests. Identical-word classes force underflow witnesses, which further edge additions cannot remove. Four-bit search is targeted to clauses false at 257, not all possible four-bit gates. Runtime defaults unchanged.'))
    print('candidates',candidate_count,'classes',len(classes),'clean clauses',sum(r['equivalent_clauses'] for r in clean),'best',best,flush=True)


if __name__=='__main__':main()
