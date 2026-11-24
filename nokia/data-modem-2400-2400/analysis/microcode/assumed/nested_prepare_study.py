"""Characterize q2's 2BC prefix and nested ROM dispatch using real call frames."""
import argparse
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path
from common import HERE, decode, read, save, table_targets, unconditional_transfer
from defined_condition_fit import load_trace
from execute import CarryInput, execute
from model import Am2901, X8X02
from rom_study import load_rom, reconstruct_lookups


def fixture(config, q, d):
    ram = config['initial_ram'][:]
    ram[4], ram[5], ram[9] = d^0xa5, d^0x5a, 255-d
    reads = {str(0x2bd): q^d, str(0x2c0): d, str(0x2c2): (73*d+q)&255}
    return ram, reads


def prediction(ram, q, d, reads, targets, source, index):
    prepared = ram[:]
    prepared[0] = q >> 1
    prepared[2] = (reads[str(0x2c2)]+q)&255
    prepared[4] = ((reads[str(0x2c0)]+q)&255)>>1
    dispatch_input = dict(scenario=index, y=0, q=q, previous_y=(ram[5]+q)&255)[source]
    target = targets[dispatch_input % len(targets)]
    final = prepared[:]
    final_q = d if target in (0x224, 0x225) else q
    if target == 0x2b3:
        final[15] = (d+q)&255
    return dict(prepared=prepared, dispatch_input=dispatch_input, target=target,
                ram=final, q=final_q)


def probe(rows, base, ram, q, d, reads, source, index, targets):
    cpu = Am2901(ram=ram[:], q=q, logic_flags=True)
    seq = X8X02(pc=0x21f)
    carry = CarryInput(base['inputs']['carry'])
    previous = dict(zero=0, carry=0, sign=0, overflow=0, y=0)
    depth = maximum = 0
    trace = []
    prepared = None
    for cycle in range(40):
        if seq.pc == 0x220:
            assert depth == 0
            return dict(pc=seq.pc, ram=cpu.ram, q=cpu.q, cycles=cycle,
                        max_depth=maximum, prepared=prepared, trace=trace)
        pc = seq.pc
        row = rows[pc]
        if pc == 0x2c4:
            prepared = dict(ram=cpu.ram[:], q=cpu.q, previous_y=previous['y'])
        operand = reads.get(str(pc), d)
        result = cpu.step(row['i'], row['a'], row['b'], operand, carry.resolve(row), 0, 0)
        carry.observe(result)
        condition = base['condition']
        if unconditional_transfer(row, base):
            test = 1
        else:
            selector = row['select']
            flag = condition['sources'][selector]
            value = condition['value'] if flag == 'constant' else previous[flag]
            test = int(bool(value)) ^ condition['polarity'][selector]
        branch = row['branch']
        dispatch_input = None
        if pc == 0x21f:
            branch = table_targets(base['dispatch']['tables'][str(pc)])[index % 82]
            assert branch == 0x2bc
        elif pc == 0x2c4:
            dispatch_input = dict(scenario=index, y=result['y'], q=cpu.q,
                                  previous_y=previous['y'])[source]
            branch = targets[dispatch_input % len(targets)]
        if row['command'] == 5 or row['command'] == 4 and test:
            depth += 1
            maximum = max(maximum, depth)
        if row['command'] in (2, 3):
            depth -= 1
        assert 0 <= depth <= 4 and not row['unused']
        seq.step(row['command'], branch, test)
        trace.append(dict(pc=pc, next_pc=seq.pc, alu=result, test=test,
                          dispatch_input=dispatch_input))
        previous = result
    raise AssertionError('nested routine did not return within the local bound')


def scenario_for(base, config, ram, q, d, reads, source):
    scenario = copy.deepcopy(base)
    scenario['name'] = 'q2 local nested preparation and ROM dispatch'
    scenario['evidence'] = config['evidence']
    scenario['initial'] = dict(pc=0x21f, ram=ram[:], q=q)
    scenario['dispatch'].update(mode='constant', source='scenario',
                                value=config['outer_index'], initial_y=0)
    scenario['dispatch']['tables'][str(0x2c4)].update(index_source=source, evidence=config['evidence'])
    scenario['io']['read'] = dict(mode='pc_table', value=d, table=[0], pc_values=reads,
                                status='stub', evidence=config['evidence'])
    return scenario


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=HERE/'results/nested-prepare-study')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    config = read(HERE/'nested-prepare-study.json')
    mapping, base = (read(HERE/config[k]) for k in ('mapping','scenario'))
    rows = decode(mapping)
    tables = read(HERE/config['tables'])['dispatch']['tables']
    rom = load_rom(config)
    # Use the explicit scoped ROM ranges, retaining their original provenance.
    for pc in (0x21f, 0x2c4):
        table = tables[str(pc)]
        lookup = table['lookup']
        assert lookup['sha256'] == config['rom_sha256']
        assert table_targets(table) == [lookup['bank']+v for v in rom[lookup['offset']:lookup['offset']+lookup['count']]]
        base['dispatch']['tables'][str(pc)] = table
    targets = table_targets(tables[str(0x2c4)])
    assert set(targets) == {0x2b3, 0x22d, 0x224, 0x225, 0x22b, 0x229, 0x22c}
    assert base['condition']['flag_timing'] == 'previous'
    counts = Counter()
    cycles = Counter()
    digest = hashlib.sha256()
    witnesses = []
    seen = set()
    for source in config['sources']:
        for q in range(256):
            for d in range(256):
                ram, reads = fixture(config, q, d)
                want = prediction(ram, q, d, reads, targets, source, config['outer_index'])
                got = probe(rows, base, ram, q, d, reads, source, config['outer_index'], targets)
                assert got['prepared'] == dict(ram=want['prepared'], q=q, previous_y=(ram[5]+q)&255)
                assert got['ram'] == want['ram'] and got['q'] == want['q']
                assert got['max_depth'] == 2
                call = next(t for t in got['trace'] if t['pc'] == 0x2c4)
                assert call['dispatch_input'] == want['dispatch_input'] and call['next_pc'] == want['target']
                if want['target'] == 0x2b3:
                    branch = next(t for t in got['trace'] if t['pc'] == 0x2b8)
                    assert branch['test'] == 1 and branch['next_pc'] == 0x227
                key = f'{source}:{want["target"]:03x}'
                counts[key] += 1
                cycles[str(got['cycles'])] += 1
                digest.update(json.dumps([source,q,d,got['cycles'],want,got['trace']],sort_keys=True,separators=(',',':')).encode())
                witness_key = (source, want['target'])
                # Prefer nonzero Q fixtures, to distinguish preserved and replaced values.
                if witness_key not in seen and q >= 1:
                    seen.add(witness_key)
                    scenario = scenario_for(base, config, ram, q, d, reads, source)
                    out = args.out/f'{source}-{want["target"]:03x}'
                    result = execute(mapping, scenario, got['cycles'], mode='integrated', out=out, trace_limit=got['cycles'])
                    assert result['clean'] and all(result['final_state'][k] == got[k] for k in ('pc','ram','q'))
                    actual = load_trace(out)
                    assert [(t['pc'],t['next_pc'],t['alu'],t['test']) for t in actual] == [(t['pc'],t['next_pc'],t['alu'],t['test']) for t in got['trace']]
                    witnesses.append(dict(path=out.name, source=source, initial_q=q, default_d=d,
                        reads=reads, prediction=want, observed=got, trace_digest=result['trace_digest'],
                        reconstructed_lookups=reconstruct_lookups(actual, scenario, rom)))
        print(source, sum(v for k,v in counts.items() if k.startswith(source+':')), 'checked local calls', flush=True)
    sources = [Path(__file__), HERE/'nested-prepare-study.json', HERE/config['mapping'],
               HERE/config['scenario'], HERE/config['tables'], HERE/'common.py', HERE/'execute.py',
               HERE/'defined_condition_fit.py', HERE/'rom_study.py', HERE.parent/'model.py']
    save(args.out/'report.json', dict(configuration=config, counts=dict(counts), cycle_counts=dict(cycles),
        execution_sha256=digest.hexdigest(), witnesses=witnesses,
        source_sha256={str(p.relative_to(HERE.parent)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='Local entry at actual call 21F with explicit nonzero fixtures, not zero-reset reachability. q2 prepares shifted Q and external sums, then selects a scoped ROM leaf. Q or preceding Y covers all seven targets; current Y selects 2B3 only. No hardware index, output consumer or physical protocol is identified.'))


if __name__ == '__main__':
    main()
