"""Screen direct D-driven accumulators and their visits in saved q3 runs."""
import argparse
from collections import defaultdict
import hashlib
import json
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ASSUMED=HERE.parent/'assumed'
sys.path.insert(0,str(ASSUMED))
from common import decode, read  # noqa: E402
from analyze import graph  # noqa: E402

TRACES={
    'q3-rom-feedback':'plan-validation/q3-rom-feedback/trace.jsonl',
    'q3-rom-carry-f9':'rom-carry-replies/reply-f9/trace.jsonl',
    'q3-frame-05':'frame-dac-bridge/frame-05/trace.jsonl',
    'q3-frame-85':'frame-dac-bridge/frame-85/trace.jsonl',
}


def cyclic_components(edges):
    """Tarjan SCCs over (PC, return-stack) states, retaining actual cycles."""
    adjacent=defaultdict(set)
    for before,after in edges:
        adjacent[(before[0],tuple(before[1]))].add((after[0],tuple(after[1])))
    sys.setrecursionlimit(max(10000,2*len(adjacent)+100))
    index=0;indices={};low={};stack=[];on_stack=set();cycles=[]
    def visit(node):
        nonlocal index
        indices[node]=low[node]=index;index+=1
        stack.append(node);on_stack.add(node)
        for target in adjacent[node]:
            if target not in indices:
                visit(target);low[node]=min(low[node],low[target])
            elif target in on_stack:
                low[node]=min(low[node],indices[target])
        if low[node]==indices[node]:
            component=[]
            while True:
                member=stack.pop();on_stack.remove(member);component.append(member)
                if member==node:break
            if len(component)>1 or node in adjacent[node]:cycles.append(component)
    for node in list(adjacent):
        if node not in indices:visit(node)
    return cycles


def run():
    profiles=read(ASSUMED/'program-reading.json')['profiles']
    candidates={};mapping_sha={}
    for name,rel in profiles.items():
        mapping_sha[name]=hashlib.sha256((ASSUMED/rel).read_bytes()).hexdigest()
        rows=decode(read(ASSUMED/rel))
        direct=[]
        for row in rows:
            if row['unused'] or 'i' not in row:continue
            ins=row['i'];source=ins&7;function=(ins>>3)&7;dest=(ins>>6)&7
            kind=('D+Q to Q' if source==6 and dest==0 else
                  'D+A to same RAM register' if source==5 and dest in (2,3)
                  and row.get('a')==row.get('b') else None)
            if function==0 and kind:
                direct.append(dict(pc=f'{row["pc"]:03X}',kind=kind))
        candidates[name]=direct
    q3_pcs={int(row['pc'],16) for row in candidates['q3']}
    scenario_path=ASSUMED/read(ASSUMED/'program-reading.json')['scenario']
    scenario=read(scenario_path)
    flow=graph(decode(read(ASSUMED/profiles['q3'])),scenario,include_states=True)
    assert not flow['exceptions'],flow['exceptions']
    cycles=cyclic_components(flow['state_edges'])
    cyclic_pcs={state[0] for component in cycles for state in component}
    assert not cyclic_pcs&q3_pcs
    trace_results={};source_sha={}
    for name,rel in TRACES.items():
        path=ASSUMED/'results'/rel
        source_sha[name]=hashlib.sha256(path.read_bytes()).hexdigest()
        visits={}
        with path.open() as stream:
            for line in stream:
                row=json.loads(line);pc=row['pc']
                if pc in q3_pcs:
                    key=f'{pc:03X}'
                    visits.setdefault(key,[]).append(dict(cycle=row['cycle'],q=row['q']))
        trace_results[name]=visits
    return dict(status='static capability and scoped dynamic visit screen',
        candidates=candidates,traces=trace_results,trace_sha256=source_sha,
        mapping_sha256=mapping_sha,
        control_flow=dict(scenario=str(scenario_path.relative_to(ASSUMED)),
                          scenario_sha256=hashlib.sha256(scenario_path.read_bytes()).hexdigest(),
                          state_count=flow['states'],state_edge_count=len(flow['state_edges']),
                          cyclic_component_count=len(cycles),
                          cyclic_pc_count=len(cyclic_pcs),
                          direct_accumulators_in_cycles=sorted(f'{pc:03X}' for pc in cyclic_pcs&q3_pcs)),
        interpretation='The four named q3 traces visit only startup direct D-to-Q add candidates, each once. The declared q3 stack-aware control-flow graph has no cyclic component containing a one-word direct D-driven accumulator.',
        limitations=['A one-word direct accumulator is not necessary; multiword or other-source phase updates remain possible.',
                     'D is an emulator input and its physical source is unknown.',
                     'Candidate field maps are alternatives; this is not one recovered hardware decode.',
                     'The graph covers only the declared dispatch and branch scenario and overapproximates run-time branch feasibility.',
                     'The trace screen covers only the four named q3 runs.'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/phase-add-screen.json')
    args=parser.parse_args();result=run();args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print({name:len(rows) for name,rows in result['candidates'].items()})
    print({name:{pc:len(v) for pc,v in rows.items()} for name,rows in result['traces'].items()})


if __name__=='__main__':main()
