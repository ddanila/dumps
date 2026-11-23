"""Compare retained mappings on the 12C mask loop; test q2's external poll."""
import argparse
import copy
import hashlib
import json
import random
from collections import Counter
from pathlib import Path
from common import HERE, decode, read, save, unconditional_transfer
from execute import CarryInput, execute
from model import Am2901, X8X02


def probe(rows,base,ram,q,d,release=False):
    cpu=Am2901(ram=ram[:],q=q,logic_flags=True);seq=X8X02(pc=0x11d)
    carry=CarryInput(base['inputs']['carry']);previous=dict(zero=0,carry=0,sign=0,overflow=0)
    seen={};trace=[];visits=0;target=q&ram[0]
    for cycle in range(32):
        key=json.dumps([seq.pc,seq.sp,seq.stack,cpu.ram,cpu.q,previous,carry.previous,min(visits,2) if release else 0],sort_keys=True)
        if seq.pc==0x12c:
            if key in seen:return dict(returned=False,pc=seq.pc,ram=cpu.ram,q=cpu.q,cycles=cycle,period=cycle-seen[key],trace=trace)
            seen[key]=cycle
        pc=seq.pc;row=rows[pc];operand=d
        if release and pc==0x12e:operand=(target^1) if visits==0 else target;visits+=1
        result=cpu.step(row['i'],row['a'],row['b'],operand,carry.resolve(row),0,0);carry.observe(result)
        if unconditional_transfer(row,base):test=1
        else:
            source=base['condition']['sources'][row['select']]
            value=base['condition']['value'] if source=='constant' else previous[source]
            test=int(bool(value))^base['condition']['polarity'][row['select']]
        trace.append(dict(pc=pc,d=operand,q=cpu.q,alu=result,test=test))
        seq.step(row['command'],row['branch'],test);previous=result
        if seq.pc==0x11e:return dict(returned=True,pc=seq.pc,ram=cpu.ram,q=cpu.q,cycles=cycle+1,trace=trace)
    raise ValueError('no completion or repeat')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/mask-variant-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'mask-variant-study.json');root=HERE/config['base'];base=read(root/'scenario.json')
    profiles=read(HERE/'program-reading.json')['profiles'];counts=Counter();witnesses=[];seen=set();digest=hashlib.sha256();decodes={}
    def verify(name,mapping,rows,ram,q,d,release=False):
        got=probe(rows,base,ram,q,d,release);masked=q&ram[0]
        want= {'q1':ram[0]==0,'q2':d==masked,'q3':ram[0]==0,'q4':ram[0]==0,
               'fitted_original':masked==ram[0],'fitted_swapped':masked==ram[7]}[name]
        if release:want=True
        expected_q=0 if name in ('q1','q3') else masked
        expected_ram=ram[:]
        if name in ('q1','q2'):
            prior_q=q if got['returned'] and not release else expected_q
            expected_ram[2]=(d+prior_q)&255
        elif name=='fitted_swapped':expected_ram[1]=ram[2]
        else:expected_ram[2]=ram[1]
        assert got['returned']==want and got['q']==expected_q and got['ram']==expected_ram,(name,ram,q,d,release,got,expected_ram)
        if not want:assert got['period']==4
        counts[f'{name}:{"release" if release else "constant"}:{"return" if want else "repeat"}']+=1
        digest.update(json.dumps([name,ram,q,d,release,got['cycles'],got['q'],got['ram'],want],separators=(',',':')).encode())
        key=(name,release,want)
        if key not in seen:
            seen.add(key);s=copy.deepcopy(base);s['initial']=dict(pc=0x11d,ram=ram,q=q)
            s['io']['read']=dict(mode='constant',value=d,table=[0],status='stub',evidence=config['evidence'])
            if release:s['io']['read'].update(mode='pc_sequence',pc_sequences={str(0x12e):[masked^1,masked]},sequence_end='hold-last')
            out=args.out/f'witness-{len(witnesses):02d}'
            run=execute(mapping,s,got['cycles'],mode='integrated',out=out,trace_limit=got['cycles'])
            assert run['clean'] and run['final_state']['pc']==got['pc'] and run['final_state']['ram']==got['ram'] and run['final_state']['q']==got['q']
            witnesses.append(dict(profile=name,ram=ram,q=q,d=d,release=release,result=got,trace_digest=run['trace_digest']))
    for name,path in profiles.items():
        mapping=read(HERE/path);rows=decode(mapping)
        decodes[name]=[dict(pc=p,source=rows[p]['i']&7,a=rows[p]['a'],b=rows[p]['b']) for p in range(0x12c,0x131)]
        rng=random.Random(config['seed'])
        for fixture in range(config['fixtures']):
            ram=[rng.randrange(256) for _ in range(16)];q=rng.randrange(256)
            if fixture==0:ram[0]=0
            if fixture==1:ram[0]=ram[7]=255;q=255
            for d in range(256):verify(name,mapping,rows,ram,q,d)
    mapping=read(HERE/profiles['q2']);rows=decode(mapping)
    for mask in range(256):
        for q in range(256):
            ram=config['initial_ram'][:];ram[0]=mask;target=q&mask
            for d in (target,target^1):verify('q2',mapping,rows,ram,q,d)
            verify('q2',mapping,rows,ram,q,config['release_default_d'],True)
    sources=[Path(__file__),HERE/'mask-variant-study.json',HERE/'execute.py',HERE/'common.py',HERE.parent/'model.py',root/'scenario.json']+[HERE/p for p in profiles.values()]
    save(args.out/'report.json',dict(configuration=config,counts=dict(counts),decodes=decodes,witnesses=witnesses,execution_sha256=digest.hexdigest(),
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='Retained q2 mapping plus explicitly shared previous-flag/defined-carry policy makes 12C an external equality poll for masked Q. Other retained mappings have different constant predicates. No mapping promoted or physical input identified.'))
    print(dict(counts),'witnesses',len(witnesses))


if __name__=='__main__':main()
