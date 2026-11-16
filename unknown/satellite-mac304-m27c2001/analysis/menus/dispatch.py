#!/usr/bin/env python3
import argparse,csv,json
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('rom',type=Path);ap.add_argument('--out',type=Path,default=Path('out'));a=ap.parse_args();b=a.rom.read_bytes();a.out.mkdir(exist_ok=True)
res={}
for name,base,nextbase,events,modes,site in [('submenu',0x2b50,0x2bf5,11,15,0x20000),('top_mode',0x2db8,0x2e52,22,7,0x23445)]:
 rows=[]
 for event in range(events):
  for mode in range(modes):
   idx=event*modes+mode
   rows.append(dict(event=event,mode=mode,action=b[base+idx],next_mode=b[nextbase+idx],action_file_offset=hex(base+idx),next_mode_file_offset=hex(nextbase+idx)))
 assert max(r['next_mode'] for r in rows)<modes
 call=b.index(bytes.fromhex('122419'),site,site+128);p=call+3
 low=int.from_bytes(b[p:p+2],'little');span=int.from_bytes(b[p+2:p+4],'little');default=int.from_bytes(b[p+4:p+6],'big')
 targets=[int.from_bytes(b[p+6+i*2:p+8+i*2],'big') for i in range(span+1)]
 record=dict(events=events,modes=modes,action_base=hex(base),next_mode_base=hex(nextbase),matrix=rows,dispatch_site=hex(call),dense_descriptor=hex(p),action_first=low,action_last=low+span,default_cpu=hex(default),action_targets=[dict(action=low+i,bank=3,cpu=hex(t),file=hex(t+0x18000)) for i,t in enumerate(targets)])
 res[name]=record
 with (a.out/f'{name}_matrix.tsv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=rows[0],delimiter='\t');w.writeheader();w.writerows(rows)
(a.out/'dispatch_tables.json').write_text(json.dumps(res,indent=2)+'\n')
for name,r in res.items():print(name,r['events'],r['modes'],r['action_first'],r['action_last'],r['dense_descriptor'])
