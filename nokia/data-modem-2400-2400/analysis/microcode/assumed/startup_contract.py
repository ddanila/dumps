"""Connect startup preparation, two independent byte waits and handler dispatch."""
import argparse
import hashlib
import shutil
import tempfile
from pathlib import Path
from common import HERE,read,save,decode
from execute import execute
from defined_condition_fit import load_trace
from handler_timing_study import scenario_for_case,classify
from model import Am2901

HANDLERS=(0x11a,0x148,0x18b,0x300,0x259,0x345,0x09e,0x133)


def prediction(code,k1,k2,r,s,a1,a2,w):
    ram=[0]*16;ram[0]=255;ram[2]=1;ram[4]=(code+a2)&255;ram[6]=(r-1)&255;ram[7]=(s-1)&255
    return dict(ram=ram,q=code,handler=HANDLERS[code%8],cycles=37+2*(k1+k2),
        first_capture=(code+a1)&255,exposed108=(w+code+int(s!=0))&255)


def scenario_for(config,code,k1,k2,r,s,a1,a2,w,fail1=255,fail2=1):
    assert fail1 in range(1,256) and fail2 in range(1,256)
    h=read(HERE/config['handler_configuration']);sc=scenario_for_case(h,'q3','previous','plp',code)
    sc.update(name=f'startup {code:02x}/{k1}/{k2}/{r:02x}/{s:02x}/{a1:02x}/{a2:02x}/{w:02x}/{fail1:02x}/{fail2:02x}',evidence=config['evidence'])
    split=code^165
    sc['io']['read']['pc_sequences'].update({str(0x002):[split],str(0x076):[(code-split)&255],
        str(0x117):[fail1]*k1+[0],str(0x106):[fail2]*k2+[0],str(0x118):[r],str(0x107):[s],str(0x115):[a1,a2],str(0x108):[w]})
    return sc


def inspect(trace,summary,code,k1,k2,r,s,a1,a2,w):
    want=prediction(code,k1,k2,r,s,a1,a2,w)
    assert summary['clean'] and not summary['unused_word_executions'] and summary['completed_cycles']==want['cycles']
    assert summary['final_state']['ram']==want['ram'] and summary['final_state']['q']==code
    assert summary['final_state']['pc']==want['handler']
    assert summary['stack']['max_depth']==2 and summary['stack']['final_depth']==0
    loads=[x for x in trace if x['pc']==0x115]
    assert [x['alu']['f'] for x in loads]==[want['first_capture'],want['ram'][4]]
    for plp,blt,k,capture in ((0x117,0x118,k1,r),(0x106,0x107,k2,s)):
        starts=[x for x in trace if x['pc']==plp];ends=[x for x in trace if x['pc']==blt]
        assert len(starts)==len(ends)==k+1
        assert [x['alu']['carry'] for x in starts]==[1]*k+[0]
        assert [x['next_pc'] for x in ends]==[plp]*k+[blt+1]
        assert all(x['alu']['f']==(capture-1)&255 and x['alu']['y']==255 for x in ends)
    at={x['pc']:x for x in trace}
    assert at[0x119]['cycle']==24+2*k1 and at[0x119]['alu']['y']==want['first_capture'] and at[0x119]['next_pc']==0x104
    assert next(x['cycle'] for x in trace if x['pc']==0x106)==32+2*k1
    assert at[0x108]['alu']['y']==want['exposed108']
    assert at[0x109]['dispatch_input']==code and at[0x109]['next_pc']==0x10a+code%8
    assert trace[-1]['next_pc']==want['handler']
    assert all(x['pc'] not in HANDLERS for x in trace)
    return want


def check_waits(mapping):
    rows=decode(mapping)
    for plp,blt,register in ((0x117,0x118,6),(0x106,0x107,7)):
        for poll in range(256):
            for capture in range(256):
                ram=[(i*37+11)&255 for i in range(16)];ram[0]=255;q=poll^capture
                cpu=Am2901(ram=ram[:],q=q,logic_flags=True)
                row=rows[plp];first=cpu.step(row['i'],row['a'],row['b'],poll,0,0,0)
                assert first['carry']==int(poll!=0) and first['y']==255 and cpu.ram[register]==(poll-1)&255
                row=rows[blt];last=cpu.step(row['i'],row['a'],row['b'],capture,0,0,0)
                ram[register]=(capture-1)&255
                assert cpu.ram==ram and cpu.q==q and last['carry']==int(capture!=0) and last['y']==255
    return 131072


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,default=HERE/'results/startup-contract');args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'startup-contract.json');h=read(HERE/config['handler_configuration']);mapping=read(HERE/h['profiles']['q3']);runs=[];witnesses=[];held=[]
    arithmetic=check_waits(mapping);print(arithmetic,'wait/capture pairs checked',flush=True)
    with tempfile.TemporaryDirectory() as temp:
        out=Path(temp)
        for code in range(256):
            for k1,k2 in ((0,0),(1,2),(3,1)):
                for r,s in ((0,0),(0,255),(255,0),(128,1)):
                    for a1,a2 in ((0,255),(255,0)):
                        w=code^r^s;values=(code,k1,k2,r,s,a1,a2,w);sc=scenario_for(config,*values);cycles=prediction(*values)['cycles']
                        result=execute(mapping,sc,cycles,mode='integrated',out=out,trace_limit=cycles);want=inspect(load_trace(out),result,*values)
                        case=dict(code=code,k1=k1,k2=k2,r=r,s=s,a1=a1,a2=a2,w=w,prediction=want,trace_digest=result['trace_digest']);runs.append(case)
                        if code in (0,255) and k1 in (0,1) and (r,s) in ((0,0),(255,0)) and a1==0:
                            name=f'{code:02x}-k-{k1}-{k2}-r-{r:02x}';shutil.copytree(out,args.out/name,dirs_exist_ok=True);witnesses.append(dict(path=name,**case))
            if code in (0,255):print(f'{code:02x}: prepared state and dispatch checked',flush=True)
        for code in (*range(8),255):
            for pc in (0x117,0x106):
                sc=scenario_for(config,code,0,0,128,255,0,255,17);sc['io']['read']['pc_sequences'][str(pc)]=[255]
                result=execute(mapping,sc,96,mode='integrated',out=out,trace_limit=96);trace=load_trace(out);finding=classify(trace,sc)
                assert result['clean'] and finding['outcome']=='repeat' and finding['dispatch'] is None
                assert finding['repeat']['period']==2 and finding['repeat']['next_pc'] in (pc,pc+1)
                assert not any(x['pc']==pc+2 for x in trace)
                case=dict(code=code,held_pc=pc,trace_digest=result['trace_digest'],finding=finding);held.append(case)
                if code==255:
                    name=f'held-{pc:03x}';shutil.copytree(out,args.out/name,dirs_exist_ok=True);witnesses.append(dict(path=name,**case))
    sources=[Path(__file__),HERE/'startup-contract.json',HERE/'execute.py',HERE/'external_line.py',HERE/'common.py',HERE/'defined_condition_fit.py',HERE/'handler_timing_study.py',HERE/'selector_prefix_study.py',HERE.parent/'model.py',HERE/config['handler_configuration'],HERE/h['profiles']['q3'],HERE/h['scenario'],HERE/h['tables']]
    save(args.out/'report.json',dict(configuration=config,arithmetic_pairs=arithmetic,prefix_cases=len(runs),held_controls=held,runs=runs,witnesses=witnesses,source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}))
    print(len(runs),'reset prefixes;',len(held),'held controls;',len(witnesses),'witnesses',flush=True)


if __name__=='__main__':main()
