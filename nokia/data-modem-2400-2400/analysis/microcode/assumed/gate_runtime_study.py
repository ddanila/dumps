"""Compare baseline and explicit BRT gates with actual integrated flags from reset."""
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
    parser.add_argument('--out',type=Path,default=HERE/'results/gate-runtime-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'gate-runtime-study.json');base=read(HERE/config['scenario'])
    static_scenario=read(HERE/config['static_scenario']);static_rows=decode(read(HERE/'sequencer.json'))
    base['branch_tables']=copy.deepcopy(static_scenario['branch_tables'])
    base['dispatch']['tables']=copy.deepcopy(static_scenario['dispatch']['tables'])
    baseline_graph=graph(static_rows,static_scenario);base_reached=set(baseline_graph['reached'])
    assert graph(static_rows,base)==baseline_graph
    static_scenario['condition']['brt_unconditional_gate']=config['gate']
    candidate_graph=graph(static_rows,static_scenario)
    assert len(candidate_graph['reached'])==1011 and not candidate_graph['exceptions']
    gated_graph_scenario=copy.deepcopy(base)
    gated_graph_scenario['condition']['brt_unconditional_gate']=config['gate']
    assert graph(static_rows,gated_graph_scenario)==candidate_graph
    counts=Counter();comparisons=[];unions={};new_hits=[]
    with tempfile.TemporaryDirectory() as temporary:
        for profile,path in config['mappings'].items():
            mapping=read(HERE/path);rows=decode(mapping)
            for index in range(8):
                for d in range(256):
                    results={};traces={}
                    for variant in ('baseline','gated'):
                        scenario=copy.deepcopy(base);scenario['initial']=dict(pc=0,ram=[0]*16,q=0)
                        scenario['dispatch']['value']=index
                        scenario['io']['read']=dict(mode='pc_sequence',value=d,table=[0],pc_sequences={str(p):[d,0] for p in (0x117,0x106)},sequence_end='hold-last',status='stub',evidence=config['evidence'])
                        if variant=='gated':scenario['condition']['brt_unconditional_gate']=config['gate']
                        keep=index in config['witness_indices'] and d in config['witness_values']
                        out=args.out/f'{profile}-{variant}-i{index}-d{d:02x}' if keep else Path(temporary)
                        result=execute(mapping,scenario,config['cycles'],mode='integrated',out=out,trace_limit=config['cycles'])
                        assert result['clean']
                        trace=load_trace(out);traces[variant]=trace
                        previous_zero=0;gate_events=[];seen=set()
                        for t in trace:
                            row=rows[t['pc']]
                            if variant=='gated' and unconditional_transfer(row,base) and not unconditional_transfer(row,scenario):
                                assert row['command']==6 and t['test']==1-previous_zero
                                if row['pc'] not in seen:
                                    seen.add(row['pc']);gate_events.append(dict(pc=row['pc'],cycle=t['cycle'],previous_zero=previous_zero,test=t['test'],next_pc=t['next_pc']))
                            previous_zero=t['alu']['zero']
                        new=sorted(set(result['visited'])-base_reached)
                        if new:new_hits.append(dict(profile=profile,variant=variant,index=index,d=d,pcs=new))
                        unions.setdefault(f'{profile}:{variant}',set()).update(result['visited'])
                        counts[f"{profile}:{variant}:"+('terminal' if result['final_state']['pc']==0x84 else 'nonterminal-at-bound')]+=1
                        results[variant]=dict(visited=result['visited'],final_state=result['final_state'],gate_events=gate_events,new_static_words=new,trace_digest=result['trace_digest'])
                    divergence=next((dict(cycle=a['cycle'],pc=a['pc'],baseline_next=a['next_pc'],gated_next=b['next_pc'],baseline_test=a['test'],gated_test=b['test']) for a,b in zip(traces['baseline'],traces['gated']) if a['test']!=b['test']),None)
                    if divergence:
                        assert divergence['baseline_test']==1 and divergence['gated_test']==0
                        counts[f'{profile}:decision-diverged']+=1
                    else:
                        assert results['baseline']['trace_digest']==results['gated']['trace_digest']
                    path_divergence=next((dict(cycle=a['cycle'],pc=a['pc'],baseline_next=a['next_pc'],gated_next=b['next_pc']) for a,b in zip(traces['baseline'],traces['gated']) if a['next_pc']!=b['next_pc']),None)
                    if path_divergence:counts[f'{profile}:path-diverged']+=1
                    comparisons.append(dict(profile=profile,index=index,d=d,first_decision_divergence=divergence,first_path_divergence=path_divergence,results=results))
                print(profile,index,{k:v for k,v in counts.items() if k.startswith(profile+':')},flush=True)
    sources=[Path(__file__),HERE/'gate-runtime-study.json',HERE/config['scenario'],HERE/config['static_scenario'],HERE/'sequencer.json',HERE/'execute.py',HERE/'common.py',HERE/'analyze.py',HERE.parent/'model.py']+[HERE/p for p in config['mappings'].values()]
    save(args.out/'report.json',dict(configuration=config,counts=dict(counts),visited_unions={k:sorted(v) for k,v in unions.items()},new_static_word_hits=new_hits,comparisons=comparisons,source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},interpretation='Matched reset runs use actual previous-zero conditions when the explicit gate relaxes a BRT. Coverage and divergences are bounded evidence under retained mappings, constant dispatch indices and diagnostic early replies; no physical gate or condition wiring is established.'))
    print('runs',2*len(comparisons),'new-static hits',len(new_hits))


if __name__=='__main__':main()
