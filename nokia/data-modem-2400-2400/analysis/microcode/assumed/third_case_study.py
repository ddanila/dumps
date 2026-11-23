"""Compare additional variable-length cases at local branch-table boundaries."""
import argparse
import copy
import json
import tempfile
from pathlib import Path
from common import HERE, decode, read, save
from analyze import graph
from execute import execute


def scenarios(base,config):
    result={}
    for name,sites in config['variants'].items():
        scenario=copy.deepcopy(base);scenario.update(name='third-case-'+name,evidence=config['evidence'])
        for site in sites:
            table=scenario['branch_tables'][str(site)]
            expected=config['baseline_counts'][str(site)]
            if table['count']!=expected or table['stride']!=1:raise ValueError('unexpected baseline table')
            table.update(count=expected+1,status='hypothesis',evidence=config['evidence'])
        result[name]=scenario
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/third-case-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'third-case-search.json')
    base=read(HERE/'results/rom-tail-study/scenario-scoped_tail.json')
    mapping=read(HERE/'sequencer.json');rows=decode(mapping);baseline=graph(rows,base);reports=[]
    for name,scenario in scenarios(base,config).items():
        cfg=graph(rows,scenario)
        save(args.out/f'scenario-{name}.json',scenario)
        runs=[];reached=set();witnesses={}
        if not cfg['exceptions']:
            for seed in range(config['seeds']):
                r=execute(mapping,scenario,config['cycles'],seed,'sequencer',trace_limit=0)
                reached.update(r['address_counts'])
                runs.append(dict(seed=seed,clean=r['clean'],coverage=r['coverage'],stack=r['stack'],trace_digest=r['trace_digest']))
                for target in config['candidate_entries']:
                    if target not in witnesses and r['address_counts'].get(target):witnesses[target]=seed
        samples=[];cache={}
        with tempfile.TemporaryDirectory() as tmp:
            for target,seed in witnesses.items():
                if seed not in cache:
                    out=args.out/f'{name}-seed-{seed}' if name==config['trace_variant'] else Path(tmp)/str(seed)
                    execute(mapping,scenario,config['cycles'],seed,'sequencer',out,config['cycles'])
                    cache[seed]=[json.loads(line) for line in (out/'trace.jsonl').read_text().splitlines()]
                records=cache[seed]
                at=next(i for i,r in enumerate(records) if r['pc']==target)
                samples.append(dict(target=target,seed=seed,dispatch=records[at-1],prefix=records[at:at+config['excerpt_cycles']],
                    trace_path=f'{name}-seed-{seed}/trace.jsonl' if name==config['trace_variant'] else None))
        report=dict(name=name,static_words=len(cfg['reached']),exceptions=cfg['exceptions'],
            gained=sorted(set(cfg['reached'])-set(baseline['reached'])),remaining=[x['pc'] for x in cfg['unreachable']],
            dynamic_words=len(reached),reached=sorted(reached),runs=runs,witnesses=samples,
            all_clean=bool(runs) and all(r['clean'] for r in runs))
        save(args.out/f'{name}.json',report)
        reports.append({k:v for k,v in report.items() if k not in ('runs','reached','witnesses')})
    baseline_reached=set(read(args.out/'baseline.json')['reached'])
    for summary in reports:
        path=args.out/(summary['name']+'.json');report=read(path)
        summary.update(dynamic_gained=sorted(set(report['reached'])-baseline_reached),
                       dynamic_lost=sorted(baseline_reached-set(report['reached'])))
        report.update(summary);save(path,report)
    save(args.out/'summary.json',dict(configuration=config,variants=reports,
        interpretation='Adjacent third-case hypotheses, not recovered dispatch encoding. Reports are independent comparisons; coverage does not rank hardware truth.'))
    print(reports)

if __name__=='__main__':main()
