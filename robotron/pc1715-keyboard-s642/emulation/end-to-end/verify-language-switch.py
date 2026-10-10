#!/usr/bin/env python3
"""Check visible font switching on the unchanged TOS/M screen heading."""
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parent

def heading(directory, stage):
    with Image.open(root / directory / 'rt1715w' / f'{stage:04d}.png') as image:
        # Two static header lines; exclude the input line and blinking cursor.
        return image.convert('RGB').crop((0, 0, 640, 40)).tobytes()

stock = [heading('snapshots-switch-stock', i) for i in range(4)]
patched = [heading('snapshots-switch-patched', i) for i in range(4)]
assert all(s == stock[0] for s in stock), 'Stock baseline unexpectedly switched'
assert patched[0] == patched[1], 'SI/SO alone should wait for the next key'
assert patched[0] != patched[2], 'The next key did not change displayed glyphs'
assert patched[0] == patched[3], 'Switching back did not restore the font'
assert patched[0] == stock[0], 'Initial display differs from the stock baseline'
for suffix in ('stock', 'patched'):
    trace = (root / f'language-switch-{suffix}.tsv').read_text()
    assert 'PASS:' in trace, f'{suffix}: OS did not request both font changes'
assert (root / 'language-switch-stock.tsv').read_bytes() == (root / 'language-switch-patched.tsv').read_bytes(), 'Keyboard/OS traces differ'
print('PASS: identical keyboard and OS traffic; patched display switches Latin -> Cyrillic -> Latin')
print('PASS: toggle alone leaves display unchanged until the next key')
