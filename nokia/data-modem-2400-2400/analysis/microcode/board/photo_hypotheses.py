"""Execute explicitly hypothetical DSC wiring with the original four PROMs.

Photo-supported device/bundle topology is combined with existing ROM-derived
field candidates. This is an experiment, not a continuity reconstruction.
"""
import argparse
import csv
import hashlib
import json
import os
from copy import deepcopy
from pathlib import Path

from engine import Engine, Stop, validate

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
PAIRS = {'10': 'U5', '11': 'U6', '17': 'U29', '18': 'U30'}


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def candidate(profile, sequence_source='registered', branch_source='literal'):
    profiles = read(ASSUMED / 'program-reading.json')['profiles']
    mapping_path = ASSUMED / profiles[profile]
    mapping = read(mapping_path)
    board = deepcopy(read(HERE / 'dsc2847.json'))
    board['name'] = f'DSC photo hypothesis: {profile}/{sequence_source}/{branch_source}'
    board['status'] = 'photo-informed-hypothesis'
    board['external'] = {k: {'width': w} for k, w in
                         [('sc', 1), ('rc', 1), ('test', 1), ('data', 8),
                          ('carry', 1), ('indirect', 10)]}
    board['observables'] = {'microaddress': 'U9.A'}
    board['hypotheses'] = {
        'topology': 'Four PROM/register pairings from nets.json candidate_bundles; two Am2901 devices from the photo inventory.',
        'register_bits': 'Identity D-to-D order is a naming convention for untraced register bits; output references use the same convention. Not a recovered pin permutation.',
        'address': 'U9 ten-bit address feeds all four PROMs without permutation; enables asserted.',
        'fields': {'path': str(mapping_path.relative_to(HERE.parent)),
                   'sha256': hashlib.sha256(mapping_path.read_bytes()).hexdigest(),
                   'mapping': mapping},
        'sequence_controls': sequence_source,
        'branch_source': branch_source,
        'condition': 'TEST = external test OR (BSR/BRT AND select=0 AND direct=1). Abstract gates H_* have no assigned PCB package or pins.',
        'datapath': 'U2 low nibble, U8 high nibble, common I/A/B; ripple carry and inter-slice RAM/Q shifts. External shift endpoints zero. Carry selector/latch circuit is bypassed by an external carry fixture.',
        'external': 'D and carry supplied by diagnostic fixture; no ADC, DAC, controller handshake, lookup ROM, or modem waveform is invented.',
        'clock': 'Register fetch rising edge, then sequencer/ALU falling and rising phases. No frequency or physical divider asserted.',
        'initial_state': 'Actual model defaults: unknown RAM/Q/registers/stack; sequencer address zero. No zero-filled RAM.',
    }
    board['limitations'] = [
        'All executable connections here are hypotheses; nets.json remains the measured/visible evidence ledger.',
        'Model completion is not G2 C2/C3/C4 acceptance or proof of actual Nokia wiring.',
        'Unmodeled physical components remain omitted. H_* cells express hypothetical logic, not identified packages.',
        'Literal branch bypasses indirect dispatch. Unknown branch leaves the indirect bus unknown until evidence supplies it.',
        'Unknown data can propagate without stopping; a completed instruction does not establish valid arithmetic.',
        'Timing rejection may be an adapter limitation, not a physical impossibility.',
    ]
    cells = board['components']
    for chip, reg in PAIRS.items():
        cells['U' + chip]['inputs'] = {'A': 'U9.A', 'ENn': 0}
        cells[reg]['inputs'] = {'D': f'U{chip}.D', 'CLK': 'EXT.rc', 'OEn': 0}
    for cell in cells.values():
        cell['connection_status'] = 'hypothesis'

    def field(name, source='registered'):
        bits = mapping['fields'][name]['bits']
        if isinstance(bits, int):
            return bits
        result = []
        for token in bits:
            chip, bit = token.lstrip('!').split('.')
            ref = f'{PAIRS[chip]}.Q[{bit}]' if source == 'registered' else f'U{chip}.D[{bit}]'
            result.append({'not': ref} if token.startswith('!') else ref)
        return result

    def scalar(expr, bit=0):
        return (expr >> bit) & 1 if isinstance(expr, int) else expr[bit]

    def gate(name, typ, a, b):
        cells[name] = {'type': typ, 'inputs': {'A': a, 'B': b},
                       'connection_status': 'hypothetical-logic-no-package-assignment'}
        return name + '.Y'

    ac, sel, direct = (field(k, sequence_source) for k in ('command', 'select', 'direct'))
    terms = [scalar(ac, 2), {'not': scalar(ac, 0)}, scalar(direct)]
    terms += [{'not': scalar(sel, bit)} for bit in range(3)]
    uncond = terms[0]
    for n, term in enumerate(terms[1:]):
        uncond = gate(f'H_unconditional_{n}', 'AND', uncond, term)
    test = gate('H_test', 'OR', uncond, 'EXT.test')
    branch = field('branch', sequence_source)
    if branch_source == 'unknown':
        # Hypothesis: direct=1 selects the encoded target, else a ten-bit bus.
        # Use padded nibble mux adapters; no claim of physical LS157 packages.
        padded = [scalar(branch, bit) for bit in range(10)] + [0, 0]
        indirect = [f'EXT.indirect[{bit}]' for bit in range(10)] + [0, 0]
        for n in range(3):
            cells[f'H_branch_{n}'] = {'type': 'MUX157', 'inputs': {
                'A': indirect[4*n:4*n+4], 'B': padded[4*n:4*n+4],
                'S': scalar(direct), 'ENn': 0},
                'connection_status': 'hypothetical-logic-no-package-assignment'}
        branch = [f'H_branch_{bit//4}.Y[{bit%4}]' for bit in range(10)]
    cells['U9']['inputs'] = {'AC': ac, 'B': branch, 'TEST': test, 'CLK': 'EXT.sc', 'ENn': 0}
    for name, high in [('U2', False), ('U8', True)]:
        cells[name]['inputs'] = {
            'I': field('i'), 'A': field('a'), 'B': field('b'),
            'D': [f'EXT.data[{bit}]' for bit in range(4 if high else 0, 8 if high else 4)],
            'Cn': 'U2.Cn4' if high else 'EXT.carry', 'CLK': 'EXT.sc', 'OEn': 0,
            'RAM0in': 'U2.RAM3out' if high else 0,
            'RAM3in': 0 if high else 'U8.RAM0out',
            'Q0in': 'U2.Q3out' if high else 0,
            'Q3in': 0 if high else 'U8.Q0out',
        }
    board['decode'] = {'AC': field('command', 'raw'), 'BRANCH': field('branch', 'raw'),
                       'I_LOW': field('i', 'raw'), 'I_HIGH': field('i', 'raw')}
    return board


def scenario(test):
    fixture = {'name': f'Diagnostic external TEST={test}, D=0, carry=0; indirect bus unknown',
            'initial_inputs': {'sc': 1, 'rc': 0, 'test': 0 if test == 'pulse17' else test, 'data': 0, 'carry': 0},
            'cycle': [
                {'name': 'fetch rise', 'set': {'rc': 1}},
                {'name': 'fetch fall', 'set': {'rc': 0}},
                {'name': 'execute fall', 'set': {'sc': 0}},
                {'name': 'execute rise', 'set': {'sc': 1}},
            ]}
    if test == 'pulse17':
        fixture['cycle_inputs'] = {'17': {'test': 1}, '18': {'test': 0}}
        fixture['note'] = 'One-cycle TEST pulse at the baseline visit to 008; diagnostic dispatch stimulus, not controller behavior.'
    return fixture


def experiment(board, fixture, cycles):
    engine = Engine(board, HERE)
    engine.initialize(fixture['initial_inputs'])
    trace, stop, completed = [], None, 0
    phase = 'initialized'
    for cycle in range(cycles):
        row = {'cycle': cycle, 'pc': f'{engine.values["U9.A"].integer():03X}'}
        try:
            if str(cycle) in fixture.get('cycle_inputs', {}):
                phase = 'external stimulus'
                engine.step(fixture['cycle_inputs'][str(cycle)])
            for event in fixture['cycle']:
                phase = event['name']
                if phase == 'execute fall':
                    i = engine.inputs('U9')
                    row.update(ac=i['AC'].integer(), test=i['TEST'].integer(), branch=i['B'].text())
                engine.step(event['set'])
            completed += 1
        except Stop as err:
            stop = str(err)
        row.update(next_pc=f'{engine.values["U9.A"].integer():03X}',
                   y=engine.values['U8.Y'].text() + engine.values['U2.Y'].text(),
                   known_ram_bytes=sum(all(engine.state[n]['ram'][r].integer() is not None
                                           for n in ('U2', 'U8')) for r in range(16)))
        trace.append(row)
        if stop:
            break
    report = {'board': board['name'], 'scenario': fixture['name'],
              'completed_cycles': completed, 'unique_pcs': len({r['pc'] for r in trace}),
              'stop': stop or 'cycle limit', 'last_phase': phase,
              'last_pc': f'{engine.values["U9.A"].integer():03X}',
              'max_known_ram_bytes': max(r['known_ram_bytes'] for r in trace),
              'faithful_nokia_execution': False,
              'g2_acceptance': False}
    return report, trace, engine.snapshot()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profiles', nargs='+', default=['q3'],
                        choices=list(read(ASSUMED / 'program-reading.json')['profiles']))
    parser.add_argument('--cycles', type=int, default=128)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--summary-only', action='store_true', help='Save aggregate results without configurations and traces.')
    args = parser.parse_args()
    if args.cycles < 1:
        parser.error('--cycles must be positive')
    args.out.mkdir(parents=True, exist_ok=True)
    reports = []
    for profile in args.profiles:
        for source in ('registered', 'raw'):
            for branch in ('literal', 'unknown'):
                board = candidate(profile, source, branch)
                if validate(board)['errors']:
                    raise ValueError(validate(board)['errors'])
                path = args.out / f'{profile}-{source}-{branch}'
                if not args.summary_only:
                    path.mkdir(exist_ok=True)
                    exported = deepcopy(board)
                    for cell in exported['components'].values():
                        if 'rom' in cell:
                            cell['rom']['path'] = os.path.relpath(HERE / cell['rom']['path'], path)
                    save(path / 'board.json', exported)
                for test in (0, 1, 'pulse17'):
                    fixture = scenario(test)
                    report, trace, snapshot = experiment(board, fixture, args.cycles)
                    report['candidate'] = path.name
                    report['external_test'] = test
                    reports.append(report)
                    if args.summary_only:
                        continue
                    save(path / f'scenario-{test}.json', fixture)
                    save(path / f'final-state-{test}.json', snapshot)
                    with (path / f'trace-{test}.csv').open('w') as f:
                        writer = csv.DictWriter(f, fieldnames=list(trace[0]), lineterminator='\n')
                        writer.writeheader()
                        writer.writerows(trace)
    save(args.out / 'summary.json', {
        'status': 'hypothesis-screen-not-hardware-validation',
        'scope': 'Photo-supported bundles plus existing field hypotheses; bounded fixture screen, not exhaustive netlist search.',
        'cycles_requested': args.cycles, 'runs': reports,
    })
    for r in reports:
        print(f'{r["candidate"]} TEST={r["external_test"]}: {r["completed_cycles"]} cycles, '
              f'{r["unique_pcs"]} PCs, last={r["last_pc"]}; {r["stop"]}')


if __name__ == '__main__':
    main()
