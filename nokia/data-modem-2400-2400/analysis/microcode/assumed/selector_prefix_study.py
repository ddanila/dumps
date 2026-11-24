"""Compare first-109 selectors across mappings and separate q1/q3 input additions."""
import argparse
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path
from common import HERE, decode, read, save, table_targets, unconditional_transfer
from execute import CarryInput, execute
from defined_condition_fit import load_trace
from model import Am2901, X8X02


def scenario_for(base, tables, config, source, d, inputs=None):
    scenario = copy.deepcopy(base)
    scenario.update(name='first-109 selector comparison', evidence=config['evidence'])
    scenario['initial'] = dict(pc=0,ram=[0]*16,q=0)
    scenario['dispatch']['tables'] = copy.deepcopy(tables['dispatch']['tables'])
    scenario['branch_tables'] = copy.deepcopy(tables['branch_tables'])
    scenario['dispatch'].update(mode='constant', source='scenario', value=2, initial_y=0)
    scenario['branch_tables'][str(0x109)].update(index_source=source,evidence=config['evidence'])
    sequences = {str(0x117):[d,0], str(0x106):[d,0]}
    if inputs is not None:
        sequences.update({str(0x002):[inputs[0]], str(0x076):[inputs[1]]})
    scenario['io']['read'] = dict(mode='pc_sequence',value=d,table=[0],pc_sequences=sequences,
        sequence_end='hold-last',status='stub',evidence=config['evidence'])
    return scenario


def run_prefix(rows, scenario):
    cpu = Am2901(logic_flags=True)
    seq = X8X02()
    carry = CarryInput(scenario['inputs']['carry'])
    previous = dict(zero=None,sign=None,carry=None,overflow=None)
    visits = Counter()
    trace = []
    q_writes = []
    event = None
    depth = maximum = 0
    for cycle in range(64):
        pc = seq.pc
        row = rows[pc]
        before_ram, before_q = cpu.ram[:], cpu.q
        policy = scenario['io']['read']
        sequence = policy['pc_sequences'].get(str(pc))
        d = policy['value'] if sequence is None else sequence[min(visits[pc],len(sequence)-1)]
        visits[pc] += 1
        carry_in = carry.resolve(row)
        result = cpu.step(row['i'],row['a'],row['b'],d,carry_in,0,0)
        carry.observe(result)
        condition = scenario['condition']
        if unconditional_transfer(row,scenario):
            test = 1
        else:
            select = row['select']
            source = condition['sources'][select]
            value = condition['value'] if source == 'constant' else previous[source]
            if value is None:
                value = condition['unknown']
            test = int(bool(value)) ^ condition['polarity'][select]
        branch = row['branch']
        index = None
        if pc == 0x109:
            source = scenario['branch_tables'][str(pc)]['index_source']
            index = dict(scenario=2,y=result['y'],q=cpu.q,previous_y=previous['y'])[source]
            branch = table_targets(scenario['branch_tables'][str(pc)])[index%8]
            event = dict(cycle=cycle,ram=before_ram,q=before_q,previous_y=previous['y'],
                         current_y=result['y'],carry_in=carry_in,index=index,entry=index%8,
                         branch_pc=branch,q_writes=q_writes[:])
        else:
            assert not (row['command']==4 and test and (not row['direct'] or str(pc) in scenario['dispatch']['tables']))
            assert not (row['command']==6 and test and str(pc) in scenario['branch_tables'])
        before = dict(sp=seq.sp,depth=depth)
        if row['command']==5 or row['command']==4 and test:
            depth += 1
            maximum = max(maximum,depth)
        if row['command'] in (2,3):
            depth -= 1
        assert 0 <= depth <= 4 and not row['unused']
        seq.step(row['command'],branch,test)
        if row['i']>>6 in (0,4,6):
            q_writes.append(dict(pc=pc,cycle=cycle,input=d,before=before_q,after=cpu.q))
        trace.append(dict(pc=pc,next_pc=seq.pc,alu=result,test=test,carry_in=carry_in,
            q=cpu.q,registers={str(i):v for i,v in enumerate(cpu.ram) if v!=before_ram[i]},
            stack_before=before,stack_after=dict(sp=seq.sp,depth=depth,values=seq.stack[:])))
        previous = result
        if event is not None and pc == event['branch_pc']:
            assert test==1 and depth==0
            event.update(handler=seq.pc,cycles=cycle+1,max_depth=maximum)
            return dict(event=event,trace=trace,ram=cpu.ram,q=cpu.q,sp=seq.sp,stack=seq.stack)
    raise AssertionError('first handler not reached within prefix bound')


def scalar_prediction(profile,d):
    nonzero = int(d!=0)
    if profile == 'q1':
        return dict(r0=255,q=(2*d)&255,y=(2*d)&255,previous_y=(3*d+nonzero)&255)
    if profile == 'q3':
        return dict(r0=255,q=(2*d)&255,y=(2*d+1)&255,previous_y=(3*d+nonzero)&255)
    if profile in ('q2','q4'):
        return dict(r0=255,q=0,y=1,previous_y=nonzero)
    if profile == 'fitted_original':
        return dict(r0=255-d,q=0,y=(d+1)&255,previous_y=0)
    if profile == 'fitted_swapped':
        return dict(r0=d,q=0,y=0,previous_y=0)
    raise ValueError(profile)


def verify(mapping,scenario,got,out):
    result = execute(mapping,scenario,got['event']['cycles'],mode='integrated',out=out,trace_limit=got['event']['cycles'])
    assert result['clean'] and result['final_state']['pc']==got['event']['handler']
    assert all(result['final_state'][k]==got[k] for k in ('ram','q','sp','stack'))
    actual = load_trace(out)
    assert len(actual)==len(got['trace'])
    for a,b in zip(actual,got['trace']):
        assert all(a[k]==v for k,v in b.items())
    return result['trace_digest']


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/selector-prefix-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'selector-prefix-study.json')
    base,tables=(read(HERE/config[k]) for k in ('scenario','tables'))
    scalar=[];counts=Counter();witnesses=[];digest=hashlib.sha256()
    for profile,path in config['profiles'].items():
        mapping=read(HERE/path);rows=decode(mapping)
        for d in range(256):
            expected=scalar_prediction(profile,d)
            common_prefix=None
            case=dict(profile=profile,d=d,sources={})
            for source in config['sources']:
                scenario=scenario_for(base,tables,config,source,d)
                got=run_prefix(rows,scenario);event=got['event']
                assert (event['ram'][0],event['q'],event['current_y'],event['previous_y'])==(expected['r0'],expected['q'],expected['y'],expected['previous_y'])
                index=2 if source=='scenario' else expected[source]
                assert event['index']==index and event['entry']==index%8
                assert event['handler']==config['handlers'][event['entry']]
                if common_prefix is None:common_prefix=got['trace'][:event['cycle']]
                assert got['trace'][:event['cycle']]==common_prefix
                counts[f'{profile}:{source}:{event["entry"]}']+=1
                if 'state' not in case:
                    case['state']=dict(r0=event['ram'][0],r1=event['ram'][1],r10=event['ram'][10],
                        q=event['q'],current_y=event['current_y'],previous_y=event['previous_y'],
                        cycle=event['cycle'],q_writes=event['q_writes'])
                case['sources'][source]={k:event[k] for k in ('index','entry','branch_pc','handler','cycles','max_depth')}
                digest.update(json.dumps([profile,d,source,got],sort_keys=True,separators=(',',':')).encode())
                if d==1 or profile=='q2' and source=='previous_y' and d==0:
                    out=args.out/f'{profile}-{source}-d{d:02x}'
                    witnesses.append(dict(path=out.name,group='scalar',trace_digest=verify(mapping,scenario,got,out)))
            scalar.append(case)
        print(profile,'1024 scalar prefixes checked',flush=True)
    split_counts=Counter();split_witnesses=[]
    for profile in ('q1','q3'):
        mapping=read(HERE/config['profiles'][profile]);rows=decode(mapping)
        # Changing the two scalar input bytes does not change control policy.
        scenario=scenario_for(base,tables,config,'q',1,[0,0])
        for a in range(256):
            for b in range(256):
                scenario['io']['read']['pc_sequences'][str(0x002)]=[a]
                scenario['io']['read']['pc_sequences'][str(0x076)]=[b]
                got=run_prefix(rows,scenario);event=got['event'];q=(a+b)&255
                assert event['ram'][0]==255 and event['q']==q and event['index']==q
                assert event['current_y']==(q+int(profile=='q3'))&255
                assert event['previous_y']==(q+2)&255
                assert [(w['pc'],w['after']) for w in event['q_writes']]==[(0x002,a),(0x076,q)]
                assert event['handler']==config['handlers'][q%8]
                split_counts[f'{profile}:{q%8}']+=1
                digest.update(json.dumps([profile,a,b,got],sort_keys=True,separators=(',',':')).encode())
                if a==0xa5 and q<8:
                    out=args.out/f'split-{profile}-entry{q}'
                    split_witnesses.append(dict(path=out.name,profile=profile,a=a,b=b,event=event,
                        trace_digest=verify(mapping,scenario,got,out)))
        print(profile,'65536 independent input pairs checked',flush=True)
    sources=[Path(__file__),HERE/'selector-prefix-study.json',HERE/config['scenario'],HERE/config['tables'],
             *(HERE/p for p in config['profiles'].values()),HERE/'common.py',HERE/'execute.py',HERE/'defined_condition_fit.py',HERE.parent/'model.py']
    save(args.out/'report.json',dict(configuration=config,scalar_counts=dict(counts),scalar_runs=scalar,
        split_counts=dict(split_counts),scalar_witnesses=witnesses,split_witnesses=split_witnesses,
        execution_sha256=digest.hexdigest(),
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='Matched zero-reset prefixes under six mappings. Constant-D input creates a parity restriction for q1/q3 Q-based dispatch; independent reads at 002 and 076 remove it. q2/q4 current-Y selector remains constant in the scalar sweep. Handler entry evidence, not complete handler behavior or recovered command wiring.'))


if __name__=='__main__':main()
