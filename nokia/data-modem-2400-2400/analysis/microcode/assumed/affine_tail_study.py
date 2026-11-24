"""Test the 28E save/load and affine-byte helper and its reset-driven consumers."""
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
from nested_reset_study import scenario_for as reset_scenario


def prediction(ram, q, skip):
    expected = ram[:]
    expected[3] = ram[0]
    expected[0] = ram[0] if skip else q
    expected[15] = (expected[0]+2*ram[1]+1)&255
    return expected


def local_scenario(base, config, ram, q, d, skip):
    scenario = copy.deepcopy(base)
    scenario.update(name='local 28E save/load and affine-byte helper', evidence=config['evidence'])
    scenario['initial'] = dict(pc=0x213, ram=ram[:], q=q)
    scenario['condition']['sources'][6] = 'external'
    scenario['inputs']['external'] = int(skip)
    scenario['io']['read'] = dict(mode='constant', value=d, table=[0],
                                status='stub', evidence=config['evidence'])
    return scenario


def probe(rows, base, ram, q, d, skip):
    cpu = Am2901(ram=ram[:], q=q, logic_flags=True)
    seq = X8X02(pc=0x213)
    carry = CarryInput(base['inputs']['carry'])
    previous = dict(zero=0, carry=0, sign=0, overflow=0)
    trace = []
    depth = 0
    for cycle in range(10):
        if seq.pc == 0x214:
            assert depth == 0
            return dict(ram=cpu.ram, q=cpu.q, cycles=cycle, trace=trace)
        pc = seq.pc
        row = rows[pc]
        result = cpu.step(row['i'], row['a'], row['b'], d, carry.resolve(row), 0, 0)
        carry.observe(result)
        if pc == 0x290:
            test = int(skip)
        elif unconditional_transfer(row, base):
            test = 1
        else:
            selector = row['select']
            source = base['condition']['sources'][selector]
            value = base['condition']['value'] if source == 'constant' else previous[source]
            test = int(bool(value)) ^ base['condition']['polarity'][selector]
        if row['command'] == 4 and test:
            depth += 1
        elif row['command'] == 3:
            depth -= 1
        assert 0 <= depth <= 1
        seq.step(row['command'], row['branch'], test)
        trace.append(dict(pc=pc, next_pc=seq.pc, alu=result, test=test))
        previous = result
    raise AssertionError('helper did not return')


def selected_registers(row):
    """ALU/Y selection, not proof of semantic dependence (e.g. zero AND B)."""
    source = row['i'] & 7
    result = set()
    if source in (0, 1, 4, 5):
        result.add(row['a'])
    if source in (1, 3):
        result.add(row['b'])
    if row['i'] >> 6 == 2:
        result.add(row['a'])  # This destination drives Y directly from A.
    return result


def inspect_reset(trace, rows):
    ram = [0]*16
    q = 0
    pending = None
    helpers = []
    live = {}
    for t in trace:
        pc = t['pc']
        row = rows[pc]
        if pc == 0x28e:
            assert pending is None
            pending = dict(entry_cycle=t['cycle'], entry_ram=ram[:], entry_q=q)
        if pending is not None and pc == 0x290:
            pending['skip'] = bool(t['test'])
        # Track each helper result until a first later ALU selection or write.
        for reg, info in list(live.items()):
            if reg in selected_registers(row):
                info['first_selected_read'] = dict(pc=pc, cycle=t['cycle'])
                del live[reg]
            elif row['i'] >> 6 >= 2 and row['b'] == reg:
                info['first_overwrite'] = dict(pc=pc, cycle=t['cycle'])
                del live[reg]
        if helpers and pc in (0x216, 0x078, 0x079):
            helper = helpers[-1]
            helper.setdefault('tail_tests', []).append(dict(pc=pc, cycle=t['cycle'],
                alu=t['alu'], test=t['test'], next_pc=t['next_pc']))
            if not helper['skip']:
                if pc == 0x216:
                    assert t['alu']['f'] == 255 and t['alu']['zero'] == 0
                else:
                    assert t['test'] == 0 and t['next_pc'] == pc+1
        for reg, value in t['registers'].items():
            ram[int(reg)] = value
        q = t['q']
        if pending is not None and pc == 0x295:
            expected = prediction(pending['entry_ram'], pending['entry_q'], pending['skip'])
            assert ram == expected and q == pending['entry_q']
            assert t['next_pc'] == 0x214
            pending.update(return_cycle=t['cycle'], return_ram=ram[:], return_q=q,
                           results={str(r):dict(value=ram[r], first_selected_read=None, first_overwrite=None) for r in (0,3,15)})
            for r in (0,3,15):
                live[r] = pending['results'][str(r)]
            helpers.append(pending)
            pending = None
    assert pending is None
    return helpers


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=HERE/'results/affine-tail-study')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    config = read(HERE/'affine-tail-study.json')
    base = read(HERE/config['scenario'])
    counts = Counter()
    digest = hashlib.sha256()
    witnesses = []
    for name, path in config['profiles'].items():
        mapping = read(HERE/path)
        rows = decode(mapping)
        for skip in (False, True):
            for q in range(256):
                for r1 in range(256):
                    ram = config['initial_ram'][:]
                    ram[0] = (73*q+17*r1)&255
                    ram[1] = r1
                    ram[2] = q^r1^0xa5
                    d = (q+31*r1)&255
                    expected = prediction(ram, q, skip)
                    got = probe(rows, base, ram, q, d, skip)
                    assert got['ram'] == expected and got['q'] == q
                    assert got['cycles'] == (8 if skip else 9)
                    assert (0x291 in [t['pc'] for t in got['trace']]) == (not skip)
                    # The temporary 292 value is also sensitive to the skipped carry producer.
                    intermediate = next(t for t in got['trace'] if t['pc'] == 0x292)
                    assert intermediate['alu']['f'] == (ram[2]-int(skip))&255
                    counts[f'{name}:skip{int(skip)}'] += 1
                    digest.update(json.dumps([name,skip,q,r1,got],sort_keys=True,separators=(',',':')).encode())
                    if [q, r1] in config['witness_pairs']:
                        scenario = local_scenario(base, config, ram, q, d, skip)
                        out = args.out/f'{name}-s{int(skip)}-q{q:02x}-r1{r1:02x}'
                        result = execute(mapping, scenario, got['cycles'], mode='integrated', out=out, trace_limit=got['cycles'])
                        assert result['clean'] and result['final_state']['pc'] == 0x214
                        assert result['final_state']['ram'] == expected and result['final_state']['q'] == q
                        actual = load_trace(out)
                        assert [(t['pc'],t['next_pc'],t['alu'],t['test']) for t in actual] == [(t['pc'],t['next_pc'],t['alu'],t['test']) for t in got['trace']]
                        witnesses.append(dict(path=out.name, profile=name, skip=skip, q=q, r1=r1, expected=expected, trace_digest=result['trace_digest']))
            print(name, 'skip', int(skip), '65536 calls checked', flush=True)
    reset_config = read(HERE/config['reset_config'])
    reset_report = read(HERE/config['reset_report'])
    mapping = read(HERE/reset_config['mapping'])
    rows = decode(mapping)
    reset_base = read(HERE/reset_config['scenario'])
    tables = read(HERE/reset_config['tables'])
    reset_runs = []
    for earlier in reset_report['runs']:
        if not earlier['nested_calls']:
            continue
        scenario = reset_scenario(reset_base, tables, reset_config, earlier['d'])
        out = args.out/f'reset-{earlier["seed"]:04d}'
        result = execute(mapping, scenario, reset_config['cycles'], seed=earlier['seed'], mode='integrated', out=out, trace_limit=reset_config['cycles'])
        assert result['clean'] and result['trace_digest'] == earlier['trace_digest']
        helpers = inspect_reset(load_trace(out), rows)
        assert len(helpers) == 1 and not helpers[0]['skip']
        assert [t['pc'] for t in helpers[0]['tail_tests']] == [0x216, 0x078, 0x079]
        assert helpers[0]['entry_q'] == earlier['nested_calls'][0]['return_q']
        reset_runs.append(dict(seed=earlier['seed'], d=earlier['d'], helpers=helpers,
            final_pc=result['final_state']['pc'], trace_digest=result['trace_digest']))
    sources = [Path(__file__), HERE/'affine-tail-study.json', HERE/config['scenario'],
               *(HERE/p for p in config['profiles'].values()), HERE/config['reset_config'], HERE/config['reset_report'],
               HERE/reset_config['scenario'], HERE/reset_config['tables'], HERE/'nested_reset_study.py',
               HERE/'common.py', HERE/'execute.py', HERE/'defined_condition_fit.py', HERE.parent/'model.py']
    save(args.out/'report.json', dict(configuration=config, counts=dict(counts), execution_sha256=digest.hexdigest(),
        witnesses=witnesses, reset_runs=reset_runs,
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='Under q1/q2/q4 and declared skip input, save old R0 in R3, optionally copy Q to R0, then store R0+2*R1+1 in R15. Five q2 reset witnesses connect nested input to this helper. Later selected-register reads include ALU operands and the direct A-to-Y path, not proof of physical output or semantic dependence.'))


if __name__ == '__main__':
    main()
