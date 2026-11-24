#!/usr/bin/env python3
"""Decode firmware OUT strobes: 2 idle, start, 8 LSB-first data, 2 stop."""
from pathlib import Path
import json
base=Path(__file__).resolve().parent
(base/'checks.json').unlink(missing_ok=True)
cases={}; current=None
for line in (base/'trace.tsv').read_text().splitlines():
    kind,t,text=line.split('\t',2); t=float(t)
    if kind=='CASE':
        current={'start':t,'bits':[],'events':[]}; cases[text]=current
    elif current is not None:
        if kind=='BIT': current['bits'].append((t,int(text)))
        elif kind in ('KEY','RELEASE'): current['events'].append([kind,t,text])
for name,c in cases.items():
    bits=c.pop('bits'); assert len(bits)%13==0,(name,len(bits))
    frames=[]
    for i in range(0,len(bits),13):
        b=[x[1] for x in bits[i:i+13]]
        assert b[:3]==[1,1,0] and b[11:]==[1,1],(name,b)
        frames.append({'time':bits[i][0], 'byte':sum(b[j+3]<<j for j in range(8))})
    c['frames']=frames
    print(name, ' '.join(f'{f["byte"]:02x}' for f in frames))
(base/'decoded.json').write_text(json.dumps(cases,indent=2)+'\n')

checks=[]
def check(name,condition):
    assert condition,name
    checks.append(name)
matrix={n:c for n,c in cases.items() if n.startswith('matrix_')}
check('91 mapped non-modifier positions tested', len(matrix)==91)
for n,c in matrix.items():
    check(n+' emits one status/keycode pair',len(c['frames'])==2 and c['frames'][0]['byte']==0xe0)
for n,c in cases.items():
    end=c['start']+2.5
    check(n+' idle after release',all(f['time']<end for f in c['frames']))
get=lambda n:[f['byte'] for f in cases[n]['frames']]
check('repress produces same pair twice',get('repress')==get('plain')*2)
check('held key stable over 1.8 seconds',get('repeat')==get('plain'))
for name,status in [('plain',0xe0),('shift',0xe2),('control',0xe1),('caps',0xe8),('caps_shift',0xea),('siso',0xe4),('siso_shift',0xe6)]:
    check(name+' status',len(get(name))==2 and get(name)[0]==status)
check('shift changes letter case',get('plain')[1]^get('shift')[1]==0x20)
check('caps agrees with shift',get('caps')[1]==get('shift')[1])
check('SI/SO status changes, base keycode stable',get('siso')[1]==get('plain')[1])
check('control status changes, base keycode stable',get('control')[1]==get('plain')[1])
(base/'checks.json').write_text(json.dumps({'passed':len(checks),'checks':checks},indent=2)+'\n')
print('PASS:',len(checks),'checks')
