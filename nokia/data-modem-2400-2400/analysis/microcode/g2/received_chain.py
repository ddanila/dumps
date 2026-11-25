"""Run USART receive, four state expiries and four sends on one 8031 image."""

import argparse
import hashlib
import json
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path

from chain_frames import run as run_injected_chain
from state_transitions import CORE, HERE, ROOT, ROM, ROM_SHA


def run():
    if hashlib.sha256(ROM.read_bytes()).hexdigest() != ROM_SHA:
        raise ValueError('controller ROM hash mismatch')
    injected = run_injected_chain()
    rows = []
    cycle_deltas = set()
    with tempfile.TemporaryDirectory() as temporary:
        exe = Path(temporary) / 'received-chain-probe'
        subprocess.run(['cc', '-O2', '-Wall', '-Wno-unused-function',
                        '-DSAT_TRACE', '-I', str(CORE),
                        str(HERE / 'received_chain_probe.c'),
                        *(str(CORE / name) for name in
                          ('core.c', 'opcodes.c', 'disasm.c')),
                        '-o', str(exe)], check=True)
        for selector in range(256):
            result = json.loads(subprocess.run(
                [str(exe), str(ROM), str(selector)],
                text=True, capture_output=True, check=True).stdout)
            steps = result['rows']
            if (result['errors'] or result['received'] != 7 or
                    result['stored_2e'] != selector or len(steps) != 4):
                raise ValueError(f'selector {selector:02X}: receive/state chain failed')
            parsed = [dict(before=f'{step["before"]:02X}',
                           after=f'{step["after"]:02X}',
                           state_cycles=step['state_cycles'],
                           wire=' '.join(f'{byte:02X}' for byte in step['wire']))
                      for step in steps]
            reference = injected['rows'][selector]['steps']
            if any((a['before'], a['after'], a['wire']) !=
                   (b['before'], b['after'], b['wire'])
                   for a, b in zip(parsed, reference)):
                raise ValueError(f'selector {selector:02X}: received and injected chains differ')
            cycle_deltas.add(tuple(a['state_cycles'] - b['state_cycles']
                                   for a, b in zip(parsed, reference)))
            rows.append(dict(selector=f'{selector:02X}',
                             received=7, stored_2e=f'{result["stored_2e"]:02X}',
                             steps=parsed))
    groups = defaultdict(list)
    for row in rows:
        signature = tuple((step['before'], step['after'], step['wire'])
                          for step in row['steps'])
        groups[signature].append(row['selector'])
    if len(groups) != 4:
        raise ValueError('controller chain class count changed')
    if cycle_deltas != {(1, 0, 0, 0)}:
        raise ValueError(f'unexpected received versus injected cycle offsets: {cycle_deltas}')
    sources = [Path(__file__), HERE / 'received_chain_probe.c',
               HERE / 'chain_frames.py', HERE / 'chain_frame_probe.c',
               HERE.parents[1] / 'interface_probe.c', ROM,
               *(CORE / name for name in
                 ('core.c', 'opcodes.c', 'disasm.c', 'emu8051.h'))]
    return dict(status='256 preserved-image USART-receive/state/send chains pass',
                controller_rom_sha256=ROM_SHA,
                preconditions=('Receive seven synthetic USART bytes at 0800: A5, '
                               'four zeros, selector, zero. Preserve RAM and SFR; '
                               'set RAM34=A0 and RAM22.4=1, force each countdown '
                               'expiry, direct PC to 1000 and then 1EE2, and '
                               'supply transmit completions; interrupts disabled.'),
                rows=rows, distinct_chains=len(groups),
                groups=[dict(selectors=selectors,
                             steps=[dict(before=a, after=b, wire=w)
                                    for a, b, w in signature])
                        for signature, selectors in groups.items()],
                comparison='All 256 received chains match fresh direct-RAM2E injected chains in states and frames; the first A0 step takes one additional cycle in the received fixture.',
                state_cycle_deltas_vs_injected=[[1, 0, 0, 0]],
                limitations=[
                    'The received input bytes and USART timing are synthetic; the physical source is unknown.',
                    'A0 start, expiry events and PC handoffs are harness-directed, not an uninterrupted call.',
                    'The four-byte output destination and DSP command semantics remain untraced.',
                    'No DSC2847 microcode or line waveform is executed in this probe.'],
                source_sha256={str(path.relative_to(ROOT)):
                               hashlib.sha256(path.read_bytes()).hexdigest()
                               for path in sources})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path,
                        default=HERE / 'results/received-chain.json')
    args = parser.parse_args()
    report = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(report['status'], 'distinct chains', report['distinct_chains'])


if __name__ == '__main__':
    main()
