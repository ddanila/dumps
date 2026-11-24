#!/usr/bin/env python3
"""Reproduce static evidence from local captures; no ROM execution or I/O."""
import argparse, hashlib, json, re, subprocess, zlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--sessions',type=Path,default=Path('/home/ddanila/fun/dosravi/sessions'));p.add_argument('--output',type=Path,default=Path('/tmp/beckman-analysis'));a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
# Inferred runtime offsets; chip7 uses E000 segment rather than F000.
bases={1:0xf000,2:0x6000,3:0xd000,5:0xb000,6:0xa000,7:0,8:0x8000}
r=[]
for c in range(1,9):
 b=(a.sessions/f'unknown-8088-20261107-chip{c:02}-read1'/f'U88C{c}R1.BIN').read_bytes()
 strings=[{'offset':hex(m.start()),'text':m.group().decode()} for m in re.finditer(rb'[ -~]{8,}',b)]
 r.append(dict(chip=c,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),crc32=f'{zlib.crc32(b):08x}',unique_bytes=len(set(b)),repeated_halves=b[:len(b)//2]==b[len(b)//2:],strings=strings))
 if c in bases:
  src=a.sessions/f'unknown-8088-20261107-chip{c:02}-read1'/f'U88C{c}R1.BIN'
  out=subprocess.check_output(['ndisasm','-b16',f'-o{bases[c]}',str(src)],text=True)
  (a.output/f'chip{c}-linear.asm').write_text(out)
(a.output/'evidence.json').write_text(json.dumps(r,indent=2)+'\n')
print('Generated evidence and linear disassembly in',a.output)
