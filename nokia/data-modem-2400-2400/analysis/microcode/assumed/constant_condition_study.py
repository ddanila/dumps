"""Bound reset reachability using the integrated scenario's fixed condition inputs."""
import argparse
import copy
import hashlib
from pathlib import Path
from analyze import graph
from common import HERE, decode, read, save
from context_branch_study import witness


def fixed_tests(row, scenario):
    """Leave flags/random free; constrain only scenario-declared fixed inputs.

    Unconditional overrides are applied by graph/witness before this callback.
    Dispatch remains free across every declared table entry.
    """
    condition=scenario['condition'];select=row['select'];mode=condition['mode']
    if mode=='constant':value=condition['value']
    elif mode=='per-select':value=condition['per_select'][select]
    elif mode=='random':return [0,1]
    elif mode=='flags':
        source=condition['sources'][select]
        if source=='constant':value=condition['value']
        elif source=='external':value=scenario['inputs']['external']
        else:return [0,1]
    else:raise ValueError('unsupported condition mode')
    return [value ^ condition['polarity'][select]]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/constant-condition-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'gate-runtime-study.json')
    base=read(HERE/config['scenario']);tables=read(HERE/config['static_scenario'])
    base['branch_tables']=copy.deepcopy(tables['branch_tables'])
    base['dispatch']['tables']=copy.deepcopy(tables['dispatch']['tables'])
    rows=decode(read(HERE/'sequencer.json'));reports={};graphs={}
    runtime=read(HERE/'results/gate-runtime-study/report.json')
    for variant in ('baseline','gated'):
        scenario=copy.deepcopy(base)
        if variant=='gated':scenario['condition']['brt_unconditional_gate']=config['gate']
        free=graph(rows,scenario);fixed=graph(rows,scenario,test_policy=fixed_tests)
        assert not free['exceptions'] and not fixed['exceptions']
        assert set(fixed['reached'])<=set(free['reached'])
        runtime_checks={}
        for key,visited in runtime['visited_unions'].items():
            if key.split(':')[1]==variant:
                assert set(visited)<=set(fixed['reached'])
                runtime_checks[key]=len(visited)
        graphs[variant]=fixed
        reports[variant]=dict(free_words=len(free['reached']),fixed_words=len(fixed['reached']),
            fixed_states=fixed['states'],exceptions=fixed['exceptions'],reached=fixed['reached'],
            excluded_by_fixed_inputs=sorted(set(free['reached'])-set(fixed['reached'])),
            runtime_subset_checks=runtime_checks)
        save(args.out/f'{variant}-scenario.json',scenario)
    free_baseline=set(graph(rows,base)['reached'])
    gained=sorted(set(graphs['gated']['reached'])-free_baseline)
    gated=read(args.out/'gated-scenario.json')
    gate_gains=sorted(set(graphs['gated']['reached'])-set(graphs['baseline']['reached']))
    paths={f'{pc:03X}':witness(rows,gated,pc,test_policy=fixed_tests) for pc in gate_gains}
    free_gated=graph(rows,gated)
    excluded=sorted((set(free_gated['reached'])-free_baseline)-set(gained))
    sources=[Path(__file__),HERE/'analyze.py',HERE/'context_branch_study.py',HERE/'common.py',
             HERE.parent/'model.py',HERE/'sequencer.json',HERE/'gate-runtime-study.json',
             HERE/config['scenario'],HERE/config['static_scenario'],HERE/'results/gate-runtime-study/report.json']
    save(args.out/'report.json',dict(variants=reports,new_words_retained=gained,new_words_excluded=excluded,
        fixed_graph_gate_gains=gate_gains,
        witnesses=paths,source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='Conservative reset graph under fixed condition inputs. ALU flags and dispatch choices remain independent and free. Sequencer witnesses obey fixed inputs but do not establish integrated datapath feasibility or physical wiring.'))
    for variant,r in reports.items():print(variant,r['free_words'],r['fixed_words'],r['fixed_states'])
    print('retained',*[f'{p:03X}' for p in gained]);print('excluded',*[f'{p:03X}' for p in excluded])


if __name__=='__main__':main()
