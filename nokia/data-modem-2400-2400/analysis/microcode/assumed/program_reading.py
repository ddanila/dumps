"""Build an evidence-linked listing without merging incompatible model claims."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from common import HERE, decode, read, save, table_targets
from analyze import graph, walk


def annotations_by_pc(config):
    indexed = [[] for _ in range(1024)]
    names = set()
    for note in config['annotations']:
        if note['name'] in names or note['status'] != 'hypothesis':
            raise ValueError('duplicate name or unsupported interpretation status')
        names.add(note['name'])
        if not note['profiles'] or not set(note['profiles']) <= set(config['profiles']):
            raise ValueError('annotation has unknown or empty profile scope')
        if not (HERE/note['evidence']).is_file() or not note['limitations']:
            raise ValueError('annotation lacks evidence or limitations')
        for low, high in note['ranges']:
            low, high = int(low, 16), int(high, 16)
            if not 0 <= low <= high < 1024:
                raise ValueError('annotation range outside control store')
            for pc in range(low, high+1):
                indexed[pc].append(note)
    return indexed


def build(config):
    notes = annotations_by_pc(config)
    rows = decode(read(HERE/'sequencer.json'))
    scenario = read(HERE/config['scenario'])
    cfg = graph(rows, scenario)
    sweep = read(HERE/config['sequencer_sweep'])
    reached = set(cfg['reached'])
    dynamic = set(sweep['reached'])
    if cfg['exceptions'] or sweep['static_words'] != len(reached) or not dynamic <= reached:
        raise ValueError('static graph and sweep disagree')
    if sorted(sweep['remaining']) != [r['pc'] for r in cfg['unreachable']]:
        raise ValueError('unresolved-word set changed')
    examples = {name:read(HERE/path) for name,path in config['reset_examples'].items()}
    profiles = {name:decode(read(HERE/path)) for name,path in config['profiles'].items()}
    for name, profile in profiles.items():
        if any(any(a[k] != b[k] for k in ('raw','command','branch','select','direct')) for a,b in zip(rows,profile)):
            raise ValueError(f'{name}: control decode differs; cannot share this listing')
    callers = {}
    for r in rows:
        if r['command'] == 4 and r['direct'] and str(r['pc']) not in scenario['dispatch']['tables']:
            callers.setdefault(r['branch'], []).append(r['pc'])
    listing = []
    for r in rows:
        pc = r['pc']
        table = (scenario['dispatch']['tables'].get(str(pc)) if r['command'] == 4 else
                 scenario.get('branch_tables', {}).get(str(pc)) if r['command'] == 6 else None)
        item = dict(pc=f'{pc:03X}', raw=bytes(r['raw']).hex().upper(), used=not r['unused'],
                    command=r['command_name'], encoded_target=f"{r['branch']:03X}",
                    select=r['select'], direct=r['direct'], static_reachable=pc in reached,
                    sequencer_sweep_visited=pc in dynamic,
                    explanation_status='unused all-FF word' if r['unused'] else
                        'unresolved entry' if pc not in reached else 'reachable under scenario',
                    direct_callers=' '.join(f'{p:03X}' for p in callers.get(pc, [])),
                    annotations=json.dumps(notes[pc], sort_keys=True),
                    dispatch=json.dumps(table, sort_keys=True) if table is not None else '')
        for name, example in examples.items():
            item[f'reset_{name}_visited'] = pc in example['visited']
        for name, profile in profiles.items():
            op = profile[pc]
            item[f'{name}_operation'] = (f"{op['operation']}; A=R{op['a']}; B=R{op['b']}; "
                                       f"mapped_carry={op['carry']}; carry_feedback_select={op['carry_select']}")
            item[f'{name}_labels'] = '; '.join(n['name'] for n in notes[pc] if name in n['profiles'])
        listing.append(item)
    structural = [dict(entry=f'{pc:03X}', callers=[f'{p:03X}' for p in sites],
                       linear_walk_hint=walk(rows, pc), annotations=notes[pc],
                       limitation='Linear walk is a boundary hint, not a complete control-flow or algorithm description.')
                  for pc,sites in sorted(callers.items())]
    dependencies = {'sequencer.json', config['scenario'], config['sequencer_sweep'],
                    *config['profiles'].values(), *config['reset_examples'].values(),
                    *(n['evidence'] for n in config['annotations'])}
    metadata = dict(configuration=config,
        source_sha256={p:hashlib.sha256((HERE/p).read_bytes()).hexdigest() for p in sorted(dependencies)},
        counts=dict(words=len(rows), used=sum(not r['unused'] for r in rows),
                    static_reachable=len(reached), sequencer_sweep_visited=len(dynamic),
                    annotated_used_words=sum(bool(notes[r['pc']]) for r in rows if not r['unused']),
                    reset_examples={name:len(r['visited']) for name,r in examples.items()}),
        unresolved=[f"{r['pc']:03X}" for r in cfg['unreachable']],
        direct_call_entries=structural,
        dispatches=[dict(pc=f'{r["pc"]:03X}', targets=[f'{p:03X}' for p in table_targets(table)])
                    for r in rows for table in [scenario['dispatch']['tables'].get(str(r['pc'])) if r['command']==4
                        else scenario.get('branch_tables',{}).get(str(r['pc'])) if r['command']==6 else None] if table is not None],
        interpretation='Evidence index, not a new execution or hardware decode. Profile scopes and scenario coverage remain separate; annotations are not a percentage of understood modem functionality.')
    return listing, metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=HERE/'results/program-reading')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    listing, metadata = build(read(HERE/'program-reading.json'))
    with (args.out/'listing.csv').open('w') as f:
        writer = csv.DictWriter(f, fieldnames=list(listing[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(listing)
    save(args.out/'catalog.json', metadata)
    print(metadata['counts'])


if __name__ == '__main__':
    main()
