"""Characterize the shared terminal tail without inventing a restart protocol."""
import argparse
from collections import defaultdict, deque
from pathlib import Path
from common import HERE, decode, read, save, unconditional_transfer
from analyze import graph
from model import Am2901, X8X02


def paths(edges, start):
    outgoing=defaultdict(set)
    for before,after in edges:outgoing[before].add(after)
    queue=deque([start]);parent={start:None}
    while queue:
        before=queue.popleft()
        for after in sorted(outgoing[before]):
            if after not in parent:parent[after]=before;queue.append(after)
    return parent


def witness(parent, target):
    result=[]
    while target is not None:result.append(target);target=parent[target]
    return list(reversed(result))


def stationary_probe(row,scenario,config):
    if not(row['command']==6 and row['branch']==row['pc'] and unconditional_transfer(row,scenario)):
        raise ValueError('not an unconditional self-branch')
    checks=0
    for av in config['a_values']:
        for q in range(256):
            cpu=Am2901(ram=[(17*i+av)&255 for i in range(16)],q=q);cpu.ram[row['a']]=av
            before=(cpu.ram[:],cpu.q);seq=X8X02(pc=row['pc']);previous=None
            for d in config['external_values']:
                result=cpu.step(row['i'],row['a'],row['b'],d,row['carry'])
                seq.step(row['command'],row['branch'],True)
                if (cpu.ram,cpu.q)!=before or seq.pc!=row['pc'] or seq.pushes or seq.pops:
                    raise ValueError('stationary probe changed state')
                if previous is not None and result!=previous:raise ValueError('external D changed loop flags/output')
                previous=result;checks+=1
    return dict(checks=checks,ram_q_pc_stack_unchanged=True,external_d_does_not_change_alu=True,
        instruction=row,interpretation='Finite component checks plus decoded no-load/self-branch structure; physical external side effects are not modeled.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/terminal-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'terminal-search.json');reports=[]
    for name in config['mappings']:
        root=HERE/f'results/selector-completion/{name}-marked'
        mapping=read(root/'mapping.json');scenario=read(root/'scenario.json');rows=decode(mapping)
        cfg=graph(rows,scenario,include_states=True)
        if cfg['exceptions']:raise ValueError(cfg['exceptions'])
        parent=paths(cfg['state_edges'],(0,()))
        contexts=sorted(s for s in parent if s[0]==config['terminal'])
        probes=[]
        for pc,stack in contexts:
            escape=graph(rows,scenario,start=config['escape_entry'],initial_stack=stack)
            probes.append(dict(stack=stack,arrival_path=[dict(pc=p,stack=s,command=rows[p]['command_name']) for p,s in witness(parent,(pc,stack))],
                escape=dict(states=escape['states'],reached=escape['reached'],exceptions=escape['exceptions'])))
        report=dict(mapping=name,contexts=probes,
            self_branches=[r['pc'] for r in rows if r['command']==6 and r['branch']==r['pc']],
            incoming_branches=[dict(pc=a,target=b,kind=k) for a,b,k in cfg['edges']
                if config['tail_start']<=b<=config['terminal'] and not config['tail_start']<=a<=config['terminal'] and k=='branch'],
            tail_listing=rows[config['tail_start']:config['helper_end']+1],
            stationary=stationary_probe(rows[config['terminal']],scenario,config))
        save(args.out/f'{name}.json',report)
        reports.append(dict(mapping=name,contexts=[r['stack'] for r in probes],self_branches=report['self_branches'],
            incoming_branches=len(report['incoming_branches']),stationary_checks=report['stationary']['checks']))
    save(args.out/'summary.json',dict(configuration=config,profiles=reports,
        interpretation='Common terminal tail is a structural label. Completion, external restart and physical I/O roles are unresolved.'))
    print(reports)

if __name__=='__main__':main()
