"""Explain input-carry release of the early 013 call-fed loop."""
import argparse
import hashlib
import shutil
import tempfile
from pathlib import Path
from common import HERE,read,save,decode
from execute import execute
from defined_condition_fit import load_trace
from handler_timing_study import classify
from early_wait import scenario_for as early_scenario
from model import Am2901


def scenario_for(config,u,d13,b,v,f,p,capture,tail,delay):
    early=read(HERE/config['early_configuration']);s=early_scenario(early,3,1,1,capture,tail)
    failure=256-u if u else 255
    replies=[failure] if delay is None else [failure]*delay+[0]
    s.update(name=f'early013 {u:02x}/{d13:02x}/{b:02x}/{v:02x}/{f:02x}/{p:02x}/{capture:02x}/{tail:02x}/{delay}',evidence=config['evidence'])
    s['io']['read']['pc_sequences'].update({str(pc):[value] for pc,value in ((0x13,d13),(0x14,u),(0x1a,b),(0x1e,v),(0x1f,f),(0x59,p))})
    s['io']['read']['pc_sequences'][str(0x1d)]=replies
    return s


def inspect(trace,summary,scenario,u,d13,b,v,f,p,capture,tail,delay):
    assert summary['clean'] and not summary['unused_word_executions']
    ram=[0]*16;ram[14]=(254-d13)&255
    held=delay is None and u!=0;effective=0 if u==0 else delay
    at={r['pc']:r for r in trace if r['pc']!=0x84}
    first=next(r for r in trace if r['pc']==0x1e)
    assert first['cycle']==28 and first['test']==1 and first['next_pc']==0x1d
    assert first['stack_before']['depth']==1 and first['stack_after']['depth']==0
    assert at[0x18]['q']==u and at[0x1a]['q']==(u+b)&255
    assert at[0x1b]['registers'].get('3',0)==0
    finding=classify(trace,scenario)
    if held:
        ram[0]=u;ram[2]=0 if trace[-1]['pc']==0x1d else (u+v)&255;q=(u+b)&255
        assert 0x1f not in at and 0x5d not in at and finding['repeat']['period']==2
    else:
        assert next(r['cycle'] for r in trace if r['pc']==0x5d)==38+2*effective
        assert len([r for r in trace if r['pc']==0x1d])==effective+1
        assert at[0x1f]['q']==(u+b-f-1)&255
        q=p;ram[0]=(p+1)&255;ram[4]=(p+capture)&255
        if p==0:
            ram[2]=1;ram[3]=(tail-1)&255
            assert next(r['cycle'] for r in trace if r['pc']==0x84)==56+2*effective
            assert summary['stack']['final_depth']==0
        else:
            assert 0x64 not in at and finding['repeat']['period']==7
    assert summary['final_state']['ram']==ram and summary['final_state']['q']==q
    assert summary['stack']['max_depth']==1
    return dict(ram=ram,q=q,carry_wait_held=held,effective_delay=effective,classification=finding)


def check_threshold(mapping):
    row=decode(mapping)[0x1d];counts=0
    for u in range(256):
        for d in range(256):
            cpu=Am2901(logic_flags=True);cpu.ram[0]=u;result=cpu.step(row['i'],row['a'],row['b'],d,0,0,0)
            assert cpu.ram[2]==(u+d)&255 and cpu.ram[0]==u and result['y']==u
            assert result['carry']==int(u+d>=256);counts+=result['carry']==0
    assert counts==32896
    return dict(pairs=65536,return_pairs=counts,carry_pairs=65536-counts)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,default=HERE/'results/early-entry13');args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'early-entry13.json');early=read(HERE/config['early_configuration']);h=read(HERE/early['handler_configuration']);mapping=read(HERE/h['profiles']['q3'])
    local=check_threshold(mapping);runs=[];witnesses=[]
    print('65536 carry-threshold pairs verified',flush=True)
    with tempfile.TemporaryDirectory() as temp:
        out=Path(temp)
        for u in range(256):
            for delay in (0,3,None):
                for p in (0,1):
                    d13=u^0x55;b=u^0xaa;v=u^0x80;f=(u+17)&255;capture=(u+31)&255;tail=u^0xff
                    s=scenario_for(config,u,d13,b,v,f,p,capture,tail,delay)
                    result=execute(mapping,s,config['cycles'],mode='integrated',out=out,trace_limit=config['cycles'])
                    want=inspect(load_trace(out),result,s,u,d13,b,v,f,p,capture,tail,delay)
                    case=dict(u=u,d13=d13,b=b,v=v,f=f,p=p,capture=capture,tail=tail,delay=delay,prediction=want,trace_digest=result['trace_digest']);runs.append(case)
                    if u in (0,255) and (p==0 or delay==3):
                        name=f'{u:02x}-delay-{delay}-p-{p}';shutil.copytree(out,args.out/name,dirs_exist_ok=True);witnesses.append(dict(path=name,**case))
    sources=[Path(__file__),HERE/'early-entry13.json',HERE/'early_wait.py',HERE/config['early_configuration'],HERE/'execute.py',HERE/'external_line.py',HERE/'common.py',HERE/'defined_condition_fit.py',HERE/'handler_timing_study.py',HERE/'selector_prefix_study.py',HERE.parent/'model.py',HERE/early['handler_configuration'],HERE/h['profiles']['q3'],HERE/h['scenario'],HERE/h['tables']]
    save(args.out/'report.json',dict(configuration=config,local=local,reset_cases=len(runs),runs=runs,witnesses=witnesses,source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}))
    print(len(runs),'reset cases;',len(witnesses),'witnesses',flush=True)


if __name__=='__main__':main()
