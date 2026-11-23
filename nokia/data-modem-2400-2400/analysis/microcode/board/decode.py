"""Static address mapping and optional evidence-backed fetched-control decoding.

Static inspection forces only the sequencer address. It never initializes
registers or substitutes fabricated control values for unknown wiring.
"""
import csv
import json
from copy import deepcopy
from logic import Word
from engine import Stop, DECODE_FIELDS

FIELDS=DECODE_FIELDS
MNEMONICS=['TSK','INC','BLT','POP','BSR','PLP','BRT','RST']


def successors(pc, command, branch=None, test=None):
    inc=(pc+1)&1023
    if command is None:return [{'target':None,'condition':'unresolved command'}]
    if command==0:return ([{'target':inc,'condition':'TEST=0'}] if test==0 else
                          [{'target':(pc+2)&1023,'condition':'TEST=1'}] if test==1 else
                          [{'target':inc,'condition':'TEST=0'},{'target':(pc+2)&1023,'condition':'TEST=1'}])
    if command in (1,5):return [{'target':inc,'condition':'always'}]
    if command==7:return [{'target':0,'condition':'always'}]
    if command==3:return [{'target':None,'condition':'stack return'}]
    taken={'target':None if command==2 else branch,'condition':'TEST=1; stack return' if command==2 else 'TEST=1'}
    return [{'target':inc,'condition':'TEST=0'}] if test==0 else [taken] if test==1 else [{'target':inc,'condition':'TEST=0'},taken]


def inspect(engine, pc):
    probe=deepcopy(engine)
    for name,c in probe.cells.items():
        if c['type']=='SEQ8X02':probe.state[name]['pc']=Word.of(pc,10)
    # Combinational inspection only: no fabricated latch/CPU clock phases.
    for _ in range(64):
        new={f'{name}.{p}':v for name in probe.cells for p,v in probe.outputs(name,probe.inputs(name)).items()}
        if new==probe.values:break
        probe.values=new
    else:raise Stop('static decode combinational network did not settle')
    lanes={name:{'physical_address':probe.inputs(name)['A'].integer(),
                 'output':probe.values[f'{name}.D'].text()} for name in probe.roms}
    fields={name:probe.expr(probe.board.get('decode',{}).get(name),width).integer() for name,width in FIELDS.items()}
    return {'address':pc,'lanes':lanes,'fields':fields,
            'edges':successors(pc,fields['AC'],fields['BRANCH'],fields['TEST'])}


def write_listing(engine,out):
    roms=list(engine.roms)
    with (out/'raw-prom-lanes.csv').open('w') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(['file_offset',*roms])
        for a in range(1024):w.writerow([f'{a:03x}',*[f'{engine.roms[n][a]:02x}' for n in roms]])
    rows=[inspect(engine,a) for a in range(1024)]
    with (out/'rom-listing.csv').open('w') as f:
        w=csv.writer(f,lineterminator='\n')
        w.writerow(['sequencer_address',*[f'{n}_physical_address' for n in roms],*[f'{n}_data_bits' for n in roms],*FIELDS,'command'])
        for row in rows:
            fields=row['fields']
            w.writerow([f'{row["address"]:03x}',*[row['lanes'][n]['physical_address'] if row['lanes'][n]['physical_address'] is not None else '?' for n in roms],
                        *[row['lanes'][n]['output'] for n in roms],*[fields[n] if fields[n] is not None else '?' for n in FIELDS],
                        '?' if fields['AC'] is None else MNEMONICS[fields['AC']]])
    graph={'note':'Static fetched-control interpretation only; stack, TEST, and pipeline behavior require runtime evidence.',
           'edges_by_address':{f'{r["address"]:03x}':r['edges'] for r in rows}}
    (out/'control-flow.json').write_text(json.dumps(graph,indent=2)+'\n')
    lines=['digraph microcode {','  rankdir=LR;','  unknown [shape=box,label="unresolved / dynamic"];']
    known=[r for r in rows if r['fields']['AC'] is not None]
    if not known:lines+=['  reset [label="8X02 power-on address 000"];','  reset -> unknown [style=dashed];']
    for r in known:
        src=f'a{r["address"]:03x}'
        lines.append(f'  {src} [label="{r["address"]:03x} {MNEMONICS[r["fields"]["AC"]]}"];')
        for edge in r['edges']:
            target='unknown' if edge['target'] is None else f'a{edge["target"]:03x}'
            lines.append(f'  {src} -> {target} [label={json.dumps(edge["condition"])}];')
    (out/'control-flow.dot').write_text('\n'.join(lines+['}'])+'\n')
