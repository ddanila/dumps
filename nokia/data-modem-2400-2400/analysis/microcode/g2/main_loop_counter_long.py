"""Trace the ROM-table counter behind the long-loop third frame byte."""

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

LONG = HERE / 'results/main-loop-long.json'


def generated_sources(directory):
    changes = {
        'main_loop_probe.c': [('wanted>12', 'wanted>64'),
                              ('cycle<200000', 'cycle<2000000')],
        'a1_main_loop_phase_probe.c': [('phases[32]', 'phases[128]'),
                                       ('phase_count>=32', 'phase_count>=128'),
                                       ('phase_count<12', 'phase_count<64')],
    }
    for name, replacements in changes.items():
        source = (HERE / name).read_text()
        for old, new in replacements:
            if source.count(old) != 1:
                raise ValueError(('base probe changed', name, old))
            source = source.replace(old, new)
        (directory / name).write_text(source)
    return changes


def validate_phase(rom, phase, frame):
    prior = {name: phase[f'prior{name}'] for name in ('32', '49', '4a', '65')}
    flags = [phase[f'flag{name}'] for name in ('22', '23', '24')]
    expected = output32(rom, phase['state'], prior['32'], flags,
                        phase['input2c'], prior['49'], prior['4a'], prior['65'])
    for field, key in (('out32', 'value'), ('out49', 'count49'),
                       ('out4a', 'count4a'), ('out65', 'count65')):
        if phase[field] != expected[key]:
            raise AssertionError((field, phase, expected))
    if phase['out32'] != frame[2]:
        raise AssertionError(('third serial byte differs from RAM32', phase, frame))
    phase['action'] = expected['action']


def run(out=HERE / 'results/main-loop-counter-long.json'):
    rom = ROM.read_bytes()
    if hashlib.sha256(rom).hexdigest() != ROM_SHA:
        raise ValueError('controller ROM mismatch')
    previous = json.loads(LONG.read_text())
    by_selector = {row['selector']: row for row in previous['runs']}
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        changes = generated_sources(directory)
        executable = directory / 'counter-probe'
        subprocess.run(['cc', '-O2', '-Wall', '-Wno-unused-parameter',
                        '-Wno-unused-function', '-DSAT_TRACE', '-I', str(CORE),
                        str(directory / 'a1_main_loop_phase_probe.c'),
                        *(str(CORE / name) for name in ('core.c', 'opcodes.c', 'disasm.c')),
                        '-o', str(executable)], check=True)
        for selector in (0x00, 0x20, 0x40, 0x60):
            process = subprocess.run([str(executable), str(ROM), str(selector),
                                      '64', '1'], text=True, capture_output=True,
                                     check=True)
            execution = json.loads(process.stdout)
            phases = json.loads(process.stderr)['phases']
            earlier = by_selector[f'{selector:02X}']['iterations']
            if (execution['errors'] or execution['completed'] != 64 or
                    len(phases) != 64 or len(earlier) != 64):
                raise AssertionError(('extended probe completion', selector))
            for index, (phase, iteration, old) in enumerate(zip(
                    phases, execution['iterations'], earlier)):
                frame = iteration['tx']
                validate_phase(rom, phase, frame)
                if (phase['state'] != iteration['state'] or
                        old['state'] != f"{phase['state']:02X}" or
                        old['frame'] != ' '.join(f'{byte:02X}' for byte in frame)):
                    raise AssertionError(('preserved long-run mismatch', selector, index))
            cases.append(dict(selector=f'{selector:02X}', phases=phases))
    table = {f'{state:02X}': dict(address=f'{0x1be + (state & 0x3f):04X}',
                                  raw=rom[0x1be + (state & 0x3f)],
                                  reloaded=((rom[0x1be + (state & 0x3f)] << 2) |
                                            (rom[0x1be + (state & 0x3f)] >> 6)) & 255)
             for state in (0xa1, 0xa5, 0xb4)}
    if [(table[state]['raw'], table[state]['reloaded'])
            for state in ('A1', 'A5', 'B4')] != [(1, 4), (2, 8), (8, 32)]:
        raise AssertionError('controller reload table changed')
    for case in cases:
        phases = case['phases']
        target = 0xb4 if int(case['selector'], 16) & 0x40 == 0 else 0xa5
        reload_index = 17 if target == 0xb4 else 25
        reload = phases[reload_index]
        if (reload['state'] != target or reload['prior49'] != 0 or
                reload['out49'] != table[f'{target:02X}']['reloaded'] or
                (reload['out32'] & 0x20)):
            raise AssertionError(('state table reload', case['selector'], reload))
        toggle_indices = [index for index in range(reload_index + 1, 64)
                          if phases[index]['state'] == target and
                          ((phases[index]['prior32'] ^ phases[index]['out32']) & 0x40)]
        expected = list(range(reload_index + 1,
                              reload_index + table[f'{target:02X}']['reloaded'] + 1, 4))
        if toggle_indices != expected:
            raise AssertionError(('counter toggle indices', case['selector'],
                                  toggle_indices, expected))
        case['table_reload_iteration'] = reload_index
        case['table_reload_value'] = reload['out49']
        case['toggle_iterations'] = toggle_indices
    sources = [Path(__file__), LONG, ROM, HERE / 'main_loop_probe.c',
               HERE / 'a1_main_loop_phase_probe.c',
               HERE.parents[1] / 'controller_output.py',
               *(CORE / name for name in ('core.c', 'opcodes.c', 'disasm.c', 'emu8051.h'))]
    report = dict(status='third frame byte bit 6 follows a state-indexed finite controller counter',
                  controller_rom_sha256=ROM_SHA,
                  fixture=dict(entry_pc='1ED3', receive_bytes='00 07 00 00 00 selector 00',
                               iterations=64, timer17_forced_underflow_per_iteration=True,
                               interrupts='disabled',
                               generated_c_replacements=changes),
                  table=table, cases=cases,
                  validation='All 256 ROM-executed output builds match independent output32 RAM32/49/4A/65 results and the serialized third byte; their states and frames match the earlier 64-iteration replay.',
                  limitations=['Counter updates and frame sends are observed under synthetic USART-ready/receive and timer-expiry events.',
                               'Four output builds are not a measured duration or an established symbol interval.',
                               'The frame destination and any conversion of bit 6 into a DSC phase pulse remain untraced.'],
                  source_sha256={str(path.relative_to(ROOT)):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path,
                        default=HERE / 'results/main-loop-counter-long.json')
    args = parser.parse_args()
    for case in run(args.out)['cases']:
        print(case['selector'], case['table_reload_value'],
              case['toggle_iterations'])
