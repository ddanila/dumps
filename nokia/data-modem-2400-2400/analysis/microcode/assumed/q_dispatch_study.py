"""Trace the 2A8 Q input through the 26F dispatch and conditional tails."""
import argparse
import copy
import hashlib
import json
import tempfile
from collections import Counter
from pathlib import Path
from common import HERE, decode, read, save
from execute import execute
from defined_condition_fit import load_trace


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/q-dispatch-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'q-dispatch-study.json');base=read(HERE/config['scenario']);mapping=read(HERE/config['mapping'])
    rows=decode(mapping);targets=set(read(HERE/'results/constant-condition-study/report.json')['new_words_retained'])
    reports=[];witnesses=[];counts=Counter();unions={}
    with tempfile.TemporaryDirectory() as temporary:
        for source in config['sources']:
            union=set()
            for value in range(256):
                scenario=copy.deepcopy(base)
                scenario['io']['read']['pc_sequences'][str(0x2a8)]=[value]
                scenario['io']['read']['evidence']=config['evidence']
                table=scenario['branch_tables'][str(0x26f)]
                table.update(index_source=source,status='hypothesis',evidence=config['evidence'])
                if source=='previous_y':scenario['dispatch']['initial_y']=0
                out=Path(temporary)
                result=execute(mapping,scenario,config['cycles'],mode='integrated',out=out,trace_limit=config['cycles'])
                assert result['clean']
                trace=load_trace(out);visited=set(result['visited']);union.update(visited)
                events=[];ram=[0]*16;previous=None;last_q=None
                for t in trace:
                    pc=t['pc'];row=rows[pc]
                    if pc==0x2a8:assert t['q']==value
                    if pc==0x26f:
                        assert t['q']==value and t['alu']['y']==0
                        assert previous['pc']==0x26e
                        expected=12 if source=='scenario' else value if source=='q' else previous['alu']['y'] if source=='previous_y' else 0
                        assert t['dispatch_input']==expected and t['dispatch_entry']==expected%16
                    if pc==0x2ce:
                        assert previous['pc']==0x2cd and previous['alu']['f']==value
                        assert t['test']==int(value!=0)
                    if pc==0x2cf:
                        assert t['q']==0 and t['alu']['f']==1 and not t['registers']
                    if pc==0x3bc:
                        assert last_q==0x2f3 and t['q']==0 and ram[0]==255
                        assert previous['pc']==0x3bb and previous['alu']['zero']==1
                    if pc in (0x26f,0x286,0x2ce,0x3bc,0x3bf) or pc in targets:
                        events.append(dict(pc=pc,next_pc=t['next_pc'],test=t['test'],q=t['q'],ram0=ram[0],previous_pc=previous['pc'],previous_alu=previous['alu'],alu=t['alu'],last_q_writer=last_q))
                    if row['i']>>6 in (0,4,6):last_q=pc
                    for k,v in t['registers'].items():ram[int(k)]=v
                    previous=t
                hits=sorted(visited&targets)
                terminal=result['final_state']['pc']==0x84
                counts[source+(' terminal' if terminal else ' nonterminal-at-bound')]+=1
                semantic_digest=hashlib.sha256(json.dumps([{k:v for k,v in t.items() if k!='dispatch_source'} for t in trace],sort_keys=True).encode()).hexdigest()
                reports.append(dict(semantic_digest=semantic_digest,source=source,value=value,new_static_words=hits,events=events,terminal=terminal,final_pc=result['final_state']['pc'],trace_digest=result['trace_digest']))
                if value in config['witness_values']:
                    name=f'{source}-{value:02x}'
                    replay=execute(mapping,scenario,config['cycles'],mode='integrated',out=args.out/name,trace_limit=config['cycles'])
                    assert replay==result
                    witnesses.append(name)
            unions[source]=sorted(union)
            print(source,dict(counts),flush=True)
    q_cases=[r for r in reports if r['source']=='q'];previous_cases=[r for r in reports if r['source']=='previous_y']
    assert all(a['semantic_digest']==b['semantic_digest'] for a,b in zip(q_cases,previous_cases))
    paths=[Path(__file__),HERE/'q-dispatch-study.json',HERE/config['scenario'],HERE/config['mapping'],HERE/'results/constant-condition-study/report.json',HERE/'execute.py',HERE/'common.py',HERE.parent/'model.py']
    save(args.out/'report.json',dict(configuration=config,runs=len(reports),counts=dict(counts),cases=reports,witnesses=witnesses,visited_unions=unions,
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        interpretation='Reset executions under q2 and optional BRT gate; one PC-keyed read byte varies, with a site-scoped 26F dispatch source hypothesis. Actual flags and stack transitions are retained; physical input channel and index source remain unknown.'))


if __name__=='__main__':main()
