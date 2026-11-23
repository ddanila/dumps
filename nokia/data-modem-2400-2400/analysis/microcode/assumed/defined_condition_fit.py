"""Refit prescribed local paths with defined logical flags and test reset extension."""
import argparse
import copy
import json
from pathlib import Path
from common import HERE, decode, read, save, unconditional_transfer
from condition_fit import fit
from execute import CarryInput, execute
from model import Am2901


def recompute(mapping, scenario, prescribed):
    rows=decode(mapping);initial=scenario['initial']
    cpu=Am2901(ram=initial['ram'][:],q=initial['q'],logic_flags=True)
    carry=CarryInput(scenario['inputs']['carry'])
    previous={k:None for k in ('zero','sign','carry','overflow')}
    observations=[];trace=[]
    for cycle,old in enumerate(prescribed):
        row=rows[old['pc']];cin=carry.resolve(row)
        flags=cpu.step(row['i'],row['a'],row['b'],old['d'],cin);carry.observe(flags)
        if row['command'] in (0,2,4,6) and not unconditional_transfer(row,scenario):
            observations.append(dict(cycle=cycle,pc=old['pc'],select=row['select'],test=old['test'],
                                     current=flags,previous=previous))
        trace.append(dict(pc=old['pc'],next_pc=old['next_pc'],ram=cpu.ram[:],q=cpu.q,
                          alu=flags,carry_in=cin,d=old['d']))
        previous=flags
    return observations,trace


def apply_policy(base,spec,config):
    scenario=copy.deepcopy(base)
    scenario['evidence']=config['evidence']
    scenario['inputs']['logic_flags']=read(HERE/'logic-flags.json')['logic_flags']
    scenario['condition']['flag_timing']=spec['timing']
    for select,(source,polarity) in spec['policy'].items():
        scenario['condition']['sources'][int(select)]=source
        scenario['condition']['polarity'][int(select)]=polarity
    return scenario


def load_trace(path):
    return [json.loads(line) for line in (path/'trace.jsonl').read_text().splitlines()]


def decision_audit(trace,rows,scenario):
    previous={k:None for k in ('zero','sign','carry','overflow')};unknown=[]
    for r in trace:
        row=rows[r['pc']]
        if row['command'] in (0,2,4,6) and not unconditional_transfer(row,scenario):
            source=scenario['condition']['sources'][row['select']]
            flags=r['alu'] if scenario['condition']['flag_timing']=='current' else previous
            if source in previous and flags[source] is None:unknown.append(dict(cycle=r['cycle'],pc=r['pc'],source=source))
        previous=r['alu']
    return unknown


def first_drain(trace):
    start=next((i for i,r in enumerate(trace) if r['pc']==0x1e9),None)
    if start is None:return None
    end=next((i for i in range(start,len(trace)) if trace[i]['pc']==0x1eb),None)
    values=[r['q'] for r in trace[start:end] if r['pc']==0x1e9]
    return dict(start_cycle=start,exit_cycle=end,iterations=len(values),shifted_q=values)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/defined-condition-fit')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'defined-condition-fit.json');analyses={};references={}
    for roles in ('original','swapped'):
        root=HERE/'results/condition-fit'/f'{roles}-zero'
        mapping=read(root/'mapping.json');base=read(root/'scenario.json')
        witness=read(HERE/f'results/first-use-study/witness-{roles}.json');all_obs=[]
        for input_name in ('zero','marked'):
            obs,trace=recompute(mapping,base,witness[input_name]['trace'])
            references[roles,input_name]=trace
            all_obs.extend(dict(input=input_name,**o) for o in obs)
        selectors=[]
        for select in sorted({o['select'] for o in all_obs}):
            selected=[o for o in all_obs if o['select']==select]
            selectors.append(dict(select=select,observations=selected,
                constants=[v for v in (0,1) if all(o['test']==v for o in selected)],
                timings={t:fit(selected,t,config['sources']) for t in config['timings']}))
        analyses[roles]=selectors
    local_runs=[];reset_runs=[];comparisons=[]
    for name,spec in config['variants'].items():
        roles=spec['roles']
        for group in analyses[roles]:
            source,polarity=spec['policy'][str(group['select'])]
            for observation in group['observations']:
                value=0 if source=='constant' else observation[spec['timing']][source]
                if value is None or (value^polarity)!=observation['test']:
                    raise ValueError('configured policy does not fit local observations')
        for input_name in ('zero','marked'):
            root=HERE/'results/condition-fit'/f'{roles}-{input_name}'
            mapping=read(root/'mapping.json');base=read(root/'scenario.json')
            scenario=apply_policy(base,spec,config);reference=references[roles,input_name]
            out=args.out/f'local-{name}-{input_name}'
            result=execute(mapping,scenario,len(reference),mode='integrated',out=out,trace_limit=len(reference))
            trace=load_trace(out);ram=scenario['initial']['ram'][:]
            if len(trace)!=len(reference) or not result['clean']:raise ValueError('local replay incomplete')
            for old,new in zip(reference,trace):
                for register,value in new['registers'].items():ram[int(register)]=value
                if any(old[k]!=new[k] for k in ('pc','next_pc','q','alu','carry_in')) or old['ram']!=ram or old['d']!=new['external_read']['value']:
                    raise ValueError('fitted local execution differs from recomputed prescribed path')
            local_runs.append(dict(variant=name,input=input_name,cycles=result['completed_cycles'],clean=result['clean'],
                                   final_state=result['final_state'],trace_digest=result['trace_digest']))
            reset_root=HERE/'results/selector-completion'/f'{roles}-{input_name}'
            reset=apply_policy(read(reset_root/'scenario.json'),spec,config)
            out=args.out/f'reset-{name}-{input_name}'
            result=execute(mapping,reset,config['reset_cycles'],mode='integrated',out=out,trace_limit=config['reset_cycles'])
            trace=load_trace(out)
            reset_runs.append(dict(variant=name,input=input_name,clean=result['clean'],stop=result['stop'],
                cycles=result['completed_cycles'],words=len(result['visited']),visited=result['visited'],
                final_state=result['final_state'],stack=result['stack'],trace_digest=result['trace_digest'],
                unknown_carry_feedback=result['carry_model']['counts'].get('unknown_feedback',0),
                reaches_preparation=0x341 in result['visited'],
                first_drain=first_drain(trace),unknown_flag_decisions=decision_audit(trace,decode(mapping),reset)))
        zero=load_trace(args.out/f'reset-{name}-zero');marked=load_trace(args.out/f'reset-{name}-marked')
        first=next((dict(cycle=i,zero=a,marked=b) for i,(a,b) in enumerate(zip(zero,marked))
                    if (a['pc'],a['next_pc'])!=(b['pc'],b['next_pc'])),None)
        comparisons.append(dict(variant=name,first_input_control_difference=first))
    save(args.out/'report.json',dict(configuration=config,selector_fits=analyses,local_runs=local_runs,reset_runs=reset_runs,input_comparisons=comparisons,
        interpretation='Fits to prescribed paths with recomputed datapath state. Successful replay is consistency evidence, not recovered condition wiring.'))
    for r in reset_runs:print(r['variant'],r['input'],r['clean'],r['words'],f"{r['final_state']['pc']:03X}",r['reaches_preparation'])


if __name__=='__main__':main()
