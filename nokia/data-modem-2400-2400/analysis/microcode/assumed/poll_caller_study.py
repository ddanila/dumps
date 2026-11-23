"""Follow the poll target from an earlier external byte across all byte values."""
import argparse
import copy
import tempfile
from pathlib import Path
from common import HERE, decode, read, save
from defined_condition_fit import load_trace
from execute import execute


def inspect(trace,rows,initial):
    ram=initial[:];writers={};events=[]
    for row in trace:
        op=rows[row['pc']];pc=row['pc']
        if pc in (0x18d,0x19c,0x1ec,0x1ee):
            events.append(dict(cycle=row['cycle'],pc=pc,r3_before=ram[3],r4_before=ram[4],
                r3_writer=writers.get(3),r4_writer=writers.get(4),q=row['q'],
                carry_in=row['carry_in'],read=row['external_read']['value'],alu=row['alu']))
            if pc==0x1ec:break
        for register,value in row['registers'].items():ram[int(register)]=value
        # Include writes that leave a register unchanged; trace deltas alone miss them.
        if op['i']>>6>=2: writers[op['b']]=dict(pc=pc,cycle=row['cycle'])
    return events


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/poll-caller-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'poll-caller-study.json');root=HERE/config['base']
    mapping=read(root/'mapping.json');base=read(root/'scenario.json');rows=decode(mapping)
    results=[];reference_paths={};path_groups={}
    with tempfile.TemporaryDirectory() as temporary:
        for value in range(256):
            for response in ('successor','unchanged'):
                scenario=copy.deepcopy(base)
                scenario['name']=f'poll-caller-{value:02x}-{response}'
                source=scenario['io']['read'];source['evidence']=config['evidence']
                source['pc_sequences'][str(config['input_pc'])]=[value]
                reply=(value+1)%256 if response=='successor' else value
                source['pc_sequences'][str(config['poll_pc'])]=[reply]
                out=args.out/scenario['name'] if value in config['witness_values'] else Path(temporary)
                result=execute(mapping,scenario,config['cycles'],mode='integrated',out=out,trace_limit=config['cycles'])
                trace=load_trace(out);events=inspect(trace,rows,scenario['initial']['ram'])
                if not result['clean'] or [e['pc'] for e in events]!=[0x18d,0x19c,0x1ec]:
                    raise ValueError('caller path differs')
                load,complement,poll=events
                if (load['alu']['f']!=value or complement['r3_before']!=value
                    or complement['carry_in']!=0 or complement['alu']['f']!=255-value
                    or complement['r3_writer']['pc']!=0x18d
                    or poll['r4_before']!=255-value or poll['r4_writer']['pc']!=0x19c):
                    raise ValueError('caller provenance differs')
                returned=any(r['pc']==0x1ee for r in trace)
                if returned!=(response=='successor'):raise ValueError('response outcome differs')
                path=[(r['pc'],r['next_pc']) for r in trace]
                reference_paths.setdefault(response,path)
                first_difference=next((i for i,(a,b) in enumerate(zip(path,reference_paths[response])) if a!=b),None)
                path_groups.setdefault((response,tuple(path)),[]).append(value)
                results.append(dict(value=value,response=response,reply=reply,clean=result['clean'],
                    returned=returned,first_control_difference_from_zero=first_difference,final_pc=result['final_state']['pc'],trace_digest=result['trace_digest'],events=events))
    save(args.out/'report.json',dict(configuration=config,runs=results,
        checks=dict(clean_runs=len(results),successor_returns=sum(r['returned'] for r in results),
            distinct_control_paths=len(path_groups)),
        control_groups=[dict(response=key[0],values=values) for key,values in path_groups.items()],
        interpretation='Under the fixed reset scenario, an external byte at 18D establishes a successor-byte poll at 1EC. The physical channel and protocol remain unidentified.'))
    print(len(results),'clean runs;',sum(r['returned'] for r in results),'returns')


if __name__=='__main__':main()
