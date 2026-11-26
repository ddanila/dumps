#!/usr/bin/env python3
"""Execute original bytes in an 8080 core, rejecting all 8085-specific opcodes.
Only isolated compatible routines are tested. Unknown ROM reads, execution
outside this image, ROM writes and unsupplied input ports fail the run.
"""
import argparse,ctypes as C,hashlib,json,subprocess,tempfile,urllib.request
from pathlib import Path
HERE=Path(__file__).resolve().parent
REV='2e57421095e18337e5b65bf2505d8f0f012766dd'
URL=f'https://raw.githubusercontent.com/ddanila/dac-emulation/{REV}/third_party/cpu/i8080/'
p=argparse.ArgumentParser();p.add_argument('--cpu-source',type=Path);args=p.parse_args()
rom=(HERE.parent/'tmm27128ad-20.bin').read_bytes()
assert hashlib.sha256(rom).hexdigest()=='739c871b383c216428ee833d2758b7590ab4e589b76a065dece91e532cfb1849'
with tempfile.TemporaryDirectory(prefix='tmm-probe-') as tmp:
 tmp=Path(tmp); source=args.cpu_source or tmp
 if args.cpu_source is None:
  for name in ['i8080.c','i8080.h','I8080_LICENSE']:(tmp/name).write_bytes(urllib.request.urlopen(URL+name).read())
 hashes={name:hashlib.sha256((source/name).read_bytes()).hexdigest() for name in ['i8080.c','i8080.h']}
 expected=json.loads((HERE/'cpu-source.json').read_text())
 assert hashes==expected['sha256'],(hashes,expected)
 libpath=tmp/'probe.so'
 subprocess.run(['cc','-shared','-fPIC','-O2','-I',str(source),str(HERE/'probe_bridge.c'),str(source/'i8080.c'),'-o',str(libpath)],check=True)
 lib=C.CDLL(str(libpath));lib.load.argtypes=[C.c_char_p];lib.load(rom)
 cases=[]
 def call(start,stop=0xffff,limit=100000):
  lib.set(5,0xf000);lib.put(0xf000,255);lib.put(0xf001,255)
  n=lib.run(start,stop,limit)
  assert n>=0,{'start':hex(start),'result':n,'pc':hex(lib.get(6)),'fault_address':hex(lib.get(7))}
  return n
 def word(a,v):lib.put(a,v&255);lib.put(a+1,v>>8)
 def record(name,count,**kw):cases.append({'name':name,'cases':count,'passed':True,**kw})
 # Reset hardware programming before RAM/self-test; no synthetic successes.
 lib.reset();call(0,0x21b)
 out=[lib.output(i) for i in range(lib.get(8))]
 assert out==[0x5008,0x60df,0x3edf,0x3adf,0x3071,0x317f,0x326d,0x3318,0x3451,0x3528,0x3618,0x3c00,0x3d00,0x3e00]
 assert lib.get(5)==0x5fff
 record('reset prefix to 021B',1,port_writes=[f'{v>>8:02X}:{v&255:02X}' for v in out])
 # Every 8-bit row/column combination, original range checker.
 for h in range(256):
  for l in range(256):
   lib.reset();lib.set(3,h*256+l);lib.set(0,0xa5);call(0x1e82)
   assert lib.get(4)==(not(1<=h<=25 and 1<=l<=80));assert lib.get(0)==0xa5
 record('80 x 25 coordinate bounds, all HL inputs',65536)
 # Cyclic display traversal in the 25 x 80 byte-per-page layout.
 for row in range(25):
  for col in range(80):
   addr=(0x60+row)*256+col;idx=row*80+col
   for entry,delta in [(0x1edc,1),(0x1ee0,-1)]:
    lib.reset();lib.set(3,addr);call(entry);new=(idx+delta)%2000
    assert lib.get(3)==(0x60+new//80)*256+new%80
 record('display forward/backward wrapping',4000)
 # Each generic queue: fill/full/dequeue/empty, repeat to cross wrap boundaries.
 queues=[(0xeef,0xefb,0x5dbd,32),(0xf06,0xf12,0x5d53,32),(0xf1d,0xf29,0x5d9a,32),(0xf34,0xf4b,0x5d2e,255),(0xf61,0xf6d,0x5d76,32),(0xf78,0xf8f,0x5dec,8),(0xfa5,0xfe3,0x5de1,32)]
 count=0
 for enq,deq,meta,capacity in queues:
  lib.reset()
  for cycle in range(3):
   for i in range(capacity):lib.set(0,(i+cycle)&255);call(enq);assert lib.get(4)==0;count+=1
   assert lib.peek(meta)==capacity
   lib.set(0,0xaa);call(enq);assert lib.get(4)==1;count+=1
   for i in range(capacity):call(deq);assert lib.get(4)==0 and lib.get(0)==(i+cycle)&255;count+=1
   call(deq);assert lib.get(4)==1 and lib.peek(meta)==0;count+=1
 record('seven queues: order/full/empty/three wrap cycles',count)
 # Optional large queue uses a 16-bit count and 2000-byte external RAM region.
 lib.reset();lib.put(0x5dfe,1);word(0x5dff,0x8000)
 for cycle in range(2):
  for i in range(2000):lib.set(0,(i+cycle)&255);call(0xfa5);assert not lib.get(4)
  call(0xfa5);assert lib.get(4)
  for i in range(2000):call(0xfe3);assert not lib.get(4) and lib.get(0)==(i+cycle)&255
  call(0xfe3);assert lib.get(4)
 record('2000-byte optional queue: full/empty/two wrap cycles',8004)
 for a in range(256):
  lib.reset();lib.set(0,a);call(0x1d58)
  assert lib.get(4)==(a>=16)
  if a<16:assert lib.get(1)&255==(12 if a<8 else 32 if a<12 else 48)
  lib.reset();lib.set(0,a);call(0x1d71)
  expected=int.from_bytes(rom[0x1d84+2*(a&15):0x1d86+2*(a&15)],'little')
  assert lib.get(3)==expected and lib.get(0)==a
 record('PUSH-key capacities and low-nibble address lookup',512)
 for a in range(12):
  lib.reset();lib.set(0,a);call(0xb24);assert lib.get(3)==0xb2f+2*a
 record('12 divisor table selections',12)
 for a in range(256):
  lib.reset();lib.set(0,a);call(0x3dfc)
  assert lib.get(0)==ord(str(a).zfill(3)[0])
  assert lib.get(1)>>8==ord(str(a).zfill(3)[1]) and lib.get(1)&255==ord(str(a).zfill(3)[2])
 record('three-digit decimal conversion',256)
 for lo,hi in [(0,0x2100),(0,0x4000),(0x2100,0x4000),(0x100,0x101)]:
  lib.reset();lib.set(3,lo);lib.set(2,hi);lib.put(0x5e01,0x37);call(0x6c0,limit=300000)
  assert lib.peek(0x5e01)==(0x37+sum(rom[lo:hi]))&255
 record('additive checksum spans',4)
 # RAM test must detect a fault, not merely return success with ideal RAM.
 for fault in (False,True):
  lib.reset();lib.set(3,0x5800);lib.set(2,0x5a00)
  if fault:lib.corrupt_read(0x5873,1)
  call(0x702);assert lib.get(4)==fault
 record('RAM low/high address patterns: healthy and injected read fault',2)
 # Keyboard transmitter tests ready and busy without touching real hardware.
 for ready in (0,2):
  lib.reset();lib.input(0x10,ready);lib.set(0,0x24);call(0xce6)
  assert lib.get(4)==(ready==0)
  assert lib.get(8)==(1 if ready else 0)
  if ready:assert lib.output(0)==0x1124
 record('keyboard ACIA transmitter ready/busy',2)
 result={'scope':'Isolated 8080-compatible routines only; 8085-only opcodes rejected; not a terminal boot.','cpu_revision':REV,'cpu_source_sha256':hashes,'groups':cases,'total_cases':sum(x['cases'] for x in cases),'all_passed':True}
 (HERE/'probe-results.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2))
