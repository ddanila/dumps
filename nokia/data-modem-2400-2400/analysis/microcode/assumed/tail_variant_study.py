"""Compare retained mappings at the reset path into 3BB and 287."""
import argparse
import copy
import hashlib
import tempfile
from collections import Counter
from pathlib import Path
from common import HERE, decode, read, save
from execute import execute
from defined_condition_fit import load_trace


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/tail-variant-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'tail-variant-study.json');base=read(HERE/config['scenario'])
    profiles=config['profiles'];cases=[];unions={};counts=Counter();witnesses=[]
    targets=set(read(HERE/'results/constant-condition-study/report.json')['new_words_retained'])
    decoded={name:decode(read(HERE/path)) for name,path in profiles.items()}
    with tempfile.TemporaryDirectory() as temporary:
        for profile,path in profiles.items():
            mapping=read(HERE/path);rows=decoded[profile];seen=set();union=set()
            for d in range(256):
                scenario=copy.deepcopy(base)
                scenario['io']['read'].update(value=d,pc_sequences={str(p):[d,0] for p in (0x117,0x106)},evidence=config['evidence'])
                result=execute(mapping,scenario,config['cycles'],mode='integrated',out=Path(temporary),trace_limit=config['cycles'])
                assert result['clean']
                trace=load_trace(Path(temporary));ram=[0]*16;q=0;events=[]
                for t in trace:
                    pc=t['pc'];row=rows[pc]
                    if pc in config['inspect_pcs']:
                        events.append(dict(pc=pc,cycle=t['cycle'],next_pc=t['next_pc'],test=t['test'],
                            before=dict(ram=ram[:],q=q),after=dict(registers=t['registers'],q=t['q']),
                            alu=t['alu'],carry_in=t['carry_in']))
                    for k,v in t['registers'].items():ram[int(k)]=v
                    q=t['q']
                hits=set(result['visited'])&targets;union.update(result['visited'])
                counts[profile+(' terminal' if result['final_state']['pc']==0x84 else ' nonterminal-at-bound')]+=1
                cases.append(dict(profile=profile,d=d,new_static_words=sorted(hits),final_pc=result['final_state']['pc'],events=events,trace_digest=result['trace_digest']))
                if d==1 or hits-seen:
                    name=f'{profile}-{d:02x}'
                    replay=execute(mapping,scenario,config['cycles'],mode='integrated',out=args.out/name,trace_limit=config['cycles'])
                    assert replay==result
                    witnesses.append(dict(path=name,profile=profile,d=d,new_words=sorted(hits-seen)))
                    seen.update(hits)
            unions[profile]=sorted(union)
            print(profile,{k:v for k,v in counts.items() if k.startswith(profile+' ')},'hits',*[f'{p:03X}' for p in sorted(seen)],flush=True)
    q3_case=next(c for c in cases if c['profile']=='q3' and c['d']==1)
    assert set(range(0x287,0x28b))<=set(q3_case['new_static_words'])
    for profile,want_f,want_next in [('q2',0,0x3c0),('q3',255,0x287),('q4',0,0x3c0)]:
        case=next(c for c in cases if c['profile']==profile and c['d']==1)
        events={e['pc']:e for e in case['events']}
        assert events[0x3bc]['before']['ram'][0]==255 and events[0x3bc]['before']['q']==0
        assert events[0x3be]['alu']['f']==want_f and events[0x3bf]['next_pc']==want_next
    sources=[Path(__file__),HERE/'tail-variant-study.json',HERE/config['scenario'],HERE/'results/constant-condition-study/report.json',HERE/'execute.py',HERE/'common.py',HERE.parent/'model.py']+[HERE/p for p in profiles.values()]
    save(args.out/'report.json',dict(configuration=config,runs=len(cases),counts=dict(counts),cases=cases,witnesses=witnesses,visited_unions=unions,
        operations={name:{f'{pc:03X}':{k:rows[pc][k] for k in ('i','a','b','operation','carry','carry_select')} for pc in config['inspect_pcs']} for name,rows in decoded.items()},
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='Matched zero-reset runs across all six retained mappings at constant dispatch index 12. Actual flags, optional gate, all default D bytes and early zero replies. Variant-dependent reachability distinguishes assumptions; it does not identify physical wiring.'))


if __name__=='__main__':main()
