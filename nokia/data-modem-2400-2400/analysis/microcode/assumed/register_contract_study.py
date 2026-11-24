"""Replay a real reset prefix and exhaust a diagnostic two-store input contract."""
import argparse
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path
from common import HERE, decode, read, save, table_targets, unconditional_transfer
from execute import CarryInput, execute
from defined_condition_fit import load_trace
from affine_tail_study import prediction as affine_prediction
from model import Am2901, X8X02


def inputs_for(snapshot, payload, first, second, adjust=True):
    initial_r6 = snapshot['ram'][6]
    after_first_r6 = payload >> 1 if first == 6 and adjust else initial_r6
    return [(initial_r6+first)&255, (after_first_r6+second)&255]


def scenario_for(base, config, payload, first, second, initial_r6, adjust=True):
    scenario = copy.deepcopy(base)
    scenario.update(name='diagnostic nested-load and indexed-store contract', evidence=config['evidence'])
    scenario['io']['read']['evidence'] = config['evidence']
    scenario['io']['read']['pc_sequences'][str(0x225)] = [payload]
    scenario['io']['read']['pc_sequences'][str(0x089)] = inputs_for(
        dict(ram=[initial_r6 if i == 6 else 0 for i in range(16)]), payload, first, second, adjust)
    scenario['dispatch']['initial_y'] = 0
    for pc in (0x07e,0x081):
        scenario['dispatch']['tables'][str(pc)].update(index_source='previous_y', evidence=config['evidence'])
    return scenario


def capture(mapping, base, config, out):
    # Future input changes cannot affect this prefix: all four changed sites
    # are absent before the first 225. Prove that against an actual core replay.
    original = load_trace(HERE/config['base'])
    cutoff = next(t['cycle'] for t in original if t['pc'] == 0x225)
    assert cutoff == config['prefix_cycles']
    assert not any(t['pc'] in (0x225,0x089,0x07e,0x081) for t in original[:cutoff])
    ram = [0]*16
    for t in original[:cutoff]:
        for reg,value in t['registers'].items():
            ram[int(reg)] = value
    scenario = scenario_for(base, config, 0, 0, 0, ram[6])
    result = execute(mapping, scenario, cutoff, seed=config['seed'], mode='integrated', out=out, trace_limit=cutoff)
    trace = load_trace(out)
    assert result['clean'] and trace == original[:cutoff]
    assert result['final_state']['pc'] == 0x225 and result['stack']['final_depth'] == 4
    state = result['final_state']
    return dict(pc=state['pc'], ram=state['ram'], q=state['q'], sp=state['sp'], stack=state['stack'],
        depth=result['stack']['final_depth'], previous=trace[-1]['alu'], cycle=cutoff,
        prefix_trace_digest=result['trace_digest'])


def prediction(snapshot, payload, d, first, second):
    # Nested leaf 225 only changes Q before the already-verified affine helper.
    ram = affine_prediction(snapshot['ram'], payload, False)
    value = payload >> 1
    helper5 = ((d-payload-1)&255) >> 1
    ram[2] = ram[1]
    ram[0],ram[5] = value,helper5
    ram[first] = value
    ram[0],ram[5] = value,helper5
    ram[second] = value
    return dict(ram=ram, q=payload, value=value, helper5=helper5)


def resume(rows, scenario, snapshot, payload, first, second, adjust=True, read_values=None):
    cpu = Am2901(ram=snapshot['ram'][:], q=snapshot['q'], logic_flags=True)
    seq = X8X02(pc=snapshot['pc'], sp=snapshot['sp'], stack=snapshot['stack'][:])
    carry = CarryInput(scenario['inputs']['carry'])
    carry.previous = snapshot['previous']['carry']
    previous = snapshot['previous']
    depth = maximum = snapshot['depth']
    reads = inputs_for(snapshot, payload, first, second, adjust) if read_values is None else read_values
    assert len(reads) == 2 and all(type(v) is int and 0 <= v <= 255 for v in reads)
    read_count = load_count = 0
    trace = []
    dispatches = []
    d = scenario['io']['read']['value']
    for offset in range(64):
        if seq.pc == 0x084:
            assert depth == 0 and read_count == 2 and load_count == 1
            return dict(ram=cpu.ram, q=cpu.q, sp=seq.sp, stack=seq.stack, cycles=offset,
                        max_depth=maximum, trace=trace, dispatches=dispatches)
        pc = seq.pc
        row = rows[pc]
        operand = d
        if pc == 0x225:
            operand = payload
            load_count += 1
        elif pc == 0x089:
            assert read_count < 2
            operand = reads[read_count]
            read_count += 1
        old_ram = cpu.ram[:]
        carry_in = carry.resolve(row)
        result = cpu.step(row['i'], row['a'], row['b'], operand, carry_in, 0, 0)
        carry.observe(result)
        condition = scenario['condition']
        if unconditional_transfer(row, scenario):
            test = 1
        else:
            select = row['select']
            source = condition['sources'][select]
            value = condition['value'] if source == 'constant' else previous[source]
            test = int(bool(value)) ^ condition['polarity'][select]
        if row['command'] == 4 and test and (not row['direct'] or str(pc) in scenario['dispatch']['tables']):
            assert pc in (0x07e,0x081), 'suffix has an unmodeled computed call'
        if row['command'] == 6 and test:
            assert str(pc) not in scenario.get('branch_tables', {}), 'suffix has an unmodeled dispatch branch'
            assert row['direct'] or scenario['indirect_branch']['source'] == 'microword'
        assert pc not in scenario['io']['read']['pc_sequences'] or pc in (0x225,0x089), 'suffix needs another input cursor'
        branch = row['branch']
        index = None
        if pc in (0x07e,0x081):
            table = scenario['dispatch']['tables'][str(pc)]
            assert table['index_source'] == 'previous_y'
            index = previous['y']
            branch = table_targets(table)[index%16]
            dispatches.append(dict(pc=pc, index=index, target=branch, register=branch-0x08a))
        before = dict(sp=seq.sp, depth=depth)
        if row['command'] == 5 or row['command'] == 4 and test:
            depth += 1
            maximum = max(maximum, depth)
        if row['command'] in (2,3):
            depth -= 1
        assert 0 <= depth <= 4 and not row['unused']
        seq.step(row['command'], branch, test)
        trace.append(dict(cycle=snapshot['cycle']+offset, pc=pc, next_pc=seq.pc,
            alu=result, test=test, carry_in=carry_in, q=cpu.q,
            registers={str(i):v for i,v in enumerate(cpu.ram) if v != old_ram[i]},
            stack_before=before, stack_after=dict(sp=seq.sp, depth=depth, values=seq.stack[:]),
            dispatch_input=index, input_value=operand))
        previous = result
    raise AssertionError('restored suffix did not reach 084')


def verify_full(mapping, scenario, config, snapshot, got, out):
    result = execute(mapping, scenario, config['cycles'], seed=config['seed'], mode='integrated', out=out, trace_limit=config['cycles'])
    assert result['clean'] and result['final_state']['pc'] == 0x084
    assert all(result['final_state'][k] == got[k] for k in ('ram','q','sp','stack'))
    trace = load_trace(out)
    prefix = load_trace(out.parent/'prefix')
    assert trace[:snapshot['cycle']] == prefix
    for actual, restored in zip(trace[snapshot['cycle']:], got['trace']):
        for key,value in restored.items():
            if key == 'input_value':
                assert actual['external_read']['value'] == value
            else:
                assert actual.get(key) == value, (key,actual,restored)
    assert trace[snapshot['cycle']+got['cycles']]['pc'] == 0x084
    return result['trace_digest']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=HERE/'results/register-contract-study')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    config = read(HERE/'register-contract-study.json')
    base_path = HERE/config['base']
    mapping, base = read(base_path/'mapping.json'), read(base_path/'scenario.json')
    rows = decode(mapping)
    assert base['initial'] == dict(pc=0,ram=[0]*16,q=0)
    assert base['condition']['mode'] == 'flags' and 'random' not in base['condition']['sources']
    snapshot = capture(mapping, base, config, args.out/'prefix')
    counts = Counter()
    values = set()
    digest = hashlib.sha256()
    witnesses = []
    for payload in range(256):
        for first in range(16):
            for second in range(16):
                scenario = scenario_for(base, config, payload, first, second, snapshot['ram'][6])
                got = resume(rows, scenario, snapshot, payload, first, second)
                want = prediction(snapshot, payload, base['io']['read']['value'], first, second)
                assert got['ram'] == want['ram'] and got['q'] == want['q']
                assert got['cycles'] == 42 and got['max_depth'] == 4
                assert [t['index'] for t in got['dispatches']] == [first,second]
                assert [t['register'] for t in got['dispatches']] == [first,second]
                lost = got['ram'][first] != want['value']
                assert lost == (first == 5 and second != 5)
                counts['contract_cases'] += 1
                counts['first_value_absent_at_finish'] += int(lost)
                counts['first_destination_r6'] += int(first == 6)
                values.add(want['value'])
                digest.update(json.dumps([payload,first,second,got],sort_keys=True,separators=(',',':')).encode())
                if [payload,first,second] in config['witnesses']:
                    out = args.out/f'q{payload:02x}-r{first:02d}-r{second:02d}'
                    trace_digest = verify_full(mapping,scenario,config,snapshot,got,out)
                    witnesses.append(dict(path=out.name,payload=payload,first=first,second=second,
                        inputs=inputs_for(snapshot,payload,first,second),prediction=want,
                        dispatches=got['dispatches'],first_value_absent_at_finish=lost,trace_digest=trace_digest))
                if first == 6:
                    naive = resume(rows, scenario, snapshot, payload, first, second, adjust=False)
                    actual_second = naive['dispatches'][1]['register']
                    bad = actual_second != second
                    assert actual_second == ((snapshot['ram'][6]+second-(payload>>1))&255)%16
                    naive_want = prediction(snapshot,payload,base['io']['read']['value'],first,actual_second)
                    assert naive['ram'] == naive_want['ram'] and naive['q'] == payload
                    counts['unadjusted_cases'] += 1
                    counts['unadjusted_wrong_second_address'] += int(bad)
                    if [payload,first,second] == config['unadjusted_witness']:
                        out = args.out/'unadjusted'
                        bad_scenario = scenario_for(base,config,payload,first,second,snapshot['ram'][6],adjust=False)
                        trace_digest = verify_full(mapping,bad_scenario,config,snapshot,naive,out)
                        witnesses.append(dict(path=out.name,payload=payload,first=first,second=second,
                            inputs=inputs_for(snapshot,payload,first,second,False),prediction=naive_want,
                            dispatches=naive['dispatches'],trace_digest=trace_digest))
        if payload%64 == 63:
            print(payload+1, 'payloads', dict(counts), flush=True)
    sources = [Path(__file__), HERE/'register-contract-study.json',
        *(base_path/name for name in ('mapping.json','scenario.json','summary.json','trace.jsonl')),
        HERE/'affine_tail_study.py', HERE/'common.py', HERE/'execute.py', HERE/'defined_condition_fit.py', HERE.parent/'model.py']
    save(args.out/'report.json', dict(configuration=config, snapshot=snapshot, counts=dict(counts),
        stored_values=sorted(values), execution_sha256=digest.hexdigest(), witnesses=witnesses,
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='Constructed diagnostic input contract under q2 and preceding-Y terminal indexing. Exhaustive suffixes restore a freshly replayed zero-reset prefix, including its real four-frame stack; selected full core runs match every restored step. This is not a recovered board protocol. Stores contain Q>>1, and the first R5 store is overwritten; a second R5 store restores its value.'))


if __name__ == '__main__':
    main()
