"""Fit shared condition sources to the saved preparation-use witnesses."""
import argparse
import copy
import json
from pathlib import Path
from common import HERE, decode, read, save, unconditional_transfer
from execute import CarryInput, execute
from model import Am2901
from rotation_study import scenario_for


def fit(observations, timing, sources):
    options=[]
    for source in sources:
        for polarity in (0,1):
            values=[o[timing][source] for o in observations]
            unknown=sum(v is None for v in values)
            mismatches=sum(v is not None and (v^polarity)!=o['test'] for v,o in zip(values,observations))
            options.append(dict(source=source,polarity=polarity,unknown=unknown,mismatches=mismatches,
                fits=not unknown and not mismatches))
    return options


def inspect(mapping, scenario, trace, initial_ram, initial_q):
    rows=decode(mapping);cpu=Am2901(ram=initial_ram[:],q=initial_q)
    carry=CarryInput(scenario['inputs']['carry']);previous={k:None for k in ('zero','sign','carry','overflow')}
    observations=[]
    for cycle,record in enumerate(trace):
        row=rows[record['pc']];cin=carry.resolve(row)
        if cin!=record['carry']:raise ValueError('carry replay mismatch')
        flags=cpu.step(row['i'],row['a'],row['b'],record['d'],cin);carry.observe(flags)
        if cpu.ram!=record['ram'] or cpu.q!=record['q'] or flags['y']!=record['y']:
            raise ValueError('datapath replay mismatch')
        current={k:flags[k] for k in previous}
        if row['command'] in (0,2,4,6) and not unconditional_transfer(row,scenario):
            observations.append(dict(cycle=cycle,pc=record['pc'],select=row['select'],test=record['test'],
                current=current,previous=previous.copy()))
        previous=current
    return observations


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/condition-fit')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'condition-fit.json');first=read(HERE/'first-use-search.json');reports=[]
    for name,spec in first['witnesses'].items():
        mapping=read(HERE/f"results/preparation-study/{spec['mapping']}.json")
        if spec['swap']:mapping['fields']['a'],mapping['fields']['b']=mapping['fields']['b'],mapping['fields']['a']
        scenario=scenario_for(mapping,read(HERE/'rotation-search.json'))
        witness=read(HERE/f'results/first-use-study/witness-{name}.json');observations=[]
        for input_name in ('zero','marked'):
            observations.extend(dict(input=input_name,**o) for o in inspect(mapping,scenario,witness[input_name]['trace'],
                witness['configuration']['initial_ram'],spec['q']))
        selectors=[]
        for select in sorted({o['select'] for o in observations}):
            selected=[o for o in observations if o['select']==select]
            selectors.append(dict(select=select,observations=selected,
                constant_candidates=[v for v in (0,1) if all(o['test']==v for o in selected)],
                timings={t:fit(selected,t,config['sources']) for t in config['timings']}))
        replays=[]
        for input_name in ('zero','marked'):
            replay=copy.deepcopy(scenario)
            replay['initial'].update(pc=witness['configuration']['start'],ram=witness['configuration']['initial_ram'][:],q=spec['q'])
            replay['condition'].update(mode='flags',flag_timing='previous',sources=['constant']*8,polarity=[0]*8,value=0)
            for select,(source,polarity) in config['replay_policies'][name].items():
                replay['condition']['sources'][int(select)]=source
                replay['condition']['polarity'][int(select)]=polarity
            replay['dispatch'].update(mode='constant',value=spec['entry'])
            data=spec['data'] if input_name=='marked' else [0]*len(spec['data'])
            replay['io']['read'].update(mode='pc_table',value=0,
                pc_values={str(witness['configuration']['preparation']+i):value for i,value in enumerate(data)},
                status='stub',evidence='Local PC-keyed preparation bytes; keys are instruction PCs, not physical read addresses.')
            replay['evidence']=config['replay_evidence']
            out=args.out/f'{name}-{input_name}'
            reference=witness[input_name]
            result=execute(mapping,replay,reference['cycles'],0,'integrated',out,reference['cycles'])
            records=[json.loads(line) for line in (out/'trace.jsonl').read_text().splitlines()]
            ram=replay['initial']['ram'][:]
            for old,new in zip(reference['trace'],records):
                for register,value in new['registers'].items():ram[int(register)]=value
                if any(old[key]!=new[key] for key in ('pc','next_pc','q')) or old['ram']!=ram or old['y']!=new['alu']['y']:
                    raise ValueError('fitted-condition replay differs from witness')
                if old['d']!=new['external_read']['value']:raise ValueError('read replay mismatch')
            if len(records)!=len(reference['trace']) or not result['clean'] or result['final_state']['pc']!=spec['stop']:
                raise ValueError('incomplete fitted replay')
            replays.append(dict(input=input_name,cycles=result['completed_cycles'],clean=result['clean'],trace_digest=result['trace_digest'],matches=True))
        reports.append(dict(witness=name,mapping=spec['mapping'],swap=spec['swap'],selectors=selectors,replays=replays))
    save(args.out/'summary.json',dict(configuration=config,witnesses=reports,
        interpretation='Fits to prescribed local paths, not independent condition-wiring recovery. Constants are external-line hypotheses; unknown flags are not treated as evidence.'))
    for r in reports:
        print(r['witness'],[(x['select'],x['constant_candidates'],{t:[(o['source'],o['polarity']) for o in opts if o['fits']] for t,opts in x['timings'].items()}) for x in r['selectors']])

if __name__=='__main__':main()
