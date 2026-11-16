import argparse,pathlib,subprocess,os,json,collections
p=argparse.ArgumentParser();p.add_argument('rom');p.add_argument('out');a=p.parse_args();rom=pathlib.Path(a.rom).resolve();data=rom.read_bytes();out=pathlib.Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True);base=pathlib.Path(__file__).resolve().parent;results=[]
for family,events,modes,entry,state,eventaddr,ab,nb in [('top',22,7,0xb445,0x77ef,0x68a7,0x2db8,0x2e52),('submenu',11,15,0x8000,0x7587,0x68a5,0x2b50,0x2bf5)]:
 for event in range(events):
  for mode in range(modes):
   d=out/f'{family}-{event:02d}-{mode:02d}';d.mkdir(exist_ok=True);(d/'calls.txt').write_text(f'3 {entry:x} 0 0 0 0\n');env=os.environ.copy();env['SAT_XRAM']=f'{state:x}={mode:x},{eventaddr:x}={event:x}'
   with (d/'trace.log').open('w') as f:r=subprocess.run([str(base/'build/sat-run'),str(rom),'12000000','5','@calls.txt'],cwd=d,env=env,stdout=f)
   text=(d/'trace.log').read_text();return_count=text.count('\nRETURN');returned=r.returncode==0 and return_count==1;ram=(d/'xram.bin').read_bytes();idx=event*modes+mode
   results.append({'family':family,'event':event,'mode':mode,'action':data[ab+idx],'table_next':data[nb+idx],'final_state':ram[state],'returned':returned,'return_count':return_count,'exit_code':r.returncode,'end':text.splitlines()[-1],'classification':'returned' if returned else 'intentional_powerdown' if r.returncode==4 and return_count==0 and 'PCON=02' in text.splitlines()[-1] else 'bounded_unresolved'})
  print(family,event,sum(x['returned'] for x in results),'/',len(results),flush=True)
(out/'results.json').write_text(json.dumps(results,indent=2));print(collections.Counter((x['family'],x['returned']) for x in results))
