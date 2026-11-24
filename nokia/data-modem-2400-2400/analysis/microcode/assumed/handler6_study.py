"""Explain q3 handler 6 as masked capture, conditional increment and two drains."""
import argparse
import hashlib
import shutil
import tempfile
from collections import Counter
from pathlib import Path
from common import HERE, read, save
from execute import execute
from defined_condition_fit import load_trace
from handler_timing_study import scenario_for_case, classify


def scenario_for(config, code, captured):
    assert code in range(6,256,8) and captured in range(256)
    scenario = scenario_for_case(read(HERE/config['handler_config']), 'q3', 'previous', 'plp', code)
    scenario.update(name='q3 handler 6 masked captured byte', evidence=config['evidence'])
    scenario['io']['read']['evidence'] = config['evidence']
    scenario['io']['read']['pc_sequences'][str(0x107)] = [(captured+1)&255]
    return scenario


def prediction(code, captured):
    masked = captured & (code+1)
    incremented = (masked+int(masked != 0))&255
    half = incremented >> 1
    iterations = (((code+2)&255)>>1).bit_length()+1
    ram = [0]*16
    ram[4],ram[7],ram[12],ram[13],ram[15] = 2,captured,half,incremented,half
    return dict(masked=masked,incremented=incremented,half=half,ram=ram,q=0,
                first_drain_iterations=iterations,second_drain_iterations=1,
                first_terminal=115+2*iterations+int(code==254))


def inspect(trace, scenario, code, captured):
    expected = prediction(code,captured)
    finding = classify(trace,scenario)
    assert finding['outcome']=='terminal' and finding['first_terminal']==expected['first_terminal']
    ram = scenario['initial']['ram'][:]
    events = {}
    for t in trace:
        pc = t['pc']
        for k,v in t['registers'].items():ram[int(k)]=v
        if pc in (0x09e,0x0a3,0x0a4,0x0ad,0x0ae,0x0b0,0x0b2,0x0b7,0x0c5,0x0c9,0x0de,0x084) and pc not in events:
            events[pc]=dict(cycle=t['cycle'],ram=ram[:],q=t['q'],alu=t['alu'],next_pc=t['next_pc'])
    assert events[0x09e]['ram'][7]==captured
    assert events[0x0ad]['ram'][13]==expected['masked']
    assert events[0x0ad]['alu']['carry']==int(expected['masked']!=0)
    assert events[0x0ae]['ram'][13]==expected['incremented']
    assert events[0x0b0]['ram'][15]==expected['half']
    assert events[0x0b2]['q']==events[0x0b7]['q']==0
    assert events[0x0c5]['ram'][2]==expected['half']+1
    assert events[0x0c9]['ram'][12]==expected['half']
    assert events[0x0a3]['alu']['carry']==int(code==254)
    assert events[0x0a4]['next_pc']==(0x0a5 if code==254 else 0x0a6)
    assert events[0x0de]['next_pc']==0x079
    assert ram==expected['ram'] and trace[-1]['q']==0
    visits=[t for t in trace if t['pc']==0x1e9]
    first=sum(t['cycle']<events[0x0b2]['cycle'] for t in visits)
    assert first==expected['first_drain_iterations'] and len(visits)-first==1
    return dict(prediction=expected,events={f'{pc:03x}':v for pc,v in events.items()},
                repeat=finding['repeat'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/handler6-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'handler6-study.json');mapping=read(HERE/config['mapping'])
    counts=Counter();terminal=Counter();values=set();runs=[];witnesses=[]
    with tempfile.TemporaryDirectory() as temporary:
        out=Path(temporary)/'run'
        for code in range(6,256,8):
            for captured in range(256):
                scenario=scenario_for(config,code,captured)
                result=execute(mapping,scenario,config['cycles'],mode='integrated',out=out,trace_limit=config['cycles'])
                assert result['clean'] and result['unused_word_executions']==0
                finding=inspect(load_trace(out),scenario,code,captured)
                want=finding['prediction']
                assert result['final_state']['ram']==want['ram'] and result['final_state']['q']==0
                assert result['stack']['final_depth']==0
                counts['clean_terminal_runs']+=1
                counts['nonzero_surviving_half']+=int(want['half']!=0)
                counts['ff_mask_wrapped_to_zero']+=int(want['masked']==255)
                terminal[want['first_terminal']]+=1;values.add(want['half'])
                runs.append(dict(code=code,captured=captured,half=want['half'],
                    first_terminal=want['first_terminal'],trace_digest=result['trace_digest']))
                if [code,captured] in config['witnesses']:
                    name=f'code-{code:02x}-capture-{captured:02x}'
                    shutil.copytree(out,args.out/name,dirs_exist_ok=True)
                    witnesses.append(dict(path=name,code=code,captured=captured,**finding))
            if code%64==62:print(code+2,'input codes',dict(counts),flush=True)
    hc=read(HERE/config['handler_config'])
    sources=[Path(__file__),HERE/'handler6-study.json',HERE/config['handler_config'],HERE/config['mapping'],
        HERE/hc['scenario'],HERE/hc['tables'],HERE/'handler_timing_study.py',HERE/'selector_prefix_study.py',
        HERE/'execute.py',HERE/'common.py',HERE/'defined_condition_fit.py',HERE.parent/'model.py']
    save(args.out/'report.json',dict(configuration=config,counts=dict(counts),terminal_cycles=dict(terminal),
        surviving_half_values=sorted(values),runs=runs,witnesses=witnesses,
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='q3 handler 6 masks captured R7 by code+1, adds one iff mask nonzero, and retains the half in R12/R15. FF wraps to zero. Two Q drains erase Q; input code affects instruction count. Previous flags, explicit PC-keyed replies and fixed later dispatch; physical algorithm and I/O meaning unresolved.'))


if __name__=='__main__':main()
