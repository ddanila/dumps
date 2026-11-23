"""Check recurrences and real loop exits in q2 wrappers 3D5 and 3EA."""
import argparse
import copy
import hashlib
import json
import tempfile
from collections import Counter
from pathlib import Path
from common import HERE, decode, read, save, unconditional_transfer
from execute import CarryInput, execute
from defined_condition_fit import load_trace
from model import Am2901, X8X02


def transform(ram, wrapper, entry):
    x = ram[10] | ram[11] << 8
    y = ram[12] | ram[13] << 8
    if wrapper in (0x3c0,0x3d5):
        a,b = [(x,y),(-y,x),(-x,-y),(y,-x)][entry]
        destination,scratch = (4,1) if wrapper == 0x3c0 else (8,2)
    else:
        a,b = [(x,x),(-y,x),(-x,x),(y,-x)][entry]
        destination,scratch = 12,3
    a,b = a&65535,b&65535
    out = ram[:]
    out[scratch] = ram[0]
    out[destination:destination+4] = [a&255,a>>8,b&255,b>>8]
    return out


def outcome(x,y,wrapper,entry):
    small = lambda v: (v&65535)<256
    if wrapper == 0x3d5:
        if entry == 0: returned = small(y)
        elif entry == 1: returned = small(x)
        elif entry == 2: returned = small(-y)
        else: returned = small(-x) or small(x)
        iterations = 2 if returned and entry == 3 and not small(-x) else 1
        period = 16 if entry == 3 and x != 0x8000 else 8
    else:
        returned = small(-x) if entry == 3 else small(x)
        iterations = 1
        period = 16 if entry == 1 and y not in (0,0x8000) else 8
    return dict(returned=returned,iterations=iterations if returned else None,period=None if returned else period)


def probe(rows,base,ram,q,d,wrapper,entry):
    call = 0x13c if wrapper == 0x3d5 else 0x13b
    cpu = Am2901(ram=ram[:],q=q,logic_flags=True)
    seq = X8X02(pc=call)
    carry = CarryInput(base['inputs']['carry'])
    previous = dict(zero=0,carry=0,sign=0,overflow=0)
    seen = {}
    trace = []
    checkpoints = []
    reference = ram[:]
    while len(trace)<40:
        if seq.pc == call+1:
            return dict(returned=True,pc=seq.pc,ram=cpu.ram,q=cpu.q,cycles=len(trace),period=None,trace=trace,checkpoints=checkpoints)
        if seq.pc == wrapper:
            key = json.dumps([seq.pc,seq.sp,seq.stack,cpu.ram,cpu.q,previous,carry.previous],sort_keys=True)
            if key in seen:
                return dict(returned=False,pc=seq.pc,ram=cpu.ram,q=cpu.q,cycles=len(trace),period=len(trace)-seen[key],trace=trace,checkpoints=checkpoints)
            seen[key] = len(trace)
        pc = seq.pc
        row = rows[pc]
        result = cpu.step(row['i'],row['a'],row['b'],d,carry.resolve(row),0,0)
        carry.observe(result)
        select = row['select']
        source = base['condition']['sources'][select]
        value = base['condition']['value'] if source == 'constant' else previous[source]
        test = 1 if unconditional_transfer(row,base) else int(bool(value)) ^ base['condition']['polarity'][select]
        branch = wrapper+5+entry*4 if pc == wrapper+2 else row['branch']
        seq.step(row['command'],branch,test)
        trace.append(dict(pc=pc,next_pc=seq.pc,alu=result,test=test))
        previous = result
        if pc == wrapper+3:
            reference = transform(reference,wrapper,entry)
            assert cpu.ram == reference and cpu.q == q
            checkpoints.append(reference[:])
    raise AssertionError('no return or repeated complete state')


def fixtures(config):
    for wrapper in (0x3d5,0x3ea):
        for entry in range(4):
            for v in range(65536):
                other = (v*257+0x1234)&65535
                x,y = (other,v) if wrapper == 0x3d5 and entry in (0,2) else (v,other)
                yield 'word-sweep',wrapper,entry,x,y,0x55,0x5a
            for x in config['boundary_words']:
                for y in config['boundary_words']:
                    for q in (0,0x55,255):
                        yield 'boundaries',wrapper,entry,x,y,q,255-q


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/q2-overwrite-study')
    args = parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    config = read(HERE/'q2-overwrite-study.json')
    mapping = read(HERE/config['mapping'])
    base = read(HERE/config['scenario'])
    rows = decode(mapping)
    assert base['condition']['flag_timing'] == 'previous'
    counts = Counter()
    digest = hashlib.sha256()
    witnesses = []
    seen = set()
    for group,wrapper,entry,x,y,q,d in fixtures(config):
        ram = config['initial_ram'][:]
        ram[10:14] = [x&255,x>>8,y&255,y>>8]
        want = outcome(x,y,wrapper,entry)
        got = probe(rows,base,ram,q,d,wrapper,entry)
        assert got['returned'] == want['returned'] and got['period'] == want['period']
        if want['returned']:
            assert len(got['checkpoints']) == want['iterations']
            assert got['cycles'] == 8*want['iterations']+2
        kind = f"return-{want['iterations']}" if want['returned'] else f"repeat-{want['period']}"
        counts[f'{group}:{wrapper:03x}:{entry}:{kind}'] += 1
        digest.update(json.dumps([group,wrapper,entry,x,y,q,d,got['pc'],got['ram'],got['cycles'],got['period']],separators=(',',':')).encode())
        key = (wrapper,entry,kind)
        if key not in seen:
            seen.add(key)
            scenario = copy.deepcopy(base)
            scenario['initial'] = dict(pc=0x13c if wrapper == 0x3d5 else 0x13b,ram=ram,q=q)
            scenario['dispatch']['value'] = entry
            scenario['io']['read'] = dict(mode='constant',value=d,table=[0],status='stub',evidence=config['evidence'])
            out = args.out/f'local-{len(witnesses):02d}'
            result = execute(mapping,scenario,got['cycles'],mode='integrated',out=out,trace_limit=got['cycles'])
            assert result['clean'] and all(result['final_state'][k] == got[k] for k in ('pc','ram','q'))
            trace = load_trace(out)
            assert [(e['pc'],e['next_pc'],e['alu'],e['test']) for e in trace] == [(e['pc'],e['next_pc'],e['alu'],e['test']) for e in got['trace']]
            witnesses.append(dict(wrapper=wrapper,entry=entry,x=x,y=y,q=q,d=d,prediction=want,observed=got,trace_digest=result['trace_digest']))
    caller_runs = []
    caller_counts = Counter()
    with tempfile.TemporaryDirectory() as temporary:
        for entry in range(4):
            for x in config['boundary_words']:
                for y in config['boundary_words']:
                    ram = config['initial_ram'][:]
                    ram[7] = 0
                    ram[10:14] = [x&255,x>>8,y&255,y>>8]
                    scenario = copy.deepcopy(base)
                    scenario['initial'] = dict(pc=0x133,ram=ram,q=1)
                    scenario['dispatch']['value'] = entry
                    scenario['io']['read'] = dict(mode='constant',value=255,table=[0],status='stub',evidence=config['evidence'])
                    out = args.out/f'chain-{entry}-{x:04x}' if y == 0x100 and x in (0,1,0x100,0xffff) else Path(temporary)
                    result = execute(mapping,scenario,64,mode='integrated',out=out,trace_limit=64)
                    trace = load_trace(out)
                    assert result['clean']
                    first_returns = ((-x)&65535)<256 if entry == 3 else x<256
                    terminal = x == 0 if entry == 3 else x<256
                    assert (result['final_state']['pc'] == 0x84) == terminal
                    assert (0x3d5 in result['visited']) == first_returns
                    assert (0x3c0 in result['visited']) == first_returns
                    gate = next(e for e in trace if e['pc'] == 0x13a)
                    assert gate['next_pc'] == 0x13b
                    expected = ram[:]
                    expected[0] = expected[5] = 1
                    expected[2] = ram[3]
                    expected[3] = 255-ram[1]
                    actual = ram[:]
                    checkpoints = []
                    for t in trace:
                        for register,value in t['registers'].items():
                            actual[int(register)] = value
                        if t['pc'] in (0x3ed,0x3d8,0x3c3):
                            wrapper = t['pc']-3
                            expected = transform(expected,wrapper,entry)
                            assert actual == expected and t['q'] == 0
                            checkpoints.append(dict(pc=t['pc'],ram=actual[:],next_pc=t['next_pc']))
                    if terminal:
                        assert result['final_state']['ram'] == expected and result['final_state']['q'] == 0
                    kind = 'terminal' if terminal else 'last-wrapper' if first_returns else 'first-wrapper'
                    caller_counts[kind] += 1
                    caller_runs.append(dict(entry=entry,x=x,y=y,outcome=kind,checkpoints=checkpoints,
                                            final_state=result['final_state'],trace_digest=result['trace_digest']))
    sources = [Path(__file__),HERE/'q2-overwrite-study.json',HERE/config['mapping'],HERE/config['scenario'],HERE/'execute.py',HERE/'common.py',HERE.parent/'model.py']
    save(args.out/'report.json',dict(configuration=config,counts=dict(counts),witnesses=witnesses,caller_counts=dict(caller_counts),caller_runs=caller_runs,execution_sha256=digest.hexdigest(),
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='q2 3D5 can negate its source X on each iteration and return on the second pass; otherwise tested wrappers return once or enter exact 8/16-instruction cycles. 3EA source aliasing produces (X,X),(-Y,X),(-X,X),(Y,-X), not an independent rotation. Local fixtures only.'))
    print('local cases',sum(counts.values()),'witnesses',len(witnesses),'caller outcomes',dict(caller_counts))


if __name__ == '__main__':
    main()
