"""Inspect real reset-path caller states without injecting table entry points."""
import argparse
import json
import tempfile
from pathlib import Path
from common import HERE, decode, read, save
from execute import execute


def inspect_trace(records, scenario):
    """Reconstruct RAM from a complete bounded prefix, retaining pre-call state."""
    ram=scenario['initial']['ram'][:]
    q=scenario['initial']['q']
    previous_y=None
    samples=[]
    for cycle,record in enumerate(records):
        if record['cycle']!=cycle:raise ValueError('caller analysis requires a contiguous trace prefix')
        before=ram[:]
        for index,value in record['registers'].items():ram[int(index)]=value
        site=str(record['pc'])
        table=scenario['dispatch']['tables'].get(site)
        if table and record['dispatch_entry'] is not None:
            y=record['alu']['y']
            samples.append(dict(cycle=cycle,site=record['pc'],entry=record['dispatch_entry'],
                target=record['next_pc'],ram_before=before,ram_at_entry=ram[:],q_before=q,q_at_entry=record['q'],
                current_y=y,previous_y=previous_y,
                candidate_indices=dict(current_y=y%table['count'],q=record['q']%table['count'],
                    previous_y=None if previous_y is None else previous_y%table['count'])))
        q=record['q'];previous_y=record['alu']['y']
    return samples


def check_rotation(sample,rows,scenario,rotation_bases):
    from rotation_study import run_entry, word
    table=scenario['dispatch']['tables'][str(sample['site'])]
    if table['base'] not in rotation_bases:return
    bank=rows[table['base']]['b']
    ram=sample['ram_at_entry']
    x,y=word(ram,10),word(ram,12)
    expected=[(x,y),(-y&65535,x),(-x&65535,-y&65535),(y,-x&65535)][sample['entry']]
    table=scenario['dispatch']['tables'][str(sample['site'])]
    cpu,_=run_entry(rows,table['base'],sample['entry'],ram,sample['q_at_entry'],scenario['inputs']['carry'])
    actual=(word(cpu.ram,bank),word(cpu.ram,bank+2))
    sample['rotation_check']=dict(expected=expected,actual=actual,matches=expected==actual)


def summarize(samples,sites):
    result={}
    for site in sites:
        selected=[s for s in samples if s['site']==site]
        result[f'{site:03X}']=dict(observations=len(selected),
            q_zero=sum(s['q_at_entry']==0 for s in selected),
            rotation_checks=sum('rotation_check' in s for s in selected),
            rotation_failures=sum(not s['rotation_check']['matches'] for s in selected if 'rotation_check' in s),
            q_values=sorted({s['q_at_entry'] for s in selected}),
            source_pair_nonzero=sum(any(s['ram_at_entry'][10:14]) for s in selected),
            selected_entries=sorted({s['entry'] for s in selected}),
            candidate_indices={source:sorted({s['candidate_indices'][source] for s in selected
                if s['candidate_indices'][source] is not None}) for source in ('current_y','q','previous_y')})
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/caller-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'caller-search.json')
    reports=[]
    for variant in range(1,4):
        mapping=read(HERE/f'results/rotation-study/variant-{variant}.json')
        scenario=read(HERE/f'results/rotation-study/scenario-{variant}.json')
        rows=decode(mapping);sites=sorted(map(int,scenario['dispatch']['tables']))
        samples=[];runs=[]
        with tempfile.TemporaryDirectory() as tmp:
            for value in config['external_read_values']:
                scenario['io']['read']['value']=value
                for seed in config['seeds']:
                    cycles=config['cycles']
                    result=execute(mapping,scenario,cycles,seed,'integrated',tmp,cycles)
                    records=[json.loads(line) for line in (Path(tmp)/'trace.jsonl').read_text().splitlines()]
                    samples.extend(dict(external_read=value,seed=seed,**sample) for sample in inspect_trace(records,scenario))
                    runs.append(dict(external_read=value,seed=seed,clean=result['clean'],coverage=result['coverage'],trace_digest=result['trace_digest']))
        rotation_bases=read(HERE/'rotation-search.json')['rotation_table_bases']
        for sample in samples:check_rotation(sample,rows,scenario,rotation_bases)
        by_input={str(value):summarize([s for s in samples if s['external_read']==value],sites)
                  for value in config['external_read_values']}
        report=dict(mapping=mapping['name'],runs=runs,sites=summarize(samples,sites),by_input=by_input,samples=samples,
            caller_listing={f'{site:03X}':rows[site-2:site+1] for site in sites})
        save(args.out/f'variant-{variant}.json',report)
        reports.append(dict(mapping=mapping['name'],sites=report['sites'],by_input=by_input,all_clean=all(r['clean'] for r in runs)))
    save(args.out/'summary.json',dict(variants=reports,configuration=config,
        interpretation='Observed caller states under saved rotation scenarios; indices are counterfactual candidates, not evidence of physical wiring. Unobserved sites remain unresolved.'))
    print('Wrote caller reports for',len(reports),'variants')

if __name__=='__main__':main()
