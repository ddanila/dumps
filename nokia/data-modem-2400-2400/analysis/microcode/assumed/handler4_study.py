"""Explain q3 handler 4's carry-qualified input selection and retained state."""
import argparse
import hashlib
import json
import shutil
import tempfile
from collections import Counter
from pathlib import Path
from common import HERE,read,save,decode,unconditional_transfer
from execute import execute,CarryInput
from defined_condition_fit import load_trace
from handler_timing_study import scenario_for_case,classify
from model import Am2901,X8X02


def scenario_for(config,a,b,captured):
    scenario=scenario_for_case(read(HERE/config['handler_config']),'q3','previous','plp',4)
    scenario.update(name='q3 handler 4 carry-qualified input selection',evidence=config['evidence'])
    scenario['io']['read']['evidence']=config['evidence']
    scenario['io']['read']['pc_sequences'].update({str(0x107):[(captured+1)&255],str(0x2a0):[a],str(0x2a2):[b]})
    return scenario


def prediction(snapshot,a,b):
    ram=snapshot['ram'][:]
    overflow=a+b>=256
    candidate=(a+1)&255
    if overflow:
        q=a;path='sum-carry';cycles=11
    elif candidate<=1:
        q=candidate;path='comparison';cycles=20
    else:
        q=1+int(ram[7]==255);path='reload';cycles=21+int(ram[7]==255)
    ram[15]=(a+b)&255
    if not overflow:ram[14]=1
    ram[4]=(q+1)&255;ram[2]=0
    final=ram[:];final[0]=final[2]=q>>1;final[5]=((-q)&255)>>1
    return dict(path=path,ram=ram,q=q,cycles=cycles,final_ram=final,
                first_terminal=snapshot['cycle']+cycles+32-int(q==0))


def capture(mapping,scenario,out):
    result=execute(mapping,scenario,71,mode='integrated',out=out,trace_limit=71)
    trace=load_trace(out)
    assert result['clean'] and result['final_state']['pc']==0x2a0 and result['stack']['final_depth']==0
    assert not any(t['pc'] in (0x2a0,0x2a2) for t in trace)
    state=result['final_state']
    assert state['ram'][0]==255 and state['ram'][1]==state['ram'][14]==0
    return dict(pc=state['pc'],ram=state['ram'],q=state['q'],sp=state['sp'],stack=state['stack'],
                previous=trace[-1]['alu'],cycle=71,prefix_trace_digest=result['trace_digest'])


def probe(rows,scenario,snapshot,a,b):
    cpu=Am2901(ram=snapshot['ram'][:],q=snapshot['q'],logic_flags=True)
    seq=X8X02(pc=snapshot['pc'],sp=snapshot['sp'],stack=snapshot['stack'][:])
    carry=CarryInput(scenario['inputs']['carry']);carry.previous=snapshot['previous']['carry']
    previous=snapshot['previous'];trace=[]
    for cycle in range(24):
        pc=seq.pc
        if pc==0x26f:return dict(ram=cpu.ram,q=cpu.q,cycles=cycle,trace=trace)
        row=rows[pc];d=a if pc==0x2a0 else b if pc==0x2a2 else 1
        assert row['command'] in (0,1,6) and not row['unused']
        before=cpu.ram[:];carry_in=carry.resolve(row)
        result=cpu.step(row['i'],row['a'],row['b'],d,carry_in,0,0);carry.observe(result)
        condition=scenario['condition'];select=row['select'];source=condition['sources'][select]
        test=1 if unconditional_transfer(row,scenario) else int(bool(condition['value'] if source=='constant' else previous[source]))^condition['polarity'][select]
        seq.step(row['command'],row['branch'],test)
        trace.append(dict(cycle=snapshot['cycle']+cycle,pc=pc,next_pc=seq.pc,q=cpu.q,alu=result,
                          test=test,carry_in=carry_in,registers={str(i):v for i,v in enumerate(cpu.ram) if v!=before[i]}))
        previous=result
    raise AssertionError('input-selection continuation did not reach 26F')


def verify_full(mapping,scenario,snapshot,got,want,out,prefix):
    result=execute(mapping,scenario,160,mode='integrated',out=out,trace_limit=160)
    assert result['clean'] and result['unused_word_executions']==0 and result['stack']['final_depth']==0
    trace=load_trace(out);assert trace[:71]==prefix
    for actual,local in zip(trace[71:],got['trace']):
        for key,value in local.items():assert actual[key]==value,(key,actual,local)
    assert trace[71+got['cycles']]['pc']==0x26f
    assert result['final_state']['ram']==want['final_ram'] and result['final_state']['q']==want['q']
    finding=classify(trace,scenario)
    assert finding['outcome']=='terminal' and finding['first_terminal']==want['first_terminal']
    return result['trace_digest']


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/handler4-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'handler4-study.json');mapping=read(HERE/config['mapping']);rows=decode(mapping)
    counts=Counter();paths=Counter();digest=hashlib.sha256();snapshots={};witnesses=[];runs=[]
    with tempfile.TemporaryDirectory() as temporary:
        for captured in (0,255):
            scenario=scenario_for(config,0,0,captured)
            prefix_path=args.out/f'prefix-{captured:02x}'
            snapshot=capture(mapping,scenario,prefix_path);snapshots[str(captured)]=snapshot;prefix=load_trace(prefix_path)
            for a in range(256):
                for b in range(256):
                    got=probe(rows,scenario,snapshot,a,b);want=prediction(snapshot,a,b)
                    assert got['ram']==want['ram'] and got['q']==want['q'] and got['cycles']==want['cycles']
                    branch=next(t for t in got['trace'] if t['pc']==0x2a3)
                    assert branch['test']==int(a+b>=256)
                    if want['path']=='reload':
                        skip=next(t for t in got['trace'] if t['pc']==0x2a8)
                        assert skip['test']==int(captured!=255)
                    counts['local_continuations']+=1;paths[f'{captured:02x}:{want["path"]}']+=1
                    digest.update(json.dumps([captured,a,b,got],sort_keys=True,separators=(',',':')).encode())
                    if b in config['full_sum_bytes']:
                        case_scenario=scenario_for(config,a,b,captured);out=Path(temporary)/'run'
                        trace_digest=verify_full(mapping,case_scenario,snapshot,got,want,out,prefix)
                        counts['clean_reset_runs']+=1
                        runs.append(dict(a=a,b=b,captured=captured,path=want['path'],q=want['q'],
                                         first_terminal=want['first_terminal'],trace_digest=trace_digest))
                        if [a,b,captured] in config['witnesses']:
                            name=f'a-{a:02x}-b-{b:02x}-r7-{captured:02x}'
                            shutil.copytree(out,args.out/name,dirs_exist_ok=True)
                            witnesses.append(dict(path=name,a=a,b=b,captured=captured,prediction=want,trace_digest=trace_digest))
                if a%64==63:print(f'R7={captured:02x}, {a+1} first bytes',dict(counts),flush=True)
    hc=read(HERE/config['handler_config'])
    sources=[Path(__file__),HERE/'handler4-study.json',HERE/config['handler_config'],HERE/config['mapping'],
        HERE/hc['scenario'],HERE/hc['tables'],HERE/'handler_timing_study.py',HERE/'selector_prefix_study.py',
        HERE/'execute.py',HERE/'common.py',HERE/'defined_condition_fit.py',HERE.parent/'model.py']
    save(args.out/'report.json',dict(configuration=config,counts=dict(counts),paths=dict(paths),snapshots=snapshots,
        continuation_sha256=digest.hexdigest(),runs=runs,witnesses=witnesses,
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='q3 handler-4 continuation preserves A on sum carry; otherwise compares A+1 modulo 256 and may reload Q. XOR carry distinguishes captured R7=00/FF at the later skip. Actual zero-reset checkpoints, exhaustive local byte pairs and selected full core continuations agree. Physical inputs, fixed dispatch and broader modem purpose remain hypotheses.'))


if __name__=='__main__':main()
