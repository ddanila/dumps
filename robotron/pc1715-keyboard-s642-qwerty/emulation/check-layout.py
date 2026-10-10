#!/usr/bin/env python3
"""Check alphabet output against MAME's physical letter-key positions."""
from pathlib import Path
import json
p=Path(__file__).resolve().parent
layout=json.loads((p/'layout-positions.json').read_text())
cases=json.loads((p/'language-test/decoded.json').read_text())
assert len(layout)==26
for letter,pos in layout.items():
    for shift in (0,1):
        name=f"mode0_shift{shift}_{pos['row']}_{pos['bit']}"
        expected=ord(letter if shift else letter.lower())
        assert cases[name]['bytes']==[0xe0 | (shift << 1), expected],name
print('PASS: all 26 letters in both Shift states (52 expected-code checks)')
