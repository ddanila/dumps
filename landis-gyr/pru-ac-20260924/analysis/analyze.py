#!/usr/bin/env python3
"""Reproduce byte-level findings; optionally regenerate MAME disassembly excerpts.
No hardware access. Python standard library only. Offsets are physical file offsets.
"""
import argparse
import collections
from difflib import SequenceMatcher
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import tempfile
import zlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

def checksum(a, b):
    # Recovered from HC11 CPU E268..E299. Excludes memory-mapped I/O hole.
    return (~(sum(a[:0x3fb0]) + sum(a[0x3fc8:0x4000]) +
              sum(a[0x4000:0x1c000]) + sum(b[:0x1c000]))) & 255

def stats(d):
    c = collections.Counter(d)
    return dict(size=len(d), sha256=hashlib.sha256(d).hexdigest(),
                sha1=hashlib.sha1(d).hexdigest(), crc32=f'{zlib.crc32(d):08x}',
                entropy_bits_per_byte=round(-sum(n/len(d)*math.log2(n/len(d)) for n in c.values()), 6),
                distinct_bytes=len(c), zero_bytes=c[0], ff_bytes=c[255],
                distinct_128_byte_pages=len({d[i:i+128] for i in range(0,len(d),128)}),
                smallest_power_of_two_period=next((2**k for k in range(len(d).bit_length()-1)
                    if d == d[:2**k]*(len(d)//2**k)), None),
                address_bit_equal_pair_fraction={f'A{k}': round(sum(d[i]==d[i^(1<<k)]
                    for i in range(len(d)) if not i&(1<<k))/(len(d)//2), 6)
                    for k in range(len(d).bit_length()-1)},
                trailing_zero_bytes=len(d)-len(d.rstrip(b'\0')))

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--unidasm', type=Path)
    args=ap.parse_args()
    chips={n:(ROOT/f'chip{n:02d}-{"28c64" if n<5 else "m27c1001"}.bin').read_bytes() for n in range(1,7)}
    a,b=chips[5],chips[6]
    report={'schema':1, 'chips':{str(n):stats(d) for n,d in chips.items()},
            'firmware_header':re.match(rb'[ -~]+',a).group().decode('ascii'),
            'checksum':{'algorithm':'complement of 8-bit byte sum', 'calculated':f'{checksum(a,b):02x}',
                'stored_chip05_offset_003fbf':f'{a[0x3fbf]:02x}', 'matches':checksum(a,b)==a[0x3fbf],
                'covered_bytes':0x4000-24+13*0x4000,
                'limitations':'8-bit additive checksum; no bank-order validation; excludes chip05 01c000..01ffff, chip06 01c000..01ffff and chip05 003fb0..003fc7; no EEPROM coverage'},
            'fixed_window':{'chip':5,'file_offset':'000000','cpu_range':'c000-ffff'},
            'banks':[], 'vectors':[]}
    stubs=[0xf408,0xf423,0xf460]+list(range(0xf47d,0xf583,0x1d))
    for bank in range(13):
        n, off=(5, (bank+1)*0x4000) if bank<6 else (6,(bank-6)*0x4000)
        d=chips[n][off:off+0x4000]
        counts={f'{s:04x}':sum(d[i:i+3]==b'\xbd'+s.to_bytes(2,'big') for i in range(len(d)-2)) for s in stubs}
        report['banks'].append(dict(selector=bank,chip=n,file_offset=f'{off:06x}',cpu_range='4000-7fff',
            restore_stub=f'{stubs[bank]:04x}',raw_jsr_stub_occurrences=counts,stats=stats(d)))
    names=['SCI','SPI','pulse accumulator input','pulse accumulator overflow','timer overflow',
           'output compare 5/input capture 4','output compare 4','output compare 3','output compare 2',
           'output compare 1','input capture 3','input capture 2','input capture 1','real-time interrupt',
           'IRQ','XIRQ','SWI','illegal opcode','COP failure','clock monitor failure','reset']
    for cpu,name in zip(range(0xffd6,0x10000,2),names):
        dest=int.from_bytes(a[cpu-0xc000:cpu-0xc000+2],'big')
        report['vectors'].append(dict(cpu_vector=f'{cpu:04x}',name=name,target=f'{dest:04x}',
                                    target_in_fixed_rom=dest>=0xc000))
    report['unmapped_eprom_tails']={str(n):stats(chips[n][0x1c000:]) for n in (5,6)}
    report['chip02_page_hex']=chips[2][:128].hex()
    report['chip03_chip04_shared_blocks']=[{'chip03_offset':f'{m.a:06x}',
        'chip04_offset':f'{m.b:06x}', 'length':m.size}
        for m in SequenceMatcher(None,chips[3],chips[4],autojunk=False).get_matching_blocks() if m.size>=64]
    report['chip04_tail_markers']=[{'offset':f'{i:06x}','value':f'{chips[4][i]:02x}',
        'distance_from_end':8191-i} for i in range(0x1700,0x2000) if chips[4][i]!=255]
    # A checksum implementation sensitivity check, not a physical read verification.
    changed=bytearray(a); changed[0x4000]^=1
    assert checksum(changed,b)!=checksum(a,b)
    assert checksum(a,b)==a[0x3fbf], 'Firmware checksum mismatch'
    assert a[0x3ffe:0x4000]==bytes.fromhex('df5d')
    assert a[0x20a6:0x20ab]==bytes.fromhex('86a0b7103d')
    assert len(stubs)==13
    (HERE/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    # Keep offsets + raw hex for every candidate, so encoding choices are reversible.
    strings={}
    for n,d in chips.items():
        strings[str(n)]=[{'offset':f'{m.start():06x}','text':m.group().decode('ascii')}
                        for m in re.finditer(rb'[ -~]{5,}',d)]
    (HERE/'ascii-strings.json').write_text(json.dumps(strings,indent=2)+'\n')
    extended={str(n):[{'offset':f'{m.start():06x}','hex':m.group().hex(),
                     'cp850':m.group().decode('cp850'),'latin1':m.group().decode('latin1')}
                for m in re.finditer(rb'[\x20-\x7e\x80-\xfe]{5,}',chips[n])
                if any(65<=x<=90 or 97<=x<=122 for x in m.group()) and any(x>=128 for x in m.group())]
              for n in (3,4)}
    (HERE/'text-encoding-candidates.json').write_text(json.dumps(extended,indent=2,ensure_ascii=False)+'\n')
    if args.unidasm:
        exe=args.unidasm.resolve()
        # Fixed, bounded windows; linear decoding is explicitly not code/data discovery.
        windows=[('reset',a[0x1f5d:0x1f9e],0xdf5d),('startup',a[0x20a6:0x20ff],0xe0a6),
                 ('ram-test',a[0x21ec:0x2268],0xe1ec),('checksum',a[0x2268:0x22a8],0xe268),
                 ('far-call',a[0x3408:0x3460],0xf408),('scheduler',a[0x1c42:0x1cd0],0xdc42),
                 ('trap-monitor',a[0x25ab:0x2657],0xe5ab),('sci',a[0x247a:0x24ac],0xe47a),
                 ('bank6-function',b[:0x110],0x4000)]
        architectures=['hc11','m6800','m6801','m6803','hd6301','hd63701','m6805','m68hc05',
                       'm6809','hd6309','i8051','sab80515','mcs48','i8085','z80','z180','z8',
                       'm6502','w65c02','x86_16','i8x9x','i8xc196','h8','h8h','tlcs870',
                       'tmp90c051','tlcs900','upd7810','upd78k0kx1','tms7000','m37710','m68000','cpu16','t11']
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/'window.bin'
            def decode(d,base,arch):
                f.write_bytes(d)
                p=subprocess.run([str(exe),str(f),'-arch',arch,'-basepc',f'{base:x}'],capture_output=True,text=True)
                if p.returncode or not re.search(r'^[0-9a-f]+:',p.stdout,re.M):
                    raise RuntimeError(f'Decoder {arch} failed: {p.stdout[:100]} {p.stderr[:100]}')
                # unidasm pads beyond EOF; do not publish fabricated operand bytes.
                lines=[]
                for line in p.stdout.splitlines():
                    m=re.match(r'^([0-9a-f]+):\s+((?:[0-9a-f]{2,8}\s+)+)',line)
                    if m and int(m[1],16)-base+sum(len(t)//2 for t in m[2].split())>len(d):
                        continue
                    lines.append(line.rstrip())
                return '\n'.join(lines)+'\n'
            listing=[]
            for label,d,base in windows:
                listing.append(f'; {label}: CPU {base:04x}, {len(d)} bytes\n'+decode(d,base,'hc11'))
            (HERE/'hc11-excerpts.asm').write_text('\n'.join(listing))
            comparison=['Linear alternative decodes of the SAME 48-byte bank6 function entry (complete instructions only).\n'
                        'Not a probability ranking. Data and intentional traps invalidate whole-ROM illegal-opcode scoring.\n']
            for arch in architectures:
                comparison.append(f'\n=== {arch} ===\n'+decode(b[:48],0x4000,arch))
            (HERE/'cpu-comparison.txt').write_text(''.join(comparison))
        (HERE/'decoder.json').write_text(json.dumps({'tool':'MAME unidasm','package':'mame-tools 0.285+dfsg1-1',
          'executable_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),
          'architectures':architectures,'note':'Bounded excerpts, no full-system emulation performed.'},indent=2)+'\n')
    print('ROM checksum', report['checksum']['calculated'], 'PASS; results regenerated.')

if __name__=='__main__':
    main()
