#!/usr/bin/env python3
"""Lossless, ROM-specific MAC 3.04 resource extraction. Python 3 stdlib only.
Offsets are file offsets unless explicitly called XRAM or CPU. No ROM writes.
See ANALYSIS.txt for evidence and limits; inferred glyphs never replace raw bytes.
"""
import argparse, collections, csv, hashlib, html, json, math, re, subprocess, sys
from pathlib import Path
EXPECTED='8bea3d9a252bcb72c86594d4bed711c56cba43158baf454b0f53ba189e564d8a'
LANGS=['en','sv','da','no','fi','nl','de','fr','it','es']
NAMES=['English','Swedish','Danish','Norwegian','Finnish','Dutch','German','French','Italian','Spanish']
# Only contextual hypotheses, NOT an independently recovered hardware glyph ROM.
ACCENTS={
 'sv':{'[':'Ä','\\':'Ö',']':'Å','{':'ä','|':'ö','}':'å'},
 'fi':{'[':'Ä','\\':'Ö',']':'Å','{':'ä','|':'ö','}':'å'},
 'da':{'[':'Æ','\\':'Ø',']':'Å','{':'æ','|':'ø','}':'å'},
 'no':{'[':'Æ','\\':'Ø',']':'Å','{':'æ','|':'ø','}':'å','`':'é'},
 'de':{'[':'Ä','\\':'Ö',']':'Ü','{':'ä','|':'ö','}':'ü','~':'ß'},
 'fr':{'#':'é','@':'à','`':'è','|':'ô'},
 'es':{'[':'á','\\':'é',']':'í','^':'ó','_':'ú','|':'ñ'},
}
SUSPECT=set(map(ord,'#@[\\]^_`{|}~'))
TABLES=[('A',0x6682,965),('B',0x71db,459)]

def hx(x): return f'0x{x:06X}'
def escaped(raw):
 return ''.join(chr(x) if 32<=x<127 and x!=92 else ('\\\\' if x==92 else f'\\x{x:02x}') for x in raw)
def proposed(raw,lang):
 m=ACCENTS.get(lang,{})
 return ''.join(m.get(chr(x),chr(x)) if 32<=x<127 else f'⟦{x:02X}⟧' for x in raw)
def dump_json(path,value): path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def tsv(path,rows,fields=None):
 if not fields: fields=list(rows[0]) if rows else ['offset']
 with path.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,delimiter='\t',extrasaction='ignore');w.writeheader()
  for row in rows:
   w.writerow({k:json.dumps(row[k],ensure_ascii=False) if isinstance(row.get(k),(list,dict)) else row.get(k,'') for k in fields})
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('rom',type=Path);ap.add_argument('--out',type=Path,default=Path('out'))
 ap.add_argument('--disassemble',action='store_true',help='Also save evidence excerpts using installed radare2 (optional)')
 a=ap.parse_args();b=a.rom.read_bytes();sha=hashlib.sha256(b).hexdigest()
 if sha!=EXPECTED: ap.error(f'Wrong ROM SHA256: {sha}; layout assumptions must be revalidated')
 out=a.out;out.mkdir(parents=True,exist_ok=True)
 def z(off):
  end=b.index(0,off)
  assert end-off<512,(hex(off),hex(end))
  return b[off:end]
 rows=[];by_slot={};groups=[]
 for name,start,count in TABLES:
  assert b[start+3*count]!=2
  for i in range(count):
   p=start+3*i;assert b[p]==2
   off=int.from_bytes(b[p+1:p+3],'big');assert 0x2f88<=off<0x6682
   raw=z(off)
   row=dict(table=name,index=i,pointer_offset=hx(p),pointer_hex=b[p:p+3].hex(),string_offset=hx(off),length=len(raw),terminator_offset=hx(off+len(raw)),raw_hex=raw.hex(),raw_escaped=escaped(raw),language='shared',language_index='',group=f'{name}.single.{i}',mapping_evidence='single entry; no language-indexed grouping assigned',glyph_status='linguistic normalization only; physical OSD glyph unresolved; Nordic subset shared')
   rows.append(row);by_slot[name,i]=row
 def group(name,indices,gid,langs=LANGS,evidence='ten-language structural ordering; common language index verified in code'):
  assert len(indices)==len(langs)
  for i,lang in zip(indices,langs):
   r=by_slot[name,i];assert r['language']=='shared'
   r.update(language=lang,language_index=LANGS.index(lang),group=gid,mapping_evidence=evidence)
  groups.append(dict(group=gid,table=name,indices=indices,english=by_slot[name,indices[0]]['raw_escaped'],pointer_base=by_slot[name,indices[0]]['pointer_offset']))
 def ten(name,start,end):
  assert (end-start)%10==0
  for i in range(start,end,10): group(name,list(range(i,i+10)),f'{name}.label.{i:03}')
 def major(name,start,width,kind):
  for i in range(width):group(name,[start+l*width+i for l in range(10)],f'{name}.{kind}.{i:02}',evidence=f'language-major {kind}: 10 blocks of {width} entries; semantic alignment')
 ten('A',8,108);ten('A',109,529)
 major('A',529,12,'month');major('A',649,17,'genre');major('A',819,8,'audio_choice')
 ten('A',905,965)
 major('B',0,4,'pal_help_line');ten('B',101,161);major('B',161,2,'ordinal')
 ten('B',181,211);ten('B',217,227);ten('B',231,261);ten('B',262,322)
 major('B',322,7,'weekday');ten('B',392,412);ten('B',447,457)
 # Structural and actual translation disagree for the IT/ES first overdraft line.
 for i in [257,258]: by_slot['A',i]['anomaly']='Italian/Spanish wording appears swapped in this first-line table; pointer assignment preserved'
 for r in rows:
  raw=bytes.fromhex(r['raw_hex']);r['proposed_unicode']=proposed(raw,r['language'])
  r['non_ascii_or_osd']=[dict(relative_offset=i,byte=f'{c:02X}') for i,c in enumerate(raw) if c<32 or c>=127]
  r['potential_national_codes']=[dict(relative_offset=i,byte=f'{c:02X}',ascii=chr(c),proposal=ACCENTS.get(r['language'],{}).get(chr(c))) for i,c in enumerate(raw) if c in SUSPECT]
 # Exact C-string segmentation of entire identified text pool: no minimum length.
 # This retains unreferenced, short, and control-only fragments, including data
 # beyond embedded NULs (do not silently join these as an executable OSD stream).
 resources={}
 def resource(off,origin,end=None):
  raw=z(off) if end is None else b[off:end]
  rec=resources.setdefault(off,dict(offset=hx(off),length=len(raw),terminator_offset=hx(off+len(raw)) if end is None else '',raw_hex=raw.hex(),raw_escaped=escaped(raw),origins=[],table_references=[],direct_loads=[]))
  if origin not in rec['origins']:rec['origins'].append(origin)
  return rec
 p=0x2f88
 while p<0x6682:
  raw=z(p);resource(p,'complete_main_pool_NUL_segment');p+=len(raw)+1
 assert p==0x6682
 for r in rows: resource(int(r['string_offset'],16),'main_table_target')['table_references'].append(dict(table=r['table'],index=r['index'],language=r['language'],group=r['group'],pointer_offset=r['pointer_offset']))
 # Extra pointer tables/embedded pointers; explicitly bounded from record structure.
 auxiliary=[]
 def aux(p,kind,lang='shared'):
  assert b[p]==2;off=int.from_bytes(b[p+1:p+3],'big')
  rr=resource(off,kind);auxiliary.append(dict(kind=kind,pointer_offset=hx(p),string_offset=hx(off),language=lang,raw_hex=rr['raw_hex'],raw_escaped=rr['raw_escaped'],proposed_unicode=proposed(bytes.fromhex(rr['raw_hex']),lang)))
 for i in range(11):aux(0x2d8e+3*i,'language_names',LANGS[i] if i<10 else 'shared')
 for p in [0x7764,0x7769,0x776c]:aux(p,'service_header_pointer')
 for i in range(13):aux(0x7eac+3*i,'PAL_audio_mode')
 receiver=[]
 for i in range(8):
  p=0x778e+8*i;aux(p+5,'receiver_service_field')
  receiver.append(dict(index=i,record_offset=hx(p),record_hex=b[p:p+8].hex(),type=b[p],parameter=b[p+1],unknown_or_min=b[p+2],unknown_or_max=b[p+3],unknown_or_default=b[p+4],pointer_offset=hx(p+5),label_offset=hx(int.from_bytes(b[p+6:p+8],'big')),label=escaped(z(int.from_bytes(b[p+6:p+8],'big')))))
 mac=[]
 for i in range(21):
  p=0x77ce+27*i;raw=z(p+8);assert len(raw)==18
  resource(p+8,'MAC_adjustment_inline_label')
  mac.append(dict(index=i,record_offset=hx(p),record_hex=b[p:p+27].hex(),metadata_hex=b[p:p+8].hex(),label_offset=hx(p+8),label=escaped(raw)))
 assert 0x77ce+21*27==0x7a05
 # C-string-shaped literals in startup data and trailing fixed data, kept as
 # candidates unless supported by code or a record; not silently promoted to menus.
 candidates=[]
 for lo,hi in [(0x29d5,0x2f88),(0x7a05,0x8000)]:
  for m in re.finditer(rb'[\x20-\x7e]+\x00',b[lo:hi]):
   off=lo+m.start();raw=m.group()[:-1]
   if len(raw)>=2: candidates.append(dict(offset=hx(off),raw_hex=raw.hex(),raw_escaped=escaped(raw),status='candidate printable NUL run; may be non-text data'))
 # Immediate generic-pointer loads: matched instruction sequences, NOT a whole
 # executable reachability analysis. Code regions exclude known fixed data.
 direct=[]
 for lo,hi in [(0x10a,0x29d5),(0x8000,0x257c6)]:
  for m in re.finditer(rb'\x7d([\x01\x02])\x7e(.)\x7f(.)',b[lo:hi],re.S):
   site=lo+m.start();tag,high,low=[x[0] for x in m.groups()];ptr=(high<<8)|low
   off=ptr if tag==2 else ptr-0x740d+0x29d5
   in_pool=(0x2f88<=off<0x6682) or (0x29d5<=off<0x2efc and tag==1) or off in resources or 0x7a05<=off<0x7a36 or 0x7c7d<=off<0x7c8a
   if not in_pool:continue
   raw=z(off)
   # Retain control-only literals too. Avoid inventing text from binary structures.
   rec=dict(site=hx(site),tag=tag,address=hx(ptr),file_offset=hx(off),raw_escaped=escaped(raw),evidence='immediate generic pointer load; inspect disassembly/caller for use')
   direct.append(rec);resource(off,'immediate_pointer_load')['direct_loads'].append(hx(site))
 # Systematic coverage of every main-pool byte including terminators.
 coverage=bytearray(len(b))
 for off,r in resources.items():
  if 'complete_main_pool_NUL_segment' in r['origins']:
   for j in range(off,off+r['length']+1):coverage[j]+=1
 assert all(x==1 for x in coverage[0x2f88:0x6682])
 assert len(rows)==1424 and all(b[int(r['terminator_offset'],16)]==0 for r in rows)
 assert all(len([r for r in rows if r['group']==g['group']])==10 for g in groups)
 assert b[0x71d1:0x71db]==bytes([3,2,3,3,3,3,4,4,4,4])
 assert b[0x00fe:0x0104]==bytes.fromhex('740d2efc29d5')
 assert b[0x2d88:0x2d8d]==bytes.fromhex('0300080a06')
 assert by_slot['A',20]['string_offset']==by_slot['A',21]['string_offset']=='0x00305B'
 assert by_slot['A',257]['string_offset']=='0x003E88' and by_slot['A',258]['string_offset']=='0x003E9C'
 # Full-ROM ASCII audit for material outside known resource structures.
 ascii_runs=[dict(offset=hx(m.start()),length=len(m.group()),raw_escaped=escaped(m.group()),in_main_pool=0x2f88<=m.start()<0x6682) for m in re.finditer(rb'[\x20-\x7e]{4,}',b)]
 # Inventory all 3-byte tag-02 pointers into the main pool, including accidental
 # matches. Known slots and aux records are separated from raw candidates.
 known_slots={int(r['pointer_offset'],16) for r in rows+auxiliary}
 pointer_candidates=[]
 for p in range(len(b)-2):
  if b[p]!=2:continue
  off=int.from_bytes(b[p+1:p+3],'big')
  if 0x2f88<=off<0x6682 and p not in known_slots:
   pointer_candidates.append(dict(offset=hx(p),target=hx(off),raw_escaped=escaped(z(off)),classification='unvalidated byte-pattern; may be instruction or incidental data'))
 pages=[]
 for p in range(0,len(b),4096):
  c=collections.Counter(b[p:p+4096]);n=sum(c.values())
  pages.append(dict(offset=hx(p),size=n,entropy=round(-sum(v/n*math.log2(v/n) for v in c.values()),6),zeros=c[0],ff=c[255]))
 langcounts=collections.Counter(r['language'] for r in rows)
 summary=dict(sha256=sha,size=len(b),zero_tail_start=hx(len(b.rstrip(b'\0'))),main_pointer_entries=len(rows),language_groups=len(groups),language_counts=dict(langcounts),unique_main_targets=len({r['string_offset'] for r in rows}),unique_all_extracted_resources=len(resources),main_pool_bytes=0x6682-0x2f88,main_pool_coverage='every byte exactly once, including NUL separators',main_pool_segments=sum('complete_main_pool_NUL_segment' in r['origins'] for r in resources.values()),short_main_entries=sum(r['length']<8 for r in rows),empty_main_entries=sum(r['length']==0 for r in rows),control_main_entries=sum(bool(r['non_ascii_or_osd']) for r in rows),main_entries_with_national_candidates=sum(bool(r['potential_national_codes']) for r in rows),auxiliary_pointer_entries=len(auxiliary),receiver_records=len(receiver),mac_records=len(mac),immediate_pointer_loads=len(direct),unvalidated_pointer_patterns=len(pointer_candidates),tests='all assertions passed')
 dump_json(out/'summary.json',summary);dump_json(out/'catalog.json',rows);tsv(out/'catalog.tsv',rows)
 dump_json(out/'groups.json',groups);dump_json(out/'resources.json',list(resources.values()));tsv(out/'resources.tsv',list(resources.values()))
 dump_json(out/'auxiliary.json',auxiliary);tsv(out/'auxiliary.tsv',auxiliary)
 dump_json(out/'service_records.json',dict(receiver=receiver,mac=mac));tsv(out/'receiver_service.tsv',receiver);tsv(out/'mac_service.tsv',mac)
 tsv(out/'immediate_pointer_loads.tsv',direct);tsv(out/'unvalidated_pointer_patterns.tsv',pointer_candidates);tsv(out/'candidate_literals.tsv',candidates);tsv(out/'full_rom_ascii_audit.tsv',ascii_runs);tsv(out/'rom_pages.tsv',pages)
 dump_json(out/'accent_hypotheses.json',dict(status='contextual inference, not hardware/font verification',maps=ACCENTS))
 # Per-language plaintext for review and side-by-side matrix preserving offsets.
 for lang in LANGS:
  lines=[f'{r["group"]}\tptr={r["pointer_offset"]}\tstr={r["string_offset"]}\t{r["raw_escaped"]}\t{r["proposed_unicode"]}' for r in rows if r['language']==lang]
  (out/f'language-{lang}.txt').write_text('\n'.join(lines)+'\n')
 matrix=[]
 for g in groups:
  rr=dict(group=g['group'],english=g['english'])
  for i,lang in zip(g['indices'],LANGS):
   r=by_slot[g['table'],i];rr[lang]=f'{r["string_offset"]} [ptr {r["pointer_offset"]}] {r["raw_escaped"]}'
  matrix.append(rr)
 tsv(out/'all_languages.tsv',matrix)
 build_html(out,rows,auxiliary,mac,summary,list(resources.values()))
 dump_json(out/'language_subsets.json',[dict(language=lang,index=i,subset=b[0x2afa+i],file_offset=hx(0x2afa+i),xram_offset=hx(0x7532+i),osd_061c=hex(0xa8|b[0x2afa+i])) for i,lang in enumerate(LANGS)])
 dump_json(out/'osd_embedded_nul_record.json',dict(offset='0x00531F',end_exclusive='0x005333',raw_hex=b[0x531f:0x5333].hex(),raw_escaped=escaped(b[0x531f:0x5333]),note='Full storage span before next pointer target; contains embedded NULs. Ordinary NUL renderer stops at5322; fixed-count renderer may consume more. Do not treat this as a proven hardware control grammar.'))
 if a.disassemble: disassemble(a.rom,out)
 for helper in ['trace_refs.py','dispatch.py']:
  subprocess.run([sys.executable,str(Path(__file__).with_name(helper)),str(a.rom),'--out',str(out)],check=True,capture_output=True)
 dump_json(out/'checksums.json',{str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob('*')) if p.is_file() and p.name!='checksums.json'})
 print(json.dumps(summary,indent=2))

def build_html(out,rows,aux,mac,summary,resources):
 # Browser-only, self contained; no network or raw HTML injection from strings.
 extra=[dict(table='aux',index=i,group=r['kind'],language=r['language'],pointer_offset=r['pointer_offset'],string_offset=r['string_offset'],raw_escaped=r['raw_escaped'],proposed_unicode=r['proposed_unicode'],raw_hex=r['raw_hex']) for i,r in enumerate(aux)]
 extra += [dict(table='MAC',index=r['index'],group='MAC adjustment',language='shared',pointer_offset=r['record_offset'],string_offset=r['label_offset'],raw_escaped=r['label'],proposed_unicode=r['label'],raw_hex='') for r in mac]
 represented={r['string_offset'] for r in rows+extra}
 extra += [dict(table='resource',index=i,group=' / '.join(r['origins']),language='unassigned',pointer_offset='',string_offset=r['offset'],raw_escaped=r['raw_escaped'],proposed_unicode=r['raw_escaped'],raw_hex=r['raw_hex']) for i,r in enumerate(resources) if r['offset'] not in represented]
 data=json.dumps(rows+extra,ensure_ascii=False).replace('<','\\u003c')
 page='''<!doctype html><meta charset="utf-8"><title>MAC 3.04 resource catalog</title>
<style>body{font:15px system-ui;margin:24px;background:#f5f7fa;color:#152332}input,select{padding:8px;margin:4px}table{border-collapse:collapse;width:100%;background:white}td,th{padding:8px;text-align:left;border-bottom:1px solid #ddd;vertical-align:top}th{position:sticky;top:0;background:#e4eaf2}pre{white-space:pre-wrap;margin:0;font:13px monospace}.muted{color:#526477}details{margin-top:5px}#status{margin:16px 0}</style>
<h1>MAC 3.04 — all-language resource catalog</h1><p>Exact structural slots, including short/empty strings and aliases. Raw byte spelling is authoritative. “Linguistic normalization” uses contextual spelling hypotheses, not physical glyph decoding. Swedish, Danish, Norwegian and Finnish share subset 2: their differing proposed letters cannot all be the physical glyph for the same byte without another control change.</p>
<input id="q" placeholder="Search text, group, offset, hex" size="50"><select id="lang"><option value="">All languages</option></select><label><input id="acc" type="checkbox">Linguistic normalization hypotheses</label><p id="status"></p><table><thead><tr><th>Table / group</th><th>Language</th><th>Pointer / text offset</th><th>Text and exact bytes</th></tr></thead><tbody id="body"></tbody></table><script>
const rows=DATA;const $=id=>document.getElementById(id);for(const l of [...new Set(rows.map(r=>r.language))]){let o=document.createElement('option');o.value=l;o.textContent=l;$('lang').append(o)}
function render(){const q=$('q').value.toLowerCase(),lang=$('lang').value;const found=rows.filter(r=>(!lang||r.language===lang)&&(!q||JSON.stringify(r).toLowerCase().includes(q)));$('status').textContent=found.length+' / '+rows.length+' entries';$('body').replaceChildren();const frag=document.createDocumentFragment();for(const r of found){const tr=document.createElement('tr');const vals=[r.table+' '+r.index+' · '+r.group,r.language,r.pointer_offset+' / '+r.string_offset];for(const val of vals){const td=document.createElement('td');td.textContent=val;tr.append(td)}const td=document.createElement('td'),pre=document.createElement('pre');pre.textContent=($('acc').checked?r.proposed_unicode:r.raw_escaped)||'⟦empty⟧';td.append(pre);const d=document.createElement('details'),s=document.createElement('summary');s.textContent='Raw bytes / evidence';d.append(s);const p=document.createElement('pre');p.textContent=r.raw_hex+'\\n'+(r.mapping_evidence||'See auxiliary/service tables')+(r.anomaly?'\\nANOMALY: '+r.anomaly:'');d.append(p);td.append(d);tr.append(td);frag.append(tr)}$('body').append(frag)}for(const id of ['q','lang','acc'])$(id).addEventListener('input',render);render();</script>'''.replace('DATA',data)
 (out/'catalog.html').write_text(page)

def disassemble(rom,out):
 regions=[('language_setter',0xed89,0x5c),('language_osd_init',0x1aadc,0x13c),('PAL_audio_table_consumer',0x24d23,0x3b),('startup_copy',0x2e,0xe0),('bank_switch',0x7bb,0x3f),('generic_pointer_read',0x2620,0xe2),('language_index',0x181dc,0x19),('table_dereference',0x1ac32,0x2a),('nul_renderer',0x1a215,0x6f),('osd_write',0x1d8d4,0x60),('service_page',0x22c16,0x117),('service_sequence',0x22d43,0x51),('sequence_caller',0x233e5,0x3b),('alternate_sequence_caller',0x17f63,0x55),('MAC_record_stride',0x11bb5,0x45),('MAC_screen',0x11ebf,0xda),('receiver_screen',0x12980,0x13c),('service_dispatch',0x22bd3,0x43),('PAL_line_counts',0x22dfe,0x97)]
 folder=out/'disassembly';folder.mkdir(exist_ok=True)
 for name,start,size in regions:
  cmd=['r2','-q','-e','scr.color=0','-e','asm.lines=false','-e','asm.comments=false','-a','8051','-c',f'pD {size} @ {start}',str(rom)]
  proc=subprocess.run(cmd,capture_output=True,text=True,check=True)
  (folder/(name+'.txt')).write_text('# Command: '+ ' '.join(cmd[:-1]+[rom.name])+'\n# Printed addresses are file offsets; banked branch targets require mapping.\n'+proc.stdout)
 (folder/'README.txt').write_text('radare2 excerpts are linear decoding from manually selected instruction boundaries. Branch targets printed for file offsets >= 0x10000 are not reliable CPU addresses; see report for the bank mapping. No full reachability proof is claimed.\n')
if __name__=='__main__': main()
