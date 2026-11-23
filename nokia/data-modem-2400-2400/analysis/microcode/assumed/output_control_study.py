"""Measure ambiguity of output-enable predicates using explicitly assumed labels."""
import argparse
import itertools
from collections import Counter
from pathlib import Path
from common import HERE, decode, field_value, load, read, save


def addresses(ranges):
    return [pc for low,high in ranges for pc in range(int(low,16),int(high,16)+1)]


def activates(terms, lanes, pc):
    return all(field_value([bit],lanes,pc)==value for bit,value in terms)


def candidates(config):
    literals=[(f'{chip}.{bit}',value) for chip in ('10','11','17','18') for bit in range(8) for value in (0,1)]
    for count in range(1,config['maximum_literals']+1):
        for terms in itertools.combinations(literals,count):
            if len({bit for bit,value in terms})==count:
                yield terms


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/output-control-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'output-control-search.json');lanes=load()
    profiles={name:read(HERE/path) for name,path in config['profiles'].items()}
    rows=decode(profiles['q2'],lanes);used=[r['pc'] for r in rows if not r['unused']]
    positive=addresses(config['positive_training']);negative=addresses(config['negative_training'])
    held_positive=addresses(config['positive_holdout']);held_negative=addresses(config['negative_holdout'])
    probes=[int(p,16) for p in config['transient_probes']]
    owners={}
    for name,mapping in profiles.items():
        owners[name]={f'{c}.{b}':[key for key,f in mapping['fields'].items()
                                if isinstance(f['bits'],list) and f'{c}.{b}' in {t.lstrip('!') for t in f['bits']}]
                      for c in lanes for b in range(8)}
    def describe(terms):
        active=[p for p in used if activates(terms,lanes,p)]
        return dict(terms=terms,active_words=active,count=len(active),
                    commands=dict(Counter(rows[p]['command_name'] for p in active)),
                    held_positive_selected=[p for p in held_positive if p in active],
                    held_negative_selected=[p for p in held_negative if p in active],
                    transient_selected=[p for p in probes if p in active],
                    field_owners={name:{bit:fields[bit] for bit,value in terms} for name,fields in owners.items()})
    tested=0;fits=[]
    for terms in candidates(config):
        tested+=1
        if all(activates(terms,lanes,p) for p in positive) and not any(activates(terms,lanes,p) for p in negative):
            fits.append(describe(terms))
    minimal=[r for r in fits if not any(set(other['terms']) < set(r['terms']) for other in fits)]
    groups={}
    for r in fits:groups.setdefault(tuple(r['active_words']),[]).append(r['terms'])
    free=[bit for bit in owners['q2'] if all(not fields[bit] for fields in owners.values())]
    report=dict(configuration=config,tested=tested,fits=fits,minimal_fits=[r['terms'] for r in minimal],
        distinct_activation_sets=len(groups),
        common_unassigned_bits=free,
        common_unassigned_values={bit:dict(training_positive=sorted({field_value([bit],lanes,p) for p in positive}),
                                         training_negative=sorted({field_value([bit],lanes,p) for p in negative})) for bit in free},
        comparison_gate=describe(config['comparison_gate']),
        interpretation='Candidate discrimination under assumed labels, not output-enable recovery. No emulator I/O behavior changed.')
    save(args.out/'report.json',report)
    print(dict(tested=tested,fits=len(fits),minimal=len(minimal),distinct_activation_sets=len(groups),
               heldout_pass=sum(len(r['held_positive_selected'])==len(held_positive) and not r['held_negative_selected'] for r in fits),
               transient_both=sum(len(r['transient_selected'])==len(probes) for r in fits),common_unassigned_bits=free))


if __name__=='__main__':main()
