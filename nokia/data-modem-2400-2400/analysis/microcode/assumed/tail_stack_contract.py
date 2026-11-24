"""Separate the 2FD return-frame contract from free-condition graph artifacts."""
import argparse
import hashlib
import tempfile
from pathlib import Path
from common import HERE, read, save, decode, unconditional_transfer
from analyze import graph
from context_branch_study import witness
from execute import execute
from defined_condition_fit import load_trace
from model import Am2901


def constant_tests(condition):
    def tests(row,scenario):
        select=row['select']
        return [condition['value']^condition['polarity'][select]] if condition['sources'][select]=='constant' else [0,1]
    return tests


def guard(rows,r0,r5):
    row=rows[0x3bb];cpu=Am2901(logic_flags=True);cpu.ram[0]=r0;cpu.ram[5]=r5
    assert (row['i'],row['a'],row['b'],row['carry'],row['carry_select'])==(201,0,5,0,0)
    result=cpu.step(row['i'],row['a'],row['b'],0,0,0,0)
    assert result['f']==(r5-r0-1)&255 and cpu.ram[5]==result['f']
    assert bool(result['zero'])==(r5==(r0+1)&255)
    return int(not result['zero'])


def replay(directory):
    directory=Path(directory);summary=read(directory/'summary.json')
    with tempfile.TemporaryDirectory() as temporary:
        out=Path(temporary)
        execute(read(directory/'mapping.json'),read(directory/'scenario.json'),summary['requested_cycles'],
                seed=summary['seed'],mode='integrated',out=out,trace_limit=summary['requested_cycles'])
        for name in ('mapping.json','scenario.json','summary.json','trace.jsonl','io.jsonl'):
            assert (directory/name).read_bytes()==(out/name).read_bytes(),name
    trace=load_trace(directory)
    return dict(clean=summary['clean'],stop=summary['stop'],trace_digest=summary['trace_digest'],
        final_stack_depth=summary['stack']['final_depth'],final_pc=summary['final_state']['pc'],
        boundaries=[dict(pc=r['pc'],cycle=r['cycle'],depth=r['stack_before']['depth'],next_pc=r['next_pc'])
                    for r in trace if r['pc'] in (0x2fd,0x2fe,0x2ff,0x220)])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/tail-stack-contract')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'tail-stack-contract.json');rows=decode(read(HERE/config['mapping']))
    scenario=read(HERE/config['scenario']);condition=read(HERE/config['condition_scenario'])['condition']
    assert condition['flag_timing']=='previous' and condition['sources'][0]=='zero' and condition['polarity'][0]==1
    sites={int(pc,16) for pc in config['relaxed_sites']}
    policy=lambda row,s:unconditional_transfer(row,s) and row['pc'] not in sites
    constrained=graph(rows,scenario,unconditional_policy=policy,test_policy=constant_tests(condition))
    path=witness(rows,scenario,0x2ff,unconditional_policy=policy,test_policy=constant_tests(condition),target_stack=())
    assert next(step for step in path if step['pc']==0x2e3)['test']==0
    assert path[-1]['next_pc']==0x2ff and not path[-1]['stack_after']
    contracts=[]
    for depth in range(5):
        result=graph(rows,scenario,start=0x2fd,initial_stack=(1024,)*depth,return_sentinel=1024,include_states=True)
        states={state for edge in result['state_edges'] for state in edge}
        contracts.append(dict(entry_depth=depth,reached_words=len(result['reached']),exceptions=result['exceptions'],
            can_return_to_sentinel=result['terminal_return_reached'],maximum_depth=max(len(stack) for pc,stack in states)))
    assert contracts[1]['exceptions']==[] and contracts[1]['can_return_to_sentinel']
    assert all(c['exceptions'] for c in contracts if c['entry_depth']!=1)
    fallthroughs=sum(guard(rows,r0,r5)==0 for r0 in range(256) for r5 in range(256))
    assert fallthroughs==256
    for pc in range(0x2df,0x2e5):
        row=rows[pc];assert row['i']>>6<2 or row['b'] not in (0,5)
    traces={name:replay(HERE/path) for name,path in config['witnesses'].items()}
    assert traces['empty_entry']['stop']=='unknown stack at PC 2ff' and not traces['empty_entry']['clean']
    assert next(r for r in traces['empty_entry']['boundaries'] if r['pc']==0x2fd)['depth']==0
    assert traces['called_entry']['clean']
    returned=next(r for r in traces['called_entry']['boundaries'] if r['pc']==0x2ff)
    assert returned['depth']==1 and returned['next_pc']==0x213
    sources=[Path(__file__),HERE/'tail-stack-contract.json',HERE/config['mapping'],HERE/config['scenario'],HERE/config['condition_scenario'],HERE/'analyze.py',HERE/'context_branch_study.py',HERE/'execute.py',HERE/'common.py',HERE/'defined_condition_fit.py',HERE.parent/'model.py']
    sources.extend(HERE/path/name for path in config['witnesses'].values() for name in ('mapping.json','scenario.json','summary.json','trace.jsonl','io.jsonl'))
    save(args.out/'report.json',dict(configuration=config,constant_constrained_graph=dict(reached=len(constrained['reached']),exceptions=constrained['exceptions']),
        shortest_constrained_underflow_path=path,local_stack_contracts=contracts,
        guard_checks=65536,guard_fallthrough_pairs=fallthroughs,witnesses=traces,
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}))
    print(dict(constrained_words=len(constrained['reached']),contracts=contracts,guard_checks=65536))


if __name__=='__main__':main()
