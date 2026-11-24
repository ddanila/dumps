"""Connect handler-1 timed continuations to input parity and final state."""
import argparse
import hashlib
import shutil
import tempfile
from pathlib import Path
from common import HERE,read,save,decode
from execute import execute
from defined_condition_fit import load_trace
from handler1_study import scenario_for as base_scenario,prediction as base_prediction
from handler_reply_study import prestate
from model import Am2901


def prediction(code,u,v,d,w,route):
    assert route in ('high','low','rise')
    base=base_prediction(code,u,v);p=(1-d)&1;ram=base['ram'][:];ram[5]=127*p
    return dict(ram=ram,q=p,transition=base['first_terminal']-31,
        first_terminal=base['first_terminal']+(4-p if route=='rise' else 0),
        temporary_half=((w+p)&255)>>1)


def scenario_for(config,code,u,v,d,w,route):
    base=read(HERE/config['handler_configuration']);s=base_scenario(base,code,u,v);want=prediction(code,u,v,d,w,route)
    s.update(name=f'handler1 branches c={code:02x} u={u:02x} v={v:02x} d={d:02x} w={w:02x} route={route}',evidence=config['evidence'])
    s['io']['read']['pc_sequences'].update({str(0x164):[d],str(0x17f):[w]})
    s['condition']['sources'][5]='external';s['condition']['polarity'][5]=0
    events=[] if route=='high' else [[want['transition'],0]]
    if route=='rise':events.append([want['transition']+3,1])
    s['inputs']['external']=dict(mode='cycle-events',initial=1,events=events,status='stub',evidence=config['evidence'])
    return s


def inspect(trace,summary,code,u,v,d,w,route):
    want=prediction(code,u,v,d,w,route);p=want['q']
    assert summary['clean'] and not summary['unused_word_executions']
    assert summary['final_state']['ram']==want['ram'] and summary['final_state']['q']==p
    at={r['pc']:r for r in trace if r['pc']!=0x84}
    assert at[0x164]['alu']['f']==(1-d)&255 and at[0x173]['q']==p
    entry=prestate(trace,0x177);assert entry['cycle']==want['transition'] and entry['q']==p
    assert entry['ram'][0]==0 and entry['ram'][3]==(1-d)&255 and entry['ram'][2]==p+1
    assert at[0x177]['next_pc']==(0x180 if route=='high' else 0x178)
    if route!='high':
        assert at[0x179]['alu']['f']==0 and at[0x17a]['alu']['f']==p
        assert at[0x17a]['next_pc']==(0x17f if route=='rise' else 0x17b)
    if route=='rise':
        assert at[0x17f]['alu']['f']==(w+p)&255
        assert at[0x17f]['next_pc']==(0x181 if p else 0x180)
        assert prestate(trace,at[0x17f]['next_pc'])['ram'][2]==want['temporary_half']
    else:assert 0x17f not in at
    assert (0x180 in at)==(route=='high' or route=='rise' and not p)
    assert (0x17b in at)==(route=='low')
    assert at[0xe9]['alu']['f']==0 and at[0xea]['next_pc']==0x7b
    assert all(pc not in at for pc in (0x78,0x79,0x7a))
    assert next(r['cycle'] for r in trace if r['pc']==0x84)==want['first_terminal']
    assert summary['stack']['max_depth']==3 and summary['stack']['final_depth']==0
    return want


def check_parity(mapping):
    rows=decode(mapping)
    for d in range(256):
        for w in range(256):
            cpu=Am2901(ram=[(i*37+11)&255 for i in range(16)],q=1,logic_flags=True);cpu.ram[15]=1
            row=rows[0x164];cpu.step(row['i'],row['a'],row['b'],d,1,0,0)
            assert cpu.ram[3]==(1-d)&255
            row=rows[0x173];cpu.step(row['i'],row['a'],row['b'],1,1,0,0)
            p=(1-d)&1;assert cpu.q==p;cpu.ram[0]=0;before=cpu.ram[:]
            row=rows[0x17a];flag=cpu.step(row['i'],row['a'],row['b'],1,0,0,0)
            assert flag['zero']==int(p==0)
            row=rows[0x17f];value=cpu.step(row['i'],row['a'],row['b'],w,0,0,0)
            before[2]=((w+p)&255)>>1
            assert cpu.ram==before and cpu.q==p and value['f']==(w+p)&255
    return 65536


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,default=HERE/'results/handler1-branches');args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'handler1-branches.json');base=read(HERE/config['handler_configuration']);h=read(HERE/base['handler_config']);mapping=read(HERE/base['mapping']);runs=[];witnesses=[]
    pairs=check_parity(mapping);print(pairs,'input/shift pairs checked',flush=True)
    with tempfile.TemporaryDirectory() as temp:
        out=Path(temp)
        for code in range(1,256,8):
            for u,v in ((0,255),(1,0),(128,128),(255,255)):
                for d in (0,1,128,255):
                    w=d^u^v;prefix=None
                    for route in ('high','low','rise'):
                        values=(code,u,v,d,w,route);s=scenario_for(config,*values)
                        summary=execute(mapping,s,config['cycles'],mode='integrated',out=out,trace_limit=config['cycles']);trace=load_trace(out)
                        want=inspect(trace,summary,*values)
                        if prefix is None:prefix=trace[:want['transition']]
                        else:
                            for actual,old in zip(trace[:want['transition']],prefix):
                                for k in ('pc','next_pc','alu','q','registers','stack_after'):assert actual[k]==old[k]
                        case=dict(code=code,u=u,v=v,d=d,w=w,route=route,prediction=want,trace_digest=summary['trace_digest']);runs.append(case)
                        if code in (1,249) and u==0 and d in (0,255):
                            name=f'{code:02x}-{route}-d-{d:02x}';shutil.copytree(out,args.out/name,dirs_exist_ok=True);witnesses.append(dict(path=name,**case))
            if code in (1,249):print(f'{code:02x}: all three continuations verified',flush=True)
    sources=[Path(__file__),HERE/'handler1-branches.json',HERE/'handler1_study.py',HERE/config['handler_configuration'],HERE/'handler_reply_study.py',HERE/'execute.py',HERE/'external_line.py',HERE/'common.py',HERE/'defined_condition_fit.py',HERE/'handler_timing_study.py',HERE/'selector_prefix_study.py',HERE.parent/'model.py',HERE/base['handler_config'],HERE/base['mapping'],HERE/h['scenario'],HERE/h['tables']]
    save(args.out/'report.json',dict(configuration=config,arithmetic_pairs=pairs,reset_cases=len(runs),prefix_comparisons=len(runs)//3*2,runs=runs,witnesses=witnesses,source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}))
    print(len(runs),'reset cases;',len(witnesses),'witnesses',flush=True)


if __name__=='__main__':main()
