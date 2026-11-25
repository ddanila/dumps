"""Resolve the A1 81/A1 frame discrepancy using preserved 8031 ROM state."""

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from state_transitions import CORE, HERE, ROM, ROM_SHA, ROOT

sys.path.insert(0, str(HERE.parents[1]))
from controller_output import output32


def compile_probe(source, executable):
    subprocess.run([
        'cc', '-O2', '-Wall', '-Wno-unused-parameter', '-Wno-unused-function',
        '-DSAT_TRACE', '-I', str(CORE), str(source),
        *(str(CORE / name) for name in ('core.c', 'opcodes.c', 'disasm.c')),
        '-o', str(executable),
    ], check=True)


def check_phase(rom, row, field_prefix):
    if field_prefix:
        prior = {name: row[f'{field_prefix}{name}'] for name in
                 ('32', '49', '4a', '65')}
        flags = [row[f'{field_prefix}{name}'] for name in ('22', '23', '24')]
    else:
        prior = {name: row[f'prior{name}'] for name in ('32', '49', '4a', '65')}
        flags = [row[f'flag{name}'] for name in ('22', '23', '24')]
    expected = output32(rom, row.get('state', 0xa1), prior['32'],
                        flags, row['input2c'], prior['49'],
                        prior['4a'], prior['65'])
    for key, value in (('out32', expected['value']),
                       ('out49', expected['count49']),
                       ('out4a', expected['count4a']),
                       ('out65', expected['count65'])):
        if row[key] != value:
            raise AssertionError((row, key, value))
    return expected['action']


def run():
    rom = ROM.read_bytes()
    if hashlib.sha256(rom).hexdigest() != ROM_SHA:
        raise ValueError('controller ROM mismatch')
    source_paths = [Path(__file__), HERE / 'a1_main_loop_phase_probe.c',
                    HERE / 'a1_counter_phase_probe.c', HERE / 'main_loop_probe.c',
                    HERE.parents[1] / 'interface_probe.c',
                    HERE.parents[1] / 'controller_output.py',
                    *(CORE / name for name in
                      ('core.c', 'opcodes.c', 'disasm.c', 'emu8051.h'))]
    main_rows = []
    held_rows = []
    repeated = []
    with tempfile.TemporaryDirectory() as temporary:
        main_exe = Path(temporary) / 'main'
        repeat_exe = Path(temporary) / 'repeat'
        compile_probe(HERE / 'a1_main_loop_phase_probe.c', main_exe)
        compile_probe(HERE / 'a1_counter_phase_probe.c', repeat_exe)
        for selector in (0x00, 0x20, 0x40, 0x60):
            process = subprocess.run([str(main_exe), str(ROM), str(selector),
                                      '12', '1'], text=True,
                                     capture_output=True, check=True)
            execution = json.loads(process.stdout)
            phases = json.loads(process.stderr)['phases']
            if (execution['errors'] or execution['completed'] != 12 or
                    len(phases) != 12 or len(execution['iterations']) != 12):
                raise AssertionError(('main-loop completion', selector))
            for phase, iteration in zip(phases, execution['iterations']):
                phase['action'] = check_phase(rom, phase, '')
                if (iteration['state'] != phase['state'] or
                        iteration['tx'][2] != phase['out32']):
                    raise AssertionError(('frame/build mismatch', selector,
                                          phase, iteration))
            if ([p['state'] for p in phases[:4]] !=
                    [0xa1, 0xa1, 0xa2, 0xa2] or
                    [p['out32'] for p in phases[:4]] !=
                    [0xa1, 0xa1, 0xa8, 0xa8] or
                    [p['flag24'] & 0x20 for p in phases[:4]] !=
                    [0x20, 0, 0x20, 0]):
                raise AssertionError(('unexpected first state phases', selector))
            main_rows.append(dict(selector=f'{selector:02X}', phases=phases))
            process = subprocess.run([str(main_exe), str(ROM), str(selector),
                                      '12', '1', '1'], text=True,
                                     capture_output=True, check=True)
            held_execution = json.loads(process.stdout)
            held_phases = json.loads(process.stderr)['phases']
            if (held_execution['errors'] or held_execution['completed'] != 12 or
                    len(held_phases) != 12 or
                    len(held_execution['iterations']) != 12):
                raise AssertionError(('held A1 completion', selector))
            for phase, iteration in zip(held_phases, held_execution['iterations']):
                phase['action'] = check_phase(rom, phase, '')
                if (iteration['state'] != phase['state'] or
                        iteration['tx'][2] != phase['out32']):
                    raise AssertionError(('held frame/build mismatch', selector,
                                          phase, iteration))
            if ([p['state'] for p in held_phases] != [0xa1]*12 or
                    [p['out32'] for p in held_phases] != [0xa1]*11 + [0x81] or
                    [p['flag24'] & 0x20 for p in held_phases] != [0x20] + [0]*11):
                raise AssertionError(('held A1 trajectory', selector))
            held_rows.append(dict(selector=f'{selector:02X}', phases=held_phases,
                                  frames=[step['tx'] for step in
                                          held_execution['iterations']]))
        for mode in range(3):
            process = subprocess.run([str(repeat_exe), str(ROM), str(mode)],
                                     text=True, capture_output=True, check=True)
            execution = json.loads(process.stdout)
            if execution['errors'] or len(execution['rows']) != 20:
                raise AssertionError(('repeat completion', mode))
            for row in execution['rows']:
                row['action'] = check_phase(rom, row, 'prior')
                if row['wire'][2] != row['out32']:
                    raise AssertionError(('serial byte mismatch', mode, row))
            repeated.append(execution)
    if ([r['out32'] for r in repeated[0]['rows']] != [0x81]*20 or
            [r['out32'] for r in repeated[1]['rows']] != [0x81]*20 or
            [r['out32'] for r in repeated[2]['rows']] !=
            [0xa1]*11 + [0x81] + [0xc1]*8):
        raise AssertionError('counter trajectory changed')
    return dict(
        status='A1 frame discrepancy resolved as controller flag/counter phase',
        controller_rom_sha256=ROM_SHA,
        main_loop_fixture='Uninterrupted polling loop, four representative selector classes, 12 iterations each; synthetic seven-byte receive events, ready status and timer underflow after every iteration.',
        held_a1_fixture='Same uninterrupted polling loop and four selector classes, but the harness clears the externally supplied RAM17.7 underflow bit at each A1 loop entry. Interrupts remain disabled, so this is a held-state diagnostic, not natural timer duration.',
        repeated_fixture='Same 8031 RAM/SFR preserved across 20 directed send calls with state held at A1. Mode 0 starts at isolated zero fixture; mode 1 enters A1 by forced A0 expiry; mode 2 additionally supplies flag24.5 on first call, then clears it before call 1 as observed between main-loop iterations. No natural-duration A1 interval is simulated.',
        main_loop=main_rows, held_a1=held_rows, repeated=repeated,
        finding='Main-loop A1 enters output32 with flag24.5=1, producing A1 and loading counter49=10; the next A1 build has flag24.5=0 and decrements to 9. Isolated A1 enters with flag24.5=0 and produces 81. With the same polling loop held in A1, all four selector classes reach 81 at iteration 11. Under directed repeated A1 sends after one reload, bit6 then toggles at call 12 (C1). The byte is counter-phase dependent, not a state-only mode code.',
        limitations=['The repeated send calls and one flag clear are harness-directed; their call count is not an A1 duration.',
                     'The main-loop fixture forces timer underflow and inserts receive events; the held-state variant suppresses only the artificial underflow. Neither establishes natural A1 duration or tone waveform.',
                     'No electrical frame destination, DAC latch, clock, or line signal is proved.'],
        source_sha256={str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in source_paths})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path,
                        default=HERE / 'results/a1-counter-phase.json')
    args = parser.parse_args()
    report = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(report['status'])


if __name__ == '__main__':
    main()
