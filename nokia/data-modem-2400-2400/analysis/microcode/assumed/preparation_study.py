"""Test the 341 preparation context against existing source/arithmetic hypotheses."""
import argparse
import copy
import math
from pathlib import Path
from common import HERE, decode, load, read, save
from independent_study import search_sources, arithmetic, loop_probe
from rotation_study import make_mapping, scenario_for
from execute import CarryInput
from model import Am2901


def preparation(rows, policy, fixture):
    cpu=Am2901(ram=fixture['ram'][:],q=fixture['q']);carry=CarryInput(policy);trace=[]
    for offset,d in enumerate(fixture['external_d']):
        row=rows[fixture['entry']+offset];before=cpu.ram[:]
        cin=carry.resolve(row);result=cpu.step(row['i'],row['a'],row['b'],d,cin)
        carry.observe(result)
        trace.append(dict(pc=row['pc'],raw=row['raw'],source=row['i']&7,a=row['a'],b=row['b'],
            d=d,carry=cin,y=result['y'],write_register=row['b'] if row['i']>>6>=2 else None,
            changes={str(i):v for i,v in enumerate(cpu.ram) if v!=before[i]}))
    return dict(trace=trace,final_ram=cpu.ram,final_q=cpu.q,
        written_registers=sorted({r['write_register'] for r in trace if r['write_register'] is not None}))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/preparation-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'preparation-search.json');independent=read(HERE/'independent-search.json')
    base=read(HERE/'rotation-search.json');lanes=load()
    sources=search_sources(lanes,independent,config);reports=[];retained=0
    for index,source in enumerate(sources,1):
        for swap in config['swap_register_roles']:
            registers=copy.deepcopy(base)
            if swap:registers['a_bits'],registers['b_bits']=registers['b_bits'],registers['a_bits']
            mapping=make_mapping(dict(i=source+independent['function_bits']+base['destination_bits']),index,registers)
            mapping['name']=f'preparation-source-{index:02d}'+('-swap' if swap else '')
            for field in mapping['fields'].values():
                if field['status']=='hypothesis':field['evidence']='Expanded source and register-role comparison; preparation-search.json. Not identified wiring.'
            result=arithmetic(mapping,independent,base)
            loop=loop_probe(mapping,independent)
            passes=not result['failures'] and loop['all_shift_counts_match'] and loop['all_returned']
            if passes:
                retained+=1;save(args.out/(mapping['name']+'.json'),mapping)
            probe=preparation(decode(mapping),scenario_for(mapping,base)['inputs']['carry'],config['fixture'])
            reports.append(dict(name=mapping['name'],source=source,swap_registers=swap,
                arithmetic_checks=result['rotation_checks']+result['output_checks'],
                failures=len(result['failures']),first_failure=next(iter(result['failures']),None),
                loop_passed=loop['all_shift_counts_match'] and loop['all_returned'],
                passes_existing_constraints=passes,preparation=probe))
    save(args.out/'summary.json',dict(configuration=config,
        source_assignments=math.prod(range(len(config['source_bits'])-2,len(config['source_bits'])+1))*8,
        source_constraint_survivors=len(sources),retained=retained,candidates=reports,
        interpretation='Expanded alternatives consistent with selected fixtures, not recovered hardware. Register swap is judged against the existing forward-transform identities, not every possible algorithm.'))
    print('Sources:',len(sources),'profiles:',len(reports),'pass existing fixtures:',retained)
    print('Swapped passing:',sum(r['passes_existing_constraints'] and r['swap_registers'] for r in reports))

if __name__=='__main__':main()
