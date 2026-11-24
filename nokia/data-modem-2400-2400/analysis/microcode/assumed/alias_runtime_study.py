"""Test the 0FC identical-word class with actual flags at reset index 3."""
import argparse
import copy
import hashlib
import itertools
import tempfile
from collections import Counter
from pathlib import Path
from common import HERE, decode, read, save, unconditional_transfer
from analyze import graph
from unconditional_gate_study import bit
from execute import execute
from defined_condition_fit import load_trace


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/alias-runtime-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'alias-runtime-study.json');base=read(HERE/config['scenario'])
    gate_scenario=read(HERE/config['gate_scenario']);base['condition']['brt_unconditional_gate']=copy.deepcopy(gate_scenario['condition']['brt_unconditional_gate'])
    rows=decode(read(HERE/'sequencer.json'));active=[r for r in rows if r['command']==6 and unconditional_transfer(r,base)]
    aliases=[r['pc'] for r in active if r['raw']==rows[0xfc]['raw']]
    tokens=[f'{chip}.{b}' for chip in (10,11,17,18) for b in range(8)]
    tokens=[('!' if bit(rows[0xfc],t) else '')+t for t in tokens]
    masks={t:sum((not bit(r,t))<<i for i,r in enumerate(active)) for t in tokens}
    want=sum((r['pc'] in aliases)<<i for i,r in enumerate(active));sizes=[];winners=[]
    for size in range(1,5):
        tested=0;winners=[]
        for clause in itertools.combinations(tokens,size):
            mask=(1<<len(active))-1
            for t in clause:mask &=masks[t]
            tested+=1
            if mask==want:winners.append(list(clause))
        sizes.append(dict(literals=size,tested=tested,matching_clauses=len(winners)))
        if winners:break
    assert config['clause'] in winners
    extended=copy.deepcopy(base)
    extended['condition']['brt_unconditional_gate']['clauses'].append(config['clause'])
    extended['condition']['brt_unconditional_gate']['evidence']=config['evidence']
    cfg=graph(rows,extended)
    assert len(cfg['reached'])==1020 and cfg['exceptions']
    save(args.out/'extended-scenario.json',extended)
    cases=[];counts=Counter();unions={};witnesses=[]
    with tempfile.TemporaryDirectory() as temporary:
        for profile,path in config['profiles'].items():
            mapping=read(HERE/path);union=set()
            for d in range(256):
                outcomes={}
                for variant,template in (('previous',base),('extended',extended)):
                    scenario=copy.deepcopy(template)
                    scenario['io']['read'].update(value=d,pc_sequences={str(p):[d,0] for p in (0x117,0x106)},evidence=config['evidence'])
                    out=args.out/f'{profile}-{variant}-ff' if d==255 else Path(temporary)
                    result=execute(mapping,scenario,256,mode='integrated',out=out,trace_limit=256)
                    trace=load_trace(out);outcomes[variant]=result
                    if variant=='extended':union.update(result['visited'])
                    counts[f"{profile}:{variant}:"+('clean' if result['clean'] else 'errors')]+=1
                    counts[f"{profile}:{variant}:"+('terminal' if result['final_state']['pc']==0x84 else 'nonterminal-at-bound')]+=1
                    events=[];previous=None
                    for t in trace:
                        if t['pc'] in aliases or 0xfa<=t['pc']<=0xff:
                            events.append(dict(pc=t['pc'],next_pc=t['next_pc'],q=t['q'],test=t['test'],alu=t['alu'],
                                previous_pc=previous['pc'],previous_alu=previous['alu'],registers=t['registers'],stack_depth=t['stack_after']['depth']))
                            if variant=='extended' and t['pc'] in aliases:assert t['test']==1-previous['alu']['zero']
                        previous=t
                    cases.append(dict(profile=profile,variant=variant,d=d,clean=result['clean'],final_pc=result['final_state']['pc'],
                        new_words=sorted(set(result['visited'])&{0xfd,0xfe,0xff}),events=events,trace_digest=result['trace_digest']))
                    if d==255:witnesses.append(f'{profile}-{variant}-ff')
                if outcomes['previous']['trace_digest']!=outcomes['extended']['trace_digest']:counts[f'{profile}:changed']+=1
            unions[profile]=sorted(union)
            print(profile,{k:v for k,v in counts.items() if k.startswith(profile+':')},flush=True)
    example=next(c for c in cases if c['profile']=='fitted_swapped' and c['variant']=='extended' and c['d']==255)
    assert example['clean'] and example['new_words']==[0xfd,0xfe,0xff] and example['final_pc']==0x84
    sources=[Path(__file__),HERE/'alias-runtime-study.json',HERE/config['scenario'],HERE/config['gate_scenario'],HERE/'sequencer.json',HERE/'execute.py',HERE/'common.py',HERE/'analyze.py',HERE/'unconditional_gate_study.py',HERE.parent/'model.py']+[HERE/p for p in config['profiles'].values()]
    save(args.out/'report.json',dict(configuration=config,alias_class=aliases,minimal_clause_search=sizes,minimal_clauses=winners,
        static_words=len(cfg['reached']),static_exceptions=cfg['exceptions'],static_remaining=[r['pc'] for r in cfg['unreachable']],
        runs=len(cases),counts=dict(counts),cases=cases,extended_visited_unions=unions,witnesses=witnesses,
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='Actual flags at constant dispatch index 3 across all byte inputs and retained mappings. Clean sampled runs do not remove the explicit conservative graph underflows or prove global safety. Raw-bit gate is an optional hypothesis, not physical wiring.'))


if __name__=='__main__':main()
