"""Constrain chip-10 ALU functions with explicit paired-arithmetic hypotheses."""
import argparse
import copy
import itertools
import random
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from common import HERE, decode, field_value, load, read, save
from analyze import listing
from execute import CarryInput, execute
from model import Am2901


def arithmetic_codes(source,negative):
    """Derive allowed ALU functions from the component model, with Q=0."""
    allowed=[]
    for function in range(8):
        good=True
        for value in (0,1,0x55,0x80,0xff):
            for carry in ((0,1) if negative else (0,)):
                cpu=Am2901(ram=[value,0x39]+[0]*14,q=0)
                result=cpu.step(source|(function<<3)|(1<<6),0,1,0x96,carry)
                want=((~value)+carry)&255 if negative else value
                if result['f']!=want:good=False
        if good:allowed.append(function)
    return allowed


def search(lanes,config):
    source_windows=set()
    for order in config['source_chip_orders']:
        for reverse in (False,True):
            stream=[f'{c}.{b}' for c in order for b in (range(7,-1,-1) if reverse else range(8)) if f'{c}.{b}' in config['source_bits']]
            source_windows.update(tuple(stream[i:i+3]) for i in range(len(stream)-2))
    source_candidates=[]
    for bits in sorted(source_windows):
        for inversion in range(8):
            first=field_value(bits,lanes,config['output_table_bases'][0])^inversion
            second=field_value(bits,lanes,config['rotation_table_bases'][0])^inversion
            if arithmetic_codes(second,False) and arithmetic_codes(second,True):
                source_candidates.append((bits,inversion,first,second))
    function_candidates=[]
    opcodes=config['positive_opcodes']+config['negative_opcodes']
    for bits in itertools.permutations(range(8),3):
        values=[sum(((v>>b)&1)<<j for j,b in enumerate(bits)) for v in opcodes]
        for inversion in range(8):
            codes=[v^inversion for v in values]
            function_candidates.append((bits,inversion,codes))
    allowed={s:(arithmetic_codes(s,False),arithmetic_codes(s,True)) for s in range(8)}
    used=[p for p in range(1024) if any(lanes[c][p]!=255 for c in lanes)]
    candidates=[]
    for sb,si,first,second in source_candidates:
        positive,negative=allowed[second]
        for fb,fi,codes in function_candidates:
            if not all(c in positive for c in codes[:4]) or not all(c in negative for c in codes[4:]):continue
            bits=list(sb)+[f'10.{b}' for b in fb]+config['destination_bits']
            inversion=si|(fi<<3)
            expression=[('!' if inversion>>j&1 else '')+b for j,b in enumerate(bits)]
            values=[field_value(expression,lanes,p) for p in used]
            parts=dict(arithmetic_fraction=sum(((v>>3)&7)<3 for v in values)/len(values),
                       first_family_uses_b=int(first in (1,3)),inversions=bin(inversion).count('1'))
            score=sum(config['weights'][k]*v for k,v in parts.items())
            candidates.append(dict(score=score,i=expression,components=parts,source_first=first,source_second=second,function_codes=codes))
    candidates.sort(key=lambda r:(-r['score'],r['i']))
    return dict(source_windows=len(source_windows),function_candidates=len(function_candidates),survivors=len(candidates),
                configuration=config,top=candidates[:20]),candidates[:config['retained']]


def make_mapping(candidate,index,config):
    mapping=copy.deepcopy(read(HERE/'sequencer.json'));mapping['name']=f'rotation-{index}'
    for name,bits in dict(i=candidate['i'],a=config['a_bits'],b=config['b_bits'],carry=config['carry_constant_bits'],
                          carry_select=config['carry_select_bits'],output_slot=config['output_slot_bits']).items():
        mapping['fields'][name]=dict(bits=bits,status='hypothesis',evidence='Paired-arithmetic experiment; see rotation-search.json constraints and limitations')
    mapping['fields']['d']=dict(bits=0,status='stub',evidence='External D input supplied by scenario, not chip-10 immediate')
    mapping['ranking']=candidate
    return mapping


def scenario_for(mapping,config):
    scenario=read(HERE/'branch-tables.json');scenario['name']='paired-arithmetic-with-virtual-outputs'
    scenario['evidence']='Retain branch-table hypotheses; test mapped carry and capture table ALU-Y into virtual paired slots.'
    scenario['inputs']['carry']=dict(mode='mapped-or-previous',constant_field='carry',select_field='carry_select',initial=0,unknown=0,status='hypothesis',
        evidence='11.0 selects preceding arithmetic carry for high bytes; otherwise 10.4 supplies carry. Logical carry unknown falls back to zero.')
    scenario['io']['read'].update(mode='constant',value=0)
    rows=decode(mapping)
    scenario['io']['writes']=[dict(pc=p,address=f"virtual-phase-output[{rows[p]['output_slot']}]",source='y',status='stub',
        evidence='Capture table ALU-Y by opcode slot tags; physical output enable and address are unresolved')
        for base in config['output_table_bases'] for p in range(base,base+16)]
    return scenario


def run_entry(rows,base,entry,ram,q,carry_policy):
    cpu=Am2901(ram=ram[:],q=q);carry=CarryInput(carry_policy);trace=[]
    for row in rows[base+4*entry:base+4*entry+4]:
        cin=carry.resolve(row)
        result=cpu.step(row['i'],row['a'],row['b'],0x96,cin)
        carry.observe(result)
        trace.append(dict(pc=row['pc'],a=row['a'],b=row['b'],i=row['i'],carry_in=cin,
                          slot=row['output_slot'],y=result['y'],carry_out=result['carry'],ram=cpu.ram[:]))
    return cpu,trace


def word(ram,index):return ram[index]|(ram[index+1]<<8)
def put(ram,index,value):ram[index]=value&255;ram[index+1]=(value>>8)&255


def fixtures(mapping,config):
    rows=decode(mapping);policy=scenario_for(mapping,config)['inputs']['carry']
    cases=[(0,0),(0,1),(1,0),(0x100,0xffff),(0x8000,0x7fff),(0xff00,0xff),(0x1234,0x5678)]
    rng=random.Random(0);cases += [(rng.randrange(65536),rng.randrange(65536)) for _ in range(32)]
    failures=[];examples=[];checks=0
    for base,bank in zip(config['rotation_table_bases'],(4,8)):
        for x,y in cases:
            expected=[(x,y),(-y&65535,x),(-x&65535,-y&65535),(y,-x&65535)]
            for entry,want in enumerate(expected):
                ram=[0xa5]*16;put(ram,10,x);put(ram,12,y)
                cpu,trace=run_entry(rows,base,entry,ram,config['fixture_q'],policy)
                got=(word(cpu.ram,bank),word(cpu.ram,bank+2));checks+=1
                if got!=want:failures.append(dict(base=base,entry=entry,x=x,y=y,want=want,got=got))
                if x==0x1234 and y==0x5678:examples.append(dict(base=base,entry=entry,output=got,trace=trace))
    output_checks=0
    for base,bank in zip(config['output_table_bases'],(4,8,12)):
        for ax,ay in cases:
            bx,by=(ax,ay) if bank==4 else (0x1357,0x2468)
            expected=[(bx+ax,by+ay),(by+ay,bx-ax),(bx-ax,by-ay),(by-ay,bx+ax)]
            for entry,want in enumerate(expected):
                ram=[0xa5]*16;put(ram,4,ax);put(ram,6,ay);put(ram,bank,bx);put(ram,bank+2,by)
                cpu,trace=run_entry(rows,base,entry,ram,0x59,policy)
                slots={t['slot']:t['y'] for t in trace}
                got=(slots[8]|slots[9]<<8,slots[10]|slots[11]<<8);want=tuple(v&65535 for v in want);output_checks+=1
                if got!=want:failures.append(dict(base=base,entry=entry,ax=ax,ay=ay,want=want,got=got))
                if ax==0x1234 and ay==0x5678:examples.append(dict(base=base,entry=entry,output=got,trace=trace))
    alias=[]
    for entry in range(4):
        ram=[0]*16;put(ram,10,0x1234);put(ram,12,0x5678)
        cpu,trace=run_entry(rows,config['alias_table_base'],entry,ram,config['fixture_q'],policy)
        alias.append(dict(entry=entry,output=(word(cpu.ram,12),word(cpu.ram,14)),trace=trace))
    return dict(mapping=mapping['name'],rotation_checks=checks,virtual_output_checks=output_checks,failures=failures,
                examples=examples,alias_table=alias,assumptions=config['limitations'],
                conclusion='Arithmetic identities hold only under the stated decode and fixture preconditions; these are not independent observations of hardware.')


def integration(task):
    mapping,scenario,seed,cycles,out=task
    r=execute(mapping,scenario,cycles,seed,'integrated',out,128)
    return out.name,r


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,default=HERE/'results/rotation-study')
    parser.add_argument('--cycles',type=int,default=10000000);parser.add_argument('--analysis-only',action='store_true')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    if args.cycles<1:parser.error('positive cycle limit required')
    config=read(HERE/'rotation-search.json');ranking,candidates=search(load(),config);save(args.out/'ranking.json',ranking)
    tasks=[];fixture_results=[]
    for index,candidate in enumerate(candidates,1):
        mapping=make_mapping(candidate,index,config);scenario=scenario_for(mapping,config)
        report=fixtures(mapping,config);fixture_results.append(report)
        save(args.out/f'variant-{index}.json',mapping);save(args.out/f'scenario-{index}.json',scenario)
        listing(decode(mapping),args.out/f'variant-{index}.csv');save(args.out/f'arithmetic-{index}.json',report)
        print(mapping['name'],'fixture failures',len(report['failures']),flush=True)
        for seed in config['integration_seeds']:
            tasks.append((mapping,scenario,seed,args.cycles if seed==0 else min(args.cycles,1000000),args.out/f'rotation-{index}-seed-{seed}'))
    if any(r['failures'] for r in fixture_results):raise RuntimeError('Arithmetic hypothesis failed its fixtures')
    if args.analysis_only:return
    with ProcessPoolExecutor(max_workers=3) as pool:results=dict(pool.map(integration,tasks))
    save(args.out/'summary.json',dict(all_clean=all(r['clean'] for r in results.values()),
        runs={n:{k:r[k] for k in ('completed_cycles','requested_cycles','coverage','clean','stop','stack','carry_model','io_writes','register_changes','trace_digest')} for n,r in results.items()},
        interpretation='Scenario-driven control flow, arithmetic-constrained decode, explicit virtual outputs; physical I/O remains unidentified.'))
    print('all clean:',all(r['clean'] for r in results.values()))

if __name__=='__main__':main()
