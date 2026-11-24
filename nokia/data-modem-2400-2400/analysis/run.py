#!/usr/bin/env python3
"""Build a bounded 8031 execution probe; run unchanged firmware and regressions."""
from pathlib import Path
import os,subprocess,json,hashlib,argparse
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CORE=ROOT/'unknown/satellite-mac304-m27c2001/analysis/emulation/emu8051'
ROM=ROOT/'nokia/data-modem-2400-2400/controller-810244e/nokia-modem-other-board-2764.bin'
SHA='daf854c513cd427664bb345f511afc2d38441e5002e4a85389d289aedbfc0038'
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=Path('/tmp/nokia2400-results'));a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
assert hashlib.sha256(ROM.read_bytes()).hexdigest()==SHA
exe=out/'harness'
subprocess.run(['cc','-O2','-Wall','-DSAT_TRACE','-I',str(CORE),str(HERE/'harness.c'),*[str(CORE/n) for n in ['core.c','opcodes.c','disasm.c']],'-o',str(exe)],check=True)
env={k:v for k,v in os.environ.items() if k not in ['WATCHDOG','SHIFT','PRESEED','DISASM']}
scenarios=[('cold-no-reset',{},2000000),('retained-reset-no-shift',{'WATCHDOG':'1'},2000000),('shift-zero',{'WATCHDOG':'1','SHIFT':'0'},20000000),('shift-ones',{'WATCHDOG':'1','SHIFT':'255'},20000000),('shift-seven',{'WATCHDOG':'1','SHIFT':'7'},20000000),('preseed-zero',{'PRESEED':'1','SHIFT':'0'},20000000)]
summary={'rom_sha256':SHA,'cpu_core_hashes':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in CORE.iterdir() if f.is_file()},'scenarios':{}}
for name,opts,cycles in scenarios:
 r=subprocess.run([str(exe),str(ROM),'5','255',str(cycles),str(out/(name+'.trace'))],env=env|opts,capture_output=True,text=True,check=True)
 data=json.loads(r.stdout);(out/(name+'.json')).write_text(json.dumps(data,indent=2)+'\n');pcs=dict(data['coverage']);assert data['exceptions']==0
 checks={'within_rom':all(0<=pc<8192 for pc in pcs),'no_cpu_exceptions':data['exceptions']==0}
 if name=='cold-no-reset':checks['stops_at_ram_check']=data['pc']==0x1ec4
 elif name=='retained-reset-no-shift':checks.update({'95_retained_resets':data['resets']==95,'waits_for_mode0_receive':data['pc']==0x0807,'timer1_interrupt_runs':pcs.get(0x1b,0)>100})
 else:
  checks.update({'reaches_main_loop':pcs.get(0x1ed6,0)>0,'mode0_input_and_output':data['tx_count']>100 and data['rx_count']>100,'both_8251_controls_written':{5,6}.issubset({x[0] for x in data['writes']}),'timer1_interrupt_runs':pcs.get(0x1b,0)>100})
 assert all(checks.values()),(name,checks)
 summary['scenarios'][name]={'cycles':cycles,'instructions':data['instructions'],'unique_instruction_starts':len(pcs),'pc':f'{data["pc"]:04x}','resets':data['resets'],'tx_count':data['tx_count'],'rx_count':data['rx_count'],'main_loop_entries':pcs.get(0x1ed6,0),'timer1_entries':pcs.get(0x1b,0),'reads':data['reads'],'writes':data['writes'],'assumptions':opts,'checks':checks}
 print(name,summary['scenarios'][name]['unique_instruction_starts'],'instruction addresses; checks pass')
# Linear decoding is a navigation aid: embedded tables are not all instructions.
r=subprocess.run([str(exe),str(ROM),'5','255','1',str(out/'disasm-unused.trace')],env=env|{'DISASM':'1'},capture_output=True,text=True,check=True)
(out/'controller-linear.asm').write_text('\n'.join(line.rstrip() for line in r.stdout.splitlines())+'\n')
(out/'disasm-unused.trace').unlink(missing_ok=True)
(out/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
