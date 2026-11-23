"""Search separated source bits for Q-independent paired arithmetic."""
import argparse
import itertools
from pathlib import Path
from common import HERE, decode, field_value, load, read, save
from analyze import listing
from rotation_study import make_mapping, scenario_for, run_entry, word, put
from execute import execute


def search_sources(lanes,config,base):
    candidates=[]
    for bits in itertools.permutations(base['source_bits'],3):
        for inversion in range(8):
            expression=[('!' if inversion>>j&1 else '')+b for j,b in enumerate(bits)]
            if all(field_value(expression,lanes,int(pc))==source for pc,source in config['source_constraints'].items()):
                candidates.append(expression)
    return sorted(candidates)


def arithmetic(mapping,config,base):
    rows=decode(mapping);policy=scenario_for(mapping,base)['inputs']['carry']
    cases=[(0,0),(1,0),(0,1),(0x100,0xffff),(0x8000,0x7fff),(0x1234,0x5678)]
    failures=[];checks=0;output_checks=0
    for q in config['q_values']:
        for table in base['rotation_table_bases']:
            bank=rows[table]['b']
            for x,y in cases:
                for entry,want in enumerate(((x,y),(-y&65535,x),(-x&65535,-y&65535),(y,-x&65535))):
                    ram=[0xa5]*16;put(ram,10,x);put(ram,12,y)
                    cpu,_=run_entry(rows,table,entry,ram,q,policy)
                    got=(word(cpu.ram,bank),word(cpu.ram,bank+2));checks+=1
                    if got!=want:failures.append(dict(table=table,entry=entry,q=q,x=x,y=y,want=want,got=got))
        for table in base['output_table_bases']:
            bank=rows[table]['b']
            for ax,ay in cases:
                bx,by=(ax,ay) if bank==4 else (0x1357,0x2468)
                expected=((ax+bx,ay+by),(ay+by,ax-bx),(ax-bx,ay-by),(ay-by,ax+bx))
                for entry,want in enumerate(expected):
                    ram=[0xa5]*16;put(ram,4,ax);put(ram,6,ay);put(ram,bank,bx);put(ram,bank+2,by)
                    _,trace=run_entry(rows,table,entry,ram,q,policy)
                    slots={t['slot']:t['y'] for t in trace}
                    got=(slots[8]|slots[9]<<8,slots[10]|slots[11]<<8);want=tuple(v&65535 for v in want);output_checks+=1
                    if got!=want:failures.append(dict(table=table,entry=entry,q=q,want=want,got=got))
    return dict(rotation_checks=checks,output_checks=output_checks,failures=failures,
        interpretation='Q-independent identities under the proposed separated source bits; subtraction in output tables is A-B, unlike the earlier B-A hypothesis.')


def loop_probe(mapping,config):
    from model import Am2901, X8X02
    rows=decode(mapping);policy=config['loop_probe'];cases=[]
    for initial_q in range(256):
        cpu=Am2901(q=initial_q);seq=X8X02(pc=(policy['return_pc']-1)&1023)
        seq.step(4,policy['entry'],True)
        iterations=0;trace=[]
        for cycle in range(policy['cycle_limit']):
            row=rows[seq.pc]
            result=cpu.step(row['i'],row['a'],row['b'],policy['external_d'],policy['carry'],policy['shift_fill'],policy['shift_fill'])
            if seq.pc==policy['entry']:iterations+=1
            trace.append(dict(pc=seq.pc,q=cpu.q,ram0=cpu.ram[0],zero=result['zero']))
            seq.step(row['command'],row['branch'],not result['zero'])
            if seq.pc==policy['return_pc']:break
        cases.append(dict(initial_q=initial_q,iterations=iterations,cycles=len(trace),final_q=cpu.q,
            returned=seq.pc==policy['return_pc'],balanced=seq.pushes==seq.pops,
            trace=trace if initial_q in (0,1,128,255) else []))
    return dict(configuration=policy,cases=cases,all_returned=all(c['returned'] and c['balanced'] for c in cases),
        all_shift_counts_match=all(c['iterations']==max(1,c['initial_q'].bit_length()) and c['final_q']==0 for c in cases),
        interpretation='Local fixture, excluded from reset coverage; 1E9 shifts Q to zero if BLT tests current nonzero and shift fill is zero.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/independent-study')
    parser.add_argument('--integrated-cycles',type=int,default=0)
    args=parser.parse_args()
    if args.integrated_cycles<0:parser.error('integration length cannot be negative')
    args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'independent-search.json');base=read(HERE/'rotation-search.json')
    profiles=read(HERE/'caller-search.json')
    candidates=search_sources(load(),config,base)
    save(args.out/'search.json',dict(configuration=config,source_assignments=len(list(itertools.permutations(base['source_bits'],3)))*8,survivors=candidates))
    summaries=[];integrations=[]
    for index,source in enumerate(candidates,1):
        candidate=dict(i=source+config['function_bits']+base['destination_bits'])
        mapping=make_mapping(candidate,index,base);mapping['name']=f'q-independent-{index}'
        for field in mapping['fields'].values():
            if field['status']=='hypothesis':field['evidence']='Q-independent paired arithmetic hypotheses; see independent-search.json and rotation-search.json'
        scenario=scenario_for(mapping,base)
        report=arithmetic(mapping,config,base)
        assert not report['failures'],report['failures'][:1]
        save(args.out/f'variant-{index}.json',mapping);save(args.out/f'scenario-{index}.json',scenario)
        save(args.out/f'loop-{index}.json',loop_probe(mapping,config))
        save(args.out/f'arithmetic-{index}.json',report);listing(decode(mapping),args.out/f'variant-{index}.csv')
        runs=[]
        for d in profiles['external_read_values']:
            scenario['io']['read']['value']=d
            for seed in profiles['seeds']:
                r=execute(mapping,scenario,profiles['cycles'],seed,'integrated',trace_limit=0)
                runs.append(dict(external_read=d,seed=seed,clean=r['clean'],coverage=r['coverage'],register_changes=r['register_changes'],trace_digest=r['trace_digest']))
        summaries.append(dict(mapping=mapping['name'],arithmetic=report,runs=runs,all_clean=all(r['clean'] for r in runs)))
        if args.integrated_cycles:
            scenario['io']['read']['value']=config['integration']['external_read']
            r=execute(mapping,scenario,args.integrated_cycles,config['integration']['seed'],'integrated',args.out/f'integrated-{index}',128)
            integrations.append(dict(mapping=mapping['name'],**{k:r[k] for k in ('completed_cycles','clean','coverage','stack','trace_digest')}))
    if integrations:
        save(args.out/'integration.json',dict(**config['integration'],runs=integrations,all_clean=all(r['clean'] for r in integrations)))
    save(args.out/'summary.json',dict(variants=summaries,profiles=profiles,interpretation='Short reset-path sensitivity runs; physical I/O and complete program semantics remain unresolved.'))
    print('Q-independent source candidates:',len(candidates))

if __name__=='__main__':main()
