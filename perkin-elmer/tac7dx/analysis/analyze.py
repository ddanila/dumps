#!/usr/bin/env python3
"""Reproducible static extraction; tables are data, not linear-disassembly code."""
from pathlib import Path
import json,hashlib,csv
BASE=Path(__file__).resolve().parent
u35=(BASE.parent/'u35-n5208003-27256-read.bin').read_bytes();u36=(BASE.parent/'u36-n5208004-27256-read.bin').read_bytes()
assert u35[:16384]==u35[16384:]
m=bytes(16384)+u35[16384:]+u36
word=lambda a:int.from_bytes(m[a:a+2],'big')
summary={'cpu':'Motorola 6809','mapping':{'U35':'4000-7fff (upper half of raw capture)','U36':'8000-ffff'},'checksums':{},'vectors':{},'command_count':0}
for n,b in [('U35',u35[16384:]),('U36',u36)]:
 stored=int.from_bytes(b[:2],'big');computed=sum(b[2:])&65535
 summary['checksums'][n]={'stored':f'{stored:04x}','computed':f'{computed:04x}','pass':stored==computed,'sha256':hashlib.sha256(b).hexdigest()};assert stored==computed
for name,a in [('SWI3',0xfff2),('SWI2',0xfff4),('FIRQ',0xfff6),('IRQ',0xfff8),('SWI',0xfffa),('NMI',0xfffc),('RESET',0xfffe)]:summary['vectors'][name]=f'{word(a):04x}'
rows=[]
for c in range(32,123):
 v=[word(t+2*(c-32)) for t in (0x5baa,0x5c60,0x5d16)]
 rows.append({'character':chr(c),'hex':f'{c:02x}','validation':f'{v[0]:04x}','action':f'{v[1]:04x}','reply':f'{v[2]:04x}','supported':v[0]!=0xa6c3})
summary['command_count']=sum(r['supported'] for r in rows)
with (BASE/'commands.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=rows[0].keys(),lineterminator='\n');w.writeheader();w.writerows(rows)
(BASE/'static-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
