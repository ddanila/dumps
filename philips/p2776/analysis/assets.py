#!/usr/bin/env python3
"""Extract literal dispatch tables and the exact 512-glyph font representation."""
import json,struct
from pathlib import Path
from analyze import load
HERE=Path(__file__).resolve().parent
def main():
 d=load();out=HERE/'results';out.mkdir(exist_ok=True)
 tables=json.loads((HERE/'tables.json').read_text());rows=[]
 for t in tables:
  for i in range(t['count']):
   v=struct.unpack_from('<H',d,t['offset']+2*i)[0]
   rows.append({'table':f"{t['offset']:05x}",'label':t['label'],'index':i,'target':f"{(t['offset']&~65535)+v:05x}"})
 (out/'dispatch-tables.json').write_text(json.dumps(rows,indent=2)+'\n')
 # F000:239B loads SI=0200. Each glyph: a little-endian word of
 # ninth-column bits followed by 16 bytes for columns 0..7.
 svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1728" viewBox="0 0 512 864">', '<rect width="512" height="864" fill="#fff"/>','<g fill="#111" shape-rendering="crispEdges">']
 expanded=bytearray();font=[]
 for g in range(512):
  p=0x200+18*g;high=struct.unpack_from('<H',d,p)[0];scan=[]
  for y,b in enumerate(d[p+2:p+18]):
   ninth=(high>>y)&1;expanded.extend([b,ninth]);row=(b<<1)|ninth;scan.append(row)
   for x in range(9):
    if row&(1<<(8-x)):svg.append(f'<path d="M{(g%16)*32+10+x} {(g//16)*27+8+y}h1v1h-1z"/>')
  font.append({'glyph':g,'offset':p,'rows':scan})
 svg.append('</g><g font-family="monospace" font-size="5" fill="#777">')
 for g in range(512):svg.append(f'<text x="{(g%16)*32+10}" y="{(g//16)*27+6}">{g:03X}</text>')
 svg.append('</g></svg>');(out/'font-atlas.svg').write_text('\n'.join(svg)+'\n')
 (out/'font.json').write_text(json.dumps(font,indent=2)+'\n')
 # Document expansion hash, not an additional top-level firmware image.
 import hashlib
 (out/'font-summary.json').write_text(json.dumps({'glyphs':512,'width':9,'height':16,'source_start':512,'source_end_exclusive':9728,'expanded_size':len(expanded),'expanded_sha256':hashlib.sha256(expanded).hexdigest(),'initial_512_bytes':'Separate per-glyph metadata copied to RAM 05CAh; not pixels.'},indent=2)+'\n')
 print('Extracted',len(rows),'dispatch entries and 512 glyphs')
if __name__=='__main__':main()
