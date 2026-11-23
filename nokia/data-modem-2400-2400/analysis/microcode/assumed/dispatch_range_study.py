"""Test full byte dispatch indices and exhaustive input at witness-compatible index 12."""
import argparse
import copy
import hashlib
import tempfile
from collections import Counter
from pathlib import Path
from common import HERE, decode, read, save, table_targets
from execute import execute
from defined_condition_fit import load_trace


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/dispatch-range-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'dispatch-range-study.json');runtime_config=read(HERE/'gate-runtime-study.json')
    base=read(HERE/'results/constant-condition-study/gated-scenario.json')
    graph_report=read(HERE/'results/constant-condition-study/report.json')
    targets=set(graph_report['new_words_retained']);allowed=set(graph_report['variants']['gated']['reached'])
    fixtures=sorted({(i,d) for i in range(256) for d in config['sample_bytes']} | {(12,d) for d in range(256)})
    cases=[];unions={};counts=Counter();witnesses=[]
    with tempfile.TemporaryDirectory() as temporary:
        for profile,path in runtime_config['mappings'].items():
            mapping=read(HERE/path);seen=set();union=set()
            for index,d in fixtures:
                scenario=copy.deepcopy(base);scenario['initial']=dict(pc=0,ram=[0]*16,q=0)
                scenario['dispatch'].update(mode='constant',source='scenario',value=index)
                scenario['io']['read']=dict(mode='pc_sequence',value=d,table=[0],pc_sequences={str(p):[d,0] for p in (0x117,0x106)},sequence_end='hold-last',status='stub',evidence=config['evidence'])
                result=execute(mapping,scenario,config['cycles'],mode='integrated',out=Path(temporary),trace_limit=config['cycles'])
                assert result['clean'] and set(result['visited'])<=allowed
                trace=load_trace(Path(temporary));visited=set(result['visited']);union.update(visited)
                hits=visited&targets;new=hits-seen
                terminal=result['final_state']['pc']==0x84
                counts[f'{profile}:'+('terminal' if terminal else 'nonterminal-at-bound')]+=1
                if new:
                    name=f'{profile}-i{index:02x}-d{d:02x}'
                    replay=execute(mapping,scenario,config['cycles'],mode='integrated',out=args.out/name,trace_limit=config['cycles'])
                    assert replay==result
                    witnesses.append(dict(path=name,profile=profile,index=index,d=d,new_words=sorted(new)))
                    seen.update(new)
                cases.append(dict(profile=profile,index=index,d=d,new_static_words=sorted(hits),terminal=terminal,
                    final_pc=result['final_state']['pc'],trace_digest=result['trace_digest'],
                    dispatches=[dict(pc=t['pc'],entry=t['dispatch_entry'],next_pc=t['next_pc']) for t in trace if t.get('dispatch_entry') is not None]))
            unions[profile]=sorted(union)
            print(profile,dict(counts),'new words',*[f'{p:03X}' for p in sorted(seen)],flush=True)
    sources=[Path(__file__),HERE/'dispatch-range-study.json',HERE/'gate-runtime-study.json',
        HERE/'results/constant-condition-study/gated-scenario.json',HERE/'results/constant-condition-study/report.json',
        HERE/'execute.py',HERE/'common.py',HERE.parent/'model.py']+[HERE/p for p in runtime_config['mappings'].values()]
    save(args.out/'report.json',dict(configuration=config,runs=len(cases),counts=dict(counts),cases=cases,
        visited_unions=unions,witnesses=witnesses,
        table_sizes={f'{int(k):03X}':len(table_targets(v)) for k,v in {**base['dispatch']['tables'],**base['branch_tables']}.items()},
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='Actual integrated flags with optional BRT gate, byte-wide constant dispatch indices and diagnostic early read replies. All index bytes are sampled; only index 12 has exhaustive input-byte coverage. A global constant index is a stub, not recovered hardware.'))


if __name__=='__main__':main()
