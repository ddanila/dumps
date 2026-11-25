"""Run four controller state expiries and sends on one preserved 8031 RAM image."""
import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from state_transitions import HERE, ROOT, ROM, CORE, ROM_SHA


def run():
    if hashlib.sha256(ROM.read_bytes()).hexdigest() != ROM_SHA:
        raise ValueError('controller ROM hash mismatch')
    sources = [Path(__file__), HERE/'chain_frame_probe.c', HERE.parents[1]/'interface_probe.c',
               *(CORE/n for n in ('core.c', 'opcodes.c', 'disasm.c', 'emu8051.h'))]
    with tempfile.TemporaryDirectory() as tmp:
        exe = Path(tmp)/'probe'
        subprocess.run(['cc', '-O2', '-Wall', '-Wno-unused-function', '-DSAT_TRACE',
                        '-I', str(CORE), str(HERE/'chain_frame_probe.c'),
                        *(str(CORE/n) for n in ('core.c', 'opcodes.c', 'disasm.c')),
                        '-o', str(exe)], check=True)
        rows = []
        for value in range(256):
            result = json.loads(subprocess.run([str(exe), str(ROM), str(value)],
                               text=True, capture_output=True, check=True).stdout)
            steps = result['rows']
            assert result['errors'] == 0 and len(steps) == 4
            assert [s['before'] for s in steps[:3]] == [0xa0, 0xa1, 0xa2]
            assert [s['after'] for s in steps[:2]] == [0xa1, 0xa2]
            assert steps[2]['after'] == (0xa3 if value & 0x40 else 0xb8)
            assert steps[3]['before'] == steps[2]['after']
            assert all((step['p1'] & 0x20) == 0 for step in steps[:2])
            rows.append(dict(selector=f'{value:02X}', steps=[
                dict(before=f'{s["before"]:02X}', after=f'{s["after"]:02X}',
                     state_cycles=s['state_cycles'],
                     wire=' '.join(f'{b:02X}' for b in s['wire']),
                     p1=f'{s["p1"]:02X}') for s in steps]))
    signatures = {}
    for row in rows:
        signature = tuple((s['before'], s['after'], s['wire']) for s in row['steps'])
        signatures.setdefault(signature, []).append(row['selector'])
    return dict(status='256 preserved-RAM controller chains executed',
        controller_rom_sha256=ROM_SHA, rows=rows,
        distinct_chains=len(signatures),
        groups=[dict(selectors=values, steps=[dict(before=a, after=b, wire=w)
                    for a,b,w in signature]) for signature,values in signatures.items()],
        preconditions='RAM34 starts A0; RAM22 qualification bit set; RAM2E set to selector; each step is forced to countdown expiry, then PC is directed to the four-byte send routine; RAM and SFR state are preserved across steps; no interrupts.',
        limitations=['The timer expiry and PC handoffs are harness-directed; this is not a natural uninterrupted call.',
                     'RAM2E is injected directly rather than received through USART in this experiment.',
                     'The physical recipients and meanings of the four-byte frames and P1 pins remain unknown.',
                     'No DSC2847 microcode or line waveform is executed.'],
        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in sources})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/chain-frames.json')
    args=parser.parse_args()
    report=run()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(report['status'], 'distinct chains', report['distinct_chains'])


if __name__=='__main__': main()
