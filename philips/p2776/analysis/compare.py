#!/usr/bin/env python3
"""Bounded public/local comparison. Downloaded reference ROMs stay in a cache."""
import argparse, hashlib,json, urllib.request
from pathlib import Path
from analyze import load
HERE=Path(__file__).resolve().parent
PUBLIC=[('philips-sp0.bin','https://www.retromelsarchive.com/uploads/1/3/0/3/130305330/philipsserpro_0rev4.bin'),('philips-sp1.bin','https://www.retromelsarchive.com/uploads/1/3/0/3/130305330/philipsserpro_1rev4.bin')]
def sha(b):return hashlib.sha256(b).hexdigest()
def compare(a,b):
 return {'exact':a==b,'equal_after_ff_padding_removal':a.rstrip(b'\xff')==b.rstrip(b'\xff'),'reference_is_contiguous_subimage':len(b)>=1024 and b in a}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--cache',type=Path,required=True);a=ap.parse_args();a.cache.mkdir(parents=True,exist_ok=True);d=load();refs=[];blobs=[]
 pins=json.loads((HERE/'reference-sources.json').read_text())['public_roms']
 for (name,url),pin in zip(PUBLIC,pins):
  p=a.cache/name
  if not p.exists():p.write_bytes(urllib.request.urlopen(url,timeout=30).read())
  b=p.read_bytes();assert sha(b)==pin['sha256'];blobs.append(b);refs.append({'url':url,'size':len(b),'sha256':sha(b),**compare(d,b)})
 transforms=[]
 for label,b in [('concatenated 0,1',blobs[0]+blobs[1]),('concatenated 1,0',blobs[1]+blobs[0]),('interleaved 0,1',bytes(v for pair in zip(*blobs) for v in pair)),('interleaved 1,0',bytes(v for pair in zip(*blobs[::-1]) for v in pair))]:
  transforms.append({'layout':label,**compare(d,b)})
 local=[];root=HERE.parents[2]
 for m in sorted(root.rglob('manifest.json')):
  try:j=json.loads(m.read_text())
  except (ValueError,UnicodeError):continue
  if j.get('schema')!='dumps-manifest/1' or m.parent==HERE.parent:continue
  for im in j.get('images',[]):
   p=m.parent/im['file']
   if not p.is_file():continue
   b=p.read_bytes();local.append({'file':p.relative_to(root).as_posix(),'size':len(b),'sha256':sha(b),**compare(d,b)})
 result={'scope':'Two public Philips service-processor ROMs (different hardware), four pair layouts, and manifest-listed repository images. Not an exhaustive public-ROM search. MAME source filename search is recorded separately, not treated as a hash catalogue.','public':refs,'public_pair_layouts':transforms,'local_count':len(local),'local':local}
 (HERE/'results'/'comparisons.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Compared',len(refs),'public images, four pair layouts and',len(local),'local images')
 print('Matches',[r for r in refs+transforms+local if any(r.get(k) for k in ('exact','equal_after_ff_padding_removal','reference_is_contiguous_subimage'))])
if __name__=='__main__':main()
