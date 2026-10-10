#!/usr/bin/env python3
from pathlib import Path
import json
base=Path(__file__).resolve().parent
cases={}; current=None
for line in (base/'trace.tsv').read_text().splitlines():
    kind,t,text=line.split('\t',2)
    if kind=='CASE':
        current={'bits':[], 'led_reads':0}; cases[text]=current
    elif current is not None:
        if kind=='BIT': current['bits'].append(int(text))
        if kind=='LED': current['led_reads']+=1
for name,c in cases.items():
    bits=c.pop('bits'); assert len(bits)%13==0,(name,len(bits))
    values=[]
    for i in range(0,len(bits),13):
        b=bits[i:i+13]
        assert b[:3]==[1,1,0] and b[11:]==[1,1],(name,b)
        values.append(sum(b[j+3]<<j for j in range(8)))
    c['bytes']=values
assert len(cases)==548,len(cases)
for name,c in cases.items():
    if name.startswith('mode0_'):
        b=cases[name.replace('mode0_','mode1_')]['bytes']
        d=cases[name.replace('mode0_','mode2_')]['bytes']
        a=c['bytes']
        assert len(a)==len(b)==len(d)==2,(name,a,b,d)
        assert a[0]^b[0]==4,(name,a,b)
        assert a[1]==b[1],(name,a,b)
        assert a==d,(name,a,d)
for name in ('toggle_1','toggle_2'):
    assert cases[name]['bytes']==[],cases[name]

(base/'decoded.json').write_text(json.dumps(cases,indent=2)+'\n')
print('PASS: 182 position/shift combinations; language status toggles by 04; keycode unchanged; second toggle restores original output.')
print('Each toggle alone produces no serial bytes.')
for mode in range(3): print('Mode',mode,'language LED I/O reads',sum(c['led_reads'] for n,c in cases.items() if n.startswith(f'mode{mode}_')))
for n in ('mode0_shift0_70_5','mode1_shift0_70_5','mode2_shift0_70_5','mode0_shift1_70_5','mode1_shift1_70_5','mode2_shift1_70_5'):
    print(n, ' '.join(f'{v:02X}' for v in cases[n]['bytes']))
