#!/usr/bin/env python3
"""Generate emulator test specifications from ROM and statically decoded handlers.
No firmware is executed here; status stays not_run. The generated cases do not establish runtime behavior.
"""
import pathlib,json,argparse
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--rom',type=pathlib.Path,default=pathlib.Path(__file__).resolve().parents[2]/'mac304-m27c2001.bin')
parser.add_argument('--out',type=pathlib.Path,default=pathlib.Path(__file__).resolve().parent)
args=parser.parse_args();p=args.out;p.mkdir(parents=True,exist_ok=True);b=args.rom.read_bytes()
import hashlib
assert hashlib.sha256(b).hexdigest()=='8bea3d9a252bcb72c86594d4bed711c56cba43158baf454b0f53ba189e564d8a','Unexpected ROM revision'
cases=[];rows=[]
def add(suite,row,start,event,expected,**kw):
 cases.append(dict(suite=suite,row=row,start=start,event=event,expected=expected,status='not_run',**kw))
for i in range(21):
 a=0x77ce+27*i;flags,dev,reg,nv,lower,upper,default,step=b[a:a+8]
 row=dict(row=i,file=hex(a),label=b[a+8:a+27].split(b'\0')[0].decode(),flags=hex(flags),device=dev,register=reg,setting_index=nv,lower_comparison_threshold=lower,upper_comparison_threshold=upper,default=default,step=step,signed=bool(flags&0x20),scratch=hex(0x6b02+i))
 row['coupled_next_row']=bool(flags&0x10)
 rows.append(row)
 for start in sorted(set([default,lower,upper,0,255,128,127])):
  for direction in [0,1]:
   if flags&0x20:expected=(start+(1 if direction else -1))&255 if start!=(127 if direction else 128) else start
   else:expected=(start+(step if direction else -step))&255 if (start<upper if direction else start>lower) else start
   add('MAC_numeric',i,start,direction,expected,call={'bank':1,'cpu':'a3c1','r7':direction},setup={'6afe':i,'6aff':flags,hex(0x6b02+i):start})
 # Bit-edit bypasses numeric step, important for VCU flags whose step=0.
 for bit in range(8):
  add('MAC_bit',i,default,bit,default^(1<<bit),call={'bank':1,'cpu':'a1f8','r7':bit},setup={'6afe':i,'6aff':flags,hex(0x6b02+i):default})
for i in range(8):
 a=0x778e+8*i;typ,setting,low,high,default=b[a:a+5]
 if typ==8:
  cases.append(dict(suite='ChangeCode_save',row=i,status='not_run',start='5678',setup={'74be..74c1':[53,54,55,56]},call={'bank':1,'cpu':'afd5'},expected_settings={'31':53,'32':54,'33':55,'34':56},expected_unchanged=['77c2','77c3','77c4']))
  continue
 for start in sorted(set([low,high,default])):
  for delta in [-1,1]:
   val=(start+delta)&65535;expected=high if val<low else low if val>high else val
   add('receiver_numeric',i,start,delta,expected,call={'bank':1,'cpu':'ade0','r7':delta&255},setup={'6874':i,hex(0x6b18+2*i):0,hex(0x6b19+2*i):start})
 if typ==2:
  for bit in range(8):add('OptionByte_bit',i,default,bit,default^(1<<bit),call={'bank':1,'cpu':'acca','r7':bit},setup={'6876':i,'6b24':0,'6b25':default},expected_apply='row6->afce no-op',expected_save_setting='30')
obj={'status':'static test specifications; not executed','call_convention':'All banked entries through common07c5; target returns07e4. Hardware I/O/draw routines need emulator support. Setup maps are hexadecimal addresses, numeric values decimal. Capture expected scratch before any dependent redraw/peripheral side effects.','mac_rows':rows,'cases':cases}
(p/'service-tests.json').write_text(json.dumps(obj,indent=2)+'\n')
with (p/'mac-rows.tsv').open('w') as f:
 f.write('row\tfile\tlabel\tflags\tlower_threshold\tupper_threshold\tdefault\tstep\tsigned\n')
 for x in rows:f.write('\t'.join(str(x[k]) for k in ['row','file','label','flags','lower_comparison_threshold','upper_comparison_threshold','default','step','signed'])+'\n')
print(len(cases),'specifications generated, none executed')
