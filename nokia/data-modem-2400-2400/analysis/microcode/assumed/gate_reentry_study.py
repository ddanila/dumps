"""Compare the unique-257 gate extension over every preceding Q-input byte."""
import argparse
import copy
import hashlib
import tempfile
from collections import Counter
from pathlib import Path
from common import HERE, read, save
from execute import execute
from defined_condition_fit import load_trace


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/gate-reentry-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    scenario_path='results/adjustment-entry-study/fixed-read-extended-fc/scenario.json'
    mapping_path='results/independent-study/variant-2.json'
    base=read(HERE/scenario_path);mapping=read(HERE/mapping_path)
    gate_path='results/gate-alias-study/scenario.json'
    gate=read(HERE/gate_path)['condition']['brt_unconditional_gate']
    cases=[];counts=Counter();changed=[]
    with tempfile.TemporaryDirectory() as temporary:
        for d in range(256):
            traces={};digests={}
            for variant in ('previous','extended'):
                scenario=copy.deepcopy(base);scenario['io']['read']['pc_sequences'][str(0x235)]=[d]
                scenario['io']['read']['evidence']='Sweep the 235 Q-input byte with the prior input setup; compare the three-bit and four-bit gate scenarios. Diagnostic inputs, not recovered physical channels.'
                if variant=='extended':scenario['condition']['brt_unconditional_gate']=gate
                out=args.out/f'{variant}-fc' if d==252 else Path(temporary)
                result=execute(mapping,scenario,256,mode='integrated',out=out,trace_limit=256)
                assert result['clean'] and result['final_state']['pc']==0x84
                trace=load_trace(out);traces[variant]=trace;digests[variant]=result['trace_digest']
                entries=[t for t in trace if t['pc']==0x258]
                assert bool(entries)==(variant=='extended' and d==252)
                for t in entries:
                    assert t['alu']['f']==255 and t['q']==255 and not t['registers']
                    assert t['stack_after']['depth']==0 and t['next_pc']==0x259
                counts[variant+':terminal']+=1
                cases.append(dict(variant=variant,d235=d,trace_digest=result['trace_digest'],visited=result['visited'],
                    events=[t for t in trace if t['pc'] in (0x257,0x258,0x259)]))
            if digests['previous']!=digests['extended']:
                divergence=next((dict(cycle=a['cycle'],pc=a['pc'],previous_next=a['next_pc'],extended_next=b['next_pc']) for a,b in zip(traces['previous'],traces['extended']) if a['next_pc']!=b['next_pc']),None)
                assert divergence and divergence['pc']==0x257 and d==252
                changed.append(dict(d235=d,first_path_divergence=divergence))
        assert len(changed)==1
    sources=[Path(__file__),HERE/scenario_path,HERE/mapping_path,HERE/gate_path,HERE/'execute.py',HERE/'common.py',HERE.parent/'model.py']
    save(args.out/'report.json',dict(runs=len(cases),counts=dict(counts),changed=changed,cases=cases,
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='512 matched q2 reset runs; the gate at 257 changes only D235=FC in this sweep, exposing 258 and a second preparation call at 259. Both variants terminate. Physical wiring and transient output consumers remain unresolved.'))
    print(dict(counts),'changed',changed,flush=True)


if __name__=='__main__':main()
