"""Characterize q2's 3C0 transform wrapper with real previous-zero loop control."""
import argparse
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path
from common import HERE, decode, read, save, unconditional_transfer
from execute import CarryInput, execute
from defined_condition_fit import load_trace
from model import Am2901, X8X02


def rotated(x, y, entry):
    return [(x,y), (-y,x), (-x,-y), (y,-x)][entry]


def prediction(ram, entry):
    x = ram[10] | ram[11] << 8
    y = ram[12] | ram[13] << 8
    a, b = (v & 65535 for v in rotated(x,y,entry))
    result = ram[:]
    result[1] = ram[0]
    result[4:8] = [a&255, a>>8, b&255, b>>8]
    return dict(returned=b < 256, ram=result, output=[a,b])


def probe(rows, base, ram, q, d, entry):
    cpu = Am2901(ram=ram[:], q=q, logic_flags=True)
    seq = X8X02(pc=0x13d)
    carry = CarryInput(base['inputs']['carry'])
    previous = dict(zero=0, carry=0, sign=0, overflow=0)
    seen = {}
    trace = []
    while len(trace) < 32:
        if seq.pc == 0x13e:
            return dict(returned=True, pc=seq.pc, ram=cpu.ram, q=cpu.q, cycles=len(trace), period=None, trace=trace)
        if seq.pc == 0x3c0:
            key = json.dumps([seq.pc,seq.sp,seq.stack,cpu.ram,cpu.q,previous,carry.previous],sort_keys=True)
            if key in seen:
                return dict(returned=False, pc=seq.pc, ram=cpu.ram, q=cpu.q, cycles=len(trace), period=len(trace)-seen[key], trace=trace)
            seen[key] = len(trace)
        pc = seq.pc
        row = rows[pc]
        result = cpu.step(row['i'], row['a'], row['b'], d, carry.resolve(row), 0, 0)
        carry.observe(result)
        select = row['select']
        source = base['condition']['sources'][select]
        value = base['condition']['value'] if source == 'constant' else previous[source]
        test = 1 if unconditional_transfer(row,base) else int(bool(value)) ^ base['condition']['polarity'][select]
        branch = 0x3c5 + entry*4 if pc == 0x3c2 else row['branch']
        seq.step(row['command'],branch,test)
        trace.append(dict(pc=pc,next_pc=seq.pc,alu=result,test=test))
        previous = result
    raise AssertionError('neither return nor exact repetition')


def fixtures(config):
    for entry in range(4):
        for v in range(65536):
            other = (v*257+0x1234)&65535
            x,y = (other,v) if entry in (0,2) else (v,other)
            yield 'controlling-word',entry,x,y,0x55,0x5a
    for entry in range(4):
        for x in config['boundary_words']:
            for y in config['boundary_words']:
                for q in (0,0x55,255):
                    yield 'boundary-pairs',entry,x,y,q,255-q


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/q2-transform-loop-study')
    args = parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    config = read(HERE/'q2-transform-loop-study.json')
    mapping = read(HERE/config['mapping'])
    base = read(HERE/config['scenario'])
    rows = decode(mapping)
    assert base['condition']['flag_timing'] == 'previous'
    assert base['dispatch']['tables'][str(0x3c2)]['base'] == 0x3c5
    counts = Counter()
    digest = hashlib.sha256()
    witnesses = []
    seen = set()
    for group,entry,x,y,q,d in fixtures(config):
        ram = config['initial_ram'][:]
        ram[10:14] = [x&255,x>>8,y&255,y>>8]
        want = prediction(ram,entry)
        got = probe(rows,base,ram,q,d,entry)
        assert got['returned'] == want['returned'] and got['ram'] == want['ram'] and got['q'] == q
        assert got['cycles'] == (10 if want['returned'] else 17)
        if not want['returned']:
            assert got['period'] == 8
        counts[f'{group}:{entry}:'+('return' if want['returned'] else 'repeat')] += 1
        digest.update(json.dumps([group,entry,x,y,q,d,got['pc'],got['cycles'],got['ram']],separators=(',',':')).encode())
        key = (entry,want['returned'],want['output'][1] == 0)
        if key not in seen:
            seen.add(key)
            scenario = copy.deepcopy(base)
            scenario['initial'] = dict(pc=0x13d,ram=ram,q=q)
            scenario['dispatch']['value'] = entry
            scenario['io']['read'] = dict(mode='constant',value=d,table=[0],status='stub',evidence=config['evidence'])
            result = execute(mapping,scenario,got['cycles'],mode='integrated',out=args.out/f'local-{len(witnesses):02d}',trace_limit=got['cycles'])
            assert result['clean'] and all(result['final_state'][k] == got[k] for k in ('pc','ram','q'))
            trace = load_trace(args.out/f'local-{len(witnesses):02d}')
            assert [(e['pc'],e['next_pc'],e['alu'],e['test']) for e in trace] == [(e['pc'],e['next_pc'],e['alu'],e['test']) for e in got['trace']]
            witnesses.append(dict(entry=entry,x=x,y=y,q=q,d=d,prediction=want,observed=got,trace_digest=result['trace_digest']))
    # Reach the wrapper through the accumulator gate, retaining its actual flags.
    caller_runs = []
    for entry in range(4):
        for v in config['boundary_words']:
            ram = config['initial_ram'][:]
            ram[7] = 2
            ram[10:14] = [v&255,v>>8,v&255,v>>8]
            scenario = copy.deepcopy(base)
            scenario['initial'] = dict(pc=0x133,ram=ram,q=1)
            scenario['dispatch']['value'] = entry
            scenario['io']['read'] = dict(mode='constant',value=255,table=[0],status='stub',evidence=config['evidence'])
            result = execute(mapping,scenario,64,mode='integrated',out=args.out/f'caller-{entry}-{v:04x}',trace_limit=64)
            trace = load_trace(args.out/f'caller-{entry}-{v:04x}')
            gate = next(e for e in trace if e['pc'] == 0x13a)
            assert result['clean'] and gate['next_pc'] == 0x13d
            assert not set(result['visited']) & {0x13b,0x13c,0x3d5,0x3ea}
            expected = prediction(ram,entry)
            returned = any(e['pc'] == 0x3c4 for e in trace)
            assert returned == expected['returned']
            assert (result['final_state']['pc'] == 0x84) == returned
            final_ram = expected['ram'][:]
            final_ram[0] = final_ram[1] = 1
            final_ram[2] = ram[3]
            final_ram[3] = 255-ram[1]
            assert result['final_state']['ram'] == final_ram
            assert result['final_state']['q'] == 0
            caller_runs.append(dict(entry=entry,v=v,returned=returned,gate=gate,final_state=result['final_state'],trace_digest=result['trace_digest']))
    sources = [Path(__file__),HERE/'q2-transform-loop-study.json',HERE/config['mapping'],HERE/config['scenario'],HERE/'execute.py',HERE/'common.py',HERE.parent/'model.py']
    save(args.out/'report.json',dict(configuration=config,counts=dict(counts),witnesses=witnesses,caller_runs=caller_runs,execution_sha256=digest.hexdigest(),
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='q2 wrapper 3C0 repeatedly computes a fixed quarter-turn into R4–R7 and exits only when the second output high byte is zero. Nonzero low bytes may return; failed fixed-index tests repeat exactly after eight instructions. Caller fixtures start with nonzero Q locally, not from reset.'))
    print(dict(counts),'local witnesses',len(witnesses),'caller runs',len(caller_runs))


if __name__ == '__main__':
    main()
