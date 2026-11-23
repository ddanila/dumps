"""Characterize the two Q drains at 2D0 and explain reset poll timing."""
import argparse
import copy
import tempfile
from pathlib import Path
from common import HERE, read, save
from defined_condition_fit import load_trace
from execute import execute


def prediction(value,carry):
    starts=[((value+carry)&255)>>1,value>>1]
    iterations=[q.bit_length()+1 for q in starts]
    return dict(q_starts=starts,iterations=iterations,cycles=11+2*sum(iterations))


def drains(trace):
    result=[];active=None;previous_q=None
    for row in trace:
        if row['pc']==0x1e9:
            if active is None:
                active=dict(initial_q=previous_q,shifted_q=[])
            active['shifted_q'].append(row['q'])
        if row['pc']==0x1eb:
            if active is None:raise ValueError('return without observed drain')
            result.append(active);active=None
        previous_q=row['q']
    if active is not None:raise ValueError('unfinished drain')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/double-drain-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'double-drain-study.json');root=HERE/config['base']
    mapping=read(root/'mapping.json');base=read(root/'scenario.json');runs=[]
    with tempfile.TemporaryDirectory() as temporary:
        for value in range(256):
            for carry in (0,1):
                expected=prediction(value,carry);s=copy.deepcopy(base)
                s['name']=f'double-drain-{value:02x}-carry{carry}'
                s['initial']=dict(pc=0x2d0,ram=config['initial_ram'][:],q=config['initial_q'])
                s['initial']['ram'][4]=value;s['inputs']['carry']['initial']=carry
                s['io']['read']=dict(mode='constant',value=config['external_d'],table=[0],
                    status='stub',evidence=config['evidence'])
                out=args.out/s['name'] if value in config['witness_values'] else Path(temporary)
                result=execute(mapping,s,expected['cycles'],mode='integrated',out=out,trace_limit=expected['cycles'])
                observed=drains(load_trace(out));ram=s['initial']['ram'][:];ram[0]=0
                if (not result['clean'] or result['final_state']['pc']!=0x1cd
                    or result['final_state']['q']!=0 or result['final_state']['ram']!=ram
                    or result['stack']['final_depth']!=0):raise ValueError('local state prediction failed')
                if ([d['initial_q'] for d in observed]!=expected['q_starts']
                    or [len(d['shifted_q']) for d in observed]!=expected['iterations']):
                    raise ValueError('drain prediction failed')
                runs.append(dict(value=value,carry=carry,expected=expected,drains=observed,
                    trace_digest=result['trace_digest'],clean=result['clean']))
    caller=read(HERE/config['caller_report']);timings=[]
    for run in caller['runs']:
        if run['response']!='successor':continue
        expected=prediction(255-run['value'],1)
        cycle=next(e['cycle'] for e in run['events'] if e['pc']==0x1ec)
        predicted=config['reset_cycles_outside_block']+expected['cycles']
        if cycle!=predicted:raise ValueError('reset timing prediction failed')
        timings.append(dict(value=run['value'],first_poll_cycle=cycle,block_cycles=expected['cycles']))
    save(args.out/'report.json',dict(configuration=config,local_runs=runs,reset_timings=timings,
        interpretation='Two input-sized Q drains under original-register/previous-zero assumptions. No physical timing or multiply/divide function established.'))
    print(len(runs),'local state checks;',len(timings),'reset timing matches')


if __name__=='__main__':main()
