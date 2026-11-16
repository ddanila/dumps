"""Generate a portable HTML gallery and byte-faithful frame JSON/text."""
import argparse,pathlib,json,re,html,hashlib
LANG=['en','sv','da','no','fi','nl','de','fr','it','es']
def frame_pages(blob):
 pages=[]
 for base in range(0,65536,2048):
  page=blob[base:base+2048]
  if not re.search(rb'[A-Za-z]{3}',page):continue
  rows=[]
  for y in range(32):
   raw=page[y*64:y*64+64]
   rows.append({'address':base+y*64,'hex':raw.hex(),'text':''.join(chr(x) if 32<=x<127 else ' ' if x==0 else '·' for x in raw)})
  pages.append({'base':base,'rows':rows})
 return pages
def generate(results,out):
 out.mkdir(parents=True,exist_ok=True);frames=[]
 for r in json.load(open(results/'screens-final/summary.json')):
  d=results/'screens-final'/f"{r['name']}-{r['language']}";p=d/f"screen-{r['frame_index']:04d}.bin"
  if not p.exists():continue
  b=p.read_bytes();frames.append(dict(r,id=f"{r['name']}-{LANG[r['language']]}",sha256=hashlib.sha256(b).hexdigest(),pages=frame_pages(b)))
 d=results/'mac-scroll'
 for i in (0,17,18,20,21):
  p=d/f'screen-{i:04d}.bin'
  if p.exists():
   b=p.read_bytes();frames.append({'id':f'mac-navigation-{i}','name':'mac-navigation','language':0,'language_name':'en','fixture':'MAC renderer followed by row-next handler1:A297; no forced page byte','returned':True,'sha256':hashlib.sha256(b).hexdigest(),'pages':frame_pages(b)})
 (out/'frames.json').write_text(json.dumps({'format':'sat-osd-v1','stride':64,'page_size':2048,'note':'Captured character bytes; ASCII approximation, controls shown ·, NUL shown space. No glyph/font/video emulation. Numeric/card fields are synthetic.','frames':frames},ensure_ascii=False,indent=2))
 lines=[];cards=[]
 for f in frames:
  text='\n\n'.join('OSD address '+hex(p['base'])+'\n'+'\n'.join(f"{r['address']:04X}  {r['text'].rstrip()}" for r in p['rows']) for p in f['pages']) or '(No text page emitted)'
  lines.append(f"=== {f['id']} ===\nfixture: {f.get('fixture','')}\n{text}\n")
  cards.append(f'<article data-name="{f["name"]}" data-lang="{LANG[f["language"]]}"><h2>{html.escape(f["id"])}</h2><p>Fixture: {html.escape(f.get("fixture","") or "boot defaults; mocked I²C / IMbus")}</p><pre>{html.escape(text)}</pre></article>')
 (out/'frames.txt').write_text('\n'.join(lines),encoding='utf8')
 options=''.join(f'<option>{n}</option>' for n in sorted(set(f['name'] for f in frames)))
 langs=''.join(f'<option>{n}</option>' for n in LANG)
 page='''<!doctype html><html lang="en"><meta charset="utf-8"><title>MAC 3.04 executed OSD gallery</title><style>body{font:16px system-ui;background:#10151e;color:#e1e6ee;margin:2rem}header{max-width:72rem}select{font:inherit;padding:.4rem;background:#263247;color:white;margin:.5rem}article{margin:1.5rem 0;padding:1rem;background:#192231;border:1px solid #344156;border-radius:8px}pre{font:14px/1.25 ui-monospace,monospace;overflow:auto;color:#f4eec7}h2{font-size:1.2rem}a{color:#9bc8ff}[hidden]{display:none}</style><header><h1>MAC 3.04 — executed OSD character captures</h1><p>Actual ROM routines executed after reset with synthetic I²C master replies and zero-valued IMbus reads. Not pixel-accurate font/video. ASCII bytes are shown literally; control/non-ASCII bytes appear as · and NUL as space. National glyph shapes are not decoded. Numbers, card records, RF status and receiver readings are fixtures, not real measurements.</p><p>64-byte memory rows, separate 2 KiB address pages. Persistent display snapshots retain earlier writes until firmware overwrites them. Unwritten cells are not inferred. A returning routine is not proof of complete hardware operation.</p><p><a href="frames.json">Byte-faithful JSON</a> · <a href="frames.txt">Text frames</a></p><label>Screen <select id="screen"><option value="all">All</option>'''+options+'''</select></label><label>Language <select id="lang"><option value="all">All</option>'''+langs+'''</select></label><p id="count"></p></header>'''+''.join(cards)+'''<script>function filter(){let n=0;for(const a of document.querySelectorAll('article')){a.hidden=!((screenSelect.value==='all'||a.dataset.name===screenSelect.value)&&(langSelect.value==='all'||a.dataset.lang===langSelect.value));if(!a.hidden)n++}document.querySelector('#count').textContent=n+' captures shown'}const screenSelect=document.querySelector('#screen'),langSelect=document.querySelector('#lang');screenSelect.onchange=langSelect.onchange=filter;langSelect.value='en';filter();</script></html>'''
 (out/'index.html').write_text(page,encoding='utf8');return len(frames)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('results');p.add_argument('out');a=p.parse_args();print(generate(pathlib.Path(a.results),pathlib.Path(a.out)))
