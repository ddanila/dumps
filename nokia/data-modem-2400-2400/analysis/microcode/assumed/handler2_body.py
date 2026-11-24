"""Compose handler 2 preparation, Q drains, input poll and terminal stores."""
import argparse
import hashlib
import shutil
import tempfile
from pathlib import Path
from common import HERE,read,save,decode
from execute import execute
from defined_condition_fit import load_trace
from handler_timing_study import scenario_for_case
from model import Am2901


def prediction(a,b,payload,delay):
    retained=254+int(bool(a&254));qsum=(a+b)&255
    ram=[0]*16;ram[0]=ram[2]=payload>>1;ram[5]=((-payload)&255)>>1;ram[12]=retained
    return dict(ram=ram,q=payload,retained=retained,release=(-retained)&255,qsum=qsum,
        first_poll=181+2*qsum.bit_length(),first_terminal=213+2*qsum.bit_length()+2*delay)


def scenario_for(config,code,a,b,payload,delay):
    h=read(HERE/config['handler_configuration']);s=scenario_for_case(h,'q3','previous','plp',code)
    s.update(name=f'q3 handler2 body {code:02x}/{a:02x}/{b:02x}/{payload:02x}/{delay}',evidence=config['evidence'])
    release=prediction(a,b,payload,delay)['release']
    s['io']['read']['pc_sequences'].update({str(0x197):[a],str(0x1a2):[b],str(0x1d0):[payload],str(0x1ec):[(release+1)&255]*delay+[release]})
    return s


def inspect(trace,summary,a,b,payload,delay):
    want=prediction(a,b,payload,delay)
    assert summary['clean'] and not summary['unused_word_executions']
    assert summary['final_state']['ram']==want['ram'] and summary['final_state']['q']==payload
    assert next(r['cycle'] for r in trace if r['pc']==0x84)==want['first_terminal']
    poll=[r for r in trace if r['pc']==0x1ec]
    assert len(poll)==delay+1 and poll[0]['cycle']==want['first_poll']
    assert [r['alu']['f'] for r in poll]==[1]*delay+[0]
    at={r['pc']:r for r in trace if r['pc']!=0x84}
    assert at[0x19c]['registers'].get('4')==want['retained']
    assert at[0x1a2]['q']==want['qsum'] and at[0x1a2]['next_pc']==0x1e7
    assert at[0x1c2]['next_pc']==0x2d0 and at[0x2d8]['next_pc']==0x1cd
    assert at[0x3a3]['registers']['12']==want['retained']
    assert at[0x1d0]['q']==payload and at[0x1d9]['next_pc']==0x7a
    assert not any(0x1c3<=r['pc']<=0x1cc or 0x1da<=r['pc']<=0x1de for r in trace)
    assert summary['stack']['max_depth']==3 and summary['stack']['final_depth']==0
    return want


def check_arithmetic(mapping):
    rows=decode(mapping)
    for a in range(256):
        for b in range(256):
            cpu=Am2901(logic_flags=True);cpu.q=a;cpu.ram[3]=1
            r=rows[0x19b];first=cpu.step(r['i'],r['a'],r['b'],1,0,0,0)
            r=rows[0x19c];cpu.step(r['i'],r['a'],r['b'],1,first['carry'],0,0)
            assert cpu.ram[4]==254+int(bool(a&254))
            r=rows[0x1a2];result=cpu.step(r['i'],r['a'],r['b'],b,0,0,0)
            assert cpu.q==(a+b)&255 and result['carry']==int(a+b>=256)
    return 65536


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,default=HERE/'results/handler2-body');args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'handler2-body.json');h=read(HERE/config['handler_configuration']);mapping=read(HERE/h['profiles']['q3'])
    arithmetic=check_arithmetic(mapping);print(arithmetic,'local arithmetic pairs checked',flush=True)
    runs=[];witnesses=[]
    with tempfile.TemporaryDirectory() as temp:
        out=Path(temp)
        for code in range(2,256,8):
            for a in (0,1,2,255):
                for b in (0,1,128,255):
                    for payload in (0,1,128,255):
                        delay=(a+b+payload)%3;s=scenario_for(config,code,a,b,payload,delay)
                        result=execute(mapping,s,config['cycles'],mode='integrated',out=out,trace_limit=config['cycles'])
                        want=inspect(load_trace(out),result,a,b,payload,delay)
                        case=dict(code=code,a=a,b=b,payload=payload,delay=delay,prediction=want,trace_digest=result['trace_digest']);runs.append(case)
                        if code in (2,250) and a in (0,255) and b==1 and payload==128:
                            name=f'{code:02x}-a-{a:02x}';shutil.copytree(out,args.out/name,dirs_exist_ok=True);witnesses.append(dict(path=name,**case))
    sources=[Path(__file__),HERE/'handler2-body.json',HERE/'execute.py',HERE/'external_line.py',HERE/'common.py',HERE/'defined_condition_fit.py',HERE/'handler_timing_study.py',HERE/'selector_prefix_study.py',HERE.parent/'model.py',HERE/config['handler_configuration'],HERE/h['profiles']['q3'],HERE/h['scenario'],HERE/h['tables']]
    save(args.out/'report.json',dict(configuration=config,arithmetic_pairs=arithmetic,reset_cases=len(runs),runs=runs,witnesses=witnesses,source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}))
    print(len(runs),'reset cases;',len(witnesses),'witnesses',flush=True)


if __name__=='__main__':main()
