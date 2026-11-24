"""Separate a releasable handler-2 poll from a preserved-state transform loop."""
import argparse
import copy
import hashlib
import shutil
import tempfile
from pathlib import Path
from common import HERE, decode, read, save, table_targets, unconditional_transfer
from execute import execute
from defined_condition_fit import load_trace
from handler_timing_study import scenario_for_case, classify
from model import Am2901


def current_loop_invariant(rows, scenario):
    table = scenario['dispatch']['tables'][str(0x3ec)]
    assert table_targets(table) == [0x3ef,0x3f3,0x3f7,0x3fb]
    body = [0x3ea,0x3eb,0x3ec,0x3ed, *range(0x3ef,0x3ff)]
    for pc in body:
        row = rows[pc]
        destination = row['i'] >> 6
        assert destination not in (0,4,6), 'loop writes Q'
        assert destination == 1 or row['b'] != 0, 'loop writes R0'
    test = rows[0x3ed]
    assert test['i'] == 0x60 and test['a'] == 0 and test['command'] == 2 and test['select'] == 0
    condition = scenario['condition']
    assert condition['mode']=='flags' and condition['flag_timing']=='current'
    assert condition['sources'][0]=='zero' and condition['polarity'][0]==1
    assert rows[0x3ea]['command']==5 and rows[0x3eb]['command']==1
    assert rows[0x3ec]['command']==4 and rows[0x3ec]['select']==0
    assert unconditional_transfer(rows[0x3ec],scenario)
    for entry in table_targets(table):
        assert [rows[p]['command'] for p in range(entry,entry+4)] == [1,1,1,3]
    return dict(preserved=['R0','Q'], repeat_predicate='(R0 & Q) != 0',
                tables=table_targets(table), independent_of='all later D values and all choices among the four table entries')


def prestate(trace, target):
    ram=[0]*16; q=0
    for row in trace:
        if row['pc']==target:
            return dict(cycle=row['cycle'],ram=ram,q=q,stack=row['stack_before'])
        for register,value in row['registers'].items():ram[int(register)]=value
        q=row['q']
    raise AssertionError(f'missing {target:03X}')


def verify_poll_bytes(rows, state):
    row=rows[0x1ec]
    assert (row['i'],row['a'],row['b'],row['carry'],row['carry_select'])==(133,4,3,0,0)
    following=rows[0x1ed]
    assert following['command']==2 and following['select']==0
    successes=[]
    for d in range(256):
        cpu=Am2901(logic_flags=True);cpu.ram=state['ram'][:];cpu.q=state['q']
        result=cpu.step(row['i'],row['a'],row['b'],d,0,0,0)
        assert result['f']==(d+state['ram'][4])&255
        assert cpu.ram[4]==state['ram'][4] and cpu.q==state['q']
        if result['zero']:successes.append(d)
    assert successes==[(-state['ram'][4])&255]
    return successes[0]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/handler-reply-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'handler-reply-study.json')
    runs=[];states=[];invariants={};witnesses=[]
    with tempfile.TemporaryDirectory() as temporary:
        out=Path(temporary)/'run'
        for profile,path in config['profiles'].items():
            mapping=read(HERE/path);rows=decode(mapping)
            for q in range(2,256,8):
                baseline=scenario_for_case(config,profile,'previous','plp',q)
                result=execute(mapping,baseline,config['cycles'],mode='integrated',out=out,trace_limit=config['cycles'])
                assert result['clean'] and not result['unused_word_executions']
                original=load_trace(out);state=prestate(original,0x1ec)
                expected_r4=(q-2)&255 if profile=='q1' else 254
                assert state['ram'][4]==expected_r4 and state['ram'][12]==expected_r4
                reply=verify_poll_bytes(rows,state)
                states.append(dict(profile=profile,input_sum=q,poll=state,reply=reply))
                for delay in config['delays']:
                    scenario=copy.deepcopy(baseline)
                    sequence=[1] if delay is None else [1]*delay+[reply]
                    scenario['io']['read']['pc_sequences'][str(0x1ec)]=sequence
                    scenario['name']=f'handler reply {profile} Q={q:02X} delay={delay}'
                    result=execute(mapping,scenario,config['cycles'],mode='integrated',out=out,trace_limit=config['cycles'])
                    assert result['clean'] and not result['unused_word_executions']
                    trace=load_trace(out)
                    assert trace[:state['cycle']]==original[:state['cycle']]
                    finding=classify(trace,scenario)
                    returns=[r['cycle'] for r in trace if r['pc']==0x1ee]
                    if delay is None:
                        assert finding['outcome']=='repeat' and not returns
                    else:
                        assert finding['outcome']=='terminal'
                        assert returns==[state['cycle']+2*delay+2]
                        assert finding['first_terminal']==state['cycle']+32+2*delay
                        assert result['final_state']['ram'][12]==expected_r4
                    case=dict(profile=profile,input_sum=q,delay=delay,reply=reply,**finding,
                              first_return=returns[0] if returns else None,trace_digest=result['trace_digest'])
                    runs.append(case)
                    if q in (2,250) and delay in (None,7):
                        name=f'{profile}-{q:02x}-{delay}'
                        shutil.copytree(out,args.out/name,dirs_exist_ok=True)
                        witnesses.append(dict(path=name,**case))
                current=scenario_for_case(config,profile,'current','blt',q)
                invariants[profile]=current_loop_invariant(rows,current)
                result=execute(mapping,current,config['cycles'],mode='integrated',out=out,trace_limit=config['cycles'])
                assert result['clean'] and not result['unused_word_executions']
                trace=load_trace(out);entry=prestate(trace,0x3ea)
                assert entry['ram'][0]==q and entry['q']==q
                assert all(r['pc']!=0x1ec for r in trace)
                states[-1]['current_transform_entry']=entry
                states[-1]['current_trace_digest']=result['trace_digest']
            print(profile,'32 reset states, 128 reply runs and 8192 byte checks',flush=True)
    sources=[Path(__file__),HERE/'handler-reply-study.json',HERE/'handler_timing_study.py',HERE/'selector_prefix_study.py',HERE/'execute.py',HERE/'common.py',HERE/'defined_condition_fit.py',HERE.parent/'model.py',HERE/config['scenario'],HERE/config['tables'],*(HERE/p for p in config['profiles'].values())]
    save(args.out/'report.json',dict(configuration=config,runs=runs,states=states,current_loop_invariants=invariants,
        witnesses=witnesses,local_byte_checks=16384,full_reset_runs=384,
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}))


if __name__=='__main__':main()
