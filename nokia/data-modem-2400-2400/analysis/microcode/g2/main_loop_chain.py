"""Run eight uninterrupted 8031 polling iterations for each receive selector."""

import argparse
import hashlib
import json
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path

from state_transitions import CORE, HERE, ROM, ROM_SHA, ROOT


def run():
    if hashlib.sha256(ROM.read_bytes()).hexdigest() != ROM_SHA:
        raise ValueError('controller ROM hash mismatch')
    sources = [Path(__file__), HERE / 'main_loop_probe.c',
               *(CORE / n for n in ('core.c', 'opcodes.c', 'disasm.c', 'emu8051.h'))]
    with tempfile.TemporaryDirectory() as temporary:
        exe = Path(temporary) / 'main-loop-probe'
        subprocess.run(['cc', '-O2', '-Wall', '-Wno-unused-parameter', '-DSAT_TRACE',
                        '-I', str(CORE), str(HERE / 'main_loop_probe.c'),
                        *(str(CORE / n) for n in ('core.c', 'opcodes.c', 'disasm.c')),
                        '-o', str(exe)], check=True)
        rows = []
        for selector in range(256):
            process = subprocess.run([str(exe), str(ROM), str(selector), '8'],
                                     text=True, capture_output=True, check=True)
            row = json.loads(process.stdout)
            assert row['selector'] == selector and row['completed'] == 8
            assert row['errors'] == 0 and len(row['iterations']) == 8
            assert all(step['rx'] == 7 and len(step['tx']) == 4 for step in row['iterations'])
            assert all(row['iterations'][i]['cycle'] < row['iterations'][i+1]['cycle']
                       for i in range(7))
            rows.append(dict(selector=f'{selector:02X}', iterations=row['iterations'],
                             final_pc=f"{row['final_pc']:04X}"))
    groups = defaultdict(list)
    for row in rows:
        signature = tuple((step['state'], tuple(step['tx'])) for step in row['iterations'])
        groups[signature].append(row['selector'])
    return dict(status='eight uninterrupted main-loop iterations under diagnostic peripheral events',
                controller_rom_sha256=ROM_SHA,
                fixture=dict(entry_pc='1ED3', initial_state='A0', initial_ram22='10',
                             initial_timer17='80', initial_ram12_ram13='FF FF',
                             receive_bytes='00 07 00 00 00 selector 00',
                             receive_note='First byte is a sync event; byte 07 is XOR-normalized to RAM2A=00.',
                             per_iteration_timer17='80',
                             external_reads={'08E5': 0, '0539': 0, '1D9D': 0, '1DBD': 0},
                             serial_tx_completion_delay=8, interrupts='disabled'),
                rows=rows,
                groups=[dict(selectors=selectors,
                             states=[f'{state:02X}' for state, _ in signature],
                             frames=[' '.join(f'{byte:02X}' for byte in frame)
                                     for _, frame in signature])
                        for signature, selectors in groups.items()],
                distinct_chains=len(groups),
                limitations=['Entry is the real polling-loop PC, but startup and timer-underflow events are imposed.',
                             'Every receive frame is a diagnostic fixed pattern except selector RAM2E.',
                             'USART and external-status reads are zero stubs; TX completion is synthetic.',
                             'No physical recipient of the four-byte output or DSC2847 execution is established.'],
                source_sha256={str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                               for path in sources})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=HERE / 'results/main-loop-chain.json')
    args = parser.parse_args()
    report = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(len(report['rows']), 'selectors;', report['distinct_chains'], 'chains')


if __name__ == '__main__':
    main()
