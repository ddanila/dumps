import argparse,pathlib,json,subprocess,collections
p=argparse.ArgumentParser();p.add_argument('rom');p.add_argument('out');a=p.parse_args();base=pathlib.Path(__file__).resolve().parent;rom=pathlib.Path(a.rom).resolve();data=rom.read_bytes();out=pathlib.Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True);index=json.load(open(base/'catalog-index.json'))
with (out/'calls.txt').open('w') as f:
 for e in index:
  slot=e['slot'];f.write(f"2 ac32 {slot&255:x} 2 {slot>>8:x} {e['language_index']:x}\n")
with (out/'trace.log').open('w') as f:subprocess.run([str(base/'build/sat-run'),str(rom),'250000000','5','@calls.txt'],cwd=out,stdout=f,check=True)
results=[]
for i,e in enumerate(index):
 slot=e['slot'];ptr=int.from_bytes(data[slot+1:slot+3],'big');expected=data[ptr:data.index(0,ptr)];actual=(out/f'call-{i:04d}.bin').read_bytes();results.append(dict(e,index=i,expected_hex=expected.hex(),actual_hex=actual.hex(),match=actual==expected))
assert len(results)==1424 and all(r['match'] for r in results)
(out/'results.json').write_text(json.dumps(results,indent=2));(out/'verification.json').write_text(json.dumps({'calls':1424,'matches':sum(r['match'] for r in results),'languages':dict(collections.Counter(r['language'] for r in results))},indent=2));print('catalog: 1424/1424 exact byte matches')
