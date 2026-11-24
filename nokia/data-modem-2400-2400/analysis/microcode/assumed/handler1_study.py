"""Explain q3 handler 1's wrapped byte sum and input-dependent drain timing."""
import argparse
import hashlib
import shutil
import tempfile
from collections import Counter
from pathlib import Path
from common import HERE, read, save, decode
from execute import execute
from defined_condition_fit import load_trace
from handler_timing_study import scenario_for_case, classify
from model import Am2901


def scenario_for(config, code, u, v):
    assert code in range(1,256,8) and u in range(256) and v in range(256)
    scenario=scenario_for_case(read(HERE/config['handler_config']),'q3','previous','plp',code)
    scenario.update(name='q3 handler 1 wrapped byte sum',evidence=config['evidence'])
    scenario['io']['read']['evidence']=config['evidence']
    scenario['io']['read']['pc_sequences'].update({str(0x167):[u],str(0x16a):[v]})
    return scenario


def prediction(code,u,v):
    first_q=((2*code)&255)>>2
    left_iterations=1 if first_q==0 else 9-((first_q&-first_q).bit_length()-1)
    ram=[0]*16
    ram[4],ram[12],ram[14],ram[15]=code+1,1,((u+v)&255)>>1,(code+3)&255
    return dict(ram=ram,q=0,half=ram[14],first_left_iterations=left_iterations,
                second_left_iterations=9,right_drain_iterations=(u>>1).bit_length()+1,
                first_terminal=195+2*left_iterations+2*(u>>1).bit_length())


def check_sum(rows,u,v):
    # Exercise the actual load/copy/sum/shift words, starting with nonzero
    # unrelated registers so accidental writes cannot hide behind reset zeros.
    ram=[(37*i+19)&255 for i in range(16)]
    cpu=Am2901(ram=ram[:],q=173,logic_flags=True)
    for pc,d in ((0x167,u),(0x168,1),(0x169,1),(0x16a,v)):
        row=rows[pc]
        assert row['carry_select']==0
        result=cpu.step(row['i'],row['a'],row['b'],d,row['carry'],0,0)
    expected=ram[:];expected[14]=((u+v)&255)>>1
    assert cpu.ram==expected and cpu.q==u>>1
    assert result['f']==(u+v)&255 and result['carry']==int(u+v>=256)
    return expected[14]


def inspect(trace,scenario,code,u,v):
    want=prediction(code,u,v);finding=classify(trace,scenario)
    assert finding['outcome']=='terminal' and finding['first_terminal']==want['first_terminal']
    ram=scenario['initial']['ram'][:];q=scenario['initial']['q'];events={}
    for t in trace:
        pc=t['pc']
        if pc in (0x148,0x150,0x151,0x157,0x158,0x160,0x16b,0x16c,0x171,0x175,0x084) and pc not in events:
            events[pc]=dict(cycle=t['cycle'],ram=ram[:],q=q)
        for k,value in t['registers'].items():ram[int(k)]=value
        q=t['q']
    assert events[0x148]['cycle']==41
    assert events[0x150]['q']==(2*code)&255 and events[0x157]['q']==254
    for pc in (0x151,0x158):assert events[pc]['q']==0 and events[pc]['ram'][0]==1
    assert events[0x160]['ram'][12]==1
    assert events[0x16b]['ram'][14]==want['half'] and events[0x16b]['q']==u>>1
    assert events[0x16c]['q']==events[0x171]['q']==0
    assert events[0x175]['ram'][15]==(code+3)&255
    assert ram==want['ram'] and q==0
    left=[t for t in trace if t['pc']==0x187]
    assert sum(t['cycle']<events[0x151]['cycle'] for t in left)==want['first_left_iterations']
    assert sum(t['cycle']>events[0x157]['cycle'] for t in left)==9
    right=[t for t in trace if t['pc']==0x1e9]
    assert sum(t['cycle']<events[0x16c]['cycle'] for t in right)==want['right_drain_iterations']
    assert len(right)==want['right_drain_iterations']+1
    assert sum(t['pc']==0x29d for t in trace)==4
    return dict(prediction=want,events={f'{pc:03x}':e for pc,e in events.items()},repeat=finding['repeat'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/handler1-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'handler1-study.json');mapping=read(HERE/config['mapping']);rows=decode(mapping)
    local_digest=hashlib.sha256();counts=Counter();terminal=Counter();runs=[];witnesses=[]
    for u in range(256):
        for v in range(256):
            half=check_sum(rows,u,v);local_digest.update(bytes((u,v,half)))
            counts['local_sum_cases']+=1;counts['sum_wraps']+=int(u+v>=256)
    with tempfile.TemporaryDirectory() as temporary:
        out=Path(temporary)/'run'
        for code in range(1,256,8):
            payloads=range(256) if code==1 else config['boundary_payloads']
            for u in payloads:
                for v in config['sum_replies']:
                    scenario=scenario_for(config,code,u,v)
                    result=execute(mapping,scenario,config['cycles'],mode='integrated',out=out,trace_limit=config['cycles'])
                    assert result['clean'] and result['unused_word_executions']==0 and result['stack']['final_depth']==0
                    finding=inspect(load_trace(out),scenario,code,u,v)
                    assert result['final_state']['ram']==finding['prediction']['ram']
                    counts['clean_terminal_runs']+=1;terminal[finding['prediction']['first_terminal']]+=1
                    runs.append(dict(code=code,u=u,v=v,first_terminal=finding['prediction']['first_terminal'],
                                     trace_digest=result['trace_digest']))
                    if [code,u,v] in config['witnesses']:
                        name=f'code-{code:02x}-u-{u:02x}-v-{v:02x}'
                        shutil.copytree(out,args.out/name,dirs_exist_ok=True)
                        witnesses.append(dict(path=name,code=code,u=u,v=v,**finding))
            print(f'code {code:02x}',dict(counts),flush=True)
    hc=read(HERE/config['handler_config'])
    sources=[Path(__file__),HERE/'handler1-study.json',HERE/config['handler_config'],HERE/config['mapping'],
        HERE/hc['scenario'],HERE/hc['tables'],HERE/'handler_timing_study.py',HERE/'selector_prefix_study.py',
        HERE/'execute.py',HERE/'common.py',HERE/'defined_condition_fit.py',HERE.parent/'model.py']
    save(args.out/'report.json',dict(configuration=config,counts=dict(counts),terminal_cycles=dict(terminal),
        local_sum_sha256=local_digest.hexdigest(),runs=runs,witnesses=witnesses,
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='q3 handler 1 retains ((D167+D16A)&FF)>>1 in R14 and clears Q. First left-drain length depends on code; later right-drain length depends on D167. Complete register/timing formula checked on reset cases; all byte sums checked locally. Previous flags, PC-keyed diagnostic reads, zero-fill shifts and fixed later dispatch remain hypotheses.'))


if __name__=='__main__':main()
