"""Compare gates while controlling the Q byte and R0 sum before 255."""
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
    parser.add_argument('--out',type=Path,default=HERE/'results/adjustment-entry-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'adjustment-entry-study.json');base=read(HERE/config['scenario']);mapping=read(HERE/config['mapping'])
    extended=read(HERE/'results/three-bit-gate-study/scenario.json')['condition']['brt_unconditional_gate']
    new_words=set(read(HERE/'results/three-bit-gate-study/report.json')['gained'])
    cases=[];counts=Counter();witnesses=[]
    with tempfile.TemporaryDirectory() as temporary:
        for family in ('fixed-read','zero-sum'):
            for value in range(256):
                q=(3+value)&255;d251=1 if family=='fixed-read' else (-q)&255
                for variant in ('previous','extended'):
                    scenario=copy.deepcopy(base)
                    scenario['io']['read']['pc_sequences'].update({str(0x2a8):[3],str(0x235):[value],str(0x251):[d251]})
                    scenario['io']['read']['evidence']=config['evidence']
                    if variant=='extended':scenario['condition']['brt_unconditional_gate']=extended
                    result=execute(mapping,scenario,config['cycles'],mode='integrated',out=Path(temporary),trace_limit=config['cycles'])
                    assert result['clean']
                    trace=load_trace(Path(temporary));events={t['pc']:t for t in trace if t['pc'] in (0x235,0x251,0x254,0x255,0x256,0x257,0x2dc,0x2dd,0x2de)}
                    assert 0x255 in events
                    assert events[0x235]['q']==q and events[0x251]['q']==q
                    assert events[0x251]['alu']['f']==(q+d251)&255
                    assert events[0x254]['alu']['f']==(q+d251)&255
                    want_entry=variant=='extended' and (q+d251)&255==0
                    assert (0x256 in events)==want_entry
                    if want_entry:
                        assert events[0x255]['alu']['carry']==int(q!=255)
                        assert events[0x256]['test']==int(q!=255)
                        assert (0x257 in events)==(q==255)
                        assert (0x2dc in events)==(q==255)
                    terminal=result['final_state']['pc']==0x84
                    counts[f'{family}:{variant}:'+('terminal' if terminal else 'nonterminal-at-bound')]+=1
                    hits=sorted(set(result['visited'])&new_words)
                    cases.append(dict(family=family,variant=variant,d235=value,d251=d251,q=q,new_words=hits,
                        terminal=terminal,final_pc=result['final_state']['pc'],trace_digest=result['trace_digest'],
                        events=[dict(pc=p,next_pc=t['next_pc'],test=t['test'],alu=t['alu'],q=t['q'],registers=t['registers']) for p,t in events.items()]))
                    if value in config['witness_values']:
                        name=f'{family}-{variant}-{value:02x}'
                        replay=execute(mapping,scenario,config['cycles'],mode='integrated',out=args.out/name,trace_limit=config['cycles'])
                        assert replay==result;witnesses.append(name)
            print(family,dict(counts),flush=True)
    sources=[Path(__file__),HERE/'adjustment-entry-study.json',HERE/config['scenario'],HERE/config['mapping'],HERE/'results/three-bit-gate-study/scenario.json',HERE/'results/three-bit-gate-study/report.json',HERE/'execute.py',HERE/'common.py',HERE.parent/'model.py']
    save(args.out/'report.json',dict(configuration=config,runs=len(cases),counts=dict(counts),cases=cases,witnesses=witnesses,
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='Matched q2 reset runs with Q-indexed 26F, early zero replies, explicit reads at 2A8/235/251 and optional gate extension. Actual flags select the adjustment tail; input channel and gate wiring are hypotheses.'))


if __name__=='__main__':main()
