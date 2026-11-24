"""Check the masked-input predicate after 2DF under q3 and q4."""
import hashlib
from collections import Counter
from common import HERE, decode, read, save, unconditional_transfer
from execute import CarryInput
from model import Am2901, X8X02


def probe(rows,scenario,profile,ram,d0,d1):
    cpu=Am2901(ram=ram[:],q=0xa5,logic_flags=True);seq=X8X02(pc=0x2df)
    carry=CarryInput(scenario['inputs']['carry']);previous=dict(zero=0,carry=0,overflow=0,sign=0);events=[]
    while 0x2df<=seq.pc<=0x2e5:
        pc=seq.pc;r=rows[pc];d=d0 if pc==0x2e0 else d1 if pc==0x2e1 else 0
        result=cpu.step(r['i'],r['a'],r['b'],d,carry.resolve(r));carry.observe(result)
        condition=scenario['condition'];source=condition['sources'][r['select']]
        value=condition['value'] if source=='constant' else previous[source]
        test=1 if unconditional_transfer(r,scenario) else value^condition['polarity'][r['select']]
        seq.step(r['command'],r['branch'],test);previous=result
        events.append(dict(pc=pc,next_pc=seq.pc,q=cpu.q,f=result['f'],test=test))
        assert len(events)<=7
    assert [e['pc'] for e in events]==list(range(0x2df,0x2e6))
    masked=d0&d1;match=masked==((ram[0]-1)&255)
    assert cpu.ram==ram and cpu.q==masked and seq.pushes==seq.pops==0
    assert events[0]['f']==((ram[4]-ram[0])&255 if profile=='q3' else ram[4])
    assert events[5]['f']==(ram[0]-masked-1)&255
    assert seq.pc==(0x2e6 if match else 0x2fd)
    return events


def main():
    config=read(HERE/'last-entry-study.json');scenario_path='results/last-entry-study/extended-scenario.json';scenario=read(HERE/scenario_path)
    counts=Counter();examples=[]
    for profile in ('q3','q4'):
        rows=decode(read(HERE/config['profiles'][profile]))
        for family in ('r0-mask','input-pair'):
            for a in range(256):
                for b in range(256):
                    ram=[0x5a]*16;ram[0]=a if family=='r0-mask' else 0;ram[4]=b;ram[5]=a^b
                    d0,d1=(b,255) if family=='r0-mask' else (a,b)
                    events=probe(rows,scenario,profile,ram,d0,d1)
                    counts[f"{profile}:{family}:{events[-1]['next_pc']:03X}"]+=1
                    if (a,b) in ((0,0),(0,255),(1,0),(255,255)):
                        examples.append(dict(profile=profile,family=family,ram=ram,d0=d0,d1=d1,events=events))
    paths=[HERE/'masked_entry_study.py',HERE/'last-entry-study.json',HERE/scenario_path,HERE/'execute.py',HERE/'common.py',HERE.parent/'model.py']+[HERE/config['profiles'][p] for p in ('q3','q4')]
    out=HERE/'results/masked-entry-study';out.mkdir(parents=True,exist_ok=True)
    save(out/'report.json',dict(cases=sum(counts.values()),counts=dict(counts),examples=examples,
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        interpretation='Local 2DF entry, not injected into reset runs. Two exhaustive byte-pair domains per profile check the mask predicate and untouched RAM. With R0=0 only D0=D1=FF takes 2E6; the other inputs branch to 2FD. This local probe stops before subsequent call/return behavior.'))
    print(dict(counts))


if __name__=='__main__':main()
