#!/usr/bin/env python3
"""Rebuild static reports; all addresses are CPU addresses with ROM origin zero.
Recursive decoding follows direct flow and explicit table seeds, not speculative
pointer scanning. Unreached bytes remain data/unclassified in disassembly.asm.
"""
import collections, hashlib, json, math, re
from pathlib import Path
from decode8085 import decode
HERE=Path(__file__).resolve().parent
ROM=(HERE.parent/'tmm27128ad-20.bin').read_bytes()
assert hashlib.sha256(ROM).hexdigest()=='739c871b383c216428ee833d2758b7590ab4e589b76a065dece91e532cfb1849'
def word(a): return int.from_bytes(ROM[a:a+2],'little')
def dump(name,obj): (HERE/name).write_text(json.dumps(obj,indent=2)+'\n')
# Directly observed tables: public primitive JMPs and four 32-entry control/key dispatches.
api=[{'entry':a,'target':word(a+1)} for a in range(0x40,0x1e4,3)]
assert all(ROM[x['entry']]==0xc3 for x in api)
dispatch=[{'table':t,'code':base+i,'target':word(t+2*i)} for t,base in [(0x25bf,0),(0x25ff,0x80),(0x263f,0xb0),(0x267f,0xd0)] for i in range(32)]
seeds=[0,8,0x10,0x18,0x20,0x24,0x28,0x2c,0x30,0x34,0x38,0x3c,0x2102]
seeds += [x['entry'] for x in api]+[x['target'] for x in dispatch]
# RAM callback initializers observed in reset/init paths; missing targets kept external.
seeds += [0x413,0x294,0x42d,0x499,0x65b,0x88d,0x22d9,0x2440,0x24d2,0x2553]
pending=list(seeds); ins={}; edges=[]; indirect=[]; external=set()
while pending:
 p=pending.pop()
 if not 0<=p<len(ROM): external.add(p); continue
 if p in ins: continue
 try: text,n=decode(ROM,p,0)
 except IndexError: continue
 if text.startswith('DB'): continue
 ins[p]=(text,n); op=ROM[p]
 targets=[]; fall=True
 if op==0xc3 or op&0xc7 in (0xc2,0xc4) or op==0xcd:
  target=word(p+1); kind='call' if op==0xcd or op&0xc7==0xc4 else 'jump'
  targets.append(target); edges.append({'source':p,'target':target,'kind':kind})
  if op==0xc3: fall=False
 elif op&0xc7==0xc7:
  targets.append(op&0x38);edges.append({'source':p,'target':op&0x38,'kind':'rst'})
 if op in (0xc9,0xe9,0x76): fall=False
 if op==0xe9: indirect.append(p)
 pending.extend(targets)
 if fall: pending.append(p+n)
covered=set(); overlaps=[]
for a,(text,n) in sorted(ins.items()):
 for i in range(a,a+n):
  if i in covered: overlaps.append(i)
  covered.add(i)
symbols=json.loads((HERE/'symbols.json').read_text())
lines=['; 8085, origin 0000h. Recursive direct-flow disassembly; DB = unclassified/data.',
       '; No claim that all executable paths were discovered. See analyze.py for seeds.']
p=0
while p<len(ROM):
 if p in ins:
  if f'{p:04X}' in symbols: lines.append('; '+symbols[f'{p:04X}'])
  text,n=ins[p];lines.append(f'{p:04X}: {ROM[p:p+n].hex(" "):11} {text}');p+=n
 else:
  end=p+1
  while end<min(p+16,len(ROM)) and end not in ins: end+=1
  lines.append(f'{p:04X}: {ROM[p:end].hex(" "):47} DB '+','.join(f'${x:02X}' for x in ROM[p:end]));p=end
(HERE/'disassembly.asm').write_text('\n'.join(lines)+'\n')
ports=collections.defaultdict(list)
for a,(text,n) in ins.items():
 if ROM[a] in (0xd3,0xdb): ports[f'{ROM[a+1]:02X}'].append({'address':a,'operation':'out' if ROM[a]==0xd3 else 'in'})
strings=[{'offset':m.start(),'text':m.group().decode()} for m in re.finditer(rb'[ -~]{5,}',ROM)]
blocks=[]
for a in range(0,len(ROM),1024):
 b=ROM[a:a+1024]; c=collections.Counter(b)
 blocks.append({'start':a,'sum8':sum(b)&255,'ff_bytes':c[255],'entropy':round(-sum(n/len(b)*math.log2(n/len(b)) for n in c.values()),4)})
report={'size':len(ROM),'sha256':hashlib.sha256(ROM).hexdigest(),'sum8':sum(ROM)&255,'sum16':sum(ROM)&65535,'non_ff_bytes':sum(x!=255 for x in ROM),'api_entries':len(api),'decoded_instructions':len(ins),'covered_bytes':len(covered),'coverage_fraction':len(covered)/len(ROM),'overlap_bytes':sorted(set(overlaps)),'external_direct_targets':sorted(external),'indirect_jumps':sorted(indirect),'blocks_1k':blocks,'address_bit_pair_differences_once':{f'A{k}':sum(ROM[a]!=ROM[a^(1<<k)] for a in range(len(ROM)) if not a&(1<<k)) for k in range(14)}}
(HERE/'api.tsv').write_text('entry\ttarget\tinterpretation\n'+'\n'.join(f"{x['entry']:04X}\t{x['target']:04X}\t{symbols.get(format(x['target'],'04X'),'unassigned')}" for x in api)+'\n')
dump('static.json',report);dump('api.json',api);dump('control-dispatch.json',dispatch);dump('edges.json',sorted(edges,key=lambda x:x['source']));dump('ports.json',dict(sorted(ports.items())));dump('strings.json',strings)
dump('push-keys.json',[{'slot':i+1,'nvram_offset':word(0x1d84+2*i),'capacity':12 if i<8 else 32 if i<12 else 48} for i in range(16)])
dump('baud-divisors.json',[{'index':i,'divisor':word(0xb2f+2*i)} for i in range(12)])
print(json.dumps({k:v for k,v in report.items() if k not in ('blocks_1k','address_bit_pair_differences_once')},indent=2))
