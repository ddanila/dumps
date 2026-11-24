"""Explain handler-2 alternate carry preparation and four computed return leaves."""
import argparse
import hashlib
import shutil
import tempfile
from pathlib import Path
from common import HERE,read,save,decode
from execute import execute
from defined_condition_fit import load_trace
from handler_timing_study import scenario_for_case
from handler_reply_study import prestate
from model import Am2901


def prediction(code,e,b,payload,index,delay):
    assert code%8==2 and 0<=index<4
    overflow=code+e>=256;r=254+int(code>=128 and not overflow);s=(code+b)&255;carry=int(code+b>=256)
    ram=[0]*16;ram[0]=ram[2]=payload>>1;ram[5]=((-payload)&255)>>1;ram[12]=r
    return dict(ram=ram,q=payload,overflow=overflow,retained=r,release=(-r)&255,qsum=s,
        leaf_value=(254+carry if index==0 else 1+carry if index==1 else carry),
        first_poll=180+2*s.bit_length()-overflow,first_terminal=212+2*s.bit_length()-overflow+2*delay)


def scenario_for(config,code,e,b,payload,index,delay):
    h=read(HERE/config['handler_configuration']);s=scenario_for_case(h,'q3','previous','plp',code);want=prediction(code,e,b,payload,index,delay)
    s.update(name=f'handler2 alternate {code:02x}/{e:02x}/{b:02x}/{payload:02x}/{index}/{delay}',evidence=config['evidence'])
    s['condition']['sources'][7]='external';s['condition']['polarity'][7]=0
    s['inputs']['external']=dict(mode='cycle-events',initial=0,events=[[92,1]],status='stub',evidence=config['evidence'])
    s['dispatch']['tables'][str(0x1a2)]['index_source']='previous_y'
    s['io']['read']['pc_sequences'].update({str(pc):[value] for pc,value in ((0x1e1,e),(0x1a1,(code+1+index)&255),(0x1a2,b),(0x1d0,payload))})
    s['io']['read']['pc_sequences'][str(0x1ec)]=[(want['release']+1)&255]*delay+[want['release']]
    return s


def inspect(trace,summary,code,e,b,payload,index,delay):
    want=prediction(code,e,b,payload,index,delay)
    assert summary['clean'] and not summary['unused_word_executions']
    assert summary['final_state']['ram']==want['ram'] and summary['final_state']['q']==payload
    at={r['pc']:r for r in trace if r['pc']!=0x84}
    entry=prestate(trace,0x195);assert entry['cycle']==92 and entry['ram'][0]==code and entry['q']==code
    assert at[0x194]['alu']['zero']==0 and at[0x195]['next_pc']==0x1e0
    assert at[0x1e1]['alu']['f']==(code+e)&255 and at[0x1e1]['alu']['carry']==want['overflow']
    assert at[0x1e2]['next_pc']==(0x1e4 if want['overflow'] else 0x1e3)
    assert (0x1e3 in at)==(not want['overflow']) and at[0x19c]['alu']['f']==want['retained']
    assert not any(pc in at for pc in range(0x196,0x19c))
    assert at[0x1a1]['alu']['y']==index
    assert at[0x1a2]['dispatch_input']==index and at[0x1a2]['next_pc']==0x1e5+index and at[0x1a2]['q']==want['qsum']
    leaf=at[0x1e5+index];assert leaf['alu']['f']==want['leaf_value'] and leaf['next_pc']==0x1a3
    assert leaf['stack_before']['depth']==1 and leaf['stack_after']['depth']==0
    poll=[r for r in trace if r['pc']==0x1ec]
    assert len(poll)==delay+1 and poll[0]['cycle']==want['first_poll']
    assert [r['alu']['f'] for r in poll]==[1]*delay+[0]
    assert next(r['cycle'] for r in trace if r['pc']==0x84)==want['first_terminal']
    assert summary['stack']['max_depth']==3 and summary['stack']['final_depth']==0
    return want


def check_arithmetic(mapping):
    rows=decode(mapping)
    for code in range(2,256,8):
        for e in range(256):
            cpu=Am2901(q=code,logic_flags=True);cpu.ram[0]=code;cpu.ram[3]=1
            r=rows[0x1e1];first=cpu.step(r['i'],r['a'],r['b'],e,0,0,0)
            assert first['carry']==int(code+e>=256)
            r=rows[0x1e2];value=cpu.step(r['i'],r['a'],r['b'],1,first['carry'],0,0)
            if not first['carry']:
                r=rows[0x1e3];cpu.step(r['i'],r['a'],r['b'],1,value['carry'],0,0)
            assert cpu.ram[0]==(0 if first['carry'] else code)
            r=rows[0x1e4];value=cpu.step(r['i'],r['a'],r['b'],1,1,0,0)
            r=rows[0x19c];cpu.step(r['i'],r['a'],r['b'],1,value['carry'],0,0)
            assert cpu.q==code and cpu.ram[4]==254+int(code>=128 and code+e<256)
        for b in range(256):
            for index in range(4):
                cpu=Am2901(q=code,logic_flags=True);cpu.ram[3]=1
                r=rows[0x1a2];value=cpu.step(r['i'],r['a'],r['b'],b,0,0,0)
                r=rows[0x1e5+index];cpu.step(r['i'],r['a'],r['b'],1,value['carry'],0,0)
                carry=int(code+b>=256);expected=254+carry if index==0 else 1+carry if index==1 else carry
                assert cpu.ram[3]==expected and cpu.q==(code+b)&255
    return dict(preparation_pairs=8192,leaf_cases=32768)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,default=HERE/'results/handler2-alternate');args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'handler2-alternate.json');h=read(HERE/config['handler_configuration']);mapping=read(HERE/h['profiles']['q3']);runs=[];witnesses=[];controls=[]
    arithmetic=check_arithmetic(mapping);print(arithmetic,flush=True)
    with tempfile.TemporaryDirectory() as temp:
        out=Path(temp)
        for code in range(2,256,8):
            base=scenario_for_case(h,'q3','previous','plp',code);execute(mapping,base,96,mode='integrated',out=out,trace_limit=96);prefix=load_trace(out)
            assert next(r for r in prefix if r['pc']==0x195)['next_pc']==0x196
            for kind in ('original-zero','late-rise'):
                s=scenario_for(config,code,0,0,0,0,0)
                if kind=='original-zero':s['condition']['sources'][7]='zero'
                else:s['inputs']['external']['events']=[[93,1]]
                result=execute(mapping,s,100,mode='integrated',out=out,trace_limit=100);trace=load_trace(out)
                assert result['clean'] and next(r for r in trace if r['pc']==0x195)['next_pc']==0x196
                assert not any(r['pc']==0x1e0 for r in trace)
                controls.append(dict(code=code,kind=kind,trace_digest=result['trace_digest']))
            for e in (0,255-code,256-code,255):
                for b,payload in ((0,0),(255,255),(256-code,128)):
                    for index in range(4):
                        delay=(e+b+index)%3;values=(code,e,b,payload,index,delay);s=scenario_for(config,*values)
                        result=execute(mapping,s,config['cycles'],mode='integrated',out=out,trace_limit=config['cycles']);trace=load_trace(out);want=inspect(trace,result,*values)
                        for actual,old in zip(trace[:92],prefix):
                            for k in ('pc','next_pc','alu','q','registers','stack_after'):assert actual[k]==old[k]
                        case=dict(code=code,e=e,b=b,payload=payload,index=index,delay=delay,prediction=want,trace_digest=result['trace_digest']);runs.append(case)
                        if code==130 and e in (0,126) and b==126:
                            name=f'82-e-{e:02x}-leaf-{index}';shutil.copytree(out,args.out/name,dirs_exist_ok=True);witnesses.append(dict(path=name,**case))
            if code in (2,250):print(f'{code:02x}: both entry controls and four leaves checked',flush=True)
    sources=[Path(__file__),HERE/'handler2-alternate.json',HERE/'handler_reply_study.py',HERE/'execute.py',HERE/'external_line.py',HERE/'common.py',HERE/'defined_condition_fit.py',HERE/'handler_timing_study.py',HERE/'selector_prefix_study.py',HERE.parent/'model.py',HERE/config['handler_configuration'],HERE/h['profiles']['q3'],HERE/h['scenario'],HERE/h['tables']]
    save(args.out/'report.json',dict(configuration=config,arithmetic=arithmetic,reset_cases=len(runs),negative_entry_controls=controls,runs=runs,witnesses=witnesses,source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}))
    print(len(runs),'reset cases;',len(controls),'negative controls;',len(witnesses),'witnesses',flush=True)


if __name__=='__main__':main()
