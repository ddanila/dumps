#!/usr/bin/env python3
"""Offline survey; pass a MAME unidasm executable to regenerate listings."""
from pathlib import Path
from collections import Counter
import hashlib, json, math, re, subprocess, sys
root=Path(__file__).resolve().parent
b=(root.parent/'read1.bin').read_bytes()
def runs(data,minimum=4):
 return [{'offset':f'{m.start():04x}','text':m.group().decode('ascii')} for m in re.finditer(rb'[ -~]{'+str(minimum).encode()+rb',}',data)]
variants={'raw':b,'inverted':bytes(x^255 for x in b),'bit_reversed':bytes(int(f'{x:08b}'[::-1],2) for x in b),'bit_reversed_inverted':bytes(int(f'{x:08b}'[::-1],2)^255 for x in b),'high_bit_toggled':bytes(x^128 for x in b),'seven_bit':bytes(x&127 for x in b)}
c=Counter(b)
r={'sha256':hashlib.sha256(b).hexdigest(),'size':len(b),'distinct_bytes':len(c),'entropy_bits_per_byte':-sum(n/len(b)*math.log2(n/len(b)) for n in c.values()),'ascii_runs':{k:runs(v) for k,v in variants.items()},'top_bytes':[(f'{v:02x}',n) for v,n in c.most_common(20)],'bit_ones':[sum(x>>j&1 for x in b) for j in range(8)],'repeated_aligned_halves':b[:1024]==b[1024:]}
# Raw opcode candidates, NOT a recovered instruction stream.
targets=[(i,b[i+1]|b[i+2]<<8) for i,x in enumerate(b[:-2]) if x in (0xc3,0xcd)]
r['8080_raw_c3_cd_candidates']=[{'offset':f'{i:04x}','target':f'{t:04x}'} for i,t in targets]
r['8080_best_aligned_2k_target_window']=max(({'base':f'{base:04x}','count':sum(base<=t<base+2048 for _,t in targets)} for base in range(0,65536,2048)),key=lambda x:x['count'])
# Strings with alternating zero bytes, aligned to either byte lane.
r['utf16_ascii_runs']={}
for endian in ['little','big']:
 found=[]
 for offset in [0,1]:
  decoded=b[offset:len(b)-(len(b)-offset)%2].decode('utf-16-le' if endian=='little' else 'utf-16-be',errors='replace')
  found += [{'offset':f'{offset+2*m.start():04x}','text':m.group()} for m in re.finditer(r'[ -~]{4,}',decoded)]
 r['utf16_ascii_runs'][endian]=found
r['cyrillic_letter_runs']={}
for enc in ['koi8-r','cp866','cp1251']:
 text=b.decode(enc,errors='replace')
 r['cyrillic_letter_runs'][enc]=[{'offset':f'{m.start():04x}','text':m.group()} for m in re.finditer(r'[А-Яа-яЁё]{6,}',text)]
if len(sys.argv)>1:
 r['disassemblers']={}
 for arch in ['i8085','z80','mcs48','i8051','t11','m6800','m6809','m6502']:
  txt=subprocess.check_output([sys.argv[1],str(root.parent/'read1.bin'),'-arch',arch],text=True)
  (root/f'{arch}.asm').write_text(txt)
  r['disassemblers'][arch]={'lines':len(txt.splitlines()),'illegal_or_data_lines':sum(bool(re.search(r'\billegal\b|\.WORD|\bkil\b',line,re.I)) for line in txt.splitlines())}
(root/'results.json').write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({k:r[k] for k in ['size','distinct_bytes','entropy_bits_per_byte','8080_best_aligned_2k_target_window','cyrillic_letter_runs','disassemblers'] if k in r},indent=2,ensure_ascii=False))
