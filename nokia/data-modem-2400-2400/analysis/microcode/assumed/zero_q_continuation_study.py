"""Check fitted_swapped's copy and Q-zero continuation at 0FA..0FF."""
import hashlib
from collections import Counter
from common import HERE, decode, read, save, unconditional_transfer
from execute import CarryInput
from model import Am2901, X8X02


def probe(rows,scenario,ram,q):
    cpu=Am2901(ram=ram[:],q=q,logic_flags=True);seq=X8X02(pc=0xfa)
    carry=CarryInput(scenario['inputs']['carry']);previous=dict(zero=0,carry=0,sign=0,overflow=0);events=[]
    while 0xfa<=seq.pc<=0xff:
        pc=seq.pc;r=rows[pc]
        result=cpu.step(r['i'],r['a'],r['b'],0,carry.resolve(r));carry.observe(result)
        condition=scenario['condition'];source=condition['sources'][r['select']]
        value=condition['value'] if source=='constant' else previous[source]
        test=1 if unconditional_transfer(r,scenario) else value^condition['polarity'][r['select']]
        seq.step(r['command'],r['branch'],test)
        events.append(dict(pc=pc,next_pc=seq.pc,f=result['f'],test=test));previous=result
        assert len(events)<=6
    want=ram[:];want[0]=ram[2]
    assert cpu.ram==want and cpu.q==q and seq.pushes==seq.pops==0
    assert seq.pc==(0x78 if q else 0x7b)
    assert [e['f'] for e in events[:3]]==[ram[2],q,(~(ram[7]^q))&255]
    if not q:assert [e['f'] for e in events[3:]]==[(~ram[15])&ram[2],ram[2],(~ram[7])&255]
    return events


def main():
    config=read(HERE/'alias-runtime-study.json');mapping_path=config['profiles']['fitted_swapped']
    rows=decode(read(HERE/mapping_path));scenario_path='results/alias-runtime-study/extended-scenario.json'
    scenario=read(HERE/scenario_path)
    assert all(rows[p]['i']&7<5 for p in range(0xfa,0x100))
    counts=Counter();examples=[]
    for family in ('q-r2','r2-r15'):
        for a in range(256):
            for b in range(256):
                ram=[0x55]*16;ram[2]=a;ram[7]=a^0x5a;ram[15]=b
                q=b if family=='q-r2' else 0
                events=probe(rows,scenario,ram,q)
                counts[f"{family}:{events[-1]['next_pc']:03X}"]+=1
                if (a,b) in ((0,0),(255,0),(255,255)):
                    examples.append(dict(family=family,initial_ram=ram,q=q,events=events))
    paths=[HERE/'zero_q_continuation_study.py',HERE/'alias-runtime-study.json',HERE/mapping_path,HERE/scenario_path,HERE/'execute.py',HERE/'common.py',HERE.parent/'model.py']
    out=HERE/'results/zero-q-continuation-study';out.mkdir(parents=True,exist_ok=True)
    save(out/'report.json',dict(cases=sum(counts.values()),counts=dict(counts),examples=examples,
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        interpretation='Local fitted_swapped entry at 0FA with the raw-alias gate. Exhaustive Q/R2 pairs cover Q/R7 by bijection; a separate exhaustive R2/R15 sweep covers the mask when Q=0. Only R0 changes, to old R2. Local states are not all claimed reset-reachable.'))
    print(dict(counts))


if __name__=='__main__':main()
