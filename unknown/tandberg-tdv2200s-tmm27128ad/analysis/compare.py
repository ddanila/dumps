#!/usr/bin/env python3
"""Compare preserved capture with pinned public ROM references and local images.
References are cached outside the repository; no public ROMs are committed.
"""
import argparse,concurrent.futures,difflib,hashlib,json,urllib.request
from pathlib import Path
HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--cache',type=Path,required=True);a=p.parse_args();a.cache.mkdir(parents=True,exist_ok=True)
b=(HERE.parent/'tmm27128ad-20.bin').read_bytes()
refs=json.loads((HERE/'reference-sources.json').read_text())
def examine(r):
 path=a.cache/r['file']
 if not path.exists():path.write_bytes(urllib.request.urlopen(r['url']).read())
 data=path.read_bytes();assert hashlib.sha256(data).hexdigest()==r['sha256']
 result={**r,'exact':data==b,'dump_in_reference_offset':data.find(b),'reference_in_dump_offset':b.find(data)}
 # Word-byte swapped layout as well as direct and embedded comparisons.
 swapped=bytearray(data)
 if len(data)%2==0:swapped[0::2],swapped[1::2]=data[1::2],data[0::2]
 result['dump_in_word_swapped_reference_offset']=swapped.find(b)
 if len(data)==len(b):
  result['aligned_equal_bytes']=sum(x==y for x,y in zip(b,data))
  if result['aligned_equal_bytes']>1000:
   blocks=difflib.SequenceMatcher(None,b,data,autojunk=False).get_matching_blocks()
   result['monotonic_matching_bytes']=sum(x.size for x in blocks)
   result['longest_exact_blocks']=[{'dump_offset':x.a,'reference_offset':x.b,'size':x.size} for x in sorted(blocks,key=lambda x:-x.size)[:20]]
 return result
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:results=list(pool.map(examine,refs))
root=HERE.parents[2];local=[];count=0
for path in sorted(root.rglob('*.bin')):
 if HERE.parent in path.parents:continue
 data=path.read_bytes();count+=1
 offset=data.find(b)
 reverse=b.find(data) if len(data)>=1024 else -1
 if offset>=0 or reverse>=0:local.append({'file':str(path.relative_to(root)),'dump_offset_in_reference':offset,'reference_offset_in_dump':reverse})
report={'public_references':results,'public_reference_count':len(results),'local_bin_files_compared':count,'local_exact_or_embedded_matches':local,'scope':'Pinned TDV-2200/2200S images from Supermagnum/Tandberg; local repository .bin images. No exhaustive Internet uniqueness claim.'}
(HERE/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')
print('Compared',len(results),'public references and',count,'local .bin images; local matches:',local)
