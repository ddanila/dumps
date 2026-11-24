"""Connect all three q3 handler-5 continuations to actual reset and terminal stores."""
import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from common import HERE,read,save
from execute import execute
from defined_condition_fit import load_trace
from handler_timing_study import scenario_for_case


def scenario_for(config,code,entry,u,v,mask):
    h=read(HERE/config['handler_configuration']);s=scenario_for_case(h,'q3','previous','plp',code)
    s.update(name=f'q3 handler5 c={code:02x} row={entry} u={u:02x} v={v:02x} mask={mask:02x}',evidence=config['evidence'])
    s['dispatch']['value']=entry
    for pc in (0x7e,0x81):s['dispatch']['tables'][str(pc)]['index_source']='previous_y'
    s['io']['read']['pc_sequences'].update({str(0x89):[2],str(0x336):[u],str(0x359):[v],str(0x354):[mask]})
    return s


def prediction(code,entry,u,v):
    ram=[0]*16;ram[3]=3
    for r in (8,13):ram[r]=(code+1)&255
    if entry==0:ram[4]=v;q=0
    elif entry==1:
        q=code;ram[0]=ram[2]=code>>1;ram[4]=(v+code)&255
        ram[5]=(255-code)>>1
    else:
        assert entry==2
        q=255;ram[0]=ram[2]=127;ram[4]=u
    calls={0:[0x366,0x357,0x335,0x357],1:[0x366,0x357],2:[0x335,0x366]}[entry]
    return dict(ram=ram,q=q,first_terminal=[129,109,110][entry],calls=calls)


def inspect(trace,summary,code,entry,u,v,mask):
    want=prediction(code,entry,u,v)
    assert summary['clean'] and not summary['unused_word_executions']
    assert summary['final_state']['ram']==want['ram'] and summary['final_state']['q']==want['q']
    assert next(r['cycle'] for r in trace if r['pc']==0x84)==want['first_terminal']
    assert [r['pc'] for r in trace if r['pc'] in (0x335,0x357,0x366)]==want['calls']
    branch=next(r for r in trace if r['pc']==0x34c)
    assert branch['dispatch_entry']==entry and branch['next_pc']==0x34d+entry
    stores=[r for r in trace if r['pc'] in (0x7e,0x81)]
    assert len(stores)==2 and all(r['dispatch_input']==2 and r['next_pc']==0x8c for r in stores)
    initial_pair=[r for r in trace if 0x392+4*entry<=r['pc']<=0x395+4*entry]
    word=2*(code+1) if entry==0 else 0
    assert [r['alu']['y'] for r in initial_pair]==[word&255,word>>8,0,0]
    masked=[r for r in trace if r['pc']==0x354]
    assert len(masked)==int(entry!=2)
    if masked:assert masked[0]['alu']['f']==mask&(code if entry==1 else 0)
    assert summary['stack']['max_depth']==3 and summary['stack']['final_depth']==0
    return want


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/handler5-branches')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'handler5-branches.json');h=read(HERE/config['handler_configuration']);mapping=read(HERE/h['profiles']['q3'])
    runs=[];witnesses=[];seen=set()
    with tempfile.TemporaryDirectory() as tmp:
        out=Path(tmp)
        for code in range(5,256,8):
            for entry in range(3):
                for u in (0,1,127,255):
                    for v in (0,1,128,255):
                        mask=u^v;scenario=scenario_for(config,code,entry,u,v,mask)
                        summary=execute(mapping,scenario,config['cycles'],mode='integrated',out=out,trace_limit=config['cycles'])
                        want=inspect(load_trace(out),summary,code,entry,u,v,mask)
                        case=dict(code=code,entry=entry,u=u,v=v,mask=mask,prediction=want,trace_digest=summary['trace_digest']);runs.append(case)
                        if code in (5,253) and (code,entry) not in seen:
                            seen.add((code,entry));name=f'{code:02x}-entry-{entry}'
                            shutil.copytree(out,args.out/name,dirs_exist_ok=True);witnesses.append(dict(path=name,**case))
            if code in (5,253):print(f'{code:02x}: three continuations verified',flush=True)
    sources=[Path(__file__),HERE/'handler5-branches.json',HERE/'execute.py',HERE/'external_line.py',HERE/'common.py',
        HERE/'defined_condition_fit.py',HERE/'handler_timing_study.py',HERE/'selector_prefix_study.py',HERE.parent/'model.py',
        HERE/config['handler_configuration'],HERE/h['profiles']['q3'],HERE/h['scenario'],HERE/h['tables']]
    save(args.out/'report.json',dict(configuration=config,reset_cases=len(runs),runs=runs,witnesses=witnesses,
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='Three q3 handler-5 continuation tables compose verified helper calls from real reset. Different Q constants and captured inputs survive terminal R2 stores; the intermediate 354 mask is overwritten. Fixed dispatch/inputs remain hypotheses.'))
    print(len(runs),'full reset cases;',len(witnesses),'witnesses')


if __name__=='__main__':main()
