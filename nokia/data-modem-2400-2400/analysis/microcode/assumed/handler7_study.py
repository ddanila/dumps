"""Explain q3 handler 7's overflow-selected transforms from real reset."""
import argparse
import hashlib
import json
import shutil
import tempfile
from collections import Counter
from pathlib import Path
from common import HERE,read,save,decode
from execute import execute,CarryInput
from model import Am2901,X8X02
from defined_condition_fit import load_trace
from handler_timing_study import scenario_for_case


def prediction(code,a,b,x):
    total=code+b+int(a>code);q=total&255
    route='direct' if total<256 else 'final-transform' if code<x else 'all-transforms'
    ram=[0]*16;ram[0]=code;ram[3]=(a-code-1)&255
    if route=='direct':ram[4]=(code+1)&255;ram[5]=code;ram[7]=x
    else:
        ram[1]=code
        if route=='all-transforms':ram[2]=ram[3]=code
    return dict(route=route,ram=ram,q=q,first_terminal={'direct':62,'final-transform':73,'all-transforms':93}[route],
        calls={'direct':[],'final-transform':[0x3c0],'all-transforms':[0x3ea,0x3d5,0x3c0]}[route])


def scenario_for(config,code,a,b,x):
    h=read(HERE/config['handler_configuration']);s=scenario_for_case(h,'q3','previous','plp',code)
    s.update(name=f'q3 handler7 c={code:02x} A={a:02x} B={b:02x} x={x:02x}',evidence=config['evidence'])
    s['io']['read']['pc_sequences'].update({str(0x137):[a],str(0x138):[b],str(0x107):[(x+1)&255]})
    return s


def check_gate(rows,carry_policy,code,a,b,x):
    cpu=Am2901(logic_flags=True);cpu.ram[0]=code;cpu.ram[7]=x;cpu.ram[3]=123;cpu.q=code
    seq=X8X02(pc=0x137);carry=CarryInput(carry_policy);previous=None;steps=[]
    while seq.pc in (0x137,0x138,0x139,0x13a):
        pc=seq.pc;row=rows[pc];d=a if pc==0x137 else b if pc==0x138 else 1
        value=cpu.step(row['i'],row['a'],row['b'],d,carry.resolve(row),0,0);carry.observe(value)
        test=int(not previous['carry']) if row['command']==6 else 0
        seq.step(row['command'],row['branch'],test);steps.append(dict(pc=pc,next_pc=seq.pc,alu=value));previous=value
    want=prediction(code,a,b,x)
    assert seq.pc=={'direct':0x13e,'final-transform':0x13d,'all-transforms':0x13b}[want['route']]
    assert cpu.q==want['q'] and cpu.ram[3]==(a-code-1)&255
    return steps,want


def inspect(trace,summary,code,a,b,x):
    want=prediction(code,a,b,x)
    assert summary['clean'] and not summary['unused_word_executions']
    assert summary['final_state']['ram']==want['ram'] and summary['final_state']['q']==want['q']
    assert next(row['cycle'] for row in trace if row['pc']==0x084)==want['first_terminal']
    assert [r['pc'] for r in trace if r['pc'] in (0x3c0,0x3d5,0x3ea)]==want['calls']
    assert summary['stack']['final_depth']==0 and summary['stack']['max_depth']==(3 if want['calls'] else 2)
    before=[r for r in trace if r['pc']==0x138];assert len(before)==1 and before[0]['q']==want['q']
    for row in trace:
        if row['pc'] in (0x3ed,0x3d8,0x3c3):assert row['test']==0
        if row['pc'] in (0x3ec,0x3d7,0x3c2):assert row['dispatch_entry']==2
    return want


def fixtures():
    for code in range(7,256,8):
        for x in sorted({0,code,min(code+1,255),255}):
            for a in sorted({0,code,min(code+1,255),255}):
                for b in sorted({0,1,255-code,256-code,255}):yield code,a,b,x


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/handler7-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'handler7-study.json');h=read(HERE/config['handler_configuration'])
    mapping=read(HERE/h['profiles']['q3']);rows=decode(mapping);s=scenario_for(config,7,0,0,0)
    local=Counter();digest=hashlib.sha256();runs=[];witnesses=[];seen=set()
    for code in (7,255):
        for x in (0,255):
            for a in range(256):
                for b in range(256):
                    steps,want=check_gate(rows,s['inputs']['carry'],code,a,b,x)
                    local[f'{code:02x}-{x:02x}-{want["route"]}']+=1
                    digest.update(json.dumps([code,a,b,x,steps],sort_keys=True,separators=(',',':')).encode())
        print(f'{code:02x}: 131072 four-instruction gate cases',flush=True)
    with tempfile.TemporaryDirectory() as tmp:
        for code,a,b,x in fixtures():
            scenario=scenario_for(config,code,a,b,x)
            summary=execute(mapping,scenario,config['cycles'],mode='integrated',out=Path(tmp),trace_limit=config['cycles'])
            trace=load_trace(Path(tmp));want=inspect(trace,summary,code,a,b,x)
            steps,_=check_gate(rows,scenario['inputs']['carry'],code,a,b,x)
            for expected in steps:
                actual=next(r for r in trace if r['pc']==expected['pc'])
                assert actual['next_pc']==expected['next_pc'] and actual['alu']==expected['alu']
            case=dict(code=code,a=a,b=b,x=x,prediction=want,trace_digest=summary['trace_digest']);runs.append(case)
            key=(code in (7,255),code==255,want['route'])
            if code in (7,255) and key not in seen:
                seen.add(key);name=f'{code:02x}-{want["route"]}'
                shutil.copytree(tmp,args.out/name,dirs_exist_ok=True);witnesses.append(dict(path=name,**case))
    sources=[Path(__file__),HERE/'handler7-study.json',HERE/'execute.py',HERE/'external_line.py',HERE/'common.py',
        HERE/'defined_condition_fit.py',HERE/'handler_timing_study.py',HERE/'selector_prefix_study.py',HERE.parent/'model.py',
        HERE/config['handler_configuration'],HERE/h['profiles']['q3'],HERE/h['scenario'],HERE/h['tables']]
    save(args.out/'report.json',dict(configuration=config,local_gate_counts=dict(local),gate_sha256=digest.hexdigest(),
        reset_cases=len(runs),runs=runs,witnesses=witnesses,
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='Actual q3 handler-7 reset paths select zero, one or three transform calls. Under fixed entry 2 and zero source registers all called transforms return after one pass, preserving Q and selectively overwriting R1/R2/R3. No physical filter purpose inferred.'))
    print(len(runs),'full reset cases;',len(witnesses),'witnesses')


if __name__=='__main__':main()
