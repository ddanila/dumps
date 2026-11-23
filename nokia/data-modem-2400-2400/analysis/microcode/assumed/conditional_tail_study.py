"""Explain the newly entered 3BC..3BF tail under the optional BRT gate."""
import hashlib
from collections import Counter
from common import HERE, decode, read, save, unconditional_transfer
from execute import CarryInput
from model import Am2901, X8X02


def probe(rows,scenario,a,q):
    ram=[(17*i)&255 for i in range(16)];ram[0]=a
    cpu=Am2901(ram=ram[:],q=q,logic_flags=True);seq=X8X02(pc=0x3bc)
    carry=CarryInput(scenario['inputs']['carry'])
    previous=dict(zero=1)  # Local entry premise: 3BB has produced zero.
    events=[]
    while 0x3bc<=seq.pc<=0x3bf:
        row=rows[seq.pc];pc=seq.pc
        result=cpu.step(row['i'],row['a'],row['b'],0,carry.resolve(row),0,0)
        carry.observe(result)
        test=1 if unconditional_transfer(row,scenario) else 1-previous['zero']
        seq.step(row['command'],row['branch'],test)
        events.append(dict(pc=pc,next_pc=seq.pc,test=test,f=result['f']))
        previous=result
        assert len(events)<=4
    assert cpu.ram==ram and cpu.q==q and seq.pushes==seq.pops==0
    return seq.pc,events


def main():
    config=read(HERE/'gate-runtime-study.json')
    mappings={k:decode(read(HERE/v)) for k,v in config['mappings'].items()}
    fields=('i','a','b','carry','carry_select','command','branch','select','direct')
    assert all(all(mappings['q2'][pc][k]==mappings['fitted_original'][pc][k] for k in fields) for pc in range(0x3bc,0x3c0))
    scenario=read(HERE/'results/constant-condition-study/gated-scenario.json')
    counts=Counter();digest=hashlib.sha256();examples=[]
    for a in range(256):
        for q in range(256):
            pc,events=probe(mappings['q2'],scenario,a,q)
            include_decrement=q==(a^255)
            difference=(q-a-int(include_decrement))&255
            expected=0x287 if difference else 0x3c0
            assert pc==expected
            assert [e['pc'] for e in events]==([0x3bc,0x3bd,0x3be,0x3bf] if include_decrement else [0x3bc,0x3bd,0x3bf])
            assert events[1]['f']==(q-a)&255
            if include_decrement:assert events[2]['f']==difference
            assert events[-1]['f']==a&q
            counts[f'{pc:03X}']+=1
            digest.update(bytes([a,q,pc&255,pc>>8]))
            if (a,q) in ((0,0),(0,255),(127,128),(255,0),(255,255),(1,2)):
                examples.append(dict(r0=a,q=q,events=events))
    sources=[HERE/'conditional_tail_study.py',HERE/'execute.py',HERE/'common.py',HERE.parent/'model.py',HERE/'results/constant-condition-study/gated-scenario.json']+[HERE/p for p in config['mappings'].values()]
    out=HERE/'results/conditional-tail-study';out.mkdir(parents=True,exist_ok=True)
    save(out/'report.json',dict(cases=65536,profiles=list(mappings),counts=dict(counts),digest=digest.hexdigest(),examples=examples,
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='Local entry at 3BC with previous zero set. Exhaustive R0/Q pairs; identical decoded tail in q2 and fitted_original. RAM/Q preserved. Physical consumer of transient ALU results unknown.'))
    print(dict(counts))


if __name__=='__main__':main()
