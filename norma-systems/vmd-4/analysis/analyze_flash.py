#!/usr/bin/env python3
"""Reproduce ROM identity, dis51 input and optional diagnostic flash summary.

python3 analyze_flash.py --hex /tmp/vmd4.hex [--flash /path/to/VMD29R3.BIN]
dis51 -l 0 3 11 19 27 35 < /tmp/vmd4.hex > /tmp/vmd4.asm
This performs static inspection, not CPU emulation or physical chip access.
"""
import argparse
from collections import Counter
from hashlib import sha256
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--hex', type=Path)
parser.add_argument('--flash', type=Path)
args = parser.parse_args()
rom = (Path(__file__).resolve().parent.parent /
       '27c512/vmd4-1.01-27c512.bin').read_bytes()
expected = '40ac0caceb2576887a4d6cbf710258689c3d200711f26cfaa90492db1d5ea386'
if sha256(rom).hexdigest() != expected:
    raise SystemExit('Unexpected ROM hash; offsets need re-analysis')
print('EPROM SHA256:', expected)
print('Fallback comparison bytes:', repr(rom[0x104:0x10a][::-1]))
if args.hex:
    records = []
    for address in range(0, len(rom), 16):
        data = rom[address:address + 16]
        record = bytes([len(data), address >> 8, address & 255, 0]) + data
        records.append(':' + (record + bytes([-sum(record) & 255])).hex().upper())
    args.hex.write_text('\n'.join(records) + '\n:00000001FF\n')
if args.flash:
    flash = args.flash.read_bytes()
    if len(flash) != 65536:
        raise SystemExit('Expected a 65536-byte flash capture')
    print('Flash SHA256:', sha256(flash).hexdigest())
    print('Byte counts:', {f'{k:02X}': v for k, v in sorted(Counter(flash).items())})
    residues = Counter((i % 128, b) for i, b in enumerate(flash) if b != 255)
    print('Non-FF (offset within page, value):', dict(sorted(residues.items())))
    # Address interpretation assumes P4=A0..7 and P5=A8..15, without permutation.
    for page in [0x152, 0x153, 0x172, 0x173, 0x192, 0x193,
                 0x1b2, 0x1b3, 0x1c3, 0x1d0]:
        base = page * 128
        print(f'Page {page:03X}, base {base:04X}: first 16 '
              f'{flash[base:base+16].hex(" ")}; last 8 '
              f'{flash[base+120:base+128].hex(" ")}')
    print('Candidate persistent access code at E184..E189:',
          flash[0xe184:0xe18a].hex(' '))
