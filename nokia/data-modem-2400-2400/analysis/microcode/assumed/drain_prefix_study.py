"""Compose the two drain calls and input preparation at 304–308."""
import argparse
import copy
import hashlib
import json
import random
from collections import Counter
from pathlib import Path
from common import HERE, decode, read, save, unconditional_transfer
from execute import CarryInput, execute
from defined_condition_fit import load_trace
from model import Am2901, X8X02


def prediction(ram,q,values,profile):
    masked = ram[0]&q if profile == 'fitted_original' else 0
    iterations = 1+((masked>>1).bit_length()+1)//2
    out = ram[:]
    out[0] = out[5] = 0
    out[12] = values[1]
    out[13] = values[4] if profile == 'fitted_original' else ram[11]
    out[4] = values[5] if profile == 'fitted_original' else ram[10]
    return dict(ram=out,q=0,cycles=26+2*iterations,first_r5=((ram[0]+masked+1)&255)>>1)


def probe(rows,base,ram,q,values):
    cpu = Am2901(ram=ram[:],q=q,logic_flags=True)
    seq = X8X02(pc=0x304)
    carry = CarryInput(base['inputs']['carry'])
    previous = dict(zero=0,carry=0,sign=0,overflow=0)
    trace = []
    reads = Counter()
    first_r5 = None
    for cycle in range(40):
        if seq.pc == 0x309:
            return dict(pc=seq.pc,ram=cpu.ram,q=cpu.q,cycles=cycle,first_r5=first_r5,trace=trace)
        pc = seq.pc
        row = rows[pc]
        d = values[min(reads[pc],1)] if pc == 0x311 else values[pc-0x314+2] if 0x314<=pc<=0x317 else 0x5a
        reads[pc] += 1
        # The differing first R5 value has no selected consumer in this prefix.
        source = row['i']&7
        assert not (row['a']==5 and source in (0,1,4,5))
        assert not (row['b']==5 and source in (1,3))
        assert not (row['a']==5 and row['i']>>6==2)
        result = cpu.step(row['i'],row['a'],row['b'],d,carry.resolve(row),0,0)
        carry.observe(result)
        select = row['select']
        source = base['condition']['sources'][select]
        value = base['condition']['value'] if source == 'constant' else previous[source]
        test = 1 if unconditional_transfer(row,base) else int(bool(value)) ^ base['condition']['polarity'][select]
        seq.step(row['command'],row['branch'],test)
        trace.append(dict(pc=pc,next_pc=seq.pc,alu=result,test=test,q=cpu.q))
        previous = result
        if seq.pc == 0x305:
            first_r5 = cpu.ram[5]
    raise AssertionError('prefix failed to return')


def fixtures(config):
    for a in range(256):
        for q in range(256):
            ram = config['initial_ram'][:]
            ram[0] = a
            yield 'ram0-q',ram,q,[0x5a]*6
    rng = random.Random(config['seed'])
    for _ in range(config['independent_cases']):
        yield 'independent', [rng.randrange(256) for _ in range(16)],rng.randrange(256),[rng.randrange(256) for _ in range(6)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/drain-prefix-study')
    args = parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    config = read(HERE/'drain-prefix-study.json')
    profiles = read(HERE/'program-reading.json')['profiles']
    base = read(HERE/config['scenario'])
    assert base['condition']['flag_timing']=='previous'
    assert base['condition']['sources'][5]=='constant' and base['condition']['value']==0 and base['condition']['polarity'][5]==1
    counts = Counter()
    digest = hashlib.sha256()
    witnesses = []
    seen = set()
    for profile in ('q2','fitted_original'):
        mapping = read(HERE/profiles[profile])
        rows = decode(mapping)
        assert rows[0x302]['select']==5 and rows[0x302]['branch']==0x319
        for group,ram,q,values in fixtures(config):
            want = prediction(ram,q,values,profile)
            got = probe(rows,base,ram,q,values)
            assert all(got[k]==want[k] for k in ('ram','q','cycles','first_r5'))
            counts[f"{profile}:{group}:{got['cycles']}"] += 1
            digest.update(json.dumps([profile,group,ram,q,values,got['ram'],got['cycles'],got['first_r5']],separators=(',',':')).encode())
            key = (profile,group,got['cycles'],got['first_r5']==0)
            if key not in seen:
                seen.add(key)
                scenario = copy.deepcopy(base)
                scenario['initial'] = dict(pc=0x304,ram=ram,q=q)
                scenario['io']['read'] = dict(mode='pc_sequence',value=0x5a,table=[0],pc_sequences={'785':values[:2],**{str(0x314+i):[values[i+2]] for i in range(4)}},sequence_end='hold-last',status='stub',evidence=config['evidence'])
                out = args.out/f'local-{len(witnesses):02d}'
                result = execute(mapping,scenario,got['cycles'],mode='integrated',out=out,trace_limit=got['cycles'])
                assert result['clean'] and all(result['final_state'][k]==got[k] for k in ('pc','ram','q'))
                trace = load_trace(out)
                assert [(e['pc'],e['next_pc'],e['alu'],e['test'],e['q']) for e in trace]==[(e['pc'],e['next_pc'],e['alu'],e['test'],e['q']) for e in got['trace']]
                witnesses.append(dict(profile=profile,group=group,initial_ram=ram,initial_q=q,values=values,prediction=want,observed=got,trace_digest=result['trace_digest']))
    sources = [Path(__file__),HERE/'drain-prefix-study.json',HERE/'program-reading.json',HERE/config['scenario'],HERE/'execute.py',HERE/'common.py',HERE.parent/'model.py']+[HERE/profiles[p] for p in ('q2','fitted_original')]
    save(args.out/'report.json',dict(configuration=config,counts=dict(counts),witnesses=witnesses,execution_sha256=digest.hexdigest(),source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},interpretation='Two ordinary 30B calls erase the first retained R5 difference before any selected consumer. Q/R0/R5 end zero; R12 keeps the second 311 input. Preparation then differs by mapping. Existing select-5 stub branches from 302 to 319, so these are local caller fixtures, not reset paths.'))
    print('cases',sum(counts.values()),'witnesses',len(witnesses),dict(counts))


if __name__ == '__main__':main()
