"""Trace last register writers before arithmetic calls on reset-started paths."""
import argparse
import json
import tempfile
from pathlib import Path
from common import HERE, decode, read, save
from execute import execute
from feedback_study import scenario_for


def provenance(records, rows, scenario, sites):
    ram=scenario['initial']['ram'][:]
    writers=[dict(kind='initial',value=value) for value in ram]
    samples=[]
    for cycle,record in enumerate(records):
        if record['cycle']!=cycle:raise ValueError('requires contiguous trace prefix')
        row=rows[record['pc']]
        before=ram[:]
        for index,value in record['registers'].items():ram[int(index)]=value
        # Destination codes 2..7 write RAM, including writes of an unchanged byte.
        if row['i']>>6>=2:
            b=row['b']
            writers[b]=dict(kind='instruction',pc=record['pc'],cycle=cycle,value=ram[b],
                old_value=before[b],a=row['a'],b=b,instruction=row['i'],
                a_before=before[row['a']],q_after=record['q'],
                external_read=record.get('external_read'))
        if record['pc'] in sites and record['dispatch_entry'] is not None:
            samples.append(dict(cycle=cycle,site=record['pc'],target=record['next_pc'],
                source_bytes=ram[10:14],writers=writers[10:14]))
    return samples


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/operand-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'operand-search.json');feedback=read(HERE/'feedback-search.json')
    reports=[]
    for variant in config['variants']:
        mapping=read(HERE/f'results/independent-study/variant-{variant}.json');rows=decode(mapping)
        writers=[r for r in rows if r['b'] in range(10,14) and r['i']>>6>=2]
        for bank in config['banks']:
            scenario=scenario_for(feedback,variant,bank);samples=[];runs=[];reached=set()
            with tempfile.TemporaryDirectory() as tmp:
                for seed in config['seeds']:
                    r=execute(mapping,scenario,config['cycles'],seed,'integrated',tmp,config['cycles'])
                    records=[json.loads(line) for line in (Path(tmp)/'trace.jsonl').read_text().splitlines()]
                    samples.extend(dict(seed=seed,**s) for s in provenance(records,rows,scenario,config['sites']))
                    reached.update(r['address_counts'])
                    runs.append(dict(seed=seed,clean=r['clean'],trace_digest=r['trace_digest']))
            report=dict(mapping=mapping['name'],bank=bank,runs=runs,samples=samples,
                writer_listing=[dict(**r,visited=r['pc'] in reached) for r in writers],
                observations=len(samples),nonzero_source_calls=sum(any(s['source_bytes']) for s in samples),
                initial_only_calls=sum(all(w['kind']=='initial' for w in s['writers']) for s in samples),
                all_clean=all(r['clean'] for r in runs))
            save(args.out/f'variant-{variant}-bank-{bank:03x}.json',report)
            reports.append({k:v for k,v in report.items() if k not in ('runs','samples','writer_listing')})
    save(args.out/'summary.json',dict(configuration=config,comparisons=reports,
        interpretation='Last writers under declared feedback mappings, including unchanged writes; no physical input path established.'))
    print(reports)

if __name__=='__main__':main()
