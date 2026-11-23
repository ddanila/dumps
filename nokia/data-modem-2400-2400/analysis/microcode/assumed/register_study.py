"""Recover a second counting field and search disjoint datapath interpretations."""
import argparse
import copy
import itertools
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from common import HERE, decode, field_value, load, read, save
from analyze import listing
from execute import execute


def recover_register(lanes, mapping, config):
    known=mapping['fields']['register']['bits']
    positions=[p for base in config['training_bases'] for p in range(base,base+config['training_length'])]
    pattern=config['expected_register_cycle']
    expected=[pattern[i%len(pattern)] for i in range(len(positions))]
    windows=set()
    for order in itertools.permutations(lanes):
        for reverse in (False,True):
            stream=[f'{chip}.{bit}' for chip in order for bit in (range(7,-1,-1) if reverse else range(8))]
            for start in range(29):
                bits=tuple(stream[start:start+4])
                if not set(bits)&set(known):windows.add(bits)
    ranked=[]
    for bits in sorted(windows):
        values=[field_value(bits,lanes,p) for p in positions]
        for inversion in range(16):
            score=sum((value^inversion)==want for value,want in zip(values,expected))
            expression=[('!' if inversion>>i&1 else '')+bit for i,bit in enumerate(bits)]
            ranked.append(dict(bits=expression,score=score))
    ranked.sort(key=lambda r:(-r['score'],r['bits']))
    best=ranked[0]
    heldout=[]
    for base in config['heldout_bases']:
        heldout.append(dict(base=base,source_values=[field_value(best['bits'],lanes,p) for p in range(base,base+16)],
                            other_values=[field_value(known,lanes,p) for p in range(base,base+16)]))
    return dict(config=config,windows=len(windows),candidates=len(ranked),training_words=len(positions),
                best=best,tied_best=[r for r in ranked if r['score']==best['score']],top=ranked[:20],heldout=heldout,
                selector_table=dict(base=0x8a,source_values=[field_value(best['bits'],lanes,p) for p in range(0x8a,0x9a)],
                    other_values=[field_value(known,lanes,p) for p in range(0x8a,0x9a)]),
                interpretation='Unique match within this contiguous-field search; register role and hardware wiring remain hypotheses.')


def rank_disjoint(lanes,mapping,config,recovered,out):
    first=recovered['best']['bits'];second=mapping['fields']['register']['bits']
    excluded=set(config['instruction_excluded'])|{x.lstrip('!') for x in first+second}
    windows=set()
    for order in config['instruction_chip_orders']:
        for reverse in (False,True):
            stream=[f'{c}.{b}' for c in order for b in (range(7,-1,-1) if reverse else range(8)) if f'{c}.{b}' not in excluded]
            for start in range(len(stream)-8):
                window=stream[start:start+9]
                groups=[window[i:i+3] for i in (0,3,6)]
                for order3 in itertools.permutations(range(3)):
                    windows.add(tuple(bit for group in order3 for bit in groups[group]))
    rows=decode(mapping,lanes);used=[r['pc'] for r in rows if not r['unused']]
    scores=[];weights=config['weights']
    for bits in sorted(windows):
        values=[field_value(bits,lanes,p) for p in range(1024)]
        dest=Counter(values[p]>>6 for p in used);fn=Counter((values[p]>>3)&7 for p in used)
        destination_scores={}
        for invert in range(8):
            destination_scores[invert]=dict(
                common_destinations=sum(n for d,n in dest.items() if d^invert in (1,2,3))/len(used),
                shift_fraction=sum(n for d,n in dest.items() if d^invert>=4)/len(used),
                nop_no_load=sum(((values[p]>>6)^invert)==1 for p in config['nop_sites'])/len(config['nop_sites']),
                loop_shift=sum(((values[p]>>6)^invert)>=4 for p in config['shift_sites'])/len(config['shift_sites']))
        for inversion in range(512):
            parts=dict(destination_scores[inversion>>6])
            parts['arithmetic_fraction']=sum(n for f,n in fn.items() if f^((inversion>>3)&7)<3)/len(used)
            parts['inversions']=bin(inversion).count('1')
            score=sum(weights[k]*v for k,v in parts.items())
            expression=[('!' if inversion>>i&1 else '')+bit for i,bit in enumerate(bits)]
            for a,b in ((first,second),(second,first)):
                scores.append(dict(score=score,components=parts,i=expression,a=a,b=b))
        scores.sort(key=lambda r:(-r['score'],r['i'],r['a'],r['b']))
        del scores[20:]
    scores.sort(key=lambda r:(-r['score'],r['i'],r['a'],r['b']))
    variants=[]
    for index,candidate in enumerate(scores[:config['retained']],1):
        variant=copy.deepcopy(mapping);variant['name']=f'register-constrained-{index}'
        for name in ('a','b','i'):
            variant['fields'][name]=dict(bits=candidate[name],status='hypothesis',evidence='Register-family constraints and disjoint instruction search; A/B role unresolved')
        variant['fields']['d']=dict(bits=[f'10.{i}' for i in range(7,-1,-1)],commands=[0,1,2,3,5,7],status='hypothesis',evidence='Retained reversed immediate hypothesis; external-data alternatives unresolved')
        variant['ranking']=candidate;variants.append(variant)
        save(out/f'variant-{index}.json',variant);listing(decode(variant,lanes),out/f'variant-{index}.csv')
    return variants,dict(candidates=len(windows)*512*2,instruction_windows=len(windows),configuration=config,top=scores[:20],
                         limitations=['These priors rank hypotheses, not wiring confidence.','Source-code polarity is unconstrained by the score except the inversion penalty.','Chip-10 instruction interpretations are not included.'])


def table_semantics(mapping,lanes,config):
    rows=decode(mapping,lanes);families=[]
    for base in config['training_bases']+config['heldout_bases']:
        signatures=[];uses_d=False
        for entry in range(4):
            signature=[]
            for row in rows[base+4*entry:base+4*entry+4]:
                uses_d |= (row['i']&7)>=5
                # With source codes 0..4, D cannot affect any modeled output.
                signature.append((row['i'],row['a'],row['b'],row.get('d') if (row['i']&7)>=5 else None))
            signatures.append(tuple(signature))
        groups=[]
        for index,signature in enumerate(signatures):
            same=[i for i,x in enumerate(signatures) if x==signature]
            if same not in groups:groups.append(same)
        families.append(dict(base=base,uses_d=uses_d,equivalent_entry_groups=groups,
            reason='Identical instruction/register inputs at each step; D omitted only when instruction source does not use it. Valid for any initial register state and common carry/shift inputs; excludes external I/O.'))
    return dict(mapping=mapping['name'],families=families,
        implication='If distinct table choices have distinct effects, these models need a different instruction/source mapping or external effects controlled by chip 10. Clean execution does not resolve that ambiguity.')


def integration(task):
    mapping,scenario,cycles,out=task
    result=execute(mapping,scenario,cycles,0,'integrated',out,64)
    return mapping['name'],result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/register-study')
    parser.add_argument('--cycles',type=int,default=10000000)
    parser.add_argument('--analysis-only',action='store_true')
    args=parser.parse_args()
    if args.cycles<1:parser.error('positive cycle limit required')
    args.out.mkdir(parents=True,exist_ok=True)
    lanes=load();mapping=read(HERE/'sequencer.json');config=read(HERE/'register-search.json')
    recovered=recover_register(lanes,mapping,config);save(args.out/'register-recovery.json',recovered)
    variants,ranking=rank_disjoint(lanes,mapping,config,recovered,args.out);save(args.out/'ranking.json',ranking)
    save(args.out/'table-semantics.json',[table_semantics(v,lanes,config) for v in variants])
    print('Register field',recovered['best'],'ties',len(recovered['tied_best']),flush=True)
    if args.analysis_only:return
    scenario=read(HERE/'branch-tables.json')
    with ProcessPoolExecutor(max_workers=3) as pool:
        results=dict(pool.map(integration,[(v,scenario,args.cycles,args.out/v['name']) for v in variants]))
    summary=dict(requested_cycles=args.cycles,all_clean=all(r['clean'] for r in results.values()),
        runs={name:{k:r[k] for k in ('completed_cycles','coverage','clean','stop','stack','register_changes','trace_digest')} for name,r in results.items()},
        interpretation='More constrained register fields, still speculative instruction fields; no recovered I/O semantics.')
    save(args.out/'summary.json',summary);print(summary)

if __name__=='__main__':main()
