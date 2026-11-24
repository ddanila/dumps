"""Reach handler-3 alternate drains using an explicit two-selector line hypothesis."""
import argparse
import hashlib
import shutil
import tempfile
from pathlib import Path
from common import HERE,read,save
from execute import execute
from defined_condition_fit import load_trace
from handler_timing_study import scenario_for_case


def scenario_for(config,code,index,first,component,mask1,mask2,high,low,fall=43,invert_select3=True):
    h=read(HERE/config['handler_configuration']);s=scenario_for_case(h,'q3','previous','plp',code)
    s.update(name=f'handler3 drains {code:02x}/{index}/{first:02x}/{component:02x}/{mask1:02x}/{mask2:02x}/{high:02x}/{low:02x}/{fall}/{invert_select3}',evidence=config['evidence'])
    s['dispatch']['value']=index;s['condition']['sources'][5]='external';s['condition']['polarity'][5]=0
    if invert_select3:s['condition']['sources'][3]='external';s['condition']['polarity'][3]=1
    s['inputs']['external']=dict(mode='cycle-events',initial=1,events=[[fall,0]],status='stub',evidence=config['evidence'])
    s['io']['read']['pc_sequences'].update({str(pc):[v] for pc,v in ((0x1f0,first),(0x1f3,component),(0x1f8,mask1),(0x1fc,mask2),(0x316,high),(0x317,low))})
    return s


def inspect(trace,summary,index,first,component,mask1,mask2,high,low):
    ram=[0]*16;ram[2]=int(index!=2);ram[4]=low;ram[13]=high
    r5=(2*(component-1))&255;word=(2*(low+256*r5))&65535 if index in (0,3) else 0
    outputs=[word&255,word>>8,0,0]
    assert summary['clean'] and not summary['unused_word_executions']
    assert summary['final_state']['ram']==ram and summary['final_state']['q']==0
    assert next(r['cycle'] for r in trace if r['pc']==0x1ef)==45
    assert next(r['cycle'] for r in trace if r['pc']==0x370)==111
    assert next(r['cycle'] for r in trace if r['pc']==0x84)==146
    at={r['pc']:r for r in trace if r['pc']!=0x84}
    assert at[0x302]['next_pc']==0x303 and at[0x303]['next_pc']==0x1ef
    assert at[0x1f0]['alu']['f']==(first-1)&255 and at[0x1f0]['q']==254
    assert at[0x1f3]['alu']['f']==(component-1)&255 and at[0x1f3]['q']==254
    assert at[0x1f8]['q']==127 and at[0x1f8]['alu']['f']==mask1
    assert at[0x1fc]['q']==0 and at[0x1fc]['alu']['f']==0
    assert [r['cycle'] for r in trace if r['pc']==0x1e9]==list(range(64,80,2))+[96]
    assert [r['cycle'] for r in trace if r['pc']==0x311]==[82,100]
    assert at[0x1ff]['next_pc']==0x308
    assert [r['alu']['y'] for r in trace if 0x379<=r['pc']<=0x388]==outputs
    assert summary['stack']['max_depth']==3 and summary['stack']['final_depth']==0
    return dict(ram=ram,q=0,paired_outputs=outputs,retained_r5_at_pair=r5,first_terminal=146)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,default=HERE/'results/handler3-drains');args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'handler3-drains.json');h=read(HERE/config['handler_configuration']);mapping=read(HERE/h['profiles']['q3']);runs=[];witnesses=[];controls=[]
    with tempfile.TemporaryDirectory() as temp:
        out=Path(temp)
        for code in range(3,256,8):
            for fall,invert in ((43,False),(44,True)):
                s=scenario_for(config,code,2,1,1,1,1,1,1,fall,invert);result=execute(mapping,s,192,mode='integrated',out=out,trace_limit=192)
                trace=load_trace(out);assert result['clean'] and not any(r['pc']==0x1ef for r in trace)
                controls.append(dict(code=code,fall=fall,invert_select3=invert,trace_digest=result['trace_digest'],first_terminal=next(r['cycle'] for r in trace if r['pc']==0x84)))
            baseline=scenario_for_case(h,'q3','previous','plp',code);execute(mapping,baseline,43,mode='integrated',out=out,trace_limit=43);prefix=load_trace(out)
            for index in range(4):
                for component in (0,1,128,255):
                    for low in (0,1,128,255):
                        first=component^255;mask1=low^0xaa;high=component^low;mask2=high^0x55
                        s=scenario_for(config,code,index,first,component,mask1,mask2,high,low)
                        result=execute(mapping,s,192,mode='integrated',out=out,trace_limit=192);trace=load_trace(out)
                        want=inspect(trace,result,index,first,component,mask1,mask2,high,low)
                        for actual,old in zip(trace[:43],prefix):
                            for k in ('pc','next_pc','alu','q','registers','stack_after'):assert actual[k]==old[k]
                        case=dict(code=code,index=index,first=first,component=component,mask1=mask1,mask2=mask2,high=high,low=low,prediction=want,trace_digest=result['trace_digest']);runs.append(case)
                        if code in (3,251) and component==128 and low==255:
                            name=f'{code:02x}-index-{index}';shutil.copytree(out,args.out/name,dirs_exist_ok=True);witnesses.append(dict(path=name,**case))
            if code in (3,251):print(f'{code:02x}: alternate drains and controls verified',flush=True)
    sources=[Path(__file__),HERE/'handler3-drains.json',HERE/'execute.py',HERE/'external_line.py',HERE/'common.py',HERE/'defined_condition_fit.py',HERE/'handler_timing_study.py',HERE/'selector_prefix_study.py',HERE.parent/'model.py',HERE/config['handler_configuration'],HERE/h['profiles']['q3'],HERE/h['scenario'],HERE/h['tables']]
    save(args.out/'report.json',dict(configuration=config,reset_cases=len(runs),runs=runs,witnesses=witnesses,controls=controls,source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}))
    print(len(runs),'reset cases;',len(controls),'negative controls;',len(witnesses),'witnesses',flush=True)


if __name__=='__main__':main()
