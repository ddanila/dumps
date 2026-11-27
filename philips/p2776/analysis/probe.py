#!/usr/bin/env python3
"""Execute original, unmodified x86-compatible ROM routines in Unicorn.
Not a V25 machine emulator: internal IDB reads are represented as a memory
overlay; no device/timing/interrupt or NEC-extension execution is claimed.
"""
import json, random, struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_16
from unicorn.x86_const import *
from analyze import load
HERE=Path(__file__).resolve().parent

def execute(entry,rom,idb=0x4f,patches=(),budget=600000,until=0xffff8):
    u=Uc(UC_ARCH_X86,UC_MODE_16);u.mem_map(0,0x200000);u.mem_write(0xe0000,rom)
    if idb is not None:u.mem_write(0xfffff,bytes([idb]))
    for addr,data in patches:u.mem_write(addr,data)
    u.reg_write(UC_X86_REG_CS,0xf000);u.reg_write(UC_X86_REG_DS,0);u.reg_write(UC_X86_REG_ES,0x4000)
    u.reg_write(UC_X86_REG_SS,0);u.reg_write(UC_X86_REG_SP,0x7ffe);u.reg_write(UC_X86_REG_EFLAGS,2)
    u.mem_write(0x7ffe,struct.pack('<H',0xfff8))
    u.emu_start(0xe0000+entry,until,count=budget)
    assert u.reg_read(UC_X86_REG_IP)==(until&65535),'Routine did not reach its expected boundary within budget'
    return u

def checksum(rom,idb):
    u=execute(0x109b2,rom,idb)
    return {'ax':u.reg_read(UC_X86_REG_AX),'carry':u.reg_read(UC_X86_REG_EFLAGS)&1,'failure_mask':int.from_bytes(u.mem_read(0x82,2),'little'),'result_slot':int.from_bytes(u.mem_read(0x86,2),'little')}

def main():
    d=load();cases=[]
    for label,idb,flips in [('CPU view, IDB=4F',0x4f,[]),('Raw EPROM view',None,[]),('Wrong IDB=40',0x40,[]),('Corrupt first byte',0x4f,[0]),('Corrupt executable byte',0x4f,[0x12345]),('Corrupt reset jump',0x4f,[0x1fff1])]:
        b=bytearray(d)
        for p in flips:b[p]^=1
        r=checksum(bytes(b),idb);cases.append({'case':label,**r})
        assert (r['ax']==0 and r['carry']==0 and r['failure_mask']==0)==(label=='CPU view, IDB=4F')
    rng=random.Random(2776);count=0;examples=[]
    for b in [bytes(271),bytes([255])*271]+[rng.randbytes(271) if hasattr(rng,'randbytes') else bytes(rng.randrange(256) for _ in range(271)) for _ in range(100)]:
        total=sum(b)&65535
        expected=(((total&0xff00)|((total+0x34)&255))+0x6132)&65535
        u=execute(0x1484f,d,patches=[(0x44026,b)])
        actual=u.reg_read(UC_X86_REG_AX);assert actual==expected
        if count<2:examples.append({'input':'zero' if count==0 else 'FF','result':actual})
        count+=1
    parser_cases=[]
    for text,expect,index,private,mode in [
        ('12;34',[12,34],1,0,2),('65535',[65535],0,0,2),
        ('65536',[0],0,0,2),('99999',[34463],0,0,2),
        ('?25',[25],0,1,2),('1;2;3;4;5;6;7;8;9;10;11',list(range(1,12)),10,0,2),
        ('1;2;3;4;5;6;7;8;9;10;11;',[0]*11,0,0,0)]:
        state=bytearray(512);state[0x155]=2
        for ch in text:
            state[0x11b]=ord(ch)
            u=execute(0x17c77,d,patches=[(0x8300,bytes(state))])
            state=bytearray(u.mem_read(0x8300,512))
        values=list(struct.unpack_from('<11H',state,0x13f))
        assert values[:len(expect)]==expect and state[0x13e]==index and state[0x159]==private and state[0x155]==mode
        parser_cases.append({'input':text,'parameters':values,'index':state[0x13e],'private_marker':state[0x159],'parser_state':state[0x155]})
    reply_cases=[]
    for mode,expected in [(0,b'\x1b/Z'),(1,b'\x9b?1;2c'),(2,b'\x9b?62;1;2;6;8;9c')]:
        u=execute(0x1b156,d,patches=[(0x8305,bytes([mode]))])
        off=int.from_bytes(u.mem_read(0x8437,2),'little');seg=int.from_bytes(u.mem_read(0x8439,2),'little');n=int.from_bytes(u.mem_read(0x843b,2),'little')
        reply=bytes(u.mem_read(seg*16+off,n));assert reply==expected
        reply_cases.append({'operation':'device attributes','mode':mode,'reply_hex':reply.hex()})
    for errors,expected in [(0,b'\x9b0n'),(2,b'\x9b3n')]:
        u=execute(0x1b34d,d,patches=[(0x843f,b'\x05\x00'),(0x82,struct.pack('<H',errors))])
        reply=bytes(u.mem_read(0x8ff2,3));assert reply==expected
        reply_cases.append({'operation':'status report','diagnostic_mask':errors,'reply_hex':reply.hex()})
    # Run the original font expansion loop, stopping before subsequent hardware setup.
    u=Uc(UC_ARCH_X86,UC_MODE_16);u.mem_map(0,0x200000);u.mem_write(0xe0000,d)
    u.reg_write(UC_X86_REG_CS,0xf000);u.reg_write(UC_X86_REG_ES,0x4000);u.reg_write(UC_X86_REG_SS,0);u.reg_write(UC_X86_REG_SP,0x7ffe);u.reg_write(UC_X86_REG_EFLAGS,2)
    u.emu_start(0xf2394,0xf23b4,count=200000)
    assert u.reg_read(UC_X86_REG_IP)==0x23b4
    expected=bytearray()
    for g in range(512):
        p=0x200+g*18;bits=int.from_bytes(d[p:p+2],'little')
        for y,b in enumerate(d[p+2:p+18]):expected.extend([b,(bits>>y)&1])
    assert bytes(u.mem_read(0x40000,16384))==bytes(expected)
    dispatch_cases=[]
    for char in range(0x40,0x80):
        target=struct.unpack_from('<H',d,0x17d4b+2*(char-0x40))[0]
        u=execute(0x17c77,d,patches=[(0x841b,bytes([char])),(0x8455,b'\x02')],until=0xf0000+target)
        dispatch_cases.append({'final':char,'handler':f'{0x10000+target:05x}'})
    cursor_cases=[]
    for row,col,origin,top,expected in [(0,0,0,0,0),(1,1,0,0,0),(24,80,0,0,0x174f),(300,400,0,0,0xfefe),(2,3,1,10,0x0b02),(255,1,1,10,0xff00)]:
        u=execute(0x1b11b,d,patches=[(0x843f,struct.pack('<HH',row,col)),(0x8469,bytes([origin])),(0x8425,bytes([top]))],until=0xf3a84)
        ax=u.reg_read(UC_X86_REG_AX);assert ax==expected
        cursor_cases.append({'row_parameter':row,'column_parameter':col,'origin_mode':origin,'scroll_top':top,'normalized_ax':ax})
    result={'csi_dispatch_cases':dispatch_cases,'cursor_argument_cases':cursor_cases,'reply_cases':reply_cases,'font_expansion_bytes_verified':16384,'parser_cases':parser_cases,'scope':'Original ROM routines only; IDB overlay, no full terminal or peripheral emulation','rom_checksum_cases':cases,'configuration_checksum_cases':count,'configuration_examples':examples}
    (HERE/'results'/'execution.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
