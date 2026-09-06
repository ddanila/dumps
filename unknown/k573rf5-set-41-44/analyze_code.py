#!/usr/bin/env python3
"""Read-only evidence checks; optionally disassemble selected code (Linux/z80dasm).

These checks validate bytes and relationships, not execution or hardware behavior.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent
COMBINED_SHA256 = 'b12fd392ea3a49fdd507e8c61decfe2f5972c3c1b7b9aec51455a329548c00b8'
RANGES = [
    (0x0000, 0x001B), (0x002B, 0x0048), (0x00C5, 0x00EC),
    (0x0120, 0x0173), (0x07FD, 0x080B), (0x0A5B, 0x0B5C),
    (0x0BAD, 0x0CE0), (0x0FF3, 0x1008), (0x17ED, 0x183B),
    (0x183B, 0x19D4), (0x1A1A, 0x1AB4), (0x1B03, 0x1B4B),
    (0x1C53, 0x1C80), (0x1D76, 0x1DA0), (0x1DF8, 0x1DFF),
]


def load_rom():
    manifest = json.loads((ROOT / 'manifest.json').read_text())
    images = []
    for chip in sorted(manifest['chips'], key=lambda c: c['label']):
        data = (ROOT / chip['filename']).read_bytes()
        if len(data) != chip['bytes'] or hashlib.sha256(data).hexdigest() != chip['sha256']:
            raise ValueError(f"image size/hash mismatch: {chip['filename']}")
        images.append(data)
    return b''.join(images)


def check_evidence(rom):
    if hashlib.sha256(rom).hexdigest() != COMBINED_SHA256:
        raise ValueError('combined order/hash mismatch')
    signatures = {
        0x0000: 'c3 2b 00',                 # reset JMP
        0x002B: '3e 92 d3 f3 d3 c3',       # peripheral initialization
        0x07FD: '78 e6 0f 32 72 80',       # 41 -> 42 flow
        0x0FFE: 'fe 07 ca 24 10',          # 42 -> 43 comparison/branch
        0x17FE: '32 77 80',                # STA spans 43 -> 44
        0x00C5: '31 01 00 21 00 00 01 fc 1f',  # checksum setup
        0x0AC7: '11 11 80 21 ee 81 3e 4e 77 23',
        0x0AD8: '3e 54 77',
        0x1856: '11 ee 81 21 c2 81 22 d3 81 3e 11 cd 1a 1a',
        0x188B: 'd3 f0',                  # message byte output
        0x18CF: '21 95 80 22 d3 81',      # receive buffer
        0x18EE: 'db f0',                  # message byte input
        0x197D: 'e6 60',                  # bus command class
        0x1983: '3a 93 80 a9 e6 1f',      # own five-bit address
        0x199C: 'fe 3f',                  # unlisten
        0x19B0: 'd6 20 ca c9 19 d6 20',   # listen/talk groups
        0x1A4A: '1a 8e 27 77',           # ADC M; DAA; store
        0x1D76: '0e 03 7e fe 2b',         # signed decimal parser
        0x1DF8: '3e 02 d3 a9 c3 48 00',   # startup detour returns
    }
    for offset, expected in signatures.items():
        data = bytes.fromhex(expected)
        if rom[offset:offset + len(data)] != data:
            raise ValueError(f'evidence signature changed at {offset:04X}')
    commands = {0x0BBE: 'N', 0x0BEE: 'P', 0x0BFD: 'T', 0x0C0C: 'H',
                0x0C45: 'R', 0x0C52: 'S', 0x0C66: 'U', 0x0CC2: 'V'}
    for offset, letter in commands.items():
        if rom[offset:offset + 2] != bytes([0xFE, ord(letter)]):
            raise ValueError(f'command comparison changed at {offset:04X}')
    checksums = []
    for i in range(4):
        # The last block stops before its own checksum at 1FFF, but includes
        # the first three stored checksums at 1FFC..1FFE.
        end = min((i + 1) * 0x800, 0x1FFF)
        total = sum(rom[i * 0x800:end]) & 0xFF
        stored = rom[0x1FFC + i]
        if (total + stored) & 0xFF:
            raise ValueError(f'internal additive checksum failed for label {41+i}')
        checksums.append((41 + i, total, stored))
    return checksums


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--disassemble', action='store_true')
    args = parser.parse_args()
    rom = load_rom()
    sums = check_evidence(rom)
    print(f'41 -> 42 -> 43 -> 44: {len(rom)} bytes, SHA256 {COMBINED_SHA256}')
    print('Code signatures, command comparisons, and four internal checksums: PASS')
    for label, total, stored in sums:
        print(f'label {label}: sum {total:02X} + stored {stored:02X} = 00 modulo 256')
    print('Raw printable runs (not necessarily text):')
    for match in re.finditer(rb'[ -~]{5,}', rom):
        print(f'{match.start():04X}: {match[0]!r}')
    if args.disassemble:
        for start, end in RANGES:
            # Seekable, in-memory file: z80dasm cannot read a normal stdin pipe.
            fd = os.memfd_create('rom-analysis')
            try:
                os.write(fd, rom[start:end])
                os.lseek(fd, 0, 0)
                print(f'\nSelected code {start:04X}..{end-1:04X}', flush=True)
                subprocess.run(['z80dasm', '-a', '-t', '-g', str(start),
                                f'/proc/self/fd/{fd}'], pass_fds=(fd,),
                               check=True, timeout=10)
            finally:
                os.close(fd)


if __name__ == '__main__':
    main()
