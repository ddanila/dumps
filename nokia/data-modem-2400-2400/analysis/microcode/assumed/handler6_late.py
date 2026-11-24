"""Explain handler-6 late capture, masked continuation and alternative terminal entry."""
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


def prediction(code,captured,route,a,u,v):
    base=base_prediction(code,captured);value=(a+1)&255 if route=='capture' else 0;mask=u&v
    alternative=bool(value&mask);ram=base['ram'][:];ram[12]=value;ram[3]=0 if alternative else value;ram[4]=mask if alternative else 2
    return dict(ram=ram,q=0,captured_value=value,masked_input=mask,alternative=alternative,
        extra_terminal_step=int(not alternative and mask==(base['half']^255)),
        transition=base['first_terminal']-(30 if route=='capture' else 26),
        first_terminal=base['first_terminal']+(26 if route=='capture' else 22)+8*alternative+int(not alternative and mask==(base['half']^255)))


def scenario_for(config,code,captured,route,a,u,v):
    base=read(HERE/config['handler_configuration']);s=base_scenario(base,code,captured);want=prediction(code,captured,route,a,u,v)
    s.update(name=f'handler6 late {code:02x}/{captured:02x}/{route}/{a:02x}/{u:02x}/{v:02x}',evidence=config['evidence'])
    s['condition']['sources'][1]='external';s['condition']['polarity'][1]=0
    s['inputs']['external']=dict(mode='cycle-events',initial=0,events=[[want['transition'],1]],status='stub',evidence=config['evidence'])
    s['io']['read']['pc_sequences'].update({str(0xe5):[a],str(0xcf):[u],str(0xd4):[v]})
    return s


def inspect(trace,summary,code,captured,route,a,u,v):
    want=prediction(code,captured,route,a,u,v)
    assert summary['clean'] and not summary['unused_word_executions']
    assert summary['final_state']['ram']==want['ram'] and summary['final_state']['q']==0
    assert next(r['cycle'] for r in trace if r['pc']==0x84)==want['first_terminal']
    at={r['pc']:r for r in trace if r['pc']!=0x84}
    branch=0xc7 if route=='capture' else 0xcb
    assert at[branch]['cycle']==want['transition']
    assert at[0xcb]['next_pc']==0xce and at[0xce]['next_pc']==0xcf
    assert (0xe5 in at)==(route=='capture')
    if route=='capture':assert at[0xe5]['alu']['f']==want['captured_value'] and at[0xe8]['next_pc']==0xc8
    assert at[0xd4]['alu']['f']==want['masked_input']
    assert at[0xd5]['q']==(want['masked_input']+int(want['masked_input']!=0))&255
    assert at[0xda]['next_pc']==0xdb and at[0xdd]['next_pc']==0x4c
    assert at[0x53]['alu']['f']==want['captured_value']&want['masked_input']
    assert at[0xde]['next_pc']==(0xdf if want['alternative'] else 0x79)
    if want['alternative']:assert at[0xdf]['next_pc']==0x1d3 and at[0x1d9]['next_pc']==0x7a
    assert summary['stack']['max_depth']==2 and summary['stack']['final_depth']==0
    return want


def check_exit(mapping):
    row=decode(mapping)[0x53];zeros=0
    for value in range(256):
        for mask in range(256):
            cpu=Am2901(logic_flags=True);cpu.ram[0]=mask;cpu.ram[12]=value
            result=cpu.step(row['i'],row['a'],row['b'],1,0,0,0)
            assert result['f']==value&mask and result['zero']==int(not(value&mask))
            zeros+=result['zero']
    assert zeros==6561
    return dict(pairs=65536,direct_pairs=zeros,alternative_pairs=65536-zeros)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,default=HERE/'results/handler6-late');args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'handler6-late.json');base=read(HERE/config['handler_configuration']);h=read(HERE/base['handler_config']);mapping=read(HERE/h['profiles']['q3']);runs=[];witnesses=[]
    local=check_exit(mapping);print('65536 exit predicates checked',flush=True)
    with tempfile.TemporaryDirectory() as temp:
        out=Path(temp)
        for code in range(6,256,8):
            for captured in (0,255):
                baseline=base_scenario(base,code,captured);execute(mapping,baseline,192,mode='integrated',out=out,trace_limit=192);prefix=load_trace(out)
                for route in ('capture','late'):
                    for a in (0,1,254,255):
                        for u,v in ((0,255),(1,255),(255,1),(255,255)):
                            s=scenario_for(config,code,captured,route,a,u,v);result=execute(mapping,s,192,mode='integrated',out=out,trace_limit=192);trace=load_trace(out)
                            want=inspect(trace,result,code,captured,route,a,u,v)
                            for actual,old in zip(trace[:want['transition']],prefix):
                                for k in ('pc','next_pc','alu','q','registers','stack_after'):assert actual[k]==old[k]
                            case=dict(code=code,captured=captured,route=route,a=a,u=u,v=v,prediction=want,trace_digest=result['trace_digest']);runs.append(case)
                            if code in (6,254) and captured==255 and a in (0,255) and u==255 and v==255:
                                name=f'{code:02x}-{route}-a-{a:02x}';shutil.copytree(out,args.out/name,dirs_exist_ok=True);witnesses.append(dict(path=name,**case))
    sources=[Path(__file__),HERE/'handler6-late.json',HERE/'handler6_study.py',HERE/config['handler_configuration'],HERE/'execute.py',HERE/'external_line.py',HERE/'common.py',HERE/'defined_condition_fit.py',HERE/'handler_timing_study.py',HERE/'selector_prefix_study.py',HERE.parent/'model.py',HERE/base['handler_config'],HERE/h['profiles']['q3'],HERE/h['scenario'],HERE/h['tables']]
    save(args.out/'report.json',dict(configuration=config,local=local,reset_cases=len(runs),runs=runs,witnesses=witnesses,source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}))
    print(len(runs),'reset cases;',len(witnesses),'witnesses',flush=True)


if __name__=='__main__':main()
