"""Trace q2's reset waits, masked poll target and explicit zero replies."""
import argparse
import copy
import hashlib
import json
import tempfile
from collections import Counter
from pathlib import Path
from common import HERE, decode, read, save
from defined_condition_fit import load_trace
from execute import execute


def inspect(trace,rows,sequences):
    ram=[0]*16;q=0;writers={};events=[];counts=Counter();visits=Counter();seen={};repeat=None
    watch={0x74,0x106,0x107,0x117,0x118,0x126,0x129,0x12b,0x12c,0x12e,0x130}
    for t in trace:
        pc=t['pc'];counts[pc]+=1
        if pc in watch and counts[pc]<=2:
            events.append(dict(pc=pc,cycle=t['cycle'],ram_before=ram[:],q_before=q,
                               writers={str(i):writers.get(i) for i in (0,7,10)},read=t.get('external_read'),alu=t['alu'],test=t['test'],next_pc=t['next_pc']))
        for i,v in t['registers'].items():ram[int(i)]=v
        if rows[pc]['i']>>6>=2:writers[rows[pc]['b']]=dict(pc=pc,cycle=t['cycle'])
        q=t['q']
        if str(pc) in sequences:visits[str(pc)]+=1
        phases={p:min(visits[p],len(values)-1) for p,values in sequences.items()}
        if t['next_pc'] in (0x117,0x106,0x127,0x12c):
            key=json.dumps([t['next_pc'],ram,q,t['alu'],t['stack_after'],phases],sort_keys=True)
            if key in seen and repeat is None:repeat=dict(pc=t['next_pc'],first_cycle=seen[key],second_cycle=t['cycle'],period=t['cycle']-seen[key])
            seen[key]=t['cycle']
    return dict(events=events,repeat=repeat,helper_returns={str(p):counts[p] for p in (0x12b,0x130)})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/q2-caller-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'q2-caller-study.json');mapping=read(HERE/config['mapping']);base=read(HERE/config['scenario']);rows=decode(mapping)
    runs=[];counts=Counter()
    with tempfile.TemporaryDirectory() as temporary:
        for profile,sites in config['reply_profiles'].items():
            for d in range(256):
                s=copy.deepcopy(base);s['initial']=dict(pc=0,ram=[0]*16,q=0);s['dispatch']['value']=0
                sequences={str(pc):[d,0] for pc in sites}
                s['io']['read']=dict(mode='constant',value=d,table=[0],status='stub',evidence=config['evidence'])
                if sequences:s['io']['read'].update(mode='pc_sequence',pc_sequences=sequences,sequence_end='hold-last')
                out=args.out/f'{profile}-d{d:02x}' if d in config['witness_values'] else Path(temporary)
                result=execute(mapping,s,config['cycles'],mode='integrated',out=out,trace_limit=config['cycles'])
                assert result['clean']
                observed=inspect(load_trace(out),rows,sequences);events=observed['events']
                first=lambda pc:next(e for e in events if e['pc']==pc)
                assert first(0x74)['alu']['f']==255
                assert first(0x117)['ram_before'][0]==255 and first(0x117)['writers']['0']['pc']==0x74
                done=d==0 or profile=='all-replies'
                if done:
                    assert result['final_state']['pc']==0x84 and observed['repeat'] is None
                    assert all(v==1 for v in observed['helper_returns'].values())
                else:
                    target=0x117 if profile=='constant' else 0x127
                    assert observed['repeat']['pc']==target and observed['repeat']['period']==(2 if target==0x117 else 4)
                    assert all(v==0 for v in observed['helper_returns'].values())
                if profile!='constant' or d==0:
                    entry=first(0x126)
                    assert entry['ram_before'][0]==255 and entry['ram_before'][10]==entry['q_before']==0
                    assert entry['writers']['0']['pc']==0x74 and entry['writers']['10'] is None
                    compare=first(0x129)
                    assert compare['q_before']==0 and compare['alu']['f']==(-d)&255
                if done:
                    assert first(0x12c)['q_before']==0 and first(0x12c)['ram_before'][0]==255
                outcome='terminal' if done else 'early-wait' if profile=='constant' else 'masked-poll'
                counts[f'{profile}:{outcome}']+=1
                runs.append(dict(profile=profile,d=d,observed=observed,final_pc=result['final_state']['pc'],trace_digest=result['trace_digest']))
    sources=[Path(__file__),HERE/'q2-caller-study.json',HERE/config['mapping'],HERE/config['scenario'],HERE/'execute.py',HERE/'common.py',HERE.parent/'model.py']
    save(args.out/'report.json',dict(configuration=config,counts=dict(counts),runs=runs,
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='q2 reset with shared previous flags and dispatch index zero reaches a zero-target masked poll after explicit replies to early carry waits. All replies reach terminal 084, but R10 target is still reset zero, not recovered nonzero data.'))
    print(dict(counts))


if __name__=='__main__':main()
