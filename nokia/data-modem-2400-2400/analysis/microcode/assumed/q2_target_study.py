"""Follow R10 writers across all eight q2 reset dispatch choices."""
import argparse
import copy
import hashlib
import json
import tempfile
from collections import Counter
from pathlib import Path
from common import HERE, decode, read, save
from defined_condition_fit import load_trace
from execute import execute


def inspect(trace, rows, sequences):
    ram = [0] * 16
    q = 0
    writers = {}
    events = []
    counts = Counter()
    visits = Counter()
    seen = {}
    repeat = None
    for t in trace:
        pc = t['pc']
        row = rows[pc]
        writes_target = row['i'] >> 6 >= 2 and row['b'] == 10
        if (writes_target or pc in (0x126, 0x12c, 0x389, 0x390, 0x399)) and counts[pc] == 0:
            events.append(dict(pc=pc, cycle=t['cycle'], ram_before=ram[:], q_before=q,
                               source_writer=writers.get(row['a']), target_writer=writers.get(10),
                               alu=t['alu'], next_pc=t['next_pc']))
        counts[pc] += 1
        for register, value in t['registers'].items():
            ram[int(register)] = value
        if row['i'] >> 6 >= 2:
            writers[row['b']] = dict(pc=pc, cycle=t['cycle'])
        q = t['q']
        if str(pc) in sequences:
            visits[str(pc)] += 1
        phases = {p: min(visits[p], len(values)-1) for p, values in sequences.items()}
        key = json.dumps([t['next_pc'], ram, q, t['alu'], t['stack_after'], phases], sort_keys=True)
        if key in seen and repeat is None:
            repeat = dict(next_pc=t['next_pc'], first_cycle=seen[key], second_cycle=t['cycle'],
                          period=t['cycle']-seen[key])
        seen[key] = t['cycle']
    return dict(events=events, repeat=repeat,
                target_writer_pcs=sorted(p for p in counts if rows[p]['i'] >> 6 >= 2 and rows[p]['b'] == 10),
                poll_pcs=sorted(p for p in (0x126, 0x12c) if counts[p]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=HERE/'results/q2-target-study')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    config = read(HERE/'q2-target-study.json')
    mapping = read(HERE/config['mapping'])
    base = read(HERE/config['scenario'])
    rows = decode(mapping)
    target_writers = [dict(pc=r['pc'], a=r['a'], operation=r['operation'], carry=r['carry'])
                      for r in rows if r['i'] >> 6 >= 2 and r['b'] == 10 and not r['unused']]
    assert [r['pc'] for r in target_writers] == [0x94, 0x38c, 0x3dc, 0x3e0, 0x3e4, 0x3e8]
    runs = []
    counts = Counter()
    with tempfile.TemporaryDirectory() as temporary:
        for index in range(8):
            for d in range(256):
                scenario = copy.deepcopy(base)
                scenario['initial'] = dict(pc=0, ram=[0]*16, q=0)
                scenario['dispatch']['value'] = index
                sequences = {str(p): [d, 0] for p in config['reply_sites']}
                scenario['io']['read'] = dict(mode='pc_sequence', value=d, table=[0],
                    pc_sequences=sequences, sequence_end='hold-last', status='stub', evidence=config['evidence'])
                out = args.out/f'index{index}-d{d:02x}' if d in config['witness_values'] else Path(temporary)
                result = execute(mapping, scenario, config['cycles'], mode='integrated', out=out, trace_limit=config['cycles'])
                assert result['clean']
                observed = inspect(load_trace(out), rows, sequences)
                assert observed['repeat'] is not None
                assert observed['target_writer_pcs'] == ([0x38c] if index == 5 else [])
                assert bool(observed['poll_pcs']) == (index == 0)
                for event in observed['events']:
                    if event['pc'] in (0x126, 0x12c):
                        assert event['ram_before'][10] == event['q_before'] == 0
                        assert event['target_writer'] is None
                    if event['pc'] == 0x38c:
                        assert index == 5 and event['alu']['f'] == (d-1)&255
                        assert event['source_writer']['pc'] == 0x118
                repetition = observed['repeat']
                if index == 5:
                    last = next(e for e in observed['events'] if e['pc'] == 0x399)
                    value = (d-1)&255
                    assert all(last['ram_before'][r] == value for r in (6,7,10,11))
                    assert last['alu']['f'] == (2*value + (2*value >> 8))&255
                    assert repetition['period'] == (1 if d == 1 else 12)
                    assert (result['final_state']['pc'] == 0x84) == (d == 1)
                counts[f"{index}:{repetition['next_pc']:03x}/{repetition['period']}"] += 1
                runs.append(dict(index=index, d=d, observed=observed, final_pc=result['final_state']['pc'],
                                 trace_digest=result['trace_digest']))
            print(index, {k:v for k,v in counts.items() if k.startswith(f'{index}:')}, flush=True)
    sources = [Path(__file__), HERE/'q2-target-study.json', HERE/config['mapping'], HERE/config['scenario'],
               HERE/'execute.py', HERE/'common.py', HERE.parent/'model.py']
    save(args.out/'report.json', dict(configuration=config, target_writers=target_writers, counts=dict(counts), runs=runs,
         source_sha256={str(p.relative_to(HERE.parent)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
         interpretation='All eight global dispatch choices with early zero replies: nonzero R10 can originate in captured R6, but no tested reset run carries a written R10 into either masked helper. No physical input or dispatch wiring identified.'))


if __name__ == '__main__':
    main()
