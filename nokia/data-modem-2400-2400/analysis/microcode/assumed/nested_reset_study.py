"""Exercise the q2 nested ROM wrapper from zero reset with actual ALU flags."""
import argparse
import copy
import hashlib
import tempfile
from collections import Counter
from pathlib import Path
from common import HERE, decode, read, save, table_targets
from defined_condition_fit import load_trace
from execute import execute
from nested_prepare_study import prediction
from rom_study import load_rom, reconstruct_lookups


def scenario_for(base, tables, config, d):
    scenario = copy.deepcopy(base)
    scenario.update(name='q2 reset with random dispatch and early replies', evidence=config['evidence'])
    scenario['initial'] = dict(pc=0, ram=[0]*16, q=0)
    scenario['dispatch']['tables'] = copy.deepcopy(tables['dispatch']['tables'])
    scenario['branch_tables'] = copy.deepcopy(tables['branch_tables'])
    scenario['dispatch'].update(mode='random', source='scenario', initial_y=0)
    scenario['io']['read'] = dict(mode='pc_sequence', value=d, table=[0],
        pc_sequences={str(0x117): [d, 0], str(0x106): [d, 0]},
        sequence_end='hold-last', status='stub', evidence=config['evidence'])
    return scenario


def inspect(trace, rows, scenario, d):
    ram = [0]*16
    q = 0
    q_writer = None
    writers = {}
    pending = None
    calls = []
    targets = table_targets(scenario['dispatch']['tables'][str(0x2c4)])
    for t in trace:
        pc = t['pc']
        if pc == 0x21f and t['next_pc'] == 0x2bc:
            assert pending is None
            pending = dict(call_cycle=t['cycle'], entry_ram=ram[:], entry_q=q,
                entry_q_writer=q_writer, entry_r5_writer=writers.get(5),
                caller_depth=t['stack_before']['depth'])
        if pending is not None and pc == 0x2c4:
            source = scenario['dispatch']['tables'][str(pc)].get('index_source', 'scenario')
            index = t.get('dispatch_input', t['dispatch_entry'])
            expected = prediction(pending['entry_ram'], pending['entry_q'], d,
                {str(0x2c0): d, str(0x2c2): d}, targets, source, index)
            assert ram == expected['prepared'] and q == pending['entry_q']
            assert t['next_pc'] == expected['target']
            pending.update(nested_cycle=t['cycle'], nested_index=index, nested_entry=t['dispatch_entry'],
                           nested_target=t['next_pc'], expected=expected)
        if pending is not None and pc == 0x2c5:
            expected = pending['expected']
            assert ram == expected['ram'] and q == expected['q']
            assert t['next_pc'] == 0x220
            assert t['stack_after']['depth'] == pending['caller_depth']
            pending.update(return_cycle=t['cycle'], return_ram=ram[:], return_q=q,
                           return_depth=t['stack_after']['depth'])
            calls.append(pending)
            pending = None
        for r, v in t['registers'].items():
            ram[int(r)] = v
        row = rows[pc]
        destination = row['i'] >> 6
        if destination >= 2:
            writers[row['b']] = dict(pc=pc, cycle=t['cycle'])
        if destination in (0, 4, 6):
            q_writer = dict(pc=pc, cycle=t['cycle'])
        q = t['q']
    assert pending is None, 'trace ends inside a nested call'
    return calls


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=HERE/'results/nested-reset-study')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    config = read(HERE/'nested-reset-study.json')
    mapping, base, tables = (read(HERE/config[k]) for k in ('mapping','scenario','tables'))
    rows = decode(mapping)
    rom = load_rom(config)
    runs = []
    counts = Counter()
    reached = set()
    witness_keys = set()
    witnesses = []
    first = None
    with tempfile.TemporaryDirectory() as temporary:
        for seed in range(config['seeds']):
            d = (seed*config['input_multiplier']+config['input_offset'])&255
            scenario = scenario_for(base, tables, config, d)
            result = execute(mapping, scenario, config['cycles'], seed=seed, mode='integrated', trace_limit=0)
            assert result['clean'] and result['unused_word_executions'] == 0
            reached.update(result['visited'])
            record = dict(seed=seed, d=d, visited=len(result['visited']),
                final_pc=result['final_state']['pc'], max_depth=result['stack']['max_depth'],
                trace_digest=result['trace_digest'], nested_calls=[])
            counts['clean'] += 1
            counts['terminal'] += int(result['final_state']['pc'] == 0x84)
            counts['visits_21f'] += int(0x21f in result['visited'])
            if 0x2bc in result['visited']:
                counts['visits_2bc'] += 1
                out = Path(temporary)
                replay = execute(mapping, scenario, config['cycles'], seed=seed, mode='integrated', out=out, trace_limit=config['cycles'])
                assert replay['trace_digest'] == result['trace_digest']
                trace = load_trace(out)
                calls = inspect(trace, rows, scenario, d)
                assert calls
                record['nested_calls'] = calls
                keys = {(c['nested_target'], c['entry_q'] != 0, c['entry_ram'][5] != 0, c['caller_depth']) for c in calls}
                for c in calls:
                    counts[f"leaf_{c['nested_target']:03x}"] += 1
                    counts['nonzero_entry_q'] += int(c['entry_q'] != 0)
                    counts['nonzero_entry_r5'] += int(c['entry_ram'][5] != 0)
                if first is None:
                    first = dict(seed=seed, d=d, scenario=scenario, trace=trace, calls=calls)
                if keys-witness_keys:
                    witness_keys.update(keys)
                    out = args.out/f'seed-{seed:04d}'
                    saved = execute(mapping, scenario, config['cycles'], seed=seed, mode='integrated', out=out, trace_limit=config['cycles'])
                    assert saved['trace_digest'] == result['trace_digest']
                    witnesses.append(dict(path=out.name, seed=seed, d=d, calls=calls,
                        reconstructed_lookups=reconstruct_lookups(trace, scenario, rom)))
            runs.append(record)
            if seed%512 == 511:
                print(seed+1, dict(counts), 'union', len(reached), flush=True)
        assert first is not None
        # Compare only through the first outer return: changing a random source
        # changes subsequent RNG consumption, so later dispatches are not matched.
        comparisons = []
        original_call = first['calls'][0]
        for source in ('scenario', 'y', 'q', 'previous_y'):
            scenario = copy.deepcopy(first['scenario'])
            scenario['dispatch']['tables'][str(0x2c4)].update(index_source=source, evidence=config['evidence'])
            out = Path(temporary)
            result = execute(mapping, scenario, config['cycles'], seed=first['seed'], mode='integrated', out=out, trace_limit=config['cycles'])
            assert result['clean']
            trace = load_trace(out)
            calls = inspect(trace, rows, scenario, first['d'])
            call = calls[0]
            assert trace[:original_call['nested_cycle']] == first['trace'][:original_call['nested_cycle']]
            assert (call['entry_ram'],call['entry_q'],call['caller_depth']) == (original_call['entry_ram'],original_call['entry_q'],original_call['caller_depth'])
            cycles = call['return_cycle']+1
            out = args.out/f'compare-{source}'
            result = execute(mapping, scenario, cycles, seed=first['seed'], mode='integrated', out=out, trace_limit=cycles)
            assert result['clean'] and result['final_state']['pc'] == 0x220
            comparisons.append(dict(source=source, seed=first['seed'], d=first['d'], call=call,
                trace_digest=result['trace_digest'], reconstructed_lookups=reconstruct_lookups(load_trace(out), scenario, rom)))
    sources = [Path(__file__), HERE/'nested-reset-study.json', HERE/config['mapping'], HERE/config['scenario'],
               HERE/config['tables'], HERE/'nested_prepare_study.py', HERE/'common.py', HERE/'execute.py',
               HERE/'defined_condition_fit.py', HERE/'rom_study.py', HERE.parent/'model.py']
    save(args.out/'report.json', dict(configuration=config, counts=dict(counts), reached=sorted(reached),
        runs=runs, witnesses=witnesses, comparisons=comparisons,
        source_sha256={str(p.relative_to(HERE.parent)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='Zero-reset integrated witnesses under q2, actual previous ALU flags, diagnostic early inputs and seeded random dispatch. Scoped ROM table assumptions remain unchanged. Matched source comparisons stop at the first outer return; subsequent RNG consumption differs. No physical input protocol or dispatch wiring is established.'))


if __name__ == '__main__':
    main()
