"""Characterize q2's two terminal register stores and datapath index candidates."""
import argparse
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path
from common import HERE, decode, read, save, unconditional_transfer, table_targets
from execute import CarryInput, execute
from defined_condition_fit import load_trace
from model import Am2901, X8X02
from nested_reset_study import scenario_for as reset_scenario


def prediction(ram, q, d, source, scenario_indices):
    expected = ram[:]
    value = q >> 1
    helper5 = ((d-q-1)&255) >> 1
    expected[2] = ram[1]
    indices = []
    for which in range(2):
        expected[0], expected[5] = value, helper5
        if which == 0:
            expected[2] = expected[1]
        index = dict(scenario=scenario_indices[which], q=q,
                     y=expected[1] if which == 0 else 0,
                     previous_y=(d-expected[6])&255)[source]
        indices.append(index)
        expected[index%16] = value
    return dict(ram=expected, q=q, indices=indices, targets=[0x8a+i%16 for i in indices],
                stored_value=value, helper_r5=helper5)


def probe(rows, base, ram, q, d, source):
    cpu = Am2901(ram=ram[:], q=q, logic_flags=True)
    seq = X8X02(pc=0x07c)
    carry = CarryInput(base['inputs']['carry'])
    previous = dict(zero=0, carry=0, sign=0, overflow=0, y=0)
    trace = []
    depth = maximum = 0
    for cycle in range(21):
        if seq.pc == 0x084:
            assert depth == 0
            return dict(ram=cpu.ram, q=cpu.q, cycles=cycle, max_depth=maximum, trace=trace)
        pc = seq.pc
        row = rows[pc]
        result = cpu.step(row['i'], row['a'], row['b'], d, carry.resolve(row), 0, 0)
        carry.observe(result)
        if unconditional_transfer(row, base):
            test = 1
        else:
            select = row['select']
            flag = base['condition']['sources'][select]
            flag_value = base['condition']['value'] if flag == 'constant' else previous[flag]
            test = int(bool(flag_value)) ^ base['condition']['polarity'][select]
        branch = row['branch']
        index = None
        if pc in (0x07e, 0x081):
            index = dict(scenario=d, q=cpu.q, y=result['y'], previous_y=previous['y'])[source]
            branch = 0x08a + index%16
        if row['command'] == 4 and test:
            depth += 1
            maximum = max(maximum, depth)
        if row['command'] == 3:
            depth -= 1
        assert 0 <= depth <= 1
        seq.step(row['command'], branch, test)
        trace.append(dict(pc=pc, next_pc=seq.pc, alu=result, test=test, index=index))
        previous = result
    raise AssertionError('terminal tail did not reach 084')


def local_scenario(base, config, ram, q, d, source):
    scenario = copy.deepcopy(base)
    scenario.update(name='q2 indexed terminal register stores', evidence=config['evidence'])
    scenario['initial'] = dict(pc=0x07c, ram=ram[:], q=q)
    scenario['dispatch'].update(mode='constant', source='scenario', value=d, initial_y=0)
    for pc in (0x07e, 0x081):
        scenario['dispatch']['tables'][str(pc)].update(index_source=source, evidence=config['evidence'])
    scenario['io']['read'] = dict(mode='constant', value=d, table=[0], status='stub', evidence=config['evidence'])
    return scenario


def inspect_reset(trace, d, source):
    ram = [0]*16
    q = 0
    start = None
    dispatches = []
    for t in trace:
        pc = t['pc']
        if pc == 0x07c:
            assert start is None
            start = dict(cycle=t['cycle'], ram=ram[:], q=q)
        if start is not None and pc in (0x07e, 0x081):
            dispatches.append(dict(pc=pc, cycle=t['cycle'], index=t['dispatch_input'],
                entry=t['dispatch_entry'], target=t['next_pc'], ram_before=ram[:]))
        if start is not None and pc == 0x084:
            assert len(dispatches) == 2
            want = prediction(start['ram'], start['q'], d, source, [t['index'] for t in dispatches])
            assert ram == want['ram'] and q == want['q']
            assert [t['index'] for t in dispatches] == want['indices']
            assert [t['target'] for t in dispatches] == want['targets']
            assert t['stack_before']['depth'] == 0
            return dict(start=start, first_terminal=t['cycle'], dispatches=dispatches,
                        prediction=want, final_ram=ram[:], final_q=q)
        for reg, value in t['registers'].items():
            ram[int(reg)] = value
        q = t['q']
    raise AssertionError('reset trace does not contain a complete terminal tail')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=HERE/'results/indexed-tail-study')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    config = read(HERE/'indexed-tail-study.json')
    mapping, base = (read(HERE/config[k]) for k in ('mapping','scenario'))
    rows = decode(mapping)
    for pc in (0x07e, 0x081):
        assert table_targets(base['dispatch']['tables'][str(pc)]) == list(range(0x08a,0x09a))
    counts = Counter()
    digest = hashlib.sha256()
    witnesses = []
    for source in config['sources']:
        for q in range(256):
            for d in range(256):
                ram = config['initial_ram'][:]
                ram[1], ram[6] = d^0xa5, (2*d+0x33)&255
                want = prediction(ram, q, d, source, [d,d])
                got = probe(rows, base, ram, q, d, source)
                assert got['ram'] == want['ram'] and got['q'] == q
                assert got['cycles'] == 20 and got['max_depth'] == 1
                calls = [t for t in got['trace'] if t['index'] is not None]
                assert [t['index'] for t in calls] == want['indices']
                assert [t['next_pc'] for t in calls] == want['targets']
                counts[f'{source}:calls'] += 1
                counts[f'{source}:different_targets'] += int(want['targets'][0] != want['targets'][1])
                counts[f'{source}:first_store_r6'] += int(want['indices'][0]%16 == 6)
                digest.update(json.dumps([source,q,d,want,got],sort_keys=True,separators=(',',':')).encode())
                if [q,d] in config['witness_pairs']:
                    scenario = local_scenario(base, config, ram, q, d, source)
                    out = args.out/f'{source}-q{q:02x}-d{d:02x}'
                    result = execute(mapping, scenario, got['cycles'], mode='integrated', out=out, trace_limit=got['cycles'])
                    assert result['clean'] and result['final_state']['pc'] == 0x084
                    assert result['final_state']['ram'] == want['ram'] and result['final_state']['q'] == q
                    actual = load_trace(out)
                    assert [(t['pc'],t['next_pc'],t['alu'],t['test']) for t in actual] == [(t['pc'],t['next_pc'],t['alu'],t['test']) for t in got['trace']]
                    witnesses.append(dict(path=out.name, source=source, q=q, d=d, prediction=want, trace_digest=result['trace_digest']))
        print(source, dict(counts), flush=True)
    reset_config = read(HERE/config['reset_config'])
    reset_report = read(HERE/config['reset_report'])
    reset_base = read(HERE/reset_config['scenario'])
    tables = read(HERE/reset_config['tables'])
    comparisons = []
    for earlier in reset_report['runs']:
        if not earlier['nested_calls']:
            continue
        prefix = None
        for source in config['sources']:
            scenario = reset_scenario(reset_base, tables, reset_config, earlier['d'])
            for pc in (0x07e,0x081):
                scenario['dispatch']['tables'][str(pc)].update(index_source=source, evidence=config['evidence'])
            out = args.out/f'reset-{earlier["seed"]:04d}-{source}'
            result = execute(mapping, scenario, reset_config['cycles'], seed=earlier['seed'], mode='integrated', out=out, trace_limit=reset_config['cycles'])
            assert result['clean'] and result['final_state']['pc'] == 0x084
            if source == 'scenario':
                assert result['trace_digest'] == earlier['trace_digest']
            trace = load_trace(out)
            observed = inspect_reset(trace, earlier['d'], source)
            boundary = observed['dispatches'][0]['cycle']
            if prefix is None:
                prefix = trace[:boundary]
            assert trace[:boundary] == prefix
            # No later random operation exists after these two terminal dispatches.
            assert not any(t['dispatch_entry'] is not None for t in trace[observed['dispatches'][1]['cycle']+1:])
            comparisons.append(dict(seed=earlier['seed'], d=earlier['d'], source=source,
                observed=observed, trace_digest=result['trace_digest']))
    sources = [Path(__file__), HERE/'indexed-tail-study.json', HERE/config['mapping'], HERE/config['scenario'],
        HERE/config['reset_config'], HERE/config['reset_report'], HERE/reset_config['scenario'], HERE/reset_config['tables'],
        HERE/'nested_reset_study.py', HERE/'common.py', HERE/'execute.py', HERE/'defined_condition_fit.py', HERE.parent/'model.py']
    save(args.out/'report.json', dict(configuration=config, counts=dict(counts), execution_sha256=digest.hexdigest(),
        witnesses=witnesses, reset_comparisons=comparisons,
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='q2 terminal tail performs two indexed stores of Q>>1 into RAM. The helper also forms R5=((D-Q-1) mod 256)>>1 and exposes D-R6 for candidate preceding-Y indexing. A first store to R6 can change the second address. Explicit candidates, not recovered physical dispatch or DAC writes.'))


if __name__ == '__main__':
    main()
