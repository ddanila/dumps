"""Check q3's conditional Q decrement and four transient tail outputs."""
import hashlib
from collections import Counter
from common import HERE, decode, read, save
from conditional_tail_study import probe
from execute import CarryInput
from model import Am2901


def main():
    mapping_path='results/independent-study/variant-3.json'
    scenario_path='results/constant-condition-study/gated-scenario.json'
    rows=decode(read(HERE/mapping_path));scenario=read(HERE/scenario_path)
    counts=Counter();examples=[]
    for a in range(256):
        for q in range(256):
            pc,events=probe(rows,scenario,a,q)
            decrement=q==(a^255)
            difference=(q-int(decrement))&255
            assert pc==(0x287 if difference else 0x3c0)
            assert events[1]['f']==q
            assert [e['pc'] for e in events]==([0x3bc,0x3bd,0x3be,0x3bf] if decrement else [0x3bc,0x3bd,0x3bf])
            if decrement:assert events[2]['f']==(q-1)&255
            counts[f'{pc:03X}']+=1
            # Independent no-load outputs: covers all (R0,R2) and (R0,R12) pairs,
            # and every Q value. Distinct source registers are not aliased.
            ram=[0x55]*16;ram[0]=a;ram[2]=q;ram[12]=q^255
            tail_q=(3*q+17)&255
            cpu=Am2901(ram=ram[:],q=tail_q,logic_flags=True);carry=CarryInput(scenario['inputs']['carry'])
            values=[]
            for p in range(0x287,0x28b):
                r=rows[p];result=cpu.step(r['i'],r['a'],r['b'],0,carry.resolve(r));carry.observe(result)
                values.append(result['f'])
                assert cpu.ram==ram and cpu.q==tail_q
            assert values==[(tail_q-1)&255,tail_q,(ram[2]-a)&255,(ram[12]-a-1)&255]
            if (a,q) in ((0,0),(255,0),(254,1),(1,2)):
                examples.append(dict(r0=a,q=q,events=events,tail_ram=ram,tail_q=tail_q,tail_outputs=values))
    paths=[HERE/'q3_tail_study.py',HERE/'conditional_tail_study.py',HERE/mapping_path,HERE/scenario_path,HERE/'execute.py',HERE/'common.py',HERE.parent/'model.py']
    out=HERE/'results/q3-tail-study';out.mkdir(parents=True,exist_ok=True)
    save(out/'report.json',dict(mapping=mapping_path,scenario=scenario_path,tail_entry_pairs=65536,output_register_pairs=65536,counts=dict(counts),examples=examples,
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        interpretation='Local 3BC entry assumes previous zero set. q3 tail preserves RAM/Q; 287..28A separately expose arithmetic values without storing them. Local pairs are not all claimed reachable from reset.'))
    print(dict(counts))


if __name__=='__main__':main()
