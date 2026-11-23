"""Constrain dispatch targets with independent Am27S31 lookup bytes."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
from common import HERE,decode,read,save,table_targets
from analyze import graph
from execute import execute


def load_rom(config):
    data=(HERE.parents[3]/'unknown-modem-am27s31dc/nokia-modem-am27s31dc.bin').read_bytes()
    if len(data)!=512 or hashlib.sha256(data).hexdigest()!=config['rom_sha256']:
        raise ValueError('Am27S31 dump size/hash mismatch')
    return data


def rom_table(data,spec,config):
    offset,count,bank=(spec[k] for k in ('offset','count','bank'))
    if offset<0 or count<1 or offset+count>len(data):raise ValueError('invalid lookup range')
    table=dict(targets=[bank+v for v in data[offset:offset+count]],allow_duplicate_targets=True,
        status='hypothesis',evidence=config['evidence'],
        lookup=dict(source='Am27S31',sha256=config['rom_sha256'],offset=offset,count=count,bank=bank))
    table_targets(table)
    return table


def scenarios(base,data,config):
    branches=copy.deepcopy(base);branches.update(name='am27s31-branch-targets',evidence=config['evidence'])
    for site,spec in config['branch_lookups'].items():branches['branch_tables'][site]=rom_table(data,spec,config)
    calls=copy.deepcopy(branches);calls['name']='am27s31-branch-and-call-targets'
    for site in config['call_sites']:calls['dispatch']['tables'][str(site)]=rom_table(data,config['call_lookup'],config)
    rejected=copy.deepcopy(calls);spec=config['rejected_alternative']
    rejected['dispatch']['tables'][str(spec['site'])]=rom_table(data,spec,config)
    return dict(rom_branches=branches,rom_calls=calls,rejected_d0=rejected)


def reconstruct_lookups(records,scenario,data):
    result=[]
    for row in records:
        if row['dispatch_entry'] is None:continue
        tables=scenario['branch_tables'] if row['command']==6 else scenario['dispatch']['tables']
        table=tables[str(row['pc'])];lookup=table.get('lookup')
        if lookup is None:continue
        address=lookup['offset']+row['dispatch_entry'];target=lookup['bank']+data[address]
        if target!=row['next_pc']:raise ValueError('lookup bytes do not reproduce executed target')
        result.append(dict(cycle=row['cycle'],pc=row['pc'],rom_address=address,rom_value=data[address],
            bank=lookup['bank'],target=target,rom_sha256=lookup['sha256'],status='hypothesis',
            interpretation='Reconstructed candidate dispatch lookup; physical bus transfer not established'))
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/rom-study')
    parser.add_argument('--integrated-cycles',type=int,default=0)
    args=parser.parse_args()
    if args.integrated_cycles<0:parser.error('negative integration length')
    args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'rom-dispatch.json');data=load_rom(config)
    base=read(HERE/'results/target-study/scenario-bounded.json');mapping=read(HERE/'sequencer.json');rows=decode(mapping)
    alternatives=scenarios(base,data,config);summaries={}
    for name,scenario in alternatives.items():
        g=graph(rows,scenario);save(args.out/f'graph-{name}.json',g);save(args.out/f'scenario-{name}.json',scenario)
        record=dict(static_reachable=len(g['reached']),exceptions=g['exceptions'])
        if not g['exceptions']:
            reached=set();runs=[]
            for seed in range(config['seeds']):
                r=execute(mapping,scenario,config['cycles'],seed,trace_limit=0)
                reached.update(r['address_counts']);runs.append(dict(seed=seed,clean=r['clean'],coverage=r['coverage'],stack=r['stack'],trace_digest=r['trace_digest']))
            record.update(reached=sorted(reached),coverage=len(reached)/1021,runs=runs,all_clean=all(r['clean'] for r in runs))
        summaries[name]=record
    roles={}
    spec=config['call_lookup'];values=sorted(set(data[spec['offset']:spec['offset']+spec['count']]))
    for bank in config['banks_to_compare']:
        checks=[]
        for value in values:
            g=graph(rows,base,start=bank+value,initial_stack=(-1,),return_sentinel=-1)
            checks.append(dict(target=bank+value,returns=g['terminal_return_reached'],exceptions=g['exceptions']))
        roles[str(bank)]=checks
    full=[round(127*math.sin(2*math.pi*i/16))&255 for i in range(16)]
    quarter=[round(127*math.sin(math.pi*i/128)) for i in range(65)]
    save(args.out/'rom-evidence.json',dict(configuration=config,
        branch_bytes={site:list(data[s['offset']:s['offset']+s['count']]) for site,s in config['branch_lookups'].items()},
        call_bytes=list(data[spec['offset']:spec['offset']+spec['count']]),call_bank_roles=roles,
        sine_full_period=dict(offset=0,count=16,exact_match=list(data[:16])==full),
        sine_quarter_period=dict(offset=256,count=65,exact_match=list(data[256:321])==quarter)))
    save(args.out/'summary.json',dict(configuration=config,comparisons=summaries,
        interpretation='ROM-derived target lists are independent data; source associations, bank bits and physical selection remain hypotheses.'))
    if args.integrated_cycles:
        spec=config['integration'];m=read(HERE/f"results/independent-study/variant-{spec['variant']}.json")
        s=read(HERE/f"results/independent-study/scenario-{spec['variant']}.json");selected=alternatives['rom_calls']
        s.update(name=selected['name'],evidence=selected['evidence'],dispatch=selected['dispatch'],branch_tables=selected['branch_tables'])
        s['io']['read']['value']=spec['external_read']
        r=execute(m,s,args.integrated_cycles,spec['seed'],'integrated',args.out/'integrated',1000)
        records=[json.loads(line) for line in (args.out/'integrated/trace.jsonl').read_text().splitlines()]
        lookups=[dict(run='integrated',**entry) for entry in reconstruct_lookups(records,s,data)]
        execute(m,s,config['cycles'],config['lookup_example_seed'],'integrated',args.out/'branch-example',config['cycles'])
        records=[json.loads(line) for line in (args.out/'branch-example/trace.jsonl').read_text().splitlines()]
        lookups.extend(dict(run='branch-example',**entry) for entry in reconstruct_lookups(records,s,data))
        save(args.out/'dispatch-lookups.json',lookups)
        print('Integrated clean:',r['clean'])
    print([(name,r['static_reachable'],len(r.get('reached',[])),r['exceptions']) for name,r in summaries.items()])

if __name__=='__main__':main()
