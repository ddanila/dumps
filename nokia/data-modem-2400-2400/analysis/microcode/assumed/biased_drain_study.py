"""Characterize 296–29E under the selected original/previous-flag hypothesis."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
from collections import Counter
from common import HERE, decode, read, save, unconditional_transfer
from execute import CarryInput, execute
from model import Am2901, X8X02


def prediction(q,d,mask,bias):
    iterations=0;overflow=0
    while True:
        iterations+=1;total=d+q
        overflow+=int(total>255)
        # With mask FF, only sums 0 and 128 can terminate. On the
        # overflow arm, D AND Q cannot be zero when D+Q is 256.
        done=(total in (0,128)) if mask==255 else total<=255
        if done:
            return dict(returned=True,q=q>>1,ram0=((bias+q)&255)>>1,
                        cycles=4+4*iterations+2*overflow,iterations=iterations)
        if q==0:return dict(returned=False,q=0,ram0=bias>>1)
        q>>=1


def probe(rows,scenario,q,d,mask,bias):
    ram=scenario['initial']['ram'][:];ram[7]=mask;ram[13]=bias
    cpu=Am2901(ram=ram,q=q,logic_flags=True);seq=X8X02(pc=0x249)
    carry=CarryInput(scenario['inputs']['carry']);previous=dict(zero=0,carry=0,sign=0,overflow=0)
    seen={};trace=[];iterations=0;condition=scenario['condition']
    for cycle in range(128):
        key=(seq.pc,seq.sp,tuple(seq.stack),tuple(cpu.ram),cpu.q,carry.previous,tuple(sorted(previous.items())))
        if seq.pc==0x298 and key in seen:return dict(pc=seq.pc,returned=False,cycles=cycle,repeat_from=seen[key],period=cycle-seen[key],ram=cpu.ram,q=cpu.q,trace=trace)
        if seq.pc==0x298:seen[key]=cycle
        row=rows[seq.pc];pc=seq.pc
        result=cpu.step(row['i'],row['a'],row['b'],d,carry.resolve(row),0,0)
        carry.observe(result)
        if unconditional_transfer(row,scenario):test=1
        else:
            source=condition['sources'][row['select']]
            value=condition['per_select'][row['select']] if source=='constant' else previous[source]
            test=int(bool(value))^condition['polarity'][row['select']]
        if pc==0x298:iterations+=1
        trace.append(dict(pc=pc,q=cpu.q,ram0=cpu.ram[0],alu=result,test=test))
        seq.step(row['command'],row['branch'],test);previous=result
        if seq.pc==0x24a:
            return dict(pc=seq.pc,returned=True,cycles=cycle+1,iterations=iterations,ram=cpu.ram,q=cpu.q,trace=trace)
    raise ValueError('neither return nor repeated state')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/biased-drain-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'biased-drain-study.json');root=HERE/config['base']
    mapping=read(root/'mapping.json');scenario=read(root/'scenario.json');rows=decode(mapping)
    assert scenario['condition']['flag_timing']=='previous'
    assert scenario['condition']['sources'][0]=='zero' and scenario['condition']['sources'][3]=='carry'
    assert scenario['condition']['polarity'][0]==scenario['condition']['polarity'][3]==1
    assert scenario['inputs']['logic_flags']['mode']=='am2901b-ripple'
    assert scenario['inputs']['ram_in']==scenario['inputs']['q_in']==0
    counts=Counter();periods=Counter();digest=hashlib.sha256();witnesses=[]
    for mask in (0,255):
        for d in range(256):
            for q in range(256):
                expected=prediction(q,d,mask,config['bias'])
                got=probe(rows,scenario,q,d,mask,config['bias'])
                ram=scenario['initial']['ram'][:];ram[7]=mask;ram[13]=config['bias'];ram[0]=expected['ram0']
                assert got['returned']==expected['returned'] and got['q']==expected['q'] and got['ram']==ram,(q,d,mask,expected,got)
                if got['returned']:assert got['cycles']==expected['cycles'] and got['iterations']==expected['iterations']
                else:periods[got['period']]+=1
                counts[f'{mask:02x}-'+('returned' if got['returned'] else 'repeated')]+=1
                digest.update(json.dumps([mask,d,q,got['returned'],got['cycles'],got['q'],got['ram']],separators=(',',':')).encode())
                if [mask,d,q] in config['witnesses']:
                    s=copy.deepcopy(scenario);s['initial']=dict(pc=0x249,ram=ram[:],q=q)
                    s['initial']['ram'][0]=scenario['initial']['ram'][0]
                    s['io']['read']=dict(mode='constant',value=d,table=[0],status='stub',evidence=config['evidence'])
                    out=args.out/f'mask{mask:02x}-d{d:02x}-q{q:02x}'
                    run=execute(mapping,s,got['cycles'],mode='integrated',out=out,trace_limit=got['cycles'])
                    assert run['final_state']['pc']==got['pc']
                    assert run['clean'] and run['final_state']['ram']==got['ram'] and run['final_state']['q']==got['q']
                    if got['returned']:assert run['final_state']['pc']==0x24a
                    witnesses.append(dict(mask=mask,d=d,q=q,expected=expected,observed=got,integrated_trace_digest=run['trace_digest']))
    sources=[Path(__file__),HERE/'biased-drain-study.json',HERE/'execute.py',HERE/'common.py',HERE.parent/'model.py',root/'mapping.json',root/'scenario.json']
    save(args.out/'report.json',dict(configuration=config,source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},counts=dict(counts),repeat_periods=dict(periods),execution_sha256=digest.hexdigest(),witnesses=witnesses,
        interpretation='Local 296 helper drains Q while writing biased shifts to R0; under selected previous-zero/carry policy, most constant-D and R7=FF cases enter an exact repeated state. This restricts the policy/input hypothesis rather than identifying a multiplier.'))
    print(dict(counts),'repeat periods',dict(periods))


if __name__=='__main__':main()
