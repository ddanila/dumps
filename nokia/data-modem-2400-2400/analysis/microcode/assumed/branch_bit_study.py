"""Test global B0/B9 replacements against reset-reachable stack constraints."""
import argparse
import copy
from collections import deque
from pathlib import Path
from common import HERE, decode, read, save
from analyze import graph, must_targets


def replacement(base, position, token):
    mapping = copy.deepcopy(base)
    mapping['name'] = f'branch-bit-{position}-{token}'
    field = mapping['fields']['branch']
    field['bits'][position] = token
    field.update(status='hypothesis', evidence='Global single-bit replacement; all other fields and dispatch tables held fixed')
    return mapping


def failure_path(rows, scenario):
    cfg = graph(rows, scenario, include_states=True)
    failures = {int(x.split(':')[0], 16) for x in cfg['exceptions'] if ':' in x}
    adjacent = {}
    for source, target in cfg['state_edges']:
        adjacent.setdefault(source, []).append(target)
    root = (0, ())
    parents = {root: None}
    queue = deque([root])
    while queue:
        state = queue.popleft()
        pc, stack = state
        row = rows[pc]
        fails = row['unused'] or (row['command'] in (2, 3) and not stack) or (row['command'] in (4, 5) and len(stack) == 4)
        if pc in failures and fails:
            path = []
            while state is not None:
                path.append(dict(pc=state[0], stack=list(state[1])))
                state = parents[state]
            return list(reversed(path))
        for target in sorted(adjacent.get(state, [])):
            if target not in parents:
                parents[target] = state
                queue.append(target)
    return []


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=HERE/'results/branch-bit-study')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    config = read(HERE/'branch-bit-search.json')
    base = read(HERE/'sequencer.json')
    scenario = read(HERE/config['scenario'])
    original = decode(base)
    baseline = graph(original, scenario)
    required = set(must_targets(original))
    reports = []
    for position in config['positions']:
        for chip in config['chips']:
            for bit in range(8):
                for polarity in ('', '!'):
                    token = f'{polarity}{chip}.{bit}'
                    mapping = replacement(base, position, token)
                    rows = decode(mapping)
                    cfg = graph(rows, scenario)
                    transfers = [r for r in rows if not r['unused'] and r['command'] in (4, 6) and r['direct']]
                    reports.append(dict(position=position, token=token, states=cfg['states'],
                        static_used_words=sum(not rows[p]['unused'] for p in cfg['reached']),
                        exceptions=cfg['exceptions'], must_target_score=len(required & {r['branch'] for r in transfers}),
                        changed_transfers=[dict(pc=r['pc'], before=original[r['pc']]['branch'], after=r['branch'])
                                           for r in transfers if r['branch'] != original[r['pc']]['branch']],
                        gained=sorted(set(cfg['reached'])-set(baseline['reached'])),
                        lost=sorted(set(baseline['reached'])-set(cfg['reached']))))
    witnesses = []
    for position, token in config['witnesses']:
        mapping = replacement(base, position, token)
        witnesses.append(dict(position=position, token=token, mapping=mapping,
                              path=failure_path(decode(mapping), scenario)))
    save(args.out/'report.json', dict(configuration=config, baseline_words=len(baseline['reached']),
                                    candidates=reports, witnesses=witnesses))
    clean = [r for r in reports if not r['exceptions']]
    print('Candidates:', len(reports), 'clean:', [(r['position'], r['token'], r['static_used_words']) for r in clean])


if __name__ == '__main__':
    main()
