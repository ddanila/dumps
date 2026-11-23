"""Search one raw-bit-controlled mux at B0 or B9 across direct transfers."""
import argparse
import csv
from pathlib import Path
from common import HERE, decode, field_value, load, read, save
from analyze import graph
from context_branch_study import witness
from joint_branch_study import ranges


def mux(rows,lanes,position,gate,source):
    result=[dict(r) for r in rows]
    for row in result:
        if row['command'] in (4,6) and row['direct'] and field_value([gate],lanes,row['pc']):
            bit=field_value([source],lanes,row['pc'])
            row['branch']=(row['branch'] & ~(1<<position)) | (bit<<position)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/branch-mux-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'branch-mux-search.json');lanes=load();rows=decode(read(HERE/'sequencer.json'))
    scenario=read(HERE/config['scenario']);base=set(graph(rows,scenario)['reached'])
    tokens=[f'{polarity}{chip}.{bit}' for chip in config['chips'] for bit in range(8) for polarity in ('','!')]
    cache={};results=[];best=None;best_rows=None;number=0
    with (args.out/'candidates.csv').open('w') as stream:
        writer=csv.writer(stream,lineterminator='\n');writer.writerow(['position','gate','source','result_id'])
        for position in config['positions']:
            for gate in tokens:
                for source in tokens:
                    candidate=mux(rows,lanes,position,gate,source)
                    changes=tuple((a['pc'],b['branch']) for a,b in zip(rows,candidate) if a['branch']!=b['branch'])
                    if changes not in cache:
                        cfg=graph(candidate,scenario);reached=set(cfg['reached']);gained=reached-base;lost=base-reached
                        result=dict(id=len(results),representative=dict(position=position,gate=gate,source=source),
                            changed=' '.join(f'{p:03X}:{v:03X}' for p,v in changes),words=len(reached),states=cfg['states'],
                            gained=ranges(gained),lost=ranges(lost),exceptions=cfg['exceptions'])
                        cache[changes]=result['id'];results.append(result)
                        if not cfg['exceptions'] and (best is None or len(reached)>best['words']):
                            best=dict(result_id=result['id'],words=len(reached),gained=sorted(gained),lost=sorted(lost))
                            best_rows=candidate
                    writer.writerow([position,gate,source,cache[changes]]);number+=1
    if best['gained']:best['witness']=witness(best_rows,scenario,best['gained'][0])
    clean=[r for r in results if not r['exceptions']]
    examples=[]
    patterns=sorted({r['gained'] for r in clean if r['gained']})
    for pattern in patterns:
        selected=max((r for r in clean if r['gained']==pattern),key=lambda r:r['words'])
        spec=selected['representative'];candidate=mux(rows,lanes,**spec)
        target=int(pattern.split()[0].split('-')[0],16)
        examples.append(dict(result_id=selected['id'],steps=witness(candidate,scenario,target)))
    save(args.out/'report.json',dict(configuration=config,baseline_words=len(base),results=results,best=best,gain_witnesses=examples,
        counts=dict(candidates=number,distinct_target_sets=len(results),clean_target_sets=len(clean),
                    clean_target_sets_with_gains=sum(bool(r['gained']) for r in clean)),
        interpretation='One gated branch-bit substitution across all direct transfers; fixed dispatch and conditions. No default runtime mapping changed.'))
    print(number,'candidates;',len(results),'distinct target sets; best',best['words'],best['gained'])


if __name__=='__main__':main()
