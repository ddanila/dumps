"""Compare actual datapath index candidates at q2's paired-arithmetic call 38F."""
import argparse
import copy
import hashlib
import json
import tempfile
from collections import Counter
from pathlib import Path
from common import HERE, read, save
from defined_condition_fit import load_trace
from execute import execute


def inspect(trace, sequences):
    ram = [0] * 16
    q = previous_y = 0
    counts = Counter()
    visits = Counter()
    events = []
    seen = {}
    repeat = None
    for t in trace:
        pc = t['pc']
        if pc in (0x38e, 0x38f, 0x390, 0x391, 0x36c, 0x36d) and counts[pc] == 0:
            events.append(dict(pc=pc, cycle=t['cycle'], ram_before=ram[:], q_before=q,
                previous_y=previous_y, alu=t['alu'], carry_in=t['carry_in'], test=t['test'],
                next_pc=t['next_pc'], dispatch_input=t.get('dispatch_input'), dispatch_entry=t.get('dispatch_entry')))
        counts[pc] += 1
        for register, value in t['registers'].items():
            ram[int(register)] = value
        q = t['q']
        previous_y = t['alu']['y']
        if str(pc) in sequences:
            visits[str(pc)] += 1
        phases = {p: min(visits[p], len(values)-1) for p, values in sequences.items()}
        key = json.dumps([t['next_pc'], ram, q, t['alu'], t['stack_after'], phases], sort_keys=True)
        if key in seen and repeat is None:
            repeat = dict(next_pc=t['next_pc'], first_cycle=seen[key], second_cycle=t['cycle'],
                          period=t['cycle']-seen[key])
        seen[key] = t['cycle']
    return dict(events=events, repeat=repeat, wrapper_returns=counts[0x391],
                poll_pcs=sorted(p for p in (0x126, 0x12c) if counts[p]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=HERE/'results/q2-dispatch-study')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    config = read(HERE/'q2-dispatch-study.json')
    mapping = read(HERE/config['mapping'])
    base = read(HERE/config['scenario'])
    runs = []
    counts = Counter()
    with tempfile.TemporaryDirectory() as temporary:
        for source in config['sources']:
            for d in range(256):
                scenario = copy.deepcopy(base)
                scenario['initial'] = dict(pc=0, ram=[0]*16, q=0)
                scenario['dispatch']['value'] = 5
                scenario['dispatch']['initial_y'] = 0
                table = scenario['dispatch']['tables'][str(config['site'])]
                table['index_source'] = source
                table['evidence'] = config['evidence']
                sequences = {str(p): [d, 0] for p in config['reply_sites']}
                scenario['io']['read'] = dict(mode='pc_sequence', value=d, table=[0],
                    pc_sequences=sequences, sequence_end='hold-last', status='stub', evidence=config['evidence'])
                out = args.out/f'{source}-d{d:02x}' if d in config['witness_values'] else Path(temporary)
                result = execute(mapping, scenario, config['cycles'], mode='integrated', out=out, trace_limit=config['cycles'])
                assert result['clean']
                observed = inspect(load_trace(out), sequences)
                event = lambda pc: next(e for e in observed['events'] if e['pc'] == pc)
                before = event(0x38e)
                dispatch = event(0x38f)
                assert before['ram_before'][14] == 0 and before['alu']['y'] == d
                assert dispatch['previous_y'] == d and dispatch['q_before'] == dispatch['alu']['y'] == 0
                index = dict(scenario=5, y=0, q=0, previous_y=d)[source]
                entry = index % 4
                assert dispatch['dispatch_input'] == index and dispatch['dispatch_entry'] == entry
                assert dispatch['next_pc'] == 0x392 + 4*entry
                value = (d-1)&255
                assert all(dispatch['ram_before'][r] == value for r in (6,7,10,11))
                returns = d == 1 or entry >= 2
                assert observed['wrapper_returns'] == int(returns)
                assert not observed['poll_pcs']
                if returns:
                    assert event(0x391)['next_pc'] == 0x347
                    carry_loop = event(0x36d)
                    assert carry_loop['ram_before'][0] == 255
                    assert carry_loop['ram_before'][1] == value and carry_loop['carry_in'] == 1
                    assert carry_loop['alu']['f'] == (2*d)&255
                    assert carry_loop['alu']['carry'] == int(d >= 128)
                terminal = returns and d < 128
                assert (result['final_state']['pc'] == 0x84) == terminal
                assert result['final_state']['ram'][10] == value
                repeat = observed['repeat']
                assert repeat is not None
                expected_period = 1 if terminal else 3 if returns else 12
                assert repeat['period'] == expected_period
                outcome = 'terminal' if terminal else 'carry-loop' if returns else 'paired-loop'
                counts[f'{source}:{outcome}'] += 1
                runs.append(dict(source=source, d=d, outcome=outcome, observed=observed,
                                 final_state=result['final_state'], trace_digest=result['trace_digest']))
            print(source, {k:v for k,v in counts.items() if k.startswith(source+':')}, flush=True)
    sources = [Path(__file__), HERE/'q2-dispatch-study.json', HERE/config['mapping'], HERE/config['scenario'],
               HERE/'execute.py', HERE/'common.py', HERE.parent/'model.py']
    save(args.out/'report.json', dict(configuration=config, counts=dict(counts), runs=runs,
         source_sha256={str(p.relative_to(HERE.parent)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
         interpretation='Preceding Y at 38F carries D from 38E and selects all four paired-arithmetic entries. Current Y and Q are zero. This candidate releases nonzero captured data from the wrapper, but does not identify physical dispatch wiring or useful external outputs.'))


if __name__ == '__main__':
    main()
