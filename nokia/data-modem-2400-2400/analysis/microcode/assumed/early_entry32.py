"""Explain early nested branch choices and their retained comparison input."""
import argparse
import hashlib
import shutil
import tempfile
from pathlib import Path
from common import HERE,read,save
from execute import execute
from defined_condition_fit import load_trace
from handler_timing_study import classify
from early_wait import scenario_for as early_scenario


def prediction(i,j,a,b,w,z,capture,tail):
    r=(b-2+int(a!=0))&255 if i in (0,2) else (w-1)&255
    if i==0:cycle=29
    elif i==2:cycle=30
    elif i==1:
        cycle=35 if j==1 and z==255 else 38 if j==1 else 36-int(j==2 and w!=1)
    else:cycle=32 if j==1 else 33-int(j==2 and w!=1)
    terminal=r==1;ram=[0]*16;ram[0]=2;ram[2]=2 if terminal else r
    ram[3]=(tail-2)&255 if terminal else r;ram[4]=(capture+1)&255
    return dict(ram=ram,q=1,comparison=r,first_wait=cycle,terminal=terminal,first_terminal=cycle+18 if terminal else None)


def scenario_for(config,i,j,a,b,w,z,capture,tail):
    early=read(HERE/config['early_configuration']);s=early_scenario(early,i,5,1,capture,tail)
    s.update(name=f'early032 {i}/{j}/{a:02x}/{b:02x}/{w:02x}/{z:02x}/{capture:02x}/{tail:02x}',evidence=config['evidence'])
    s['branch_tables']['8']['index_source']='previous_y';s['branch_tables'][str(0x3c)]['index_source']='previous_y'
    s['io']['read']['pc_sequences'].update({str(pc):[value] for pc,value in ((0x33,a),(0x34,b),(0x3b,j),(0x3c,w),(0x36,z))})
    return s


def inspect(trace,summary,scenario,i,j,a,b,w,z,capture,tail):
    want=prediction(i,j,a,b,w,z,capture,tail)
    assert summary['clean'] and not summary['unused_word_executions']
    assert summary['final_state']['ram']==want['ram'] and summary['final_state']['q']==1
    at={r['pc']:r for r in trace if r['pc']<0x5d}
    assert at[8]['next_pc']==0x32 and at[8]['dispatch_input']==6
    assert at[0x32]['q']==1 and at[0x36]['next_pc']==0x37+i
    assert (0x3c in at)==(i in (1,3))
    if i in (1,3):
        assert at[0x3c]['dispatch_input']==j and at[0x3c]['next_pc']==0x3d+j
        if j==2:assert at[0x3f]['next_pc']==(0x40 if w==1 else 0x41)
    assert 0x43 not in at and 0x44 not in at
    assert (0x46 in at)==(i==1 and j==1 and z!=255)
    assert next(r['cycle'] for r in trace if r['pc']==0x5d)==want['first_wait']
    finding=classify(trace,scenario)
    if want['terminal']:
        assert next(r['cycle'] for r in trace if r['pc']==0x84)==want['first_terminal']
        assert summary['stack']['final_depth']==0
    else:
        assert not any(r['pc']==0x64 or r['pc']==0x84 for r in trace)
        assert finding['repeat']['period']==7
    assert summary['stack']['max_depth']==1
    return dict(**want,classification=finding)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,default=HERE/'results/early-entry32');args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'early-entry32.json');early=read(HERE/config['early_configuration']);h=read(HERE/early['handler_configuration']);mapping=read(HERE/h['profiles']['q3'])
    runs=[];witnesses=[];seen=set()
    with tempfile.TemporaryDirectory() as temp:
        out=Path(temp)
        for i in range(4):
            for j in range(3):
                for a in (0,1):
                    for b in (0,1,2,255):
                        for w in (0,1,2,255):
                            for z in (1,255):
                                capture=b^w;tail=a^z;s=scenario_for(config,i,j,a,b,w,z,capture,tail)
                                result=execute(mapping,s,config['cycles'],mode='integrated',out=out,trace_limit=config['cycles'])
                                want=inspect(load_trace(out),result,s,i,j,a,b,w,z,capture,tail)
                                case=dict(i=i,j=j,a=a,b=b,w=w,z=z,capture=capture,tail=tail,prediction=want,trace_digest=result['trace_digest']);runs.append(case)
                                key=(i,j,w==1,z==255) if i in (1,3) else (i,)
                                if key not in seen:
                                    seen.add(key);name='case-'+'-'.join(str(int(k)) for k in key);shutil.copytree(out,args.out/name,dirs_exist_ok=True);witnesses.append(dict(path=name,**case))
            print('first branch',i,'verified',flush=True)
    sources=[Path(__file__),HERE/'early-entry32.json',HERE/'early_wait.py',HERE/config['early_configuration'],HERE/'execute.py',HERE/'external_line.py',HERE/'common.py',HERE/'defined_condition_fit.py',HERE/'handler_timing_study.py',HERE/'selector_prefix_study.py',HERE.parent/'model.py',HERE/early['handler_configuration'],HERE/h['profiles']['q3'],HERE/h['scenario'],HERE/h['tables']]
    save(args.out/'report.json',dict(configuration=config,reset_cases=len(runs),runs=runs,witnesses=witnesses,source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}))
    print(len(runs),'reset cases;',len(witnesses),'witnesses',flush=True)


if __name__=='__main__':main()
