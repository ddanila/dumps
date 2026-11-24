"""Compare every fitted ROM gate on eight unchanged input-selected handlers."""
import argparse
import hashlib
import shutil
import tempfile
from collections import Counter
from pathlib import Path
from common import HERE, read, save, load
from execute import execute
from defined_condition_fit import load_trace
from handler_timing_study import scenario_for_case, classify
from rom_gate_study import search


def scenario_for_gate(config,q,pcs=None,delay=None):
    scenario=scenario_for_case(config,'q3','previous','plp',q)
    if pcs is not None:
        scenario['io']['read'].update(expected_sha256=config['rom_sha256'],
            address=dict(source='previous_y',bank=256,initial_y=0,pcs=pcs,
                         status='hypothesis',evidence=config['evidence']))
    if delay is not None:
        scenario['io']['read']['pc_sequences'][str(0x36d)]=[1]*delay+[0]
    return scenario


def outcome(trace,summary,scenario):
    finding=dict(outcome='model_error',repeat=None,first_terminal=None,dispatch=None)
    if summary['clean'] and not summary['unused_word_executions']:
        try:finding=classify(trace,scenario)
        except AssertionError:
            finding=dict(outcome='bounded',repeat=None,first_terminal=None,dispatch=None)
    state=dict(summary['final_state'])
    if trace:state['previous_y']=trace[-1]['alu']['y']
    return dict(**finding,clean=summary['clean'],stop=summary['stop'],
                unused=summary['unused_word_executions'],trace_digest=summary['trace_digest'],
                final_state=state,max_depth=summary['stack']['max_depth'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/rom-gate-handlers')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'rom-gate-handlers.json');search_config=read(HERE/config['gate_search'])
    _,fits=search(search_config,load());mapping=read(HERE/config['profiles']['q3'])
    baselines={};runs=[];witnesses=[];counts=Counter();delays=[]
    with tempfile.TemporaryDirectory() as temporary:
        out=Path(temporary)/'run'
        for gate,pcs in [(None,None)]+[(i,f['pcs']) for i,f in enumerate(fits)]:
            for q in config['input_sums']:
                scenario=scenario_for_gate(config,q,pcs)
                scenario['name']=f'handler gate={gate} input sum={q}'
                summary=execute(mapping,scenario,config['cycles'],mode='integrated',out=out,trace_limit=config['cycles'])
                trace=load_trace(out);finding=outcome(trace,summary,scenario)
                case=dict(gate=gate,input_sum=q,**finding)
                if gate is None:baselines[str(q)]=case
                else:
                    counts[finding['outcome']]+=1
                    case['same_outcome_as_baseline']=finding['outcome']==baselines[str(q)]['outcome']
                    case['same_final_state_as_baseline']=finding['final_state']==baselines[str(q)]['final_state']
                    runs.append(case)
                if q in (0,2,5) and gate in (None,0,50):
                    name=f'gate-{gate}-q{q}'
                    shutil.copytree(out,args.out/name,dirs_exist_ok=True)
                    witnesses.append(dict(path=name,**case))
            if gate is not None and gate%32==0:print('gate',gate,'checked',flush=True)
        for delay in (0,1,7):
            scenario=scenario_for_gate(config,5,fits[0]['pcs'],delay)
            scenario['name']=f'two-bit gate delayed reply {delay}'
            summary=execute(mapping,scenario,config['cycles'],mode='integrated',out=out,trace_limit=config['cycles'])
            trace=load_trace(out);finding=outcome(trace,summary,scenario)
            assert finding['clean'] and finding['outcome']=='terminal'
            assert finding['first_terminal']==110+3*delay
            original=load_trace(args.out/'gate-0-q5')
            first=next(i for i,r in enumerate(trace) if r['pc']==0x36d)
            assert trace[:first]==original[:first]
            name=f'gate-0-reply-{delay}'
            shutil.copytree(out,args.out/name,dirs_exist_ok=True)
            delays.append(dict(path=name,delay=delay,**finding))
    vectors=Counter(tuple(r['outcome'] for r in runs if r['gate']==gate) for gate in range(len(fits)))
    sources=[Path(__file__),HERE/'rom-gate-handlers.json',HERE/config['gate_search'],HERE/'rom_gate_study.py',HERE/'output_control_study.py',HERE/'handler_timing_study.py',HERE/'selector_prefix_study.py',HERE/'execute.py',HERE/'common.py',HERE/'defined_condition_fit.py',HERE.parent/'model.py',HERE/config['scenario'],HERE/config['tables'],HERE/config['profiles']['q3']]
    save(args.out/'report.json',dict(configuration=config,baselines=baselines,runs=runs,witnesses=witnesses,
        delayed_replies=delays,counts=dict(counts),outcome_vectors=[dict(outcomes=list(k),gates=v) for k,v in vectors.items()],
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}))
    print(dict(counts=counts,outcome_vectors=len(vectors)))


if __name__=='__main__':main()
