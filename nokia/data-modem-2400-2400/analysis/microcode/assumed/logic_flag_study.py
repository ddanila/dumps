"""Compare fitted reset paths with explicit Am2901B logical flag semantics."""
import argparse
import copy
import json
import tempfile
from pathlib import Path
from common import HERE, decode, read, save
from execute import execute
from condition_extension import unknown_decisions


def records(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/logic-flag-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'logic-flags.json');reports=[]
    for name in config['profiles']:
        root=HERE/'results/selector-completion'/name
        mapping=read(root/'mapping.json');base=read(root/'scenario.json');archive=read(root/'summary.json')
        scenario=copy.deepcopy(base)
        scenario.update(name='defined-logic-flags-'+name,evidence=config['evidence'])
        scenario['inputs']['logic_flags']=config['logic_flags']
        with tempfile.TemporaryDirectory() as tmp:
            before=execute(mapping,base,config['cycles'],mode='integrated',out=Path(tmp),trace_limit=config['cycles'])
            prior=records(Path(tmp)/'trace.jsonl')
        if before['trace_digest']!=archive['trace_digest'] or before['completed_cycles']!=archive['completed_cycles']:
            raise ValueError('historical reset example no longer reproduces')
        out=args.out/name
        after=execute(mapping,scenario,config['cycles'],mode='integrated',out=out,trace_limit=config['cycles'])
        later=records(out/'trace.jsonl')
        first_control=next((dict(cycle=i,before=a,after=b) for i,(a,b) in enumerate(zip(prior,later))
                            if (a['pc'],a['next_pc'])!=(b['pc'],b['next_pc'])),None)
        first_flags=next((dict(cycle=i,before=a,after=b) for i,(a,b) in enumerate(zip(prior,later))
                          if a['alu']!=b['alu']),None)
        rows=decode(mapping)
        def compact(summary,trace,policy):
            return dict(clean=summary['clean'],completed_cycles=summary['completed_cycles'],
                        words=len(summary['visited']),final_state=summary['final_state'],
                        stack=summary['stack'],carry_model=summary['carry_model'],
                        unknown_decisions=unknown_decisions(trace,rows,policy),trace_digest=summary['trace_digest'])
        reports.append(dict(profile=name,before=compact(before,prior,base),after=compact(after,later,scenario),
                            first_control_difference=first_control,first_alu_difference=first_flags,
                            gained=sorted(set(after['visited'])-set(before['visited'])),
                            lost=sorted(set(before['visited'])-set(after['visited']))))
    long_runs=[]
    for name in config['long_profiles']:
        mapping=read(args.out/name/'mapping.json');scenario=read(args.out/name/'scenario.json')
        result=execute(mapping,scenario,config['long_cycles'],mode='integrated',out=args.out/('long-'+name),
                       trace_limit=config['long_trace_limit'])
        long_runs.append(dict(profile=name,clean=result['clean'],cycles=result['completed_cycles'],
                              words=len(result['visited']),stack=result['stack'],carry_model=result['carry_model'],
                              final_pc=result['final_state']['pc'],trace_digest=result['trace_digest']))
    save(args.out/'report.json',dict(configuration=config,profiles=reports,long_runs=long_runs,
        interpretation='Defined component flag experiment, not a refit of condition wiring or proof of modem behavior.'))
    for r in reports:
        print(r['profile'],r['before']['words'],r['after']['words'],'clean',r['after']['clean'],
              'first_control',None if r['first_control_difference'] is None else r['first_control_difference']['cycle'],
              'unknown carry',r['before']['carry_model']['counts'].get('unknown_feedback',0),
              r['after']['carry_model']['counts'].get('unknown_feedback',0))


if __name__=='__main__':main()
