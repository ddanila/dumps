#!/usr/bin/env python3
"""Run the headless ROM harness in a user-selected output directory."""
import argparse,pathlib,subprocess,os
p=argparse.ArgumentParser();p.add_argument('--rom',required=True,type=pathlib.Path);p.add_argument('--out',required=True,type=pathlib.Path);p.add_argument('--ticks',type=int,default=12000000);p.add_argument('--mock',type=int,choices=range(6),default=5);p.add_argument('--calls',type=pathlib.Path);p.add_argument('--set-xram',default='',help='Hex address=byte pairs, applied before each injected call');a=p.parse_args();base=pathlib.Path(__file__).resolve().parent
if not (base/'build/sat-run').exists():subprocess.run([str(base/'build.sh')],check=True)
out=a.out.resolve();out.mkdir(parents=True,exist_ok=True);cmd=[str(base/'build/sat-run'),str(a.rom.resolve()),str(a.ticks),str(a.mock)]
if a.calls:cmd+=['@'+str(a.calls.resolve())]
env=os.environ.copy();env['SAT_XRAM']=a.set_xram
with (out/'trace.log').open('w') as f,(out/'stderr.log').open('w') as err:r=subprocess.run(cmd,cwd=out,env=env,stdout=f,stderr=err)
print((out/'trace.log').read_text().splitlines()[-1]);raise SystemExit(r.returncode)
