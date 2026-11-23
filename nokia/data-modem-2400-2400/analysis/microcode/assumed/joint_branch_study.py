"""Combine distinct clean contextual branch alternatives and measure interactions."""
import argparse
import csv
import hashlib
from collections import Counter
from itertools import combinations
from pathlib import Path
from common import HERE, decode, read, save
from analyze import graph
from context_branch_study import witness


def alternatives(report):
    unique={}
    for candidate in report['candidates']:
        if candidate['exceptions'] or not candidate['changed']:continue
        key=tuple((r['pc'],r['after']) for r in candidate['changed'])
        unique.setdefault(key,dict(changed=candidate['changed'],sources=[]))['sources'].append(
            {k:candidate[k] for k in ('command','select','position','token')})
    return [dict(id=i,**v) for i,v in enumerate(unique.values())]


def combine(rows,a,b):
    # Each representative is scoped to one command/select class. Keep classes
    # distinct even if two particular substitutions happen to change disjoint PCs.
    ca,cb=a['sources'][0],b['sources'][0]
    if (ca['command'],ca['select'])==(cb['command'],cb['select']):return None
    result=[dict(r) for r in rows]
    for option in (a,b):
        for change in option['changed']:result[change['pc']]['branch']=change['after']
    return result


def ranges(values):
    groups=[]
    for value in sorted(values):
        if groups and value==groups[-1][1]+1:groups[-1][1]=value
        else:groups.append([value,value])
    return ' '.join(f'{lo:03X}' if lo==hi else f'{lo:03X}-{hi:03X}' for lo,hi in groups)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/joint-branch-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'joint-branch-search.json');source=HERE/config['source_report']
    choices=alternatives(read(source));rows=decode(read(HERE/'sequencer.json'))
    scenario=read(HERE/config['scenario']);base=set(graph(rows,scenario)['reached'])
    counts=Counter();histogram=Counter();best=None;best_rows=None;clean_gained=set();most_gains=None;most_rows=None
    with (args.out/'pairs.csv').open('w') as stream:
        writer=csv.writer(stream,lineterminator='\n')
        writer.writerow(['first','second','reached','exceptions','gained','lost'])
        for a,b in combinations(choices,2):
            candidate=combine(rows,a,b)
            if candidate is None:counts['same_class_skipped']+=1;continue
            cfg=graph(candidate,scenario);reached=set(cfg['reached']);gained=reached-base;lost=base-reached
            counts['tested']+=1
            writer.writerow([a['id'],b['id'],len(reached),len(cfg['exceptions']),
                ranges(gained),ranges(lost)])
            if cfg['exceptions']:counts['with_exceptions']+=1;continue
            counts['clean']+=1;histogram[len(reached)]+=1;clean_gained.update(gained)
            if gained:counts['clean_with_gains']+=1
            if most_gains is None or (len(gained),len(reached))>(len(most_gains['gained']),most_gains['words']):
                most_gains=dict(first=a['id'],second=b['id'],words=len(reached),gained=sorted(gained),lost=sorted(lost))
                most_rows=candidate
            if best is None or len(reached)>best['words']:
                best=dict(first=a['id'],second=b['id'],words=len(reached),gained=sorted(gained),lost=sorted(lost))
                best_rows=candidate
    if best and best['gained']:best['witness']=witness(best_rows,scenario,best['gained'][0])
    if most_gains and most_gains['gained']:most_gains['witness']=witness(most_rows,scenario,most_gains['gained'][0])
    save(args.out/'report.json',dict(configuration=config,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        alternatives=choices,counts=dict(counts),clean_coverage_histogram=dict(histogram),
        clean_gained=sorted(clean_gained),best=best,most_gains=most_gains,
        interpretation='Pairs of individually clean contextual hypotheses, with distinct command/select classes. Static possible paths, not recovered hardware or default runtime behavior.'))
    print(dict(counts),'best words',best['words'],'clean gained',sorted(clean_gained))


if __name__=='__main__':main()
