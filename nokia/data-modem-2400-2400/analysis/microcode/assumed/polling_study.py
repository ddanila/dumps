"""Test a changing external byte at 1EC without changing condition policies."""
import argparse
import copy
from pathlib import Path
from common import HERE, read, save
from defined_condition_fit import load_trace
from execute import execute


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/polling-study')
    args=parser.parse_args()
    config=read(HERE/'polling-study.json');base=HERE/config['base']
    mapping=read(base/'mapping.json');original=read(base/'scenario.json');runs=[]
    for name,values in config['sequences'].items():
        scenario=copy.deepcopy(original);scenario['name']='external-poll-'+name
        source=scenario['io']['read']
        sequences={pc:[value] for pc,value in source.pop('pc_values').items()}
        sequences[str(config['poll_pc'])]=values
        source.update(mode='pc_sequence',pc_sequences=sequences,sequence_end=config['sequence_end'],
                      status='stub',evidence=config['evidence'])
        out=args.out/name
        result=execute(mapping,scenario,config['cycles'],mode='integrated',out=out,trace_limit=config['cycles'])
        trace=load_trace(out);samples=[];ram=scenario['initial']['ram'][:]
        for index,row in enumerate(trace):
            if row['pc']==config['poll_pc']:
                following=trace[index+1] if index+1<len(trace) else None
                samples.append(dict(cycle=row['cycle'],r4_before=ram[4],read=row['external_read'],
                    alu=row['alu'],branch_next_pc=following['next_pc'] if following else None))
            for register,value in row['registers'].items():ram[int(register)]=value
        returns=[r['cycle'] for r in trace if r['pc']==0x1ee]
        if not result['clean'] or not samples:raise ValueError('reset experiment incomplete')
        for sample in samples:
            if sample['r4_before']!=255 or sample['alu']['f']!=(sample['read']['value']+255)%256:
                raise ValueError('poll arithmetic differs from prediction')
            expected=0x1ee if sample['read']['value']==1 else 0x1ec
            if sample['branch_next_pc'] is not None and sample['branch_next_pc']!=expected:
                raise ValueError('previous-zero branch differs from prediction')
        if (1 in values)!=bool(returns):raise ValueError('poll release differs from prediction')
        if returns and returns[0]!=samples[0]['cycle']+2*values.index(1)+2:
            raise ValueError('poll delay differs from prediction')
        runs.append(dict(name=name,sequence=values,clean=result['clean'],words=len(result['visited']),
            final_state=result['final_state'],stack=result['stack'],trace_digest=result['trace_digest'],
            samples=samples,return_cycles=returns))
        print(name,len(samples),returns,f"{result['final_state']['pc']:03X}")
    save(args.out/'report.json',dict(configuration=config,runs=runs,
        interpretation='A PC-keyed external-input stub releases the existing previous-zero poll. This does not identify a physical input address, device, or sample clock.'))


if __name__=='__main__':main()
