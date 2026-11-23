"""Check q2 handler 133's accumulator update and transform-call gates."""
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


def prediction(ram, q, d):
    result = ram[:]
    result[0] = result[5] = q
    result[2] = ram[3]
    result[3] = 255-ram[1]
    pc = 0x13e if q+d < 256 else 0x13d if q < ram[7] else 0x13b
    return dict(pc=pc, ram=result, q=(q+d)&255)


def probe(rows, base, ram, q, d):
    cpu = Am2901(ram=ram[:], q=q, logic_flags=True)
    seq = X8X02(pc=0x133)
    carry = CarryInput(base['inputs']['carry'])
    previous = dict(zero=0, carry=0, sign=0, overflow=0)
    trace = []
    while seq.pc not in (0x13b, 0x13d, 0x13e):
        assert len(trace) < 16
        pc = seq.pc
        row = rows[pc]
        result = cpu.step(row['i'], row['a'], row['b'], d, carry.resolve(row), 0, 0)
        carry.observe(result)
        select = row['select']
        source = base['condition']['sources'][select]
        value = base['condition']['value'] if source == 'constant' else previous[source]
        test = 1 if unconditional_transfer(row, base) else int(bool(value)) ^ base['condition']['polarity'][select]
        seq.step(row['command'], row['branch'], test)
        trace.append(dict(pc=pc, next_pc=seq.pc, alu=result, test=test))
        previous = result
    assert seq.pushes == seq.pops == 1
    return dict(pc=seq.pc, ram=cpu.ram, q=cpu.q, cycles=len(trace), trace=trace)


def fixtures(config):
    for q in range(256):
        for d in range(256):
            ram = config['initial_ram'][:]
            ram[7] = 0
            yield 'addition', ram, q, d
    for q in range(256):
        for threshold in range(256):
            ram = config['initial_ram'][:]
            ram[7] = threshold
            yield 'comparison', ram, q, 255
    for r1 in range(256):
        for q, d in config['carry_boundary_cases']:
            ram = config['initial_ram'][:]
            ram[1] = r1
            yield 'carry-setup', ram, q, d


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=HERE/'results/q2-accumulator-study')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    config = read(HERE/'q2-accumulator-study.json')
    mapping = read(HERE/config['mapping'])
    base = read(HERE/config['scenario'])
    assert base['condition']['flag_timing'] == 'previous'
    rows = decode(mapping)
    counts = Counter()
    digest = hashlib.sha256()
    witnesses = []
    seen = set()
    for group, ram, q, d in fixtures(config):
        expected = prediction(ram, q, d)
        got = probe(rows, base, ram, q, d)
        assert all(got[k] == expected[k] for k in ('pc', 'ram', 'q'))
        by_pc = {e['pc']: e for e in got['trace']}
        assert by_pc[0x137]['alu']['carry'] == 0
        assert by_pc[0x138]['alu']['carry'] == int(q+d >= 256)
        assert by_pc[0x139]['alu']['carry'] == int(q >= ram[7])
        counts[f"{group}:{got['pc']:03x}"] += 1
        digest.update(json.dumps([group, ram, q, d, expected, got['cycles']], separators=(',', ':')).encode())
        key = (group, got['pc'], q+d == 256, q == ram[7])
        if key not in seen:
            seen.add(key)
            scenario = copy.deepcopy(base)
            scenario['initial'] = dict(pc=0x133, ram=ram, q=q)
            scenario['io']['read'] = dict(mode='constant', value=d, table=[0], status='stub', evidence=config['evidence'])
            out = args.out/f'local-{len(witnesses):02d}'
            result = execute(mapping, scenario, got['cycles'], mode='integrated', out=out, trace_limit=got['cycles'])
            assert result['clean'] and all(result['final_state'][k] == expected[k] for k in ('pc', 'ram', 'q'))
            integrated = load_trace(out)
            assert [(e['pc'], e['next_pc'], e['alu'], e['test']) for e in integrated] == [(e['pc'], e['next_pc'], e['alu'], e['test']) for e in got['trace']]
            witnesses.append(dict(group=group, initial_ram=ram, initial_q=q, d=d, observed=got, trace_digest=result['trace_digest']))
    reset_runs = []
    with tempfile.TemporaryDirectory() as temporary:
        for d in range(256):
            scenario = copy.deepcopy(base)
            scenario['initial'] = dict(pc=0, ram=[0]*16, q=0)
            scenario['dispatch']['value'] = 7
            scenario['io']['read'] = dict(mode='pc_sequence', value=d, table=[0],
                pc_sequences={str(p): [d, 0] for p in (0x117, 0x106)}, sequence_end='hold-last', status='stub', evidence=config['evidence'])
            out = args.out/f'reset-d{d:02x}' if d in config['reset_witnesses'] else Path(temporary)
            result = execute(mapping, scenario, config['reset_cycles'], mode='integrated', out=out, trace_limit=config['reset_cycles'])
            trace = load_trace(out)
            entry = next(e for e in trace if e['pc'] == 0x133)
            assert entry['q'] == 0
            update = next(e for e in trace if e['pc'] == 0x138)
            gate = next(e for e in trace if e['pc'] == 0x139)
            assert result['clean'] and result['final_state']['pc'] == 0x84
            assert update['q'] == d and update['alu']['carry'] == 0
            assert gate['next_pc'] == 0x13e
            assert not set(result['visited']) & {0x13b, 0x13c, 0x13d, 0x3c0, 0x3d5, 0x3ea}
            reset_runs.append(dict(d=d, entry=entry, update=update, gate=gate, final_state=result['final_state'], trace_digest=result['trace_digest']))
    sources = [Path(__file__), HERE/'q2-accumulator-study.json', HERE/config['mapping'], HERE/config['scenario'],
               HERE/'execute.py', HERE/'common.py', HERE.parent/'model.py']
    save(args.out/'report.json', dict(configuration=config, counts=dict(counts), witnesses=witnesses, reset_runs=reset_runs,
        execution_sha256=digest.hexdigest(), source_sha256={str(p.relative_to(HERE.parent)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='Under q2 and previous flags, handler 133 updates Q by D and bypasses transform calls unless that byte addition carries. On carry, old Q<R7 skips the first two calls. Nonzero-Q cases are local fixtures; all tested reset inputs bypass the transform calls.'))
    print(dict(counts), 'local witnesses', len(witnesses), 'reset runs', len(reset_runs))


if __name__ == '__main__':
    main()
