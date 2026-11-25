"""Extend the unchanged 8031 polling-loop fixture to 64 iterations."""

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from state_transitions import CORE, HERE, ROM, ROM_SHA, ROOT

sys.path.insert(0, str(HERE.parents[1]))
from controller_scrambler import transform


def run():
    if hashlib.sha256(ROM.read_bytes()).hexdigest() != ROM_SHA:
        raise ValueError('controller ROM hash mismatch')
    probe = HERE / 'main_loop_probe.c'
    source = probe.read_text()
    for old, new in [('wanted>12', 'wanted>64'),
                     ('cycle<200000', 'cycle<2000000')]:
        if source.count(old) != 1:
            raise ValueError(f'probe fixture changed: {old}')
        source = source.replace(old, new)
    sources = [Path(__file__), probe, HERE.parents[1] / 'controller_scrambler.py',
               *(CORE / n for n in ('core.c', 'opcodes.c', 'disasm.c', 'emu8051.h'))]
    runs = []
    with tempfile.TemporaryDirectory() as temporary:
        extended = Path(temporary) / 'main_loop_extended.c'
        exe = Path(temporary) / 'main_loop_extended'
        extended.write_text(source)
        subprocess.run(['cc', '-O2', '-Wall', '-Wno-unused-parameter', '-DSAT_TRACE',
                        '-I', str(CORE), str(extended),
                        *(str(CORE / n) for n in ('core.c', 'opcodes.c', 'disasm.c')),
                        '-o', str(exe)], check=True)
        for selector in (0x00, 0x20, 0x40, 0x60):
            result = json.loads(subprocess.run(
                [str(exe), str(ROM), str(selector), '64', '1'],
                text=True, capture_output=True, check=True).stdout)
            assert result['completed'] == 64 and result['errors'] == 0
            assert result['final_pc'] == 0x1ed3
            rows = []
            for step in result['iterations']:
                assert step['rx'] == 7 and len(step['tx']) == 4
                line = [value for addr, value in zip(step['write_addresses'], step['writes'])
                        if addr == 1]
                events = step['scramble']
                expected = [transform(e['history'], e['input'], e['delay'])[1]
                            for e in events]
                assert line == expected
                assert all(e['delay'] == (5 if selector & 0x20 else 18) for e in events)
                rows.append(dict(state=f"{step['state']:02X}",
                                 frame=' '.join(f'{byte:02X}' for byte in step['tx']),
                                 line_sources=[f"{e['input']:02X}" for e in events],
                                 line_bytes=[f'{byte:02X}' for byte in line]))
            runs.append(dict(selector=f'{selector:02X}', completed=64, errors=0,
                             final_pc='1ED3', line_byte_count=sum(len(r['line_bytes']) for r in rows),
                             iterations=rows))
    return dict(status='64 uninterrupted controller polling iterations per selector',
                controller_rom_sha256=ROM_SHA,
                fixture=dict(entry_pc='1ED3', initial_state='A0', initial_ram22='10',
                             initial_timer17='80', per_iteration_timer17='80',
                             receive_bytes='00 07 00 00 00 selector 00',
                             external_reads={'08E5': 0, '0539': 1, '1D9D': 1,
                                             '1DBD': 1, '1DC6': 0},
                             serial_tx_completion_delay=8, interrupts='disabled',
                             generated_source_changes=['wanted>12 → wanted>64',
                                                       'cycle<200000 → cycle<2000000']),
                validation='Every port-01 write matches the independent bit-serial scrambler result.',
                limitations=['Forced timer expiry and USART-ready status are diagnostic fixtures.',
                             'The transmitted four-byte frame recipient and physical line route are untraced.',
                             'Frame byte changes are not yet identified as carrier phase reversals.'],
                runs=runs,
                source_sha256={str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                               for path in sources})


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=HERE / 'results/main-loop-long.json')
    args = parser.parse_args()
    report = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(len(report['runs']), 'selectors; 64 iterations each; independent line-byte check passed')


if __name__ == '__main__':
    main()
