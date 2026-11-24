"""Explain early shift selection and a carry-dependent skipped BLT."""
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


def prediction(q,a,x,y):
    r1=(q-1+int(a+q>=256))&255;n=q>>1
    first=int(x+n>=256);pop=int(y+n+first>=256)
    return dict(q=n,r1=r1,pops=bool(pop),first_carry=first,temporary=(r1+n+1)&255 if pop else 0,
                branch=0x028 if q==0 else 0x025,instructions=12+pop,frame_retained=1-pop)


def scenario_for(config,a,shift,x,y,capture):
    early=read(HERE/config['early_configuration']);s=early_scenario(early,4,1,1,capture,1)
    s.update(name=f'early022 {a:02x}/{shift:02x}/{x:02x}/{y:02x}/{capture:02x}',evidence=config['evidence'])
    s['io']['read']['pc_sequences'].update({str(pc):[value] for pc,value in ((0x22,a),(0x25,shift),(0x28,shift),(0x2b,x),(0x2c,y))})
    return s


def inspect(trace,summary,scenario,a,shift,x,y,capture):
    want=prediction(255,a,x,y);ram=[0]*16;ram[0]=128;ram[1]=want['r1'];ram[4]=(capture+127)&255
    assert summary['clean'] and not summary['unused_word_executions']
    assert summary['final_state']['ram']==ram and summary['final_state']['q']==127
    at={r['pc']:r for r in trace if r['pc']<0x5d}
    assert at[0x24]['next_pc']==0x25
    assert at[0x2d]['next_pc']==(0x2e if want['pops'] else 0x2f)
    assert at[0x31]['stack_after']['depth']==want['frame_retained']
    assert next(r['cycle'] for r in trace if r['pc']==0x5d)==32+int(want['pops'])
    assert summary['stack']['max_depth']==1+want['frame_retained']
    if want['pops']:assert at[0x2e]['test']==0 and at[0x2e]['next_pc']==0x2f
    assert not any(r['pc']==0x64 or r['pc']==0x84 for r in trace)
    finding=classify(trace,scenario);assert finding['repeat']['period']==7
    return dict(**want,ram=ram,classification=finding)


def check_arithmetic(mapping):
    rows=decode(mapping);pop_count=0
    for a in range(256):
        for q in range(256):
            cpu=Am2901(logic_flags=True);cpu.q=q
            r=rows[0x22];v=cpu.step(r['i'],r['a'],r['b'],a,0,0,0)
            r=rows[0x23];v=cpu.step(r['i'],r['a'],r['b'],0,v['carry'],0,0)
            assert cpu.ram[1]==(q-1+int(a+q>=256))&255
            assert v['carry']==int(q!=0)
    for x in range(256):
        for y in range(256):
            cpu=Am2901(logic_flags=True);cpu.q=127
            r=rows[0x2b];v=cpu.step(r['i'],r['a'],r['b'],x,0,0,0)
            r=rows[0x2c];v=cpu.step(r['i'],r['a'],r['b'],y,v['carry'],0,0)
            want=prediction(255,1,x,y);assert v['carry']==want['pops'];pop_count+=want['pops']
    return dict(preparation_pairs=65536,carry_pairs=65536,pop_pairs=pop_count,skip_pairs=65536-pop_count)


def inspect_local(mapping,config,ram,q,a,shift,x,y,out):
    scenario=scenario_for(config,a,shift,x,y,1);scenario['initial']=dict(pc=0x22,ram=ram[:],q=q)
    want=prediction(q,a,x,y);result=execute(mapping,scenario,want['instructions'],mode='integrated',out=out,trace_limit=want['instructions'])
    expected=ram[:];expected[0]=expected[2]=want['temporary'];expected[1]=want['r1']
    assert result['clean'] and result['final_state']['pc']==0x5b
    assert result['final_state']['ram']==expected and result['final_state']['q']==want['q']
    assert result['stack']['max_depth']==1 and result['stack']['final_depth']==want['frame_retained']
    trace=load_trace(out);assert next(r['next_pc'] for r in trace if r['pc']==0x24)==want['branch']
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,default=HERE/'results/early-entry22');args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'early-entry22.json');early=read(HERE/config['early_configuration']);h=read(HERE/early['handler_configuration']);mapping=read(HERE/h['profiles']['q3'])
    arithmetic=check_arithmetic(mapping);runs=[];witnesses=[];locals=[]
    print('131072 arithmetic pairs verified',flush=True)
    with tempfile.TemporaryDirectory() as temp:
        out=Path(temp)
        for x in range(256):
            for y in (127,128,129,255):
                a=(x+y)&255;shift=x^0xaa;capture=x^y;s=scenario_for(config,a,shift,x,y,capture)
                result=execute(mapping,s,config['cycles'],mode='integrated',out=out,trace_limit=config['cycles'])
                want=inspect(load_trace(out),result,s,a,shift,x,y,capture)
                case=dict(a=a,shift=shift,x=x,y=y,capture=capture,prediction=want,trace_digest=result['trace_digest']);runs.append(case)
                if x in (128,129) and y in (127,128):
                    name=f'x-{x:02x}-y-{y:02x}';shutil.copytree(out,args.out/name,dirs_exist_ok=True);witnesses.append(dict(path=name,**case))
        for q in (0,1,128,255):
            ram=[(q+19*i)&255 for i in range(16)];a=255-q;x=255;y=255
            result=inspect_local(mapping,config,ram,q,a,127,x,y,out)
            name=f'local-q-{q:02x}';shutil.copytree(out,args.out/name,dirs_exist_ok=True)
            locals.append(dict(path=name,ram=ram,q=q,a=a,shift=127,x=x,y=y,trace_digest=result['trace_digest']))
    sources=[Path(__file__),HERE/'early-entry22.json',HERE/'early_wait.py',HERE/config['early_configuration'],HERE/'execute.py',HERE/'external_line.py',HERE/'common.py',HERE/'defined_condition_fit.py',HERE/'handler_timing_study.py',HERE/'selector_prefix_study.py',HERE.parent/'model.py',HERE/early['handler_configuration'],HERE/h['profiles']['q3'],HERE/h['scenario'],HERE/h['tables']]
    save(args.out/'report.json',dict(configuration=config,arithmetic=arithmetic,reset_cases=len(runs),runs=runs,witnesses=witnesses,local_witnesses=locals,source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}))
    print(len(runs),'reset cases;',len(witnesses),'reset and',len(locals),'local witnesses',flush=True)


if __name__=='__main__':main()
