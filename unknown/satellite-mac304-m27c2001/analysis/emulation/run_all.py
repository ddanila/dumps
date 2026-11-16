#!/usr/bin/env python3
"""Reproduce the bounded firmware experiments. C compiler + Python stdlib only."""
import argparse,pathlib,subprocess,json,os,hashlib,re,shutil,gzip,collections
BASE=pathlib.Path(__file__).resolve().parent
SHA='8bea3d9a252bcb72c86594d4bed711c56cba43158baf454b0f53ba189e564d8a'
def invoke(rom,d,plan=None,mock=5,ticks=12000000,fixture='',expect=0):
 d.mkdir(parents=True,exist_ok=True);cmd=[str(BASE/'build/sat-run'),str(rom),str(ticks),str(mock)]
 if plan is not None:(d/'calls.txt').write_text(plan);cmd+=['@calls.txt']
 env=os.environ.copy();env['SAT_XRAM']=fixture
 with (d/'trace.log').open('w') as f,(d/'stderr.log').open('w') as err:r=subprocess.run(cmd,cwd=d,env=env,stdout=f,stderr=err)
 assert r.returncode==expect,(d,r.returncode,expect)
 return (d/'trace.log').read_text()
def verify_languages(work):
 idx={e['slot']:e for e in json.load(open(BASE/'catalog-index.json'))};pairs=set();fixed=[];subset=[]
 for r in json.load(open(work/'screens-final/summary.json')):
  d=work/'screens-final'/f"{r['name']}-{r['language']}"
  for line in (d/'language-slots.tsv').read_text().splitlines():
   tick,ci,pc,lang,tag,slot=line.split();e=idx.get(int(slot,16))
   if int(ci)!=1 or not e or e['language']=='shared':continue
   if e['language_index']==int(lang):pairs.add((e['group'],e['language']))
   else:fixed.append(dict(screen=r['name'],selected=int(lang),slot=slot,slot_language=e['language'],hook=pc))
  values=[int(x.split()[2],16) for x in (d/'osd-writes.tsv').read_text().splitlines() if x.split()[1]=='061c' and int(x.split()[0])>=4000000]
  expected=0xa8|[0,2,2,2,2,0,1,4,3,5][r['language']]
  subset.append(dict(screen=r['name'],language=r['language'],expected=expected,observed=values,match=expected in values))
 assert all(x['match'] for x in subset)
 frozen={tuple(x) for x in json.load(open(BASE/'expected-language-pairs.json'))}
 assert pairs==frozen and len(pairs)==252, 'Language selection coverage changed'
 exceptions={('service','6c5b','en'),('service','6c3d','en'),('channel_programming','730a','en'),('system_programming','676c','en')}
 assert len(fixed)==36 and {(x['screen'],x['slot'],x['slot_language']) for x in fixed}==exceptions
 assert all(x['selected'] in range(1,10) for x in fixed)
 assert collections.Counter((x['screen'],x['slot'],x['slot_language']) for x in fixed)=={key:9 for key in exceptions}

 result={'selected_group_language_pairs':len(pairs),'selected_groups':len({g for g,l in pairs}),'pairs':sorted(pairs),'nonmatching_selections':fixed,'note':'Nonmatching selections include explicit English slots in nonlocalized setup/service screens; catalog injection alone does not validate language grouping.','subset_checks':subset}
 (work/'language-validation.json').write_text(json.dumps(result,indent=2));return result

def main():
 p=argparse.ArgumentParser();p.add_argument('--rom',required=True,type=pathlib.Path);p.add_argument('--out',required=True,type=pathlib.Path);p.add_argument('--keep-details',action='store_true',help='Keep large per-case raw traces and memory dumps');a=p.parse_args();rom=a.rom.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True);work=out/'details';work.mkdir(exist_ok=True)
 assert hashlib.sha256(rom.read_bytes()).hexdigest()==SHA,'Wrong ROM for these firmware-specific tests'
 subprocess.run([str(BASE/'build.sh')],check=True)
 for mode in range(6):invoke(rom,work/f'reset-{mode}',mock=mode,ticks=10000000)
 # Each call plan starts from actual reset and injects only at the main scheduler.
 plans={'gate-caller':'3 b32e 3b 0 0 0\n3 b32e 9 0 0 0\n3 b32e 19 0 0 0\n','gate-wrong':'3 ad43 6 0 0 0\n3 ad43 9 0 0 0\n3 ad43 8 0 0 0\n','gate-timeout':'3 ad43 6 0 0 0\n3 ad43 a 0 0 0 3000000\n3 ad43 8 0 0 0\n','mac-scroll':'1 9e50 0 0 0 0\n'+'1 a297 1 0 0 0\n'*21}
 for name,plan in plans.items():invoke(rom,work/name,plan,ticks=20000000)
 for name,expected in [('gate-wrong',['02','03','03']),('gate-timeout',['02','01','03'])]:
  t=(work/name/'trace.log').read_text();assert re.findall(r'^RETURN .*gate=([0-9a-f]{2})',t,re.M)==expected
 ram=(work/'gate-caller/xram.bin').read_bytes();assert ram[0x77ef]==5 and b'SERVICE MENU' in (work/'gate-caller/screen-0002.bin').read_bytes()
 scroll=b''.join(f.read_bytes() for f in (work/'mac-scroll').glob('screen-*.bin'));rows=json.load(open(BASE/'service-tests.json'))['mac_rows'];assert all(x['label'].encode() in scroll for x in rows),'Missing MAC row'
 invoke(rom,work/'budget-check','3 ac16 0 0 0 0\n',ticks=10,expect=4)
 invoke(rom,work/'malformed-check','not a call\n',ticks=10,expect=1)
 for script,folder,extra in [('execute_catalog.py','catalog',[]),('execute_screens.py','screens-final',[]),('execute_service_tests.py','service-tests',[str(BASE/'service-tests.json')]),('execute_dispatch.py','dispatch',[])]:
  subprocess.run(['python3',str(BASE/script),str(rom),*extra,str(work/folder)],check=True)
 screens=json.load(open(work/'screens-final/summary.json'));assert len(screens)==310 and all(x['returned'] for x in screens)
 tests=json.load(open(work/'service-tests/results.json'));assert len(tests)==471 and all(x['status']=='pass' for x in tests)
 dispatch=json.load(open(work/'dispatch/results.json'));assert len(dispatch)==319;assert collections.Counter(x['classification'] for x in dispatch)=={'returned':314,'intentional_powerdown':5}
 assert all(x['exit_code']==4 and x['event']==7 and x['family']=='top' for x in dispatch if not x['returned'])
 credit_it=(work/'screens-final/credit_enabled-8/screen-0001.bin').read_bytes();credit_es=(work/'screens-final/credit_enabled-9/screen-0001.bin').read_bytes();assert b'Giro en descubierto' in credit_it and b'concesso' in credit_it and b'Ammontare scoperto' in credit_es and b'autorizado' in credit_es
 lang=verify_languages(work)
 subprocess.run(['python3',str(BASE/'gallery.py'),str(work),str(out/'gallery')],check=True)
 compact=out/'results';compact.mkdir(exist_ok=True)
 for src,dst in [('catalog/results.json','catalog.json'),('catalog/verification.json','catalog-summary.json'),('screens-final/summary.json','screens.json'),('service-tests/results.json','service-tests.json'),('dispatch/results.json','dispatch.json'),('language-validation.json','language-validation.json')]:shutil.copy2(work/src,compact/dst)
 evidence=out/'evidence';evidence.mkdir(exist_ok=True)
 selected=[work/f'reset-{i}' for i in range(6)]+[work/n for n in plans]+[work/'service-tests/470',work/'dispatch/top-07-00',work/'screens-final/credit_enabled-8',work/'screens-final/credit_enabled-9']
 for d in selected:
  name=d.relative_to(work).as_posix().replace('/','--')
  for file in ['trace.log','stderr.log','coverage.tsv','settings-writes.tsv','language-slots.tsv','calls.txt']:
   if (d/file).exists():
    with gzip.GzipFile(filename=str(evidence/f'{name}--{file}.gz'),mode='wb',mtime=0) as f:f.write((d/file).read_bytes())
 summary={'rom_sha256':SHA,'catalog_pointer_injections':1424,'catalog_byte_matches':1424,'screen_state_language_calls':len(screens),'screen_state_language_returns':sum(x['returned'] for x in screens),'screen_case_note':'31 cases x10; includes scan-start action and editor candidate that emits no text, not 31 distinct proven menus.','service_tests_matched':471,'top_mode_returns':149,'top_mode_powerdowns':5,'submenu_returns':165,'mac_rows_rendered':21,'gate_caller_success':True,'gate_wrong_rejected':True,'gate_timeout_rejected':True,'credit_localization_swap_confirmed':True,'selected_language_groups':lang['selected_groups'],'selected_group_language_pairs':lang['selected_group_language_pairs']}
 (out/'SUMMARY.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
 if not a.keep_details:shutil.rmtree(work)
if __name__=='__main__':main()
