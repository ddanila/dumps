"""Classify disconnected fragments and test their paired arithmetic tails."""
import argparse
import copy
import itertools
from pathlib import Path
from common import HERE, decode, read, save
from analyze import graph
from execute import CarryInput
from model import Am2901, X8X02
from rom_study import load_rom


def tail(rows, policy, start, ram, q, d, initial):
    policy = copy.deepcopy(policy)
    policy['initial'] = initial
    carry = CarryInput(policy)
    alu = Am2901(ram=ram[:], q=q)
    seq = X8X02(pc=start)
    ys = []
    states = []
    for pc in range(start, start+3):
        row = rows[pc]
        expected = 1 if pc < start+2 else 6
        if row['command'] != expected or (expected == 6 and (row['select'] != 0 or not row['direct'])):
            raise ValueError('expected two INC words followed by an unconditional direct BRT')
        result = alu.step(row['i'], row['a'], row['b'], d, carry.resolve(row))
        carry.observe(result)
        seq.step(row['command'], row['branch'], True)
        ys.append(result['y'])
        states.append(dict(pc=seq.pc, sp=seq.sp, stack=seq.stack[:],
                           datapath=dict(ram=alu.ram[:], q=alu.q, flags=result, carry=carry.previous)))
    return dict(y=ys, state_preserved=alu.ram == ram and alu.q == q, states=states)


def arithmetic(config):
    reports = []
    for variant in config['variants']:
        rows = decode(read(HERE/f'results/independent-study/variant-{variant}.json'))
        policy = read(HERE/f'results/independent-study/scenario-{variant}.json')['inputs']['carry']
        cases = failures = convergence_failures = 0
        examples = []
        for a, b, q, d, initial in itertools.product(config['a_values'], range(256), config['q_values'],
                                                   config['d_values'], config['initial_carries']):
            ram = [(17*i+3)&255 for i in range(16)]
            ram[0], ram[12], ram[15] = a, b, b ^ 0x5a
            pair = [tail(rows, policy, start, ram, q, d, initial) for start in config['tails']]
            valid = (all(x['state_preserved'] for x in pair)
                     and ((pair[1]['y'][0]-pair[0]['y'][0]) & 255) == 1
                     and pair[0]['y'][1:] == pair[1]['y'][1:])
            cases += 1
            failures += not valid
            convergence_failures += (pair[0]['states'][1]['datapath'] != pair[1]['states'][1]['datapath']
                                     or pair[0]['states'][2] != pair[1]['states'][2])
            if (a == 85 and b in (0, 255) and q == 165 and d == 255 and initial == 1) or (not valid and len(examples)<10):
                examples.append(dict(a=a, b=b, q=q, d=d, initial_carry=initial, pair=pair, valid=valid))
        reports.append(dict(variant=variant, paired_cases=cases, failures=failures,
                            convergence_failures=convergence_failures, examples=examples,
                            decoded_tails=[[rows[p] for p in range(start,start+3)] for start in config['tails']]))
    return reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=HERE/'results/fragment-study')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    config = read(HERE/'fragment-search.json')
    data = load_rom(config)
    scenario = read(HERE/config['scenario'])
    rows = decode(read(HERE/'sequencer.json'))
    baseline = graph(rows, scenario)
    unresolved = {r['pc'] for r in baseline['unreachable']}
    records = []
    incoming = set()
    for pc in sorted(unresolved):
        empty = graph(rows, scenario, start=pc)
        caller = graph(rows, scenario, start=pc, initial_stack=(-1,), return_sentinel=-1)
        incoming.update(b for a,b,_ in empty['edges'] if a in unresolved and b in unresolved)
        records.append(dict(pc=pc, raw=rows[pc]['raw'], command=rows[pc]['command_name'],
            rom_offsets=[i for i,value in enumerate(data) if value == (pc & 255)],
            empty=dict(exceptions=empty['exceptions'], unresolved_reached=sorted(unresolved & set(empty['reached']))),
            caller=dict(exceptions=caller['exceptions'], returns=caller['terminal_return_reached'],
                        unresolved_reached=sorted(unresolved & set(caller['reached'])))))
    roots = sorted(unresolved-incoming)
    save(args.out/'report.json', dict(configuration=config, reset_reachable=len(baseline['reached']),
        unresolved=sorted(unresolved), roots_without_internal_predecessor=roots,
        roots_absent_from_rom=[r['pc'] for r in records if r['pc'] in roots and not r['rom_offsets']],
        fragments=records, arithmetic=arithmetic(config)))
    print('Unresolved:', len(unresolved), 'roots:', [f'{p:03X}' for p in roots])


if __name__ == '__main__':
    main()
