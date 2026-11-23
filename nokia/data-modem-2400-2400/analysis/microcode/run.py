"""Execute real PROM bytes under an explicitly supplied, possibly speculative map."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from model import Am2901, X8X02, UnknownStack

HERE = Path(__file__).resolve().parent
NOKIA = HERE.parents[2]
ROMS = {
    '10': ('810237c', 'eae7ef704a0f6a1d262134826d364bd651a99351ebb395eaf19c78790b67e2bc'),
    '11': ('810238c', '260733c911c861d6ae19a28ce48717b1fe755e79636ab3da6f9b9b10e65a3939'),
    '17': ('810239c', '52972d336004697ae3883784a477bbfa0bcccc5f003995d7288e0669ae7fa231'),
    '18': ('810240c', 'e44a0e77fbcb525f5a758ea3db85c2d6b82021c2f73af30514ce9f4837abbb6b'),
}


def load():
    lanes = {}
    for chip, (label, sha) in ROMS.items():
        data = (NOKIA / 'unknown-modem-810237c' / f'chip{chip}-{label}.bin').read_bytes()
        if len(data) != 1024 or hashlib.sha256(data).hexdigest() != sha:
            raise ValueError(f'chip {chip}: ROM size or SHA-256 mismatch')
        lanes[chip] = data
    return lanes


def field_value(spec, lanes, pc):
    # LSB-first list, e.g. ["10.0", "10.1", "!17.3"]; integer constants.
    if isinstance(spec, int):
        return spec
    value = 0
    for index, token in enumerate(spec):
        invert = token.startswith('!')
        chip, bit = token.lstrip('!').split('.')
        value |= ((((lanes[chip][pc] >> int(bit)) & 1) ^ invert) << index)
    return value


def execute(mapping, cycles, path, test):
    lanes = load()
    cpu, seq = Am2901(), X8X02()
    visited, seen = set(), {}
    reason = 'cycle limit'
    with path.open('w') as out:
        writer = csv.writer(out, lineterminator='\n')
        writer.writerow(['cycle', 'pc', 'chip10', 'chip11', 'chip17', 'chip18',
                         'i', 'a', 'b', 'd', 'command', 'branch', 'test', 'f', 'y', 'q', 'next_pc'])
        for cycle in range(cycles):
            state = (seq.pc, seq.sp, tuple(seq.stack), tuple(cpu.ram), cpu.q)
            if state in seen:
                reason = f'repeated complete modeled state; period {cycle - seen[state]}'
                break
            seen[state] = cycle
            pc = seq.pc
            visited.add(pc)
            v = {k: field_value(s, lanes, pc) for k, s in mapping['fields'].items()}
            result = cpu.step(v['i'], v['a'], v['b'], v['d'], v['carry'], v['ram_in'], v['q_in'])
            condition = test if test in (0, 1) else result['zero']
            try:
                seq.step(v['command'], v['branch'], condition)
            except UnknownStack as err:
                reason = str(err)
                seq.pc = None
            writer.writerow([cycle, f'{pc:03x}', *[f'{lanes[c][pc]:02x}' for c in ROMS],
                             v['i'], v['a'], v['b'], v['d'], v['command'], v['branch'],
                             condition, result['f'], result['y'], cpu.q,
                             '' if seq.pc is None else f'{seq.pc:03x}'])
            if seq.pc is None:
                break
    return dict(mapping=mapping['name'], status=mapping['status'], test=test,
                executed=len(seen), unique_addresses=len(visited), stop=reason,
                interpretation='Hypothesis experiment only; not a verified Nokia execution.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mapping', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--cycles', type=int, default=10000)
    args = parser.parse_args()
    mapping = json.loads(args.mapping.read_text())
    args.out.mkdir(parents=True, exist_ok=True)
    results = [execute(mapping, args.cycles, args.out / f'test-{t}.csv', t) for t in (0, 1, 'zero')]
    (args.out / 'summary.json').write_text(json.dumps(results, indent=2) + '\n')
    print(json.dumps(results, indent=2))
