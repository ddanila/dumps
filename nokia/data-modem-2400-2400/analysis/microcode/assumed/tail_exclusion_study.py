"""Check a compositional exclusion argument for 287..28A under gated q2."""
import hashlib
from collections import defaultdict
from common import HERE, decode, read, save, unconditional_transfer
from analyze import graph
from constant_condition_study import fixed_tests
from conditional_tail_study import probe as tail_probe
from execute import CarryInput
from model import Am2901, X8X02


def reaching_writers(rows,pred,start,writes):
    pending=list(pred[start]);seen=set();writers=set()
    while pending:
        pc=pending.pop()
        if pc in seen:continue
        seen.add(pc)
        if writes(rows[pc]):writers.add(pc)
        else:pending.extend(pred[pc])
    return sorted(writers),sorted(pc for pc in seen if not pred[pc] and pc not in writers)


def main():
    mapping_path='results/independent-study/variant-2.json'
    scenario_path='results/constant-condition-study/gated-scenario.json'
    rows=decode(read(HERE/mapping_path));scenario=read(HERE/scenario_path)
    assert scenario['initial']==dict(pc=0,q=0,ram=[0]*16)
    assert scenario['condition']['mode']=='flags' and scenario['condition']['flag_timing']=='previous'
    assert scenario['condition']['sources'][0]=='zero' and scenario['condition']['polarity'][0]==1
    assert scenario['inputs']['ram_in']==scenario['inputs']['q_in']==0
    cfg=graph(rows,scenario,test_policy=fixed_tests);assert not cfg['exceptions']
    pred=defaultdict(set)
    for a,b,kind in cfg['edges']:pred[b].add(a)
    required={0x287:{0x286,0x3bf},0x286:{0x285},0x285:{0x284},0x284:{0x283},
        0x283:{0x282},0x282:{0x281},0x281:{0x200},0x200:{0x26f},
        0x3bf:{0x3bd,0x3be},0x3be:{0x3bd},0x3bd:{0x3bc},0x3bc:{0x3bb},
        0x3bb:{0x2e4,0x2f5,0x2f6},0x1ce:{0x1cd},0x1cd:{0x1eb,0x2d8},
        0x2d8:{0x1eb},0x1eb:{0x1ea},0x1ea:{0x1e9},
        0:{},1:{0},2:{1},3:{2},0x100:{3},0x101:{0x100},0x6f:{0x101},
        0x70:{0x6f},0x71:{0x70},0x72:{0x71},0x73:{0x72},0x74:{0x73},
        0x288:{0x287},0x289:{0x288},0x28a:{0x289}}
    for pc,want in required.items():assert pred[pc]==set(want),(pc,pred[pc],want)
    q_defs,q_roots=reaching_writers(rows,pred,0x3bb,lambda r:r['i']>>6 in (0,4,6))
    r0_defs,r0_roots=reaching_writers(rows,pred,0x3bb,lambda r:r['i']>>6>=2 and r['b']==0)
    assert q_defs==[0x2e1,0x2f3] and not q_roots
    assert r0_defs==[0x73,0x74,0x1ce] and not r0_roots
    # Exact input-independent forms: F=0&Q at 26F, Q=0&R0 at both reaching Q writers.
    assert rows[0x26f]['i']==98
    assert all(rows[p]['i']==36 and rows[p]['a']==0 for p in q_defs)
    for q in range(256):
        cpu=Am2901(q=q,logic_flags=True);r=rows[0x26f]
        result=cpu.step(r['i'],r['a'],r['b'])
        assert result['f']==0 and result['zero']==1
    assert not unconditional_transfer(rows[0x200],scenario)
    assert rows[0x200]['command']==6 and rows[0x200]['select']==0
    for a in range(256):
        for q in range(256):
            for pc in q_defs:
                ram=[0]*16;ram[0]=a;cpu=Am2901(ram=ram,q=q,logic_flags=True);r=rows[pc]
                cpu.step(r['i'],r['a'],r['b']);assert cpu.q==0
    # R9 is initially zero and no instruction before 070 writes it.
    prefix=[0,1,2,3,0x100,0x101,0x6f]
    assert all(not (rows[p]['i']>>6>=2 and rows[p]['b']==9) for p in prefix)
    expected_setup=[(196,9,0),(106,0,0),(65,9,0),(371,2,0),(201,9,0)]
    assert [(rows[p]['i'],rows[p]['a'],rows[p]['b']) for p in range(0x70,0x75)]==expected_setup
    setup_values=set()
    for q in range(256):
        ram=[0x55]*16;ram[9]=0;cpu=Am2901(ram=ram,q=q,logic_flags=True)
        carry=CarryInput(scenario['inputs']['carry'])
        for pc in range(0x70,0x75):
            r=rows[pc];result=cpu.step(r['i'],r['a'],r['b'],0,carry.resolve(r),0,0);carry.observe(result)
            if pc==0x73:assert cpu.ram[0]==0;setup_values.add(cpu.ram[0])
            if pc==0x74:assert cpu.ram[0]==255;setup_values.add(cpu.ram[0])
    # Returning from the zero-fill drain forces Q=0 before POP 1EB.
    assert rows[0x1e9]['i']==258 and rows[0x1e9]['carry_select']==0 and rows[0x1e9]['carry']==0
    assert rows[0x1ea]['select']==0 and rows[0x1ea]['command']==2 and rows[0x1ea]['i']==96
    drain_counts={}
    for q in range(256):
        cpu=Am2901(q=q,logic_flags=True);seq=X8X02(pc=0x1cc);seq.step(4,0x1e9,True)
        previous=dict(zero=0);carry=CarryInput(scenario['inputs']['carry']);steps=0
        while seq.pc!=0x1eb:
            assert seq.pc in (0x1e9,0x1ea) and steps<20
            r=rows[seq.pc];result=cpu.step(r['i'],r['a'],r['b'],0,carry.resolve(r),0,0);carry.observe(result)
            seq.step(r['command'],r['branch'],1-previous['zero']);previous=result;steps+=1
        assert cpu.q==0 and cpu.ram[0]==0 and seq.pushes-seq.pops==1
        drain_counts[steps]=drain_counts.get(steps,0)+1
    # D may differ at the two AND writes: each is zero for every D and carry.
    assert all(rows[p]['i']==230 and rows[p]['b']==0 for p in (0x1eb,0x1ce))
    for pc in (0x1eb,0x1ce):
        for d in range(256):
            for carry in (0,1):
                cpu=Am2901(q=0,logic_flags=True);r=rows[pc]
                cpu.step(r['i'],r['a'],r['b'],d,carry);assert cpu.ram[0]==0 and cpu.q==0
    assert all(rows[p]['i']>>6 not in (0,4,6) for p in (0x1cd,0x2d8))
    assert rows[0x3bb]['b']!=0 and rows[0x3bb]['i']>>6==3
    tail_cases=[]
    for a in sorted(setup_values):
        pc,events=tail_probe(rows,scenario,a,0)
        assert pc==0x3c0
        tail_cases.append(dict(r0=a,q=0,events=events))
    for a in range(256):
        pc,_=tail_probe(rows,scenario,a,0)
        assert pc==(0x3c0 if a in (0,255) else 0x287)
    paths=[HERE/'tail_exclusion_study.py',HERE/'conditional_tail_study.py',HERE/'constant_condition_study.py',
        HERE/'analyze.py',HERE/'common.py',HERE/'execute.py',HERE.parent/'model.py',HERE/mapping_path,HERE/scenario_path]
    out=HERE/'results/tail-exclusion-study';out.mkdir(parents=True,exist_ok=True)
    save(out/'report.json',dict(status='hypothesis',mapping=mapping_path,scenario=scenario_path,
        graph_words=len(cfg['reached']),graph_states=cfg['states'],
        predecessors={f'{p:03X}':[f'{a:03X}' for a in sorted(pred[p])] for p in required},
        reaching_writers=dict(q=[f'{p:03X}' for p in q_defs],r0=[f'{p:03X}' for p in r0_defs]),
        checks=dict(zero_flag_q_values=256,q_clear_pairs_per_writer=65536,setup_q_values=256,
                    drain_q_values=256,and_d_carry_cases_per_writer=512,drain_step_counts=drain_counts),
        tail_cases=tail_cases,excluded_words=['287','288','289','28A'],
        additionally_excluded=['281','282','283','284','285','286'],
        q_zero_tail_all_r0_values=256,
        argument=['Only 286 fallthrough and 3BF branch enter 287.',
                  'Every route to 286 passes 26F->200->281. 26F sets zero, forcing gated 200 to fall through instead.',
                  'All reaching Q writers at 3BB clear Q. All reaching R0 writers produce 0 or FF from reset.',
                  '3BB preserves R0/Q; if gated 3BC enters the tail, both possible R0/Q pairs force 3BF to fall through to 3C0.',
                  '288..28A have only the preceding tail word as predecessor.'],
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        interpretation='Compositional exclusion under the stated gated q2 mapping, zero reset, fixed condition inputs, previous flags and zero-fill shifts. Arbitrary byte reads and any declared dispatch entries are allowed. This is not a hardware unreachability claim or a proof for other mappings.'))
    print('excluded 287..28A; reaching Q writers',q_defs,'R0 writers',r0_defs)


if __name__=='__main__':main()
