"""Follow input-selected handlers with matched and crossed flag/reply timing."""
import argparse
import hashlib
import shutil
import tempfile
from collections import Counter
from pathlib import Path
from common import HERE, read, save
from execute import execute
from external_line import external_line_phase
from defined_condition_fit import load_trace
from selector_prefix_study import scenario_for


def scenario_for_case(config, profile, timing, replies, q):
    base, tables = (read(HERE/config[k]) for k in ('scenario', 'tables'))
    scenario = scenario_for(base, tables, config, 'q', 1, [165, (q-165)&255])
    scenario['name'] = f'handler timing {profile} {timing} {replies} Q={q:02X}'
    scenario['condition']['flag_timing'] = timing
    sequences = scenario['io']['read']['pc_sequences']
    for pc in (0x117, 0x106):
        del sequences[str(pc)]
    for pc in ((0x117, 0x106) if replies == 'plp' else (0x118, 0x107)):
        sequences[str(pc)] = [1, 0]
    return scenario


def classify(trace, scenario):
    """Prove recurrence including saturated input cursors and stale stack slots.

    This key is sufficient only for this deterministic, constant-dispatch study.
    The ALU carry is also the carry-feedback state. Log counters have no effect
    on execution. Preserve all flags/Y, not merely the currently tested flag.
    """
    assert scenario['dispatch']['mode'] == 'constant'
    assert scenario['io']['read']['mode'] == 'pc_sequence'
    assert scenario['io']['read']['sequence_end'] == 'hold-last'
    ram = scenario['initial']['ram'][:]
    sequences = scenario['io']['read']['pc_sequences']
    visits = Counter()
    seen = {}
    dispatch = terminal = repeat = None
    for row in trace:
        pc = row['pc']
        visits[str(pc)] += 1
        for register, value in row['registers'].items():
            ram[int(register)] = value
        if pc == 0x109 and dispatch is None:
            dispatch = dict(cycle=row['cycle'], index=row['dispatch_input'], entry=row['dispatch_entry'])
        if pc == 0x084 and terminal is None:
            terminal = row['cycle']
        stack = row['stack_after']
        key = (row['next_pc'], tuple(ram), row['q'], tuple(sorted(row['alu'].items())),
               stack['sp'], stack['depth'], tuple(stack['values']),
               tuple((pc, min(visits[pc], len(values)-1)) for pc, values in sorted(sequences.items())))
        if isinstance(scenario['inputs']['external'],dict):
            key += (external_line_phase(scenario['inputs']['external'],row['cycle']+1),)
        if key in seen and repeat is None:
            repeat = dict(first_after_cycle=seen[key], after_cycle=row['cycle'],
                          period=row['cycle']-seen[key], next_pc=row['next_pc'])
        seen.setdefault(key, row['cycle'])
    assert repeat is not None, 'bound did not establish a repeated state'
    return dict(outcome='terminal' if terminal is not None else 'repeat',
                first_terminal=terminal, dispatch=dispatch, repeat=repeat,
                transform_entries=sorted({r['pc'] for r in trace if r['pc'] in (0x3EA,0x3D5,0x3C0)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=HERE/'results/handler-timing-study')
    args = parser.parse_args(); args.out.mkdir(parents=True, exist_ok=True)
    config = read(HERE/'handler-timing-study.json')
    runs = []; witnesses = []; counts = Counter(); chosen = set()
    with tempfile.TemporaryDirectory() as temporary:
        out = Path(temporary)/'run'
        for profile, path in config['profiles'].items():
            mapping = read(HERE/path)
            for timing in ('previous', 'current'):
                for replies in ('plp', 'blt'):
                    for q in range(256):
                        scenario = scenario_for_case(config, profile, timing, replies, q)
                        result = execute(mapping, scenario, config['cycles'], mode='integrated', out=out, trace_limit=config['cycles'])
                        assert result['clean'] and result['unused_word_executions'] == 0
                        trace = load_trace(out)
                        finding = classify(trace, scenario)
                        case = dict(profile=profile, timing=timing, replies=replies, input_sum=q,
                                    trace_digest=result['trace_digest'], max_depth=result['stack']['max_depth'], **finding)
                        runs.append(case)
                        counts[f'{profile}:{timing}:{replies}:{finding["outcome"]}'] += 1
                        group = (profile,timing,replies,q%8 if finding['dispatch'] else None)
                        if group not in chosen or q == 255:
                            chosen.add(group)
                            name = f'{profile}-{timing}-{replies}-{q:02x}'
                            shutil.copytree(out,args.out/name,dirs_exist_ok=True)
                            witnesses.append(dict(path=name, **case))
                    print(profile,timing,replies,flush=True)
    sources = [Path(__file__), HERE/'handler-timing-study.json', HERE/'selector_prefix_study.py',
               HERE/'execute.py', HERE/'common.py', HERE/'defined_condition_fit.py', HERE.parent/'model.py',
               HERE/config['scenario'], HERE/config['tables'], *(HERE/p for p in config['profiles'].values())]
    save(args.out/'report.json',dict(configuration=config,counts=dict(counts),runs=runs,witnesses=witnesses,
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}))


if __name__ == '__main__': main()
