"""Check controller line-side writes in 12 uninterrupted polling iterations."""

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

from state_transitions import CORE, HERE, ROM, ROM_SHA, ROOT

sys.path.insert(0, str(HERE.parents[1]))
from controller_scrambler import transform


def run():
    if hashlib.sha256(ROM.read_bytes()).hexdigest() != ROM_SHA:
        raise ValueError('controller ROM hash mismatch')
    source_paths = [Path(__file__), HERE / 'main_loop_probe.c',
                    HERE.parents[1] / 'controller_scrambler.py',
                    *(CORE / n for n in ('core.c', 'opcodes.c', 'disasm.c', 'emu8051.h'))]
    with tempfile.TemporaryDirectory() as temporary:
        exe = Path(temporary) / 'main-loop-probe'
        subprocess.run(['cc', '-O2', '-Wall', '-Wno-unused-parameter', '-DSAT_TRACE',
                        '-I', str(CORE), str(HERE / 'main_loop_probe.c'),
                        *(str(CORE / n) for n in ('core.c', 'opcodes.c', 'disasm.c')),
                        '-o', str(exe)], check=True)
        rows = []
        for selector in range(256):
            process = subprocess.run([str(exe), str(ROM), str(selector), '12', '1'],
                                     text=True, capture_output=True, check=True)
            result = json.loads(process.stdout)
            assert result['selector'] == selector and result['status'] == 1
            assert result['completed'] == 12 and result['errors'] == 0
            assert len(result['iterations']) == 12
            stream = []
            sources = []
            delays = []
            for step in result['iterations']:
                assert step['rx'] == 7 and len(step['tx']) == 4
                line_writes = [value for addr, value in zip(step['write_addresses'], step['writes'])
                               if addr == 1]
                reference = [transform(event['history'], event['input'], event['delay'])[1]
                             for event in step['scramble']]
                if line_writes != reference:
                    raise AssertionError((selector, line_writes, reference))
                stream.extend(line_writes)
                sources.extend(event['input'] for event in step['scramble'])
                delays.extend(event['delay'] for event in step['scramble'])
            expected_delay = 5 if selector & 0x20 and not selector & 0x10 else 18
            assert delays and set(delays) == {expected_delay}
            assert len(stream) == (6 if selector & 0x40 else 8)
            rows.append(dict(selector=f'{selector:02X}', states=[f'{s["state"]:02X}' for s in result['iterations']],
                             frames=[' '.join(f'{b:02X}' for b in s['tx']) for s in result['iterations']],
                             line_sources=sources, line_bytes=stream, delay=expected_delay,
                             first_line_iteration=7 if selector & 0x40 else 5,
                             final_pc=f"{result['final_pc']:04X}"))
    groups = defaultdict(list)
    for row in rows:
        signature = (tuple(row['states']), tuple(row['line_sources']),
                     tuple(row['line_bytes']), row['delay'])
        groups[signature].append(row['selector'])
    return dict(status='continuous controller frame and line-side byte execution under ready-status stub',
                controller_rom_sha256=ROM_SHA, rows=rows,
                groups=[dict(selectors=members, states=list(signature[0]),
                             line_sources=list(signature[1]), line_bytes=list(signature[2]),
                             delay=signature[3]) for signature, members in groups.items()],
                distinct_streams=len(groups),
                fixture=dict(entry_pc='1ED3', initial_state='A0', initial_ram22='10',
                             initial_timer17='80', per_iteration_timer17='80',
                             receive_bytes='00 07 00 00 00 selector 00',
                             external_reads={'08E5': 0, '0539': 1, '1D9D': 1,
                                             '1DBD': 1, '1DC6': 0},
                             serial_tx_completion_delay=8, interrupts='disabled'),
                validation='Every port-01 write equals the independent 23-bit bit-serial scrambler result from the recorded input, history and selected delay.',
                limitations=['Initial RAM/state, timer underflow and USART-ready status are diagnostic fixtures.',
                             'Port-01 writes are controller output bytes, not a measured wire waveform.',
                             'No DSC2847 input path, output converter, receiver or echo-canceller is connected.'],
                source_sha256={str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                               for path in source_paths})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=HERE / 'results/main-loop-serial.json')
    args = parser.parse_args()
    report = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(len(report['rows']), 'selectors;', report['distinct_streams'], 'line streams')


if __name__ == '__main__':
    main()
