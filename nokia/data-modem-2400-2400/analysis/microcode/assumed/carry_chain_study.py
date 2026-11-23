"""Characterize three-add loop 36C–36E and distinguish flag timing locally."""
import argparse
import copy
import hashlib
import json
import random
import tempfile
from collections import Counter
from pathlib import Path
from common import HERE, decode, read, save
from execute import CarryInput, execute
from defined_condition_fit import load_trace
from model import Am2901, X8X02


def prediction(a,inputs):
    first=a+inputs[0];second=(first&255)+inputs[1]+(first>>8)
    third=(second&255)+inputs[2]
    return dict(registers=[first&255,second&255,third&255],y=[a,first&255,second&255],
                carries=[first>>8,second>>8,third>>8])


def fixtures(config):
    for a in range(256):
        for d in range(256):yield a,[d]*3
    rng=random.Random(config['seed'])
    for _ in range(config['independent_cases']):yield rng.randrange(256),[rng.randrange(256) for _ in range(3)]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/carry-chain-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'carry-chain-study.json');root=HERE/config['base']
    mapping=read(root/'mapping.json');base=read(root/'scenario.json');rows=decode(mapping)
    assert [rows[p]['command'] for p in (0x36c,0x36d,0x36e)]==[5,1,2]
    counts=Counter();digest=hashlib.sha256();witnesses=[];seen=set();disagreements=0
    for index,(a,inputs) in enumerate(fixtures(config)):
        expected=prediction(a,inputs)
        if index<65536 and expected['carries'][1]!=expected['carries'][2]:disagreements+=1
        for timing,flag_index in [('previous',1),('current',2)]:
            ram=config['initial_ram'][:];ram[0]=a
            cpu=Am2901(ram=ram[:],q=config['initial_q'],logic_flags=True);seq=X8X02(pc=0x36c)
            carry=CarryInput(base['inputs']['carry']);repeat=bool(expected['carries'][flag_index]);trace=[];snapshots=[]
            for iteration in range(2 if repeat else 1):
                results=[]
                for offset in range(3):
                    pc=0x36c+offset;assert seq.pc==pc;row=rows[pc]
                    result=cpu.step(row['i'],row['a'],row['b'],inputs[offset],carry.resolve(row),0,0);carry.observe(result);results.append(result)
                    test=results[flag_index]['carry'] if offset==2 else 0
                    seq.step(row['command'],row['branch'],test)
                    trace.append(dict(pc=pc,alu=result,q=cpu.q,ram=cpu.ram[:],test=test))
                assert [r['y'] for r in results]==expected['y']
                assert [r['carry'] for r in results]==expected['carries']
                snapshots.append([seq.pc,seq.sp,seq.stack[:],cpu.ram[:],cpu.q,carry.previous,results[-1]])
            wanted=ram[:];wanted[1:4]=expected['registers']
            assert cpu.ram==wanted and cpu.q==config['initial_q']
            assert seq.pc==(0x36c if repeat else 0x36f) and seq.pushes==seq.pops
            if repeat:assert snapshots[0]==snapshots[1]
            group='constant' if index<65536 else 'independent'
            counts[f'{timing}:{group}:'+('repeat' if repeat else 'exit')]+=1
            digest.update(json.dumps([a,inputs,timing,seq.pc,cpu.ram,expected],sort_keys=True).encode())
            key=(timing,group,tuple(expected['carries']))
            if key not in seen:
                seen.add(key);s=copy.deepcopy(base);s['condition']['flag_timing']=timing
                s['initial']=dict(pc=0x36c,ram=ram,q=config['initial_q'])
                s['io']['read']=dict(mode='pc_table',value=0,table=[0],pc_values={str(0x36c+i):v for i,v in enumerate(inputs)},status='stub',evidence=config['evidence'])
                out=args.out/f'witness-{len(witnesses):02d}'
                run=execute(mapping,s,len(trace),mode='integrated',out=out,trace_limit=len(trace))
                assert run['clean'] and run['final_state']['pc']==seq.pc and run['final_state']['ram']==wanted and run['final_state']['q']==cpu.q
                witnesses.append(dict(a=a,inputs=inputs,timing=timing,expected=expected,repeat=repeat,trace=trace,integrated_trace_digest=run['trace_digest']))
    reset_runs=[]
    with tempfile.TemporaryDirectory() as temporary:
        for d in config['reset_values']:
            s=copy.deepcopy(base);s['initial']=dict(pc=0,ram=[0]*16,q=0)
            s['branch_tables']['265']['index_source']='y'
            s['io']['read']=dict(mode='constant',value=d,table=[0],status='stub',evidence=config['evidence'])
            out=args.out/f'reset-d{d:02x}' if d in config['reset_witnesses'] else Path(temporary)
            run=execute(mapping,s,config['reset_cycles'],mode='integrated',out=out,trace_limit=config['reset_cycles'])
            trace=load_trace(out);ram=[0]*16;writer=None;entry=None;chain=[]
            for t in trace:
                if t['pc']==0x36c and entry is None:entry=dict(cycle=t['cycle'],ram=ram[:],writer=writer)
                if entry is not None and len(chain)<3:chain.append(t)
                for i,v in t['registers'].items():ram[int(i)]=v
                op=rows[t['pc']]
                if op['i']>>6>=2 and op['b']==0:writer=dict(pc=t['pc'],cycle=t['cycle'])
            assert run['clean'] and entry['ram'][0]==255-d and entry['writer']['pc']==0x74
            expected=prediction(255-d,[d]*3)
            assert [t['pc'] for t in chain]==[0x36c,0x36d,0x36e]
            assert [t['alu']['carry'] for t in chain]==expected['carries']
            assert [t['alu']['y'] for t in chain]==expected['y']
            assert expected['carries'][1]==1 and chain[-1]['next_pc']==0x36c
            assert expected['carries'][2]==int(d>=128)
            reset_runs.append(dict(d=d,entry=entry,prediction=expected,chain=chain,trace_digest=run['trace_digest']))
    sources=[Path(__file__),HERE/'carry-chain-study.json',HERE/'execute.py',HERE/'common.py',HERE.parent/'model.py',root/'mapping.json',root/'scenario.json']
    save(args.out/'report.json',dict(configuration=config,counts=dict(counts),reset_runs=reset_runs,constant_input_timing_disagreements=disagreements,witnesses=witnesses,
        execution_sha256=digest.hexdigest(),source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='36C–36E chains three byte additions, forwards first carry to second add, and preserves R0/Q. Previous flag repeats on middle carry, current flag on last carry. No physical operand/output channel identified.'))
    print(dict(counts),'timing disagreements',disagreements,'witnesses',len(witnesses))


if __name__=='__main__':main()
