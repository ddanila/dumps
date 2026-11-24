"""Explain q3 handler 0 and its timing-dependent, input-independent waits."""
import argparse
import hashlib
import shutil
import tempfile
from pathlib import Path
from common import HERE,read,save
from execute import execute
from defined_condition_fit import load_trace
from handler_timing_study import scenario_for_case


def scenario_for(config,code,capture,before,after,temporary):
    h=read(HERE/config['handler_configuration'])
    s=scenario_for_case(h,'q3','current','blt',code)
    s.update(name=f'q3 handler0 {code:02x}/{capture:02x}/{before:02x}/{after:02x}/{temporary:02x}',evidence=config['evidence'])
    s['io']['read']['pc_sequences'].update({str(pc):[d] for pc,d in ((0x115,capture),(0x126,before),(0x12b,after),(0x271,temporary))})
    return s


def prediction(code,capture):
    ram=[0]*16;ram[0]=ram[2]=127;ram[4]=(code+capture)&255;ram[6]=ram[7]=255
    return dict(ram=ram,q=255,first_terminal=126)


def inspect(trace,summary,code,capture,before,after,temporary):
    want=prediction(code,capture)
    assert summary['clean'] and not summary['unused_word_executions']
    assert summary['final_state']['ram']==want['ram'] and summary['final_state']['q']==want['q']
    assert next(r['cycle'] for r in trace if r['pc']==0x84)==want['first_terminal']
    at={r['pc']:r for r in trace if r['pc']!=0x84}
    assert at[0x126]['q']==(code+before)&255
    assert at[0x128]['q']==0 and at[0x12b]['q']==after and at[0x12d]['q']==0
    assert at[0x271]['q']==temporary and at[0x23f]['q']==255
    assert [r['pc'] for r in trace if r['pc'] in (0x126,0x12c,0x9a,0x270,0x238,0x240,0x131)]==[0x126,0x9a,0x12c,0x9a,0x270,0x238,0x131,0x240,0x131]
    assert at[0x12a]['test']==at[0x12f]['test']==0
    assert at[0x278]['next_pc']==0x27b and at[0x27d]['next_pc']==0x27f
    assert at[0x125]['next_pc']==0x79 and at[0x79]['next_pc']==0x7b
    assert summary['stack']['max_depth']==2 and summary['stack']['final_depth']==0
    return want


def check_local(mapping,config,out):
    counts={}
    for timing in ('previous','current'):
        for entry,caller,return_cycles in ((0x126,0x11b,7),(0x12c,0x11d,6)):
            returned=0
            for a in range(256):
                s=scenario_for(config,8,1,a^0xa5,a^0x5a,1)
                s['condition']['flag_timing']=timing
                ram=[(a+17*i)&255 for i in range(16)];ram[0]=a
                s['initial']=dict(pc=caller,ram=ram,q=a^0x3c)
                exits=a==(0 if timing=='previous' else 255)
                cycles=return_cycles if exits else (14 if entry==0x126 else 13)
                result=execute(mapping,s,cycles,mode='integrated',out=out,trace_limit=cycles)
                assert result['clean'] and result['stack']['max_depth']==2
                final=result['final_state'];expected=ram[:];expected[2]=ram[1]
                assert final['ram']==expected
                assert final['q']==((a^0x5a) if exits and entry==0x126 else 0)
                assert result['stack']['final_depth']==(0 if exits else 1)
                if exits:assert final['pc']==caller+1
                else:
                    trace=load_trace(out);header=0x127 if entry==0x126 else 0x12c
                    ends=[r for r in trace if r['next_pc']==header and r['pc']==header+3]
                    assert len(ends)>=2
                    for key in ('next_pc','alu','q','stack_after'):assert ends[-1][key]==ends[-2][key]
                    assert ends[-1]['cycle']-ends[-2]['cycle']==4
                returned+=exits
            counts[f'{timing}-{entry:03x}']=dict(cases=256,returns=returned,repeats=256-returned)
    return counts


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,default=HERE/'results/handler0-study');args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True);config=read(HERE/'handler0-study.json');h=read(HERE/config['handler_configuration']);mapping=read(HERE/h['profiles']['q3'])
    runs=[];witnesses=[]
    with tempfile.TemporaryDirectory() as temp:
        out=Path(temp);local=check_local(mapping,config,out)
        print('1024 local timing/return cases checked',flush=True)
        for code in range(0,256,8):
            for capture in (0,1,127,255):
                for after in (0,1,128,255):
                    for temporary in (0,1,128,255):
                        before=capture^temporary;s=scenario_for(config,code,capture,before,after,temporary)
                        result=execute(mapping,s,config['cycles'],mode='integrated',out=out,trace_limit=config['cycles'])
                        want=inspect(load_trace(out),result,code,capture,before,after,temporary)
                        case=dict(code=code,capture=capture,before=before,after=after,temporary=temporary,prediction=want,trace_digest=result['trace_digest']);runs.append(case)
                        if code in (0,248) and capture in (0,255) and after==0 and temporary==255:
                            name=f'{code:02x}-capture-{capture:02x}';shutil.copytree(out,args.out/name,dirs_exist_ok=True);witnesses.append(dict(path=name,**case))
    sources=[Path(__file__),HERE/'handler0-study.json',HERE/'execute.py',HERE/'external_line.py',HERE/'common.py',HERE/'defined_condition_fit.py',HERE/'handler_timing_study.py',HERE/'selector_prefix_study.py',HERE.parent/'model.py',HERE/config['handler_configuration'],HERE/h['profiles']['q3'],HERE/h['scenario'],HERE/h['tables']]
    save(args.out/'report.json',dict(configuration=config,local=local,reset_cases=len(runs),runs=runs,witnesses=witnesses,source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}))
    print(len(runs),'reset cases;',len(witnesses),'saved witnesses',flush=True)


if __name__=='__main__':main()
