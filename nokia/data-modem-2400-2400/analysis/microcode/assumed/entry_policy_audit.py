"""Explain default graph gaps and audit all witnessed forced-jump relaxations."""
import argparse
import hashlib
from collections import Counter
from pathlib import Path
from common import HERE, read, save, decode, unconditional_transfer
from analyze import graph
from defined_condition_fit import load_trace
from reset_witness_catalog import build_catalog


def relaxed_graph(rows,scenario,sites):
    return graph(rows,scenario,unconditional_policy=lambda row,s:
                 unconditional_transfer(row,s) and row['pc'] not in sites)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/entry-policy-audit')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    catalog=build_catalog();config=catalog['configuration'];scenario=read(HERE/config['baseline_scenario'])
    rows=decode(read(HERE/'sequencer.json'));sites=set();support={}
    for witness in config['witnesses']:
        for row in load_trace(HERE/witness['path']):
            if row['command']==6 and row['test']==0 and unconditional_transfer(rows[row['pc']],scenario):
                sites.add(row['pc']);support.setdefault(f"{row['pc']:03X}",[]).append(dict(witness=witness['id'],cycle=row['cycle']))
    sites=sorted(sites);results=[];histogram=Counter();complete=[]
    for mask in range(1<<len(sites)):
        selected=[pc for bit,pc in enumerate(sites) if mask>>bit&1]
        got=relaxed_graph(rows,scenario,set(selected))
        result=dict(mask=mask,relaxed=[f'{p:03X}' for p in selected],reached=len(got['reached']),exceptions=got['exceptions'])
        results.append(result);histogram[len(got['reached'])]+=1
        if not got['unreachable']:complete.append(result)
    minimum=min(len(r['relaxed']) for r in complete)
    smallest=[r for r in complete if len(r['relaxed'])==minimum]
    sources=[Path(__file__),HERE/'reset_witness_catalog.py',HERE/'reset-witnesses.json',HERE/'analyze.py',HERE/'common.py',HERE/'execute.py',HERE.parent/'model.py',HERE/'sequencer.json',HERE/config['baseline_scenario']]
    save(args.out/'report.json',dict(status='hypothesis',
        scope='Analysis-only optional false tests at witnessed default-unconditional BRT sites. Original targets, dispatch tables, stack semantics and free conditions retained. Not a runtime policy, physical gate recovery or full-plan completion.',
        baseline_words=catalog['baseline_words'],gap_words=catalog['target_words'],entries=catalog['entries'],
        witnessed_relaxations=[f'{p:03X}' for p in sites],witness_support=support,subsets=results,
        reachable_histogram=dict(histogram),complete_subsets=len(complete),
        complete_without_stack_exceptions=sum(not r['exceptions'] for r in complete),minimum_size=minimum,smallest=smallest,
        witness_catalog_source_sha256=catalog['source_sha256'],
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}))
    print(dict(sites=len(sites),subsets=len(results),complete=len(complete),minimum=minimum,smallest=smallest))


if __name__=='__main__':main()
