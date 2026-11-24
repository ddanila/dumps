"""Retain successful and failing reset runs when the 2DE alias class falls through."""
import argparse
import copy
import hashlib
import tempfile
from collections import Counter
from pathlib import Path
from common import HERE, decode, read, save, unconditional_transfer
from analyze import graph
from execute import execute
from defined_condition_fit import load_trace


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/last-entry-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'last-entry-study.json');base=read(HERE/config['scenario'])
    base['condition']['brt_unconditional_gate']=copy.deepcopy(read(HERE/config['gate_scenario'])['condition']['brt_unconditional_gate'])
    extended=copy.deepcopy(base);extended['condition']['brt_unconditional_gate']['clauses'].append(config['clause'])
    extended['condition']['brt_unconditional_gate']['evidence']=config['evidence']
    rows=decode(read(HERE/'sequencer.json'));aliases=[r['pc'] for r in rows if unconditional_transfer(r,base) and not unconditional_transfer(r,extended)]
    assert aliases==[r['pc'] for r in rows if r['raw']==rows[0x2de]['raw']]
    cfg=graph(rows,extended);assert not cfg['unreachable'] and cfg['exceptions']
    save(args.out/'extended-scenario.json',extended)
    cases=[];counts=Counter();witnesses=[]
    with tempfile.TemporaryDirectory() as temporary:
        for profile,path in config['profiles'].items():
            mapping=read(HERE/path)
            for d in range(256):
                for variant,template in (('previous',base),('extended',extended)):
                    scenario=copy.deepcopy(template)
                    scenario['io']['read'].update(value=d,pc_sequences={str(p):[d,0] for p in (0x117,0x106)},evidence=config['evidence'])
                    keep=d in (0,255);name=f'{profile}-{variant}-{d:02x}'
                    out=args.out/name if keep else Path(temporary)
                    result=execute(mapping,scenario,512,mode='integrated',out=out,trace_limit=512)
                    trace=load_trace(out);entered=0x2df in result['visited']
                    outcome='error' if not result['clean'] else 'terminal' if result['final_state']['pc']==0x84 else 'nonterminal-at-bound'
                    counts[f'{profile}:{variant}:{outcome}']+=1
                    cases.append(dict(profile=profile,variant=variant,d=d,outcome=outcome,entered_2df=entered,
                        stop=result['stop'],completed_cycles=result['completed_cycles'],final_pc=result['final_state']['pc'],
                        stack=result['stack'],trace_digest=result['trace_digest'],
                        events=[dict(pc=t['pc'],cycle=t['cycle'],next_pc=t['next_pc'],test=t['test'],q=t['q'],alu=t['alu'],registers=t['registers'],stack_depth=t['stack_after']['depth']) for t in trace if t['pc'] in (0x2de,0x2df,0x2e0,0x2e1,0x2e4,0x2e5,0x2e6,0x2eb,0x2fd,0x2fe,0x2ff)]))
                    if keep:witnesses.append(name)
            print(profile,{k:v for k,v in counts.items() if k.startswith(profile+':')},flush=True)
    for profile in ('q3','q4'):
        case=next(c for c in cases if c['profile']==profile and c['variant']=='extended' and c['d']==255)
        assert case['entered_2df'] and case['outcome']=='terminal'
    sources=[Path(__file__),HERE/'last-entry-study.json',HERE/config['scenario'],HERE/config['gate_scenario'],HERE/'sequencer.json',HERE/'execute.py',HERE/'common.py',HERE/'analyze.py',HERE.parent/'model.py']+[HERE/p for p in config['profiles'].values()]
    save(args.out/'report.json',dict(configuration=config,alias_class=aliases,static_words=len(cfg['reached']),static_exceptions=cfg['exceptions'],
        runs=len(cases),counts=dict(counts),cases=cases,witnesses=witnesses,
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='Diagnostic extension admits every used word structurally, but explicitly fails for many inputs/mappings. Successful q3/q4 reset witnesses at FF do not establish global safety or physical wiring. Errors are retained without stack repair.'))


if __name__=='__main__':main()
