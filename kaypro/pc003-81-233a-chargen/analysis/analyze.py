#!/usr/bin/env python3
"""Reproduce the PC003 glyph analysis. Python 3 standard library; MIT.

The reference is fetched into memory, or supplied with --reference. Historical
ROM bytes are not relicensed. SVGs are derived visualizations, not CRT photos.
"""
import argparse
import csv
import hashlib
import html
import json
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent
REFERENCE_URL = 'https://retrocmp.de/dwnld/U43_CHAR_81-146A_2716_2K.ROM'
REFERENCE_SHA1 = '5cb880083b94bd8220aac1f87d537db7cfeb9013'
CAPTURE_SHA256 = 'a01b7398e41170d0cf81f7974260cfd38f06f84c3390f1e871869387eee93d99'


def pixels(data, slot):
    """Eight rows, D4 at left, D0 at right; raw EPROM zero means lit."""
    return [[1 - ((value >> bit) & 1) for bit in range(4, -1, -1)]
            for value in data[slot * 8:slot * 8 + 8]]


def text(x, y, value, size=14, color='#263545'):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}">{html.escape(value)}</text>'


def begin(width, height, title, subtitle):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">',
            f'<title>{html.escape(title)}</title>',
            f'<desc>{html.escape(subtitle)}</desc>',
            '<rect width="100%" height="100%" fill="#f5f7fa"/>',
            '<g font-family="monospace">', text(24, 34, title, 22), text(24, 60, subtitle, 12)]


def cell(out, x, y, current, reference=None, scale=5):
    # Seven-dot by ten-line cell: one side margin and two blank bottom lines.
    out.append(f'<rect x="{x}" y="{y}" width="{7*scale}" height="{10*scale}" fill="#101b26"/>')
    for row in range(8):
        for col in range(5):
            on = current[row][col]
            old = reference[row][col] if reference is not None else on
            color = '#e7f2ff' if on and old else '#29c783' if on else '#f17c4a' if old else None
            if color:
                out.append(f'<rect x="{x+(col+1)*scale}" y="{y+row*scale}" width="{scale}" height="{scale}" fill="{color}"/>')


def save_svg(path, out):
    path.write_text('\n'.join(out + ['</g></svg>']) + '\n')


def atlas(data, slots, output, screen_codes, name='PC003 · 81-233A'):
    rows = (len(slots) + 15) // 16
    title = name + (' · visible character atlas' if screen_codes else ' · all 256 ROM slots')
    sub = ('Labels: screen code / ROM slot. Raw zero = lit; D4 → D0; 7 × 10 cells.'
           if screen_codes else 'Labels are ROM slots. 00–7F: blank half. 80–FF: visible half. Raw zero = lit.')
    out = begin(1176, 100 + rows * 104, title, sub)
    for index, slot in enumerate(slots):
        x, y = 24 + index % 16 * 72, 88 + index // 16 * 104
        label = f'{slot ^ 128:02X}/{slot:02X}' if screen_codes else f'{slot:02X}'
        out.append(text(x, y, label, 12))
        cell(out, x+9, y+10, pixels(data, slot), scale=7)
    save_svg(output, out)


def comparison(current, reference, slots, output):
    cols, width = 4, 1248
    out = begin(width, 126 + ((len(slots)+cols-1)//cols)*152,
                'PC003 81-233A vs 81-146A · every changed glyph',
                'Left: 81-146A. Middle: PC003. Right: overlay — white unchanged, green added, orange removed.')
    for index, slot in enumerate(slots):
        x, y = 24 + index % cols * 306, 106 + index // cols * 152
        screen = slot ^ 128
        label = f'screen {screen:02X} · ROM {slot:02X}'
        if 32 <= screen < 127:
            label += f' · {chr(screen)!r}'
        out.append(text(x, y, label, 13))
        a, b = pixels(current, slot), pixels(reference, slot)
        for offset, glyph, other, name in [(0,b,None,'81-146A'),(91,a,None,'PC003'),(182,a,b,'changes')]:
            cell(out,x+offset,y+12,glyph,other,scale=8)
            out.append(text(x+offset,y+110,name,12))
    save_svg(output,out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path)
    parser.add_argument('--out', type=Path, default=ROOT)
    args = parser.parse_args()
    capture = (ROOT.parent/'81-233a.bin').read_bytes()
    reference = args.reference.read_bytes() if args.reference else urlopen(REFERENCE_URL, timeout=30).read()
    assert len(capture) == len(reference) == 2048
    assert hashlib.sha256(capture).hexdigest() == CAPTURE_SHA256
    assert hashlib.sha1(reference).hexdigest() == REFERENCE_SHA1
    # Independent known-glyph checks catch bit order, polarity and bank mistakes.
    assert all(v == 255 for v in capture[:1024])
    assert all(v == 255 for v in reference[:1024])
    assert pixels(capture, 0xa0) == [[0]*5 for _ in range(8)]
    assert pixels(capture, 0xc1)[0] == [0,1,1,1,0]
    assert pixels(capture, 0xc1)[3] == [1,1,1,1,1]
    assert pixels(reference, 0xc1)[0] == [0,0,1,0,0]
    changes = []
    for slot in range(256):
        old, new = reference[slot*8:slot*8+8], capture[slot*8:slot*8+8]
        if old == new:
            continue
        a,b = pixels(capture,slot),pixels(reference,slot)
        added = sum(a[y][x] and not b[y][x] for y in range(8) for x in range(5))
        removed = sum(b[y][x] and not a[y][x] for y in range(8) for x in range(5))
        changes.append(dict(rom_slot=f'{slot:02X}',screen_code=f'{slot^128:02X}',
                            offset=f'{slot*8:04X}',reference_hex=old.hex(),capture_hex=new.hex(),
                            differing_bytes=sum(x!=y for x,y in zip(old,new)),
                            added_pixels=added,removed_pixels=removed))
    report = dict(capture_sha256=CAPTURE_SHA256,reference_url=REFERENCE_URL,
                  reference_sha1=REFERENCE_SHA1,
                  reference_name='retrocmp 81-146A; identical to MAME 81-146.u43',
                  reference_scope='closest among checked 81-146, 81-146A and omni_ii_u43 images',
                  size=2048,differing_bytes=sum(x!=y for x,y in zip(capture,reference)),
                  changed_rom_slots=len(changes),unchanged_rom_slots=256-len(changes),
                  changed_visible_glyphs=sum(int(c['rom_slot'],16)>=128 for c in changes),
                  unchanged_visible_glyphs=128-sum(int(c['rom_slot'],16)>=128 for c in changes),
                  upper_three_bits_changed=any((a^b)&224 for a,b in zip(capture,reference)),
                  added_pixels=sum(c['added_pixels'] for c in changes),
                  removed_pixels=sum(c['removed_pixels'] for c in changes),
                  changes=changes)
    assert sum(c['differing_bytes'] for c in changes)==report['differing_bytes']
    assert report['added_pixels']+report['removed_pixels']==sum(bin((x^y)&31).count('1') for x,y in zip(capture,reference))
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')
    with (args.out/'changes.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(changes[0]));writer.writeheader();writer.writerows(changes)
    atlas(capture,list(range(128,256)),args.out/'atlas.svg',True)
    atlas(reference,list(range(128,256)),args.out/'reference-atlas.svg',True,'Reference · 81-146A')
    atlas(capture,list(range(256)),args.out/'raw-slots.svg',False)
    comparison(capture,reference,[int(c['rom_slot'],16) for c in changes],args.out/'differences.svg')
    print(json.dumps({k:v for k,v in report.items() if k!='changes'},indent=2))


if __name__=='__main__':
    main()
