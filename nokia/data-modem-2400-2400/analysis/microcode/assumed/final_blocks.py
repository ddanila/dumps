"""Explain the early clear/capture diversion and current-flag handler-6 exit."""
import argparse
import hashlib
import shutil
import tempfile
from pathlib import Path
from common import HERE,read,save,decode
from execute import execute
from defined_condition_fit import load_trace
from handler_timing_study import scenario_for_case,classify
from early_entry32 import scenario_for as early_base
from handler6_early import scenario_for as previous_early
from model import Am2901


def early_prediction(a,b,g,capture,tail):
    r=(b-2+int(a!=0))&255;terminal=r==0;ram=[0]*16;ram[0]=1;ram[2]=1 if terminal else r
    ram[3]=(tail-1)&255 if terminal else r;ram[4]=capture;ram[12]=r
    return dict(ram=ram,q=0,comparison=r,terminal=terminal,first_wait=40,first_terminal=58 if terminal else None)


def early_scenario(config,a,b,g,capture,tail):
    s=early_base(read(HERE/config['early_configuration']),2,0,a,b,1,1,capture,tail)
    s.update(name=f'early043 {a:02x}/{b:02x}/{g:02x}/{capture:02x}/{tail:02x}',evidence=config['evidence'])
    s['condition']['sources'][3]='external';s['condition']['polarity'][3]=1
    s['inputs']['external']=dict(mode='cycle-events',initial=0,events=[[26,1]],status='stub',evidence=config['evidence'])
    s['io']['read']['pc_sequences'][str(0x43)]=[g]
    return s


def inspect_early(trace,result,s,a,b,g,capture,tail):
    want=early_prediction(a,b,g,capture,tail);at={r['pc']:r for r in trace if r['pc']<0x5d}
    assert result['clean'] and not result['unused_word_executions']
    assert result['final_state']['ram']==want['ram'] and result['final_state']['q']==0
    assert at[0x42]['cycle']==26 and at[0x42]['next_pc']==0x43 and at[0x41]['alu']['carry']==0
    assert at[0x43]['alu']['f']==(g-2)&255 and at[0x44]['next_pc']==0x4c
    assert at[0x50]['q']==0 and at[0x51]['alu']['f']==want['comparison']
    assert at[0x53]['next_pc']==0x45 and at[0x45]['next_pc']==0x5b
    assert next(r['cycle'] for r in trace if r['pc']==0x5d)==40
    finding=classify(trace,s)
    if want['terminal']:
        assert finding['outcome']=='terminal' and finding['first_terminal']==58 and result['stack']['final_depth']==0
    else:
        assert finding['outcome']=='repeat' and finding['repeat']['period']==7 and result['stack']['final_depth']==1
    assert result['stack']['max_depth']==1
    return want


def current_prediction(code,d,a,v):
    t=(code+2)&255;h=t>>1;transition=78+2*max(1,h.bit_length());m=d&v;q=(m+int(m!=0))&255
    direct=m==(h^255);ram=[0]*16;ram[0]=ram[2]=q>>1;ram[3]=(a-1)&255 if direct else 0
    ram[4]=2 if direct else m;ram[5]=((-q)&255)>>1;ram[6]=ram[7]=255;ram[12]=ram[15]=h;ram[13]=t
    return dict(ram=ram,q=q,half=h,mask=m,direct=direct,transition=transition,first_terminal=transition+(54 if direct else 62))


def current_scenario(config,code,d,a,v):
    h=read(HERE/config['handler_configuration']);s=scenario_for_case(h,'q3','current','blt',code);want=current_prediction(code,d,a,v)
    s.update(name=f'current exit {code:02x}/{d:02x}/{a:02x}/{v:02x}',evidence=config['evidence'])
    s['condition']['sources'][1]='external';s['condition']['polarity'][1]=0
    s['inputs']['external']=dict(mode='cycle-events',initial=0,events=[[want['transition'],1]],status='stub',evidence=config['evidence'])
    s['io']['read']['pc_sequences'].update({str(pc):[value] for pc,value in ((0xc6,d),(0xe5,a),(0xd4,v))})
    return s


def inspect_current(trace,result,code,d,a,v):
    want=current_prediction(code,d,a,v);at={r['pc']:r for r in trace if r['pc']!=0x84}
    assert result['clean'] and not result['unused_word_executions']
    assert result['final_state']['ram']==want['ram'] and result['final_state']['q']==want['q']
    assert at[0xc0]['cycle']==want['transition'] and at[0xc0]['next_pc']==0xe0
    assert at[0xe1]['q']==255 and at[0xe5]['alu']['f']==(a-1)&255
    assert at[0xce]['q']==d and at[0xce]['next_pc']==0xd0 and 0xcf not in at
    assert at[0xd4]['alu']['f']==want['mask'] and at[0xd5]['q']==want['q']
    assert at[0xd9]['alu']['carry']==0 and at[0xda]['alu']['carry']==1 and at[0xda]['next_pc']==0x1dc
    assert at[0x1dc]['alu']['f']==(want['q']+int(want['mask']==255))&255
    assert at[0x1dd]['next_pc']==(0x79 if want['direct'] else 0x1de)
    assert (0x1de in at)==(not want['direct'])
    if want['direct']:assert at[0x79]['next_pc']==0x7b and 0x7a not in at
    else:assert at[0x1de]['next_pc']==0x1d3 and at[0x1d9]['next_pc']==0x7a
    assert next(r['cycle'] for r in trace if r['pc']==0x84)==want['first_terminal']
    assert result['stack']['max_depth']==2 and result['stack']['final_depth']==0
    return want


def check_current_exit(mapping):
    rows=decode(mapping)
    for m in range(256):
        for h in range(256):
            cpu=Am2901(q=(m+int(m!=0))&255,logic_flags=True);cpu.ram[0]=m;cpu.ram[2]=int(m==255);cpu.ram[7]=255;cpu.ram[15]=h
            before=cpu.ram[:];q=cpu.q
            row=rows[0xda];value=cpu.step(row['i'],row['a'],row['b'],1,1,0,0);assert value['carry']==1
            row=rows[0x1dc];value=cpu.step(row['i'],row['a'],row['b'],1,0,0,0);assert value['carry']==0
            row=rows[0x1dd];value=cpu.step(row['i'],row['a'],row['b'],1,value['carry'],0,0)
            assert value['zero']==int(m==(h^255)) and cpu.ram==before and cpu.q==q
    return 65536


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,default=HERE/'results/final-blocks');args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'final-blocks.json');h=read(HERE/config['handler_configuration']);mapping=read(HERE/h['profiles']['q3']);early=[];current=[];controls=[];witnesses=[]
    local=check_current_exit(mapping);print(local,'current exit predicates checked',flush=True)
    with tempfile.TemporaryDirectory() as temp:
        out=Path(temp)
        for a in (0,1):
            for b in range(256):
                base=early_base(read(HERE/config['early_configuration']),2,0,a,b,1,1,0,255);execute(mapping,base,32,mode='integrated',out=out,trace_limit=32);prefix=load_trace(out)
                assert next(r for r in prefix if r['pc']==0x42)['next_pc']==0x45
                for capture,tail in ((0,255),(255,0)):
                    g=a^b;values=(a,b,g,capture,tail);s=early_scenario(config,*values);r=execute(mapping,s,128,mode='integrated',out=out,trace_limit=128);trace=load_trace(out);want=inspect_early(trace,r,s,*values)
                    for actual,old in zip(trace[:26],prefix):
                        for key in ('pc','next_pc','alu','q','registers','stack_after'):assert actual[key]==old[key]
                    case=dict(a=a,b=b,g=g,capture=capture,tail=tail,prediction=want,trace_digest=r['trace_digest']);early.append(case)
                    if capture==0 and b in (0,2-int(a!=0)):
                        name=f'early-{a}-{b}';shutil.copytree(out,args.out/name,dirs_exist_ok=True);witnesses.append(dict(path=name,family='early',**case))
                if b in (0,1,2,255):
                    for kind in ('carry-source','late-rise'):
                        s=early_scenario(config,a,b,1,0,255)
                        if kind=='carry-source':s['condition']['sources'][3]='carry'
                        else:s['inputs']['external']['events']=[[27,1]]
                        r=execute(mapping,s,32,mode='integrated',out=out,trace_limit=32);trace=load_trace(out)
                        assert r['clean'] and next(x for x in trace if x['pc']==0x42)['next_pc']==0x45
                        controls.append(dict(family='early',a=a,b=b,kind=kind,trace_digest=r['trace_digest']))
        print(len(early),'early reset cases checked',flush=True)
        for code in range(6,256,8):
            base=scenario_for_case(h,'q3','current','blt',code);execute(mapping,base,192,mode='integrated',out=out,trace_limit=192);prefix=load_trace(out)
            half=((code+2)&255)>>1
            pairs=list(dict.fromkeys(((0,255),(1,255),(255,255),(255,0),(half^255,255),(255,half^255))))
            for d,v in pairs:
                for a in (0,1,255):
                    values=(code,d,a,v);s=current_scenario(config,*values);r=execute(mapping,s,192,mode='integrated',out=out,trace_limit=192);trace=load_trace(out);want=inspect_current(trace,r,*values)
                    for actual,old in zip(trace[:want['transition']],prefix):
                        for key in ('pc','next_pc','alu','q','registers','stack_after'):assert actual[key]==old[key]
                    case=dict(code=code,d=d,a=a,v=v,prediction=want,trace_digest=r['trace_digest']);current.append(case)
                    if code in (6,254) and a==0 and v==255 and d in (0,half^255):
                        name=f'current-{code:02x}-{d:02x}';shutil.copytree(out,args.out/name,dirs_exist_ok=True);witnesses.append(dict(path=name,family='current',**case))
            s=previous_early(read(HERE/config['previous_configuration']),code,255,0xc0,255,0,255,255,1,1)
            r=execute(mapping,s,192,mode='integrated',out=out,trace_limit=192);trace=load_trace(out)
            assert r['clean'];at=next(x for x in trace if x['pc']==0xda);assert at['alu']['carry']==1 and at['next_pc']==0xdb
            controls.append(dict(family='current',code=code,kind='previous-flags',trace_digest=r['trace_digest']))
    sources=[Path(__file__),HERE/'final-blocks.json',HERE/config['early_configuration'],HERE/config['previous_configuration'],HERE/'early_entry32.py',HERE/'early_wait.py',HERE/'early-wait.json',HERE/'handler6_early.py',HERE/'handler6_study.py',HERE/'handler6-study.json',HERE/'execute.py',HERE/'external_line.py',HERE/'common.py',HERE/'defined_condition_fit.py',HERE/'handler_timing_study.py',HERE/'selector_prefix_study.py',HERE.parent/'model.py',HERE/config['handler_configuration'],HERE/h['profiles']['q3'],HERE/h['scenario'],HERE/h['tables']]
    save(args.out/'report.json',dict(configuration=config,local_exit_pairs=local,early_cases=early,current_cases=current,controls=controls,witnesses=witnesses,source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}))
    print(len(early),'early;',len(current),'current;',len(controls),'controls;',len(witnesses),'witnesses',flush=True)


if __name__=='__main__':main()
