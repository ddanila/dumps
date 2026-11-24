"""Explain handler-6 early complement diversion and conditional input reload."""
import argparse
import hashlib
import shutil
import tempfile
from pathlib import Path
from common import HERE,read,save,decode
from execute import execute
from defined_condition_fit import load_trace
from handler6_study import scenario_for as base_scenario,prediction as base_prediction
from model import Am2901


def prediction(code,captured,branch,d,a,u,v):
    base=base_prediction(code,captured);s=(a-1)&255;reload=d==255;q=(u-1)&255 if reload else d;m=q&v
    alternative=bool(m&s);extra=int(not alternative and m==(base['half']^255))
    ram=base['ram'][:];ram[12]=s;ram[3]=0 if alternative else s;ram[4]=m if alternative else 2
    return dict(ram=ram,q=0,captured_value=s,reload=reload,mask_source=q,masked_input=m,alternative=alternative,
        extra_terminal_step=extra,transition=base['first_terminal']-37+int(branch==0xc1),
        first_terminal=base['first_terminal']+28+int(branch==0xc1)-int(not reload)+8*alternative+extra)


def scenario_for(config,code,captured,branch,d,a,u,v,transient2,transient3):
    base=read(HERE/config['handler_configuration']);s=base_scenario(base,code,captured);want=prediction(code,captured,branch,d,a,u,v)
    s.update(name=f'handler6 early {code:02x}/{captured:02x}/{branch:03x}/{d:02x}/{a:02x}/{u:02x}/{v:02x}/{transient2:02x}/{transient3:02x}',evidence=config['evidence'])
    s['condition']['sources'][1]='external';s['condition']['polarity'][1]=0
    s['inputs']['external']=dict(mode='cycle-events',initial=0,events=[[want['transition'],1]],status='stub',evidence=config['evidence'])
    s['io']['read']['pc_sequences'].update({str(pc):[value] for pc,value in ((0xc6,d),(0xe5,a),(0xcf,u),(0xd4,v),(0xe2,transient2),(0xe3,transient3))})
    return s


def inspect(trace,summary,code,captured,branch,d,a,u,v):
    want=prediction(code,captured,branch,d,a,u,v)
    assert summary['clean'] and not summary['unused_word_executions']
    assert summary['final_state']['ram']==want['ram'] and summary['final_state']['q']==0
    at={r['pc']:r for r in trace if r['pc']!=0x84}
    assert at[branch]['cycle']==want['transition'] and at[branch]['next_pc']==0xe0
    assert at[0xe1]['q']==255 and at[0xe4]['next_pc']==0xc4
    assert at[0xc6]['alu']['f']==d and at[0xc7]['alu']['carry']==0
    assert at[0xe5]['alu']['f']==want['captured_value']
    assert at[0xcb]['alu']['carry']==int(d!=255)
    assert at[0xce]['q']==d and at[0xce]['next_pc']==(0xcf if want['reload'] else 0xd0)
    assert (0xcf in at)==want['reload'] and at[0xd4]['alu']['f']==want['masked_input']
    assert at[0xde]['next_pc']==(0xdf if want['alternative'] else 0x79)
    assert next(r['cycle'] for r in trace if r['pc']==0x84)==want['first_terminal']
    assert summary['stack']['max_depth']==2 and summary['stack']['final_depth']==0
    return want


def check_carry(mapping):
    rows=decode(mapping)
    for d in range(256):
        for a in range(256):
            cpu=Am2901(logic_flags=True);cpu.q=255
            row=rows[0xc6];value=cpu.step(row['i'],row['a'],row['b'],d,0,0,0)
            row=rows[0xc7];value=cpu.step(row['i'],row['a'],row['b'],1,value['carry'],0,0);assert value['carry']==0
            row=rows[0xe5];value=cpu.step(row['i'],row['a'],row['b'],a,value['carry'],0,0);assert cpu.ram[5]==(a-1)&255
            row=rows[0xcb];value=cpu.step(row['i'],row['a'],row['b'],1,0,0,0);assert value['carry']==int(d!=255)
    return 65536


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,default=HERE/'results/handler6-early');args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'handler6-early.json');base=read(HERE/config['handler_configuration']);h=read(HERE/base['handler_config']);mapping=read(HERE/h['profiles']['q3']);runs=[];witnesses=[]
    pairs=check_carry(mapping);print(pairs,'capture/reload pairs checked',flush=True)
    with tempfile.TemporaryDirectory() as temp:
        out=Path(temp)
        for code in range(6,256,8):
            captured=0 if code==6 else 255
            baseline=base_scenario(base,code,captured);execute(mapping,baseline,192,mode='integrated',out=out,trace_limit=192);prefix=load_trace(out)
            for branch in (0xc0,0xc1):
                for d in (0,1,128,255):
                    for a in (0,1,255):
                        for u,v in ((0,255),(255,1),(255,255)):
                            t2=d^a;t3=u^v;s=scenario_for(config,code,captured,branch,d,a,u,v,t2,t3)
                            result=execute(mapping,s,192,mode='integrated',out=out,trace_limit=192);trace=load_trace(out);want=inspect(trace,result,code,captured,branch,d,a,u,v)
                            for actual,old in zip(trace[:want['transition']],prefix):
                                for k in ('pc','next_pc','alu','q','registers','stack_after'):assert actual[k]==old[k]
                            case=dict(code=code,captured=captured,branch=branch,d=d,a=a,u=u,v=v,transient2=t2,transient3=t3,prediction=want,trace_digest=result['trace_digest']);runs.append(case)
                            if code in (6,254) and d in (1,255) and a==0 and u==255 and v==255:
                                name=f'{code:02x}-{branch:03x}-d-{d:02x}';shutil.copytree(out,args.out/name,dirs_exist_ok=True);witnesses.append(dict(path=name,**case))
    sources=[Path(__file__),HERE/'handler6-early.json',HERE/'handler6_study.py',HERE/config['handler_configuration'],HERE/'execute.py',HERE/'external_line.py',HERE/'common.py',HERE/'defined_condition_fit.py',HERE/'handler_timing_study.py',HERE/'selector_prefix_study.py',HERE.parent/'model.py',HERE/base['handler_config'],HERE/h['profiles']['q3'],HERE/h['scenario'],HERE/h['tables']]
    save(args.out/'report.json',dict(configuration=config,arithmetic_pairs=pairs,reset_cases=len(runs),runs=runs,witnesses=witnesses,source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}))
    print(len(runs),'reset cases;',len(witnesses),'witnesses',flush=True)


if __name__=='__main__':main()
