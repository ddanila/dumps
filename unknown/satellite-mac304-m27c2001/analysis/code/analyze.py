#!/usr/bin/env python3
"""Reproduce compact static evidence; Python 3 + radare2 required. No source writes."""
import pathlib,sys,hashlib,json,subprocess,re,tempfile,argparse
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--rom',type=pathlib.Path,default=pathlib.Path(__file__).resolve().parents[2]/'mac304-m27c2001.bin')
parser.add_argument('--out',type=pathlib.Path,default=pathlib.Path(__file__).resolve().parent)
args=parser.parse_args();src=args.rom;out=args.out;out.mkdir(parents=True,exist_ok=True);b=src.read_bytes()
assert hashlib.sha256(b).hexdigest()=='8bea3d9a252bcb72c86594d4bed711c56cba43158baf454b0f53ba189e564d8a','Unexpected ROM revision'
meta={'source':'mac304-m27c2001.bin','sha256':hashlib.sha256(b).hexdigest(),'size':len(b),'last_nonzero':hex(max(i for i,x in enumerate(b) if x))}
functions=[('bank_init',0,0x7bb),('far_call',0,0x7c5),('far_return',0,0x7e4),('i2c_isr',0,0x67f),('timer0',0,0x61b),('service_key_match',3,0xad43),('service_entry_caller',3,0xb3e5),('service_events',3,0xa847),('service_root_render',3,0xac16),('receiver_setup_render',1,0xa953),('mac_setup_render',1,0x9e50),('receiver_save',1,0xafd5),('mac_save',1,0xa5d2),('receiver_apply',1,0xaed0),('receiver_bit_edit',1,0xacca),('mac_bit_edit',1,0xa1f8),('text_draw',2,0xa215),('text_field_draw',2,0xa2e7),('generic_code_pointer',0,0x26e9),('switch_dispatch',0,0x2487),('startup_key_loop',1,0xff46)]
fs=[{'name':s,'bank':n,'cpu':hex(a),'file':hex(a+n*0x8000 if a>=0x8000 else a)} for s,n,a in functions]
(out/'functions.json').write_text(json.dumps(fs,indent=2)+'\n')
calls=[]
for m in re.finditer(rb'\x74(.)\x90(..)\x12\x07\xc5',b,re.S):
 n=m[1][0];a=int.from_bytes(m[2],'big');calls.append({'file':m.start(),'bank':n,'cpu':a,'target':a+n*0x8000 if a>=0x8000 else a})
with (out/'far_calls.tsv').open('w') as f:
 f.write('file_offset\tbank\tcpu_target\tfile_target\n')
 for x in calls:f.write(f'{x["file"]:06x}\t{x["bank"]}\t{x["cpu"]:04x}\t{x["target"]:06x}\n')
meta['far_call_pattern_count']=len(calls)
# Reconstruct initialized external data using startup descriptors at fe and104.
x=bytearray(65536);copies=[]
for p in [0xfe,0x104]:
 dst,end,start=[int.from_bytes(b[p+i:p+i+2],'big') for i in (0,2,4)]
 x[dst:dst+end-start]=b[start:end];copies.append({'descriptor':hex(p),'source_start':hex(start),'source_end_exclusive':hex(end),'destination':hex(dst),'size':end-start})
meta['initializers']=copies
meta['key_match_defaults']={'state':x[0x77c0],'reverse_table':list(x[0x77c1:0x77c5]),'sequence':list(x[0x77c2:0x77c5][::-1])}
meta['service_event_table']=[]
p=0x22874
while b[p:p+2]!=b'\0\0':
 meta['service_event_table'].append({'event':hex(b[p+2]),'cpu':hex(int.from_bytes(b[p:p+2],'big'))});p+=3
meta['receiver_records']=[{'file':hex(p),'raw':b[p:p+8].hex(),'type':b[p],'setting_index':hex(b[p+1]),'min':b[p+2],'max':b[p+3],'default':b[p+4],'text_pointer':hex(int.from_bytes(b[p+6:p+8],'big'))} for p in range(0x778e,0x77ce,8)]
(out/'inventory.json').write_text(json.dumps(meta,indent=2)+'\n')
# Only targeted, correctly based snippets. No whole-ROM disassembly artifacts.
sections=[(0,0,0x10a),(0,0x61b,0x7fa),(0,0x2487,0x24ad),(0,0x26e9,0x26f6),(3,0xad43,0xad94),(3,0xb3e5,0xb420),(3,0xabd3,0xac16),(3,0xa9b5,0xaa18),(1,0x9f99,0x9fc8),(1,0xa953,0xa99c),(1,0xaed0,0xb086),(1,0xacca,0xadde),(1,0xade0,0xaed0),(1,0xa3c1,0xa56b),(1,0xff46,0xffb8)]
with tempfile.TemporaryDirectory(dir=out) as tmp, (out/'evidence.asm').open('w') as f:
 for n in range(4):pathlib.Path(tmp,f'b{n}').write_bytes(b[:0x8000]+b[0x8000+n*0x8000:0x10000+n*0x8000])
 for n,a,z in sections:
  f.write(f'\nBANK {n} CPU {a:04x} FILE {a+n*0x8000 if a>=0x8000 else a:06x}\n')
  cmd=['r2','-q','-a','8051','-e','scr.color=0','-e','asm.comments=false','-e','asm.lines=false','-c',f'pD {z-a} @ {a};q',str(pathlib.Path(tmp,f'b{n}'))]
  f.write(subprocess.check_output(cmd,text=True))
print(json.dumps(meta,indent=2))
