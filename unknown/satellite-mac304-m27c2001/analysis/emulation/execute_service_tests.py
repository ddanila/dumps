import argparse,json,pathlib,subprocess,os,collections
p=argparse.ArgumentParser();p.add_argument('rom');p.add_argument('spec');p.add_argument('out');a=p.parse_args();rom=str(pathlib.Path(a.rom).resolve());base=pathlib.Path(__file__).resolve().parent;out=pathlib.Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
cases=json.load(open(a.spec))['cases'];results=[]
for i,t in enumerate(cases):
 d=out/f'{i:03d}';d.mkdir(exist_ok=True);setup={}
 for k,v in t['setup'].items():
  if '..' in k:
   lo,hi=[int(x,16) for x in k.split('..')];setup.update({lo+j:val for j,val in enumerate(v)})
  else:setup[int(k,16)]=v
 env=os.environ.copy();env['SAT_XRAM']=','.join(f'{k:x}={v:x}' for k,v in setup.items());c=t['call'];(d/'calls.txt').write_text(f"{c['bank']:x} {c['cpu']} {c.get('r7',0):x} 0 0 0\n")
 with (d/'trace.log').open('w') as f:r=subprocess.run([str(base/'build/sat-run'),rom,'12000000','5','@calls.txt'],cwd=d,env=env,stdout=f)
 trace=(d/'trace.log').read_text();return_count=trace.count('\nRETURN');returned=r.returncode==0 and return_count==1;ram=(d/'xram.bin').read_bytes();suite=t['suite'];actual=None
 if suite.startswith('MAC'):actual=ram[0x6b02+t['row']]
 elif suite in ['receiver_numeric','OptionByte_bit']:addr=0x6b18+2*t['row'];actual=int.from_bytes(ram[addr:addr+2],'big')
 if suite=='ChangeCode_save':
  lines=(d/'settings-writes.tsv').read_text().splitlines();writes={int(z[1],16):int(z[4],16) for z in map(str.split,lines) if len(z)>4};expected={int(k,16):v for k,v in t['expected_settings'].items()};actual={k:writes.get(k) for k in expected};ok=actual==expected and ram[0x77c2:0x77c5]==bytes([8,10,6])
 else:ok=actual==t['expected']
 results.append({'index':i,'suite':suite,'row':t['row'],'returned':returned,'exit_code':r.returncode,'return_count':return_count,'actual':actual,'expected':t.get('expected',t.get('expected_settings')),'match':ok,'status':'pass' if ok and returned else 'mismatch' if returned else 'bounded'})
 if i%50==0:print(i,collections.Counter(x['status'] for x in results),flush=True)
(out/'results.json').write_text(json.dumps(results,indent=2));print(collections.Counter(x['status'] for x in results))
