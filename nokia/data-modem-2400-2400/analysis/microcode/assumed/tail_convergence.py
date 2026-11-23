"""Replay the adjustment tails and measure state convergence at their join."""
import argparse
import copy
import json
from pathlib import Path
from common import HERE, read, save
from execute import execute


def scenario(config, entry, select_value=0):
    s = read(HERE/f"results/independent-study/scenario-{config['variant']}.json")
    control = read(HERE/'results/third-case-study/scenario-all_cases.json')
    s.update(name=f'adjustment-convergence-{entry:03x}-{select_value}', status=config['status'],
             evidence=config['evidence'], dispatch=copy.deepcopy(control['dispatch']),
             branch_tables=copy.deepcopy(control['branch_tables']))
    s['initial'] = dict(pc=entry, ram=config['initial_ram'][:], q=config['q'])
    s['inputs']['carry']['initial'] = config['initial_carry']
    s['condition'].update(mode='per-select', per_select=[0]*8, polarity=[0]*8)
    s['condition']['per_select'][config['wrapper_select']] = select_value
    s['dispatch'].update(mode='constant', source='scenario', value=0)
    s['io'] = dict(read=dict(mode='constant', value=config['d'], table=[0]), writes=[])
    return s


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=HERE/'results/tail-convergence')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    config = read(HERE/'tail-convergence.json')
    mapping = read(HERE/f"results/independent-study/variant-{config['variant']}.json")
    runs = []
    traces = []
    for entry in config['entries']:
        out = args.out/f'tail-{entry:03x}'
        result = execute(mapping, scenario(config, entry), config['cycles'], mode='integrated', out=out,
                         trace_limit=config['cycles'])
        records = [json.loads(line) for line in (out/'trace.jsonl').read_text().splitlines()]
        traces.append(records)
        runs.append(dict(entry=entry, clean=result['clean'], final_state=result['final_state'],
                         carry=result['carry_model']['previous'], first_three=records[:3]))
    wrappers = []
    for value, cycles in ((1, 4), (0, 5)):
        out = args.out/f'wrapper-{value}'
        result = execute(mapping, scenario(config, config['wrapper'], value), cycles,
                         mode='integrated', out=out, trace_limit=cycles)
        records = [json.loads(line) for line in (out/'trace.jsonl').read_text().splitlines()]
        wrappers.append(dict(select_value=value, cycles=cycles, clean=result['clean'],
                             path=[r['pc'] for r in records], final_state=result['final_state'],
                             last_alu=records[-1]['alu'], carry=result['carry_model']['previous']))
    report = dict(configuration=config, tails=runs, wrappers=wrappers,
                  joined_at_expected_pc=all(t[2]['next_pc']==config['join'] for t in traces)
                      and all(w['final_state']['pc']==config['join'] for w in wrappers),
                  tail_suffix_records_equal=traces[0][3:]==traces[1][3:],
                  tail_final_states_equal=runs[0]['final_state']==runs[1]['final_state'],
                  wrapper_join_states_equal=all(wrappers[0][k]==wrappers[1][k]
                                               for k in ('final_state','last_alu','carry')),
                  interpretation='Equal modeled state after the join under fixed inputs; first Y is transient. External side effects and clock-relative behavior remain unknown.')
    save(args.out/'report.json', report)
    print({k:v for k,v in report.items() if k not in ('configuration','tails','wrappers','interpretation')})


if __name__ == '__main__':
    main()
