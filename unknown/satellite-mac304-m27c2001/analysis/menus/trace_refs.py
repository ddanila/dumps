from pathlib import Path
import re,json,csv,argparse
ap=argparse.ArgumentParser();ap.add_argument("rom",type=Path);ap.add_argument("--out",type=Path,default=Path("out"));args=ap.parse_args()
b=args.rom.read_bytes()
rows=json.loads((args.out/'catalog.json').read_text());slots={int(r['pointer_offset'],16):r for r in rows}
refs=[]
for m in re.finditer(rb'\x24(.)[\s\S]{1,5}?\x34(.)',b):
 p=m.start();lo=m[1][0];hi=m[2][0];addr=hi*256+lo
 if addr not in slots or p<0x8000:continue
 between=b[p+2:m.end()-2]
 if between not in [b'\xff\xe4',b'\xff\xee',b'\xf5\x82\xe4',b'\xf5\x82\xee']: continue
 tail=b[m.end():m.end()+6]
 if not (tail.startswith(bytes.fromhex('f583e493')) or tail.startswith(bytes.fromhex('fe7d02'))):continue
 r=slots[addr];prev=b[max(0,p-48):p]
 refs.append(dict(site=f'0x{p:06X}',base=f'0x{addr:04X}',table=r['table'],index=r['index'],group=r['group'],label=r['raw_escaped'],language_nearby=b'\x90\x74\x47' in prev,previous_far_return=f'0x{b.rfind(bytes.fromhex("0207e4"),0,p)+3:06X}',context=b[p-24:p+36].hex()))
for m in re.finditer(rb'\x7d\x02\x7e(.)\x7f(.)',b,re.S):
 p=m.start();addr=m[1][0]*256+m[2][0]
 if addr not in slots or p<0x8000:continue
 r=slots[addr];refs.append(dict(site=f'0x{p:06X}',base=f'0x{addr:04X}',table=r['table'],index=r['index'],group=r['group'],label=r['raw_escaped'],language_nearby=False,previous_far_return=f'0x{b.rfind(bytes.fromhex("0207e4"),0,p)+3:06X}',context=b[p-24:p+36].hex()))
for m in re.finditer(rb'\x90(..)\x12\x26\xe9',b,re.S):
 p=m.start();addr=int.from_bytes(m[1],'big')
 if addr not in slots or p<0x8000:continue
 r=slots[addr];refs.append(dict(site=f'0x{p:06X}',base=f'0x{addr:04X}',table=r['table'],index=r['index'],group=r['group'],label=r['raw_escaped'],language_nearby=False,previous_far_return=f'0x{b.rfind(bytes.fromhex("0207e4"),0,p)+3:06X}',context=b[p-24:p+36].hex()))
refs.sort(key=lambda r:r['site']);(args.out/'table_code_refs.json').write_text(json.dumps(refs,indent=2))
print(len(refs), 'table code reference patterns')
