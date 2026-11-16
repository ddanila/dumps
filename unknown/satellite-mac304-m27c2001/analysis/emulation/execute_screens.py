"""Reset, initialize OSD in each language, then call a bounded renderer."""
import argparse,json,pathlib,subprocess,os
LANGUAGES=['en','sv','da','no','fi','nl','de','fr','it','es']
SCREENS=[
 ('main',0,0xc9ee,0,''),('parental',0,0xcd3f,0,''),('clock',0,0xd13a,0,''),('favourites',0,0xd7c2,0,''),('timer_clock_select',1,0x9620,0,''),('access',2,0x8161,0,''),('mac_audio',3,0x8ac0,0,''),('subtitles',3,0xad94,0,'7505=0'),('pal_audio',3,0xcba6,0,''),('service',3,0xac16,0,''),('receiver',1,0xa953,0,''),('mac',1,0x9e50,0,''),
 ('channel_programming',0,0x9bdc,4,''),('installation',0,0xd028,0,''),('system_programming',0,0xdf73,4,''),('language_popup',0,0xecbe,0,''),('timer_editor',1,0x93d3,0,''),('consultation',1,0xb25e,0,''),('subscription_categories',1,0xb5df,0,''),('subscription_details_default',1,0xb97e,0,''),('credit_enabled',1,0xc069,8,'7370=1,7371=1'),('access_settings',2,0x84d3,0,''),
 ('subscription_details',1,0xb97e,0,'756e=1'),('prebooked_ppv',1,0xb97e,0,'756e=2'),('impulse_ppv',1,0xb97e,0,'756e=3'),('subscription_variant',1,0xb97e,0,'756e=4'),('purchase_confirmation',1,0xdc08,0,''),('maturity_warning',1,0xdd0c,0,'6701=0'),('pal_help',3,0xad94,0,'7505=3'),('editor_candidate_no_output',2,0xce00,0,''),('scan_start_action',0,0xc8d1,0,'')]
def execute(rom,out):
 base=pathlib.Path(__file__).resolve().parent;results=[];out.mkdir(parents=True,exist_ok=True)
 for name,b,e,arg,fixture in SCREENS:
  for lang in range(10):
   d=out/f'{name}-{lang}';d.mkdir(exist_ok=True);(d/'calls.txt').write_text(f'2 abf1 0 0 0 {lang:x}\n{b:x} {e:x} {arg:x} 0 0 {lang:x}\n');env=os.environ.copy();env['SAT_XRAM']=fixture
   with (d/'trace.log').open('w') as f,(d/'stderr.log').open('w') as err:r=subprocess.run([str(base/'build/sat-run'),str(rom),'20000000','5','@calls.txt'],cwd=d,env=env,stdout=f,stderr=err)
   text=(d/'trace.log').read_text();returns=text.count('\nRETURN');ram=(d/'xram.bin').read_bytes();results.append({'name':name,'bank':b,'entry':hex(e),'argument':arg,'language':lang,'language_name':LANGUAGES[lang],'fixture':fixture,'exit_code':r.returncode,'returned':r.returncode==0 and returns==2,'return_count':returns,'frame_index':1,'bytes':(d/'call-0001.bin').stat().st_size if (d/'call-0001.bin').exists() else 0,'scan_flag':ram[0x7751]})
  print(name,[(r['language'],r['returned'],r['bytes']) for r in results if r['name']==name],flush=True)
 (out/'summary.json').write_text(json.dumps(results,indent=2));return results
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('rom');p.add_argument('out');a=p.parse_args();execute(pathlib.Path(a.rom).resolve(),pathlib.Path(a.out).resolve())
