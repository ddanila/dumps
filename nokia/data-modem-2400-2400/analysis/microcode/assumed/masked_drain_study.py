"""Compare 30B's cleared-Q and masked-Q interpretations under previous flags."""
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


def prediction(ram,q,profile):
    masked = ram[0]&q if profile == 'fitted_original' else 0
    out = ram[:]
    out[5] = ((ram[0]+masked+1)&255)>>1
    out[0] = 0
    iterations = 1+((masked>>1).bit_length()+1)//2
    return dict(ram=out,q=0,iterations=iterations,cycles=5+2*iterations,masked=masked)


def probe(rows,base,ram,q,d):
    cpu = Am2901(ram=ram[:],q=q,logic_flags=True)
    seq = X8X02(pc=0x304)
    carry = CarryInput(base['inputs']['carry'])
    previous = dict(zero=0,carry=0,sign=0,overflow=0)
    trace = []
    while seq.pc != 0x305:
        assert len(trace)<20
        pc = seq.pc
        row = rows[pc]
        result = cpu.step(row['i'],row['a'],row['b'],d,carry.resolve(row),0,0)
        carry.observe(result)
        select = row['select']
        source = base['condition']['sources'][select]
        value = base['condition']['value'] if source == 'constant' else previous[source]
        test = 1 if unconditional_transfer(row,base) else int(bool(value)) ^ base['condition']['polarity'][select]
        seq.step(row['command'],row['branch'],test)
        trace.append(dict(pc=pc,next_pc=seq.pc,alu=result,test=test,q=cpu.q))
        previous = result
    assert seq.pushes == seq.pops
    return dict(pc=seq.pc,ram=cpu.ram,q=cpu.q,cycles=len(trace),trace=trace,
                iterations=sum(e['pc']==0x30e for e in trace))


def fixtures(config):
    for a in range(256):
        for q in range(256):
            yield 'ram0-q',a,q,0x5a
    for a,q in config['input_fixtures']:
        for d in range(256):
            yield 'external-byte',a,q,d


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/masked-drain-study')
    args = parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    config = read(HERE/'masked-drain-study.json')
    profiles = read(HERE/'program-reading.json')['profiles']
    mappings = {name:read(HERE/profiles[name]) for name in ('q1','q2','q3','q4','fitted_original')}
    decoded = {name:decode(mapping) for name,mapping in mappings.items()}
    fields = ('i','a','b','carry','carry_select','command','branch','select','direct')
    for name in ('q1','q3','q4'):
        assert all(all(decoded[name][pc][k] == decoded['q2'][pc][k] for k in fields) for pc in range(0x30b,0x311))
    base = read(HERE/config['scenario'])
    assert base['condition']['flag_timing'] == 'previous'
    counts = Counter()
    digest = hashlib.sha256()
    witnesses = []
    seen = set()
    for profile in ('q2','fitted_original'):
        rows = decoded[profile]
        for group,a,q,d in fixtures(config):
            ram = config['initial_ram'][:]
            ram[0] = a
            want = prediction(ram,q,profile)
            got = probe(rows,base,ram,q,d)
            assert all(got[k] == want[k] for k in ('ram','q','cycles','iterations'))
            events = {e['pc']:e for e in got['trace']}
            assert events[0x30c]['q'] == want['masked']
            assert next(e for e in got['trace'] if e['pc']==0x30b)['q'] == ((q+d)&255 if profile=='q2' else q)
            counts[f"{profile}:{group}:{got['iterations']}"] += 1
            digest.update(json.dumps([profile,group,a,q,d,got['ram'],got['cycles']],separators=(',',':')).encode())
            key = (profile,group,got['iterations'],want['ram'][5] == 0)
            if key not in seen:
                seen.add(key)
                scenario = copy.deepcopy(base)
                scenario['initial'] = dict(pc=0x304,ram=ram,q=q)
                scenario['io']['read'] = dict(mode='constant',value=d,table=[0],status='stub',evidence=config['evidence'])
                out = args.out/f'local-{len(witnesses):02d}'
                result = execute(mappings[profile],scenario,got['cycles'],mode='integrated',out=out,trace_limit=got['cycles'])
                assert result['clean'] and all(result['final_state'][k] == got[k] for k in ('pc','ram','q'))
                trace = load_trace(out)
                assert [(e['pc'],e['next_pc'],e['alu'],e['test'],e['q']) for e in trace] == [(e['pc'],e['next_pc'],e['alu'],e['test'],e['q']) for e in got['trace']]
                witnesses.append(dict(profile=profile,group=group,a=a,q=q,d=d,prediction=want,observed=got,trace_digest=result['trace_digest']))
    differences = sum(prediction([a]+[0]*15,q,'q2')['ram'][5] != prediction([a]+[0]*15,q,'fitted_original')['ram'][5] for a in range(256) for q in range(256))
    sources = [Path(__file__),HERE/'masked-drain-study.json',HERE/'program-reading.json',HERE/config['scenario'],HERE/'execute.py',HERE/'common.py',HERE.parent/'model.py']
    sources += [HERE/profiles[name] for name in mappings]
    save(args.out/'report.json',dict(configuration=config,counts=dict(counts),output_disagreements=differences,witnesses=witnesses,execution_sha256=digest.hexdigest(),
        equivalent_helper_profiles=['q1','q2','q3','q4'],source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='With original register roles, q1–q4 clear Q before the shift loop; fitted_original masks it with R0. Both return and clear R0/Q, but retain different R5 values and iteration counts. Shared previous flags and zero shift fill remain hypotheses; swapped register roles are outside this comparison.'))
    print(dict(counts),'output disagreements',differences,'witnesses',len(witnesses))


if __name__ == '__main__':
    main()
