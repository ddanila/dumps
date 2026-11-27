#!/usr/bin/env python3
"""Reproducible NEC V25-family static survey. No hardware access.

Capstone handles the shared 8086/80186 instructions. NEC 0F bit operations
are decoded separately; unsupported NEC extensions stop a path, never become
modern x86 instructions. Recursive traversal is evidence, not whole-program
coverage: indirect targets require explicit seeds in annotations.json.
"""
import argparse, collections, hashlib, json, math, re, struct
from pathlib import Path
from capstone import Cs, CS_ARCH_X86, CS_MODE_16
from capstone.x86 import X86_OP_IMM
HERE=Path(__file__).resolve().parent
SHA='f8bf2df93c70c01c9f7b4bae5ce335a935d03deb4ba41bec691152e7bc041980'
CS=Cs(CS_ARCH_X86,CS_MODE_16); CS.detail=True
PREFIX={0x26:'es',0x2e:'cs',0x36:'ss',0x3e:'ds',0xf0:'lock',0xf2:'repne',0xf3:'rep'}
def decode(d,p):
    q=p
    while q<len(d) and d[q] in PREFIX: q+=1
    if q>=len(d): return None
    if d[q]==0x0f:
        if q+2>=len(d): return None
        op=d[q+1]
        if op in (0x25,0x91,0x92,0x9e):
            return {'p':p,'size':q-p+2,'mn':{0x25:'movspa',0x91:'retrbi',0x92:'fint',0x9e:'stop'}[op],'args':'','kind':'stop' if op in (0x91,0x9e) else 'nec','target':None}
        if not 0x10<=op<=0x1f: return None
        mod=d[q+2]; width=op&1
        # Decode the effective operand using an otherwise equivalent MOV.
        synth=d[p:q]+bytes([0x8a+width,mod&0xc7])+d[q+3:q+9]
        x=next(CS.disasm(synth,p&65535,count=1),None)
        if x is None:return None
        n=x.size+1; imm=op>=0x18
        if p+n+imm>len(d):return None
        operand=x.op_str.split(', ',1)[1]
        bit=str(d[p+n] & (15 if width else 7)) if imm else 'cl'
        return {'p':p,'size':n+imm,'mn':['test1','clr1','set1','not1'][(op&7)//2], 'args':operand+', '+bit,'kind':'nec','target':None}
    # Reject 386+ operand/address-size prefixes, which are not this CPU.
    if d[q] in (0x64,0x65,0x66,0x67):return None
    x=next(CS.disasm(d[p:p+15],p&65535,count=1),None)
    if not x:return None
    target=None; kind='normal'
    if x.mnemonic in ('lcall','ljmp') and len(x.operands)==2 and all(o.type==X86_OP_IMM for o in x.operands):
        target=(x.operands[0].imm*16+x.operands[1].imm)&0xfffff; target-=0xe0000
        kind='call' if x.mnemonic=='lcall' else 'jump'
    elif x.mnemonic=='call' or x.mnemonic.startswith('j') or x.mnemonic.startswith('loop'):
        kind='call' if x.mnemonic=='call' else ('jump' if x.mnemonic=='jmp' else 'branch')
        if x.operands and x.operands[0].type==X86_OP_IMM: target=(p&~65535)+(x.operands[0].imm&65535)
    elif x.mnemonic in ('ret','retf','iret','iretw','hlt'):kind='stop'
    args=x.op_str
    if target is not None and x.mnemonic not in ('lcall','ljmp'): args=hex(target&65535)
    return {'p':p,'size':x.size,'mn':x.mnemonic,'args':args,'kind':kind,'target':target}
def walk(d,seeds):
    todo=list(seeds); done={}; failed=[]; edges=[]
    while todo:
        p=todo.pop()
        while 0<=p<len(d) and p not in done:
            x=decode(d,p)
            if not x:failed.append(p);break
            done[p]=x
            if x['target'] is not None:
                edges.append({'from':p,'to':x['target'],'kind':x['kind']})
                if 0<=x['target']<len(d):todo.append(x['target'])
            if x['kind'] in ('jump','stop'):break
            p+=x['size']
    return done,edges,sorted(set(failed))
def load(path=None):
    if path: p=Path(path)
    else:
        p=HERE.parent/'d27010.bin'
        if not p.exists():
            m=json.loads((HERE.parent/'manifest.json').read_text())
            p=HERE.parents[3]/m['details']['capture']['session']/'read1.bin'
    d=p.read_bytes()
    assert len(d)==131072 and hashlib.sha256(d).hexdigest()==SHA,'Unexpected input image'
    return d

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--rom');ap.add_argument('--output',type=Path,default=HERE/'results');ap.add_argument('--range',nargs=2,type=lambda s:int(s,0));a=ap.parse_args();d=load(a.rom)
    if a.range:
        p,end=a.range
        while p<end:
            x=decode(d,p)
            if not x: print(f'{p:05x} unsupported {d[p:p+8].hex()}');break
            print(f'{p:05x} {d[p:p+x["size"]].hex():22} {x["mn"]:8} {x["args"]}');p+=x['size']
        return
    a.output.mkdir(parents=True,exist_ok=True)
    annotations=json.loads((HERE/'annotations.json').read_text()) if (HERE/'annotations.json').exists() else {}
    seeds={0x1fff0,*(int(k,16) for k in annotations)}
    done,edges,failed=walk(d,seeds)
    covered=set();overlaps=[]
    for p,x in sorted(done.items()):
        bs=set(range(p,p+x['size']))
        if covered&bs:overlaps.append(p)
        covered|=bs
    with (a.output/'disassembly.txt').open('w') as f:
        f.write('; File offsets; CPU physical address = offset + E0000h.\n; Recursive direct-flow traversal plus documented seeds; gaps are not decoded.\n')
        prev=-1
        for p,x in sorted(done.items()):
            if p!=prev:f.write('\n')
            if f'{p:05x}' in annotations:f.write('; '+annotations[f'{p:05x}']+'\n')
            f.write(f'{p:05x} {d[p:p+x["size"]].hex():22} {x["mn"]:8} {x["args"]}'.rstrip()+'\n');prev=p+x['size']
    strings=[{'offset':m.start(),'text':m.group().decode('ascii')} for m in re.finditer(rb'[\x20-\x7e]{5,}',d)]
    blocks=[]
    for p in range(0,len(d),4096):
        b=d[p:p+4096];c=collections.Counter(b)
        blocks.append({'offset':p,'size':len(b),'ff':c[255],'zero':c[0],'entropy':round(-sum(n/len(b)*math.log2(n/len(b)) for n in c.values()),4),'decoded_bytes':len(covered&set(range(p,p+len(b))))})
    io=[x for x in done.values() if x['mn'] in ('in','out','insb','insw','outsb','outsw') or re.search(r'0xff[0-9a-f]{2}\]',x['args'])]
    summary={'sha256':SHA,'size':len(d),'sum8':sum(d)&255,'sum16_bytes':sum(d)&65535,'sum16_words':sum(struct.unpack('<65536H',d))&65535,'instructions':len(done),'decoded_bytes':len(covered),'overlapping_starts':overlaps,'unsupported_offsets':failed,'nec_instructions':sum(x['kind']=='nec' for x in done.values()),'indirect_transfers':[x for x in done.values() if x['kind'] in ('call','jump') and x['target'] is None]}
    for name,value in [('summary',summary),('strings',strings),('blocks',blocks),('edges',edges),('io-accesses',sorted(io,key=lambda x:x['p']))]:
        (a.output/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='indirect_transfers'},indent=2))
if __name__=='__main__':main()
