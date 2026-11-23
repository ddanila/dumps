"""Test real lookup bytes as ALU-D feedback with explicit retained-address hypotheses."""
import argparse
import json
import tempfile
from collections import Counter
from pathlib import Path
from common import HERE,read,save,decode
from execute import execute


def scenario_for(config,variant,bank):
    scenario=read(HERE/f'results/independent-study/scenario-{variant}.json')
    control=read(HERE/'results/rom-study/scenario-rom_calls.json')
    scenario.update(name=f'alu-rom-feedback-bank-{bank:03x}',evidence=config['evidence'],
        dispatch=control['dispatch'],branch_tables=control['branch_tables'])
    scenario['io']['read'].update(mode='am27s31',expected_sha256=config['rom_sha256'],
        address=dict(source='previous_y',bank=bank,initial_y=config['initial_y'],status='hypothesis',evidence=config['evidence']))
    return scenario


def arithmetic_calls(records,scenario,rows,sites):
    from caller_study import inspect_trace
    from rotation_study import word
    observations=[]
    for sample in inspect_trace(records,scenario):
        if sample['site'] not in sites:continue
        tail=records[sample['cycle']+1:sample['cycle']+5]
        if len(tail)!=4 or [r['pc'] for r in tail]!=list(range(sample['target'],sample['target']+4)):
            continue
        ram=sample['ram_at_entry'][:]
        for record in tail:
            for index,value in record['registers'].items():ram[int(index)]=value
        bank=rows[sample['target']]['b'];source=(word(sample['ram_at_entry'],10),word(sample['ram_at_entry'],12))
        actual=(word(ram,bank),word(ram,bank+2))
        observations.append(dict(cycle=sample['cycle'],site=sample['site'],entry=sample['entry'],
            q=sample['q_at_entry'],source_pair=source,destination_bank=bank,actual_pair=actual))
    return observations


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/feedback-study')
    parser.add_argument('--integrated-cycles',type=int,default=0)
    args=parser.parse_args()
    if args.integrated_cycles<0:parser.error('negative integration length')
    args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'feedback-search.json');reports=[]
    for variant in config['variants']:
        mapping=read(HERE/f'results/independent-study/variant-{variant}.json')
        for bank in config['banks']:
            scenario=scenario_for(config,variant,bank);runs=[];addresses=Counter();reached=set();calls=[]
            rows=decode(mapping)
            temporary=tempfile.TemporaryDirectory()
            for seed in config['seeds']:
                r=execute(mapping,scenario,config['cycles'],seed,'integrated',temporary.name,config['cycles'])
                records=[json.loads(line) for line in (Path(temporary.name)/'trace.jsonl').read_text().splitlines()]
                calls.extend(dict(seed=seed,**call) for call in arithmetic_calls(records,scenario,rows,config['arithmetic_call_sites']))
                addresses.update(r['rom_reads']['address_counts']);reached.update(r['address_counts'])
                runs.append(dict(seed=seed,clean=r['clean'],coverage=r['coverage'],stack=r['stack'],
                    register_changes=r['register_changes'],selected_reads=r['rom_reads']['selected_by_alu'],trace_digest=r['trace_digest']))
            temporary.cleanup()
            report=dict(mapping=mapping['name'],bank=bank,reached=sorted(reached),address_counts=dict(addresses),
                arithmetic_calls=calls,nonzero_source_calls=sum(any(c['source_pair']) for c in calls),
                all_clean=all(r['clean'] for r in runs),runs=runs)
            save(args.out/f'variant-{variant}-bank-{bank:03x}.json',report)
            reports.append({k:v for k,v in report.items() if k!='runs'})
    save(args.out/'summary.json',dict(configuration=config,comparisons=reports,
        interpretation='Actual ROM bytes supplied to ALU D under assumed address feedback; physical bus and timing not recovered.'))
    if args.integrated_cycles:
        spec=config['integration'];mapping=read(HERE/f"results/independent-study/variant-{spec['variant']}.json")
        scenario=scenario_for(config,spec['variant'],spec['bank'])
        r=execute(mapping,scenario,args.integrated_cycles,spec['seed'],'integrated',args.out/'integrated',1000)
        print('Integrated clean:',r['clean'])
    print([(r['mapping'],r['bank'],len(r['address_counts']),r['all_clean']) for r in reports])

if __name__=='__main__':main()
