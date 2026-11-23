"""Reproduce PROM field evidence, conservative CFG and bounded datapath search."""
import argparse
import csv
import itertools
from collections import Counter, deque
from common import HERE, NAMES, decode, digest, field_value, load, read, save, unconditional_transfer, table_targets


def must_targets(rows):
    return [p for p in range(1, 1024) if not rows[p]['unused']
            and rows[p-1]['command'] == 3 and (p < 2 or rows[p-2]['command'] != 0)]


def search_address(lanes, rows):
    required = set(must_targets(rows))
    transfers = [r['pc'] for r in rows if r['command'] in (4, 6) and r['direct'] and not r['unused']]
    columns = {f'{c}.{b}': [(lanes[c][p] >> b) & 1 for p in transfers]
               for c in lanes for b in range(8)}
    def score(bits):
        targets = {sum((columns[t.lstrip('!')][i] ^ t.startswith('!')) << j
                       for j, t in enumerate(bits)) for i in range(len(transfers))}
        return len(required & targets)
    best, winners, count = -1, [], 0
    for chips in itertools.permutations(lanes):
        for reverse in (False, True):
            stream = [f'{c}.{b}' for c in chips for b in (range(7,-1,-1) if reverse else range(8))]
            for start in range(23):
                for invert in (False, True):
                    bits = [('!' if invert else '') + b for b in stream[start:start+10]]
                    value = score(bits); count += 1
                    if value > best: best, winners = value, []
                    if value == best: winners.append(bits)
    chosen = read(HERE/'sequencer.json')['fields']['branch']['bits']
    refined, value = chosen[:], score(chosen)
    while True:
        options = []
        for i in range(10):
            for b in columns:
                for inv in ('', '!'):
                    candidate = refined[:]; candidate[i] = inv+b
                    if len({x.lstrip('!') for x in candidate}) == 10:
                        options.append((score(candidate), candidate))
        candidate_score, candidate = sorted(options, key=lambda x: (-x[0], x[1]))[0]
        if candidate_score <= value: break
        value, refined = candidate_score, candidate
    return dict(required=sorted(required), windows_tested=count, best_window_score=best,
                best_windows=winners, chosen_score=score(chosen), refined_score=value,
                refined_bits=refined, target_count=len(required),
                b0_b9_alternatives=[dict(bits=[b0]+chosen[1:9]+[b9],score=score([b0]+chosen[1:9]+[b9]))
                    for b0,b9 in itertools.product(['11.0','!11.0','18.7','!18.7'],repeat=2)
                    if b0.lstrip('!') != b9.lstrip('!')])


def walk(rows, start):
    depth = 0
    for p in range(start,1024):
        c = rows[p]['command']
        if c == 5: depth += 1
        if c == 2:
            depth -= 1
            if depth < 0: return dict(end=p,reason='BLT consumes entry stack',balanced=False)
        if c == 3: return dict(end=p,reason='POP',balanced=depth==0)
    return dict(end=1023,reason='end of store',balanced=False)


def graph(rows, scenario):
    """Conservative finite-state stack exploration; no fabricated return edges."""
    queue = deque([(0, ())]); states = set(); edges = set(); exceptions = set()
    while queue:
        pc, stack = queue.popleft()
        if (pc,stack) in states: continue
        states.add((pc,stack))
        if len(states) > 500000:
            exceptions.add('state budget 500000 exhausted'); break
        r = rows[pc]; c = r['command']; nxt = (pc+1)&1023
        if r['unused']:
            exceptions.add(f'{pc:03x}: unused word reached'); continue
        tests = [1] if unconditional_transfer(r,scenario) else [0,1]
        for test in tests:
            dest, ns, kind = nxt, stack, 'fallthrough'
            if c==0: dest=(nxt+test)&1023; kind='skip' if test else kind
            elif c in (2,3):
                if not stack:
                    exceptions.add(f'{pc:03x}: possible stack underflow'); continue
                ns=stack[:-1]; kind='loop' if c==2 else 'return'
                if c==3 or test: dest=stack[-1]
            elif c==5 or (c==4 and test):
                if len(stack)==4:
                    exceptions.add(f'{pc:03x}: possible stack overflow'); continue
                ns=stack+(pc if c==5 else nxt,)
                if c==4:
                    kind='call'
                    if r['direct'] and str(pc) not in scenario['dispatch']['tables']: dest=r['branch']
                    else:
                        t=scenario['dispatch']['tables'][str(pc)]
                        for target in table_targets(t):
                            edges.add((pc,target,'dispatch:'+t['status'])); queue.append((target,ns))
                        continue
            elif c==6 and test:
                dest=r['branch']; kind='branch'
                table=scenario.get('branch_tables',{}).get(str(pc))
                if table is not None:
                    for target in table_targets(table):
                        edges.add((pc,target,'branch-dispatch:'+table['status']));queue.append((target,ns))
                    continue
                if not r['direct']:
                    policy=scenario['indirect_branch'];kind='indirect-branch:'+policy['status']
                    if policy['source']=='constant': dest=policy['value']
                    elif policy['source']!='microword':
                        exceptions.add(f'{pc:03x}: unresolved datapath branch');continue
            elif c==7: dest=0; kind='reset'
            edges.add((pc,dest,kind)); queue.append((dest,ns))
    reached={p for p,s in states}
    return dict(states=len(states),reached=sorted(reached),edges=sorted(edges),
                exceptions=sorted(exceptions),unreachable=[dict(pc=r['pc'],reason='No path under declared direct and dispatch edges; unresolved wiring/dispatch hypothesis') for r in rows if not r['unused'] and r['pc'] not in reached])


def rank_layouts(lanes, rows, out):
    base=read(HERE/'sequencer.json')
    # Explicit bounded search, not an exhaustive claim about all pin permutations.
    config=read(HERE/'search.json')
    streams=[[f'{c}.{b}' for c in order for b in range(7,-1,-1)]
             for order in config['instruction_orders']]
    reserved=set(config['reserved'])
    streams=[[b for b in stream if b not in reserved] for stream in streams]
    register=base['fields']['register']['bits']
    streams += [[b for b in stream if b not in register] for stream in streams[:]]
    fields=[]
    for chips in config['register_orders']:
        stream=[f'{c}.{b}' for c in chips for b in range(7,-1,-1)]
        fields += [stream[i:i+4] for i in range(len(stream)-3)]
    tables=[list(range(0x8a,0x9a))]+[list(range(x,x+16)) for x in (0x379,0x392,0x3ab,0x3c5,0x3da,0x3ef)]
    scored=[]
    used=[r['pc'] for r in rows if not r['unused']]
    for stream in streams:
        for start in range(len(stream)-8):
            ibits=stream[start:start+9]
            inst=[field_value(ibits,lanes,p) for p in range(1024)]
            freq=Counter((inst[p]>>6)&7 for p in used)
            setup=sum(((inst[(p-1)&1023]>>6)&7) in (0,2,3) for p in used if rows[p]['command']==5)
            loop_shift=sum(((inst[p]>>6)&7)>=4 for p in used if rows[p]['command']==2)
            for other in fields:
                if not config['allow_identical_register_fields'] and other==register: continue
                vals=[field_value(other,lanes,p) for p in range(1024)]
                pattern=sum(len(set(vals[p] for p in table)) for table in tables)
                for swap in (False,True):
                    a,b=(other,register) if swap else (register,other)
                    parts=dict(register_diversity=pattern,common_destinations=sum(freq[x] for x in (1,2,3))/len(used),loop_setup=setup,loop_shifts=loop_shift)
                    parts['shared_bits']=len(set(ibits)&(set(a)|set(b)))+len(set(a)&set(b))
                    score=sum(parts[k]*v for k,v in config['weights'].items())
                    scored.append(dict(score=score,components=parts,i=ibits,a=a,b=b))
    unique={digest({k:x[k] for k in ('i','a','b')}):x for x in scored}
    ranked=sorted(unique.values(),key=lambda x:(-x['score'],x['i'],x['a'],x['b']))
    for index,candidate in enumerate(ranked[:config['retained']]):
        mapping=json_copy(base); mapping['name']=f'datapath-{index+1}'
        for k in ('i','a','b'):
            mapping['fields'][k]=dict(bits=candidate[k],status='hypothesis',evidence='Bounded structural ranking; not identified wiring')
        mapping['fields']['d']=dict(bits=[f'10.{i}' for i in range(7,-1,-1)],status='hypothesis',evidence='Reversed immediate-byte hypothesis',commands=[0,1,2,3,5,7])
        mapping['ranking']=candidate
        save(out/f'datapath-{index+1}.json',mapping)
        listing(decode(mapping,lanes),out/f'datapath-{index+1}.csv')
    return dict(search='Two reversed residual-bit streams, contiguous I windows; reversed A/B windows plus counting field, both roles',
                configuration=config,
                candidates=len(ranked),top=ranked[:20],limitations=['All instruction values legal; plausibility is weak evidence', 'Dynamic and immediate-constant evidence reported separately; no invented semantic score', 'A/B role ties retained', 'No globally exhaustive wiring search'])


def json_copy(x):
    import copy
    return copy.deepcopy(x)


def listing(rows,path):
    keys=['pc','raw','unused']+sorted(set().union(*(r.keys() for r in rows))-{'pc','raw','unused'})
    with path.open('w') as f:
        w=csv.DictWriter(f,keys,lineterminator="\n");w.writeheader();w.writerows(rows)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=__import__('pathlib').Path,required=True)
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    lanes=load();rows=decode(read(HERE/'sequencer.json'),lanes);scenario=read(HERE/'baseline.json')
    address=search_address(lanes,rows);cfg=graph(rows,scenario)
    summary=dict(histogram=dict(Counter(NAMES[r['command']] for r in rows if not r['unused'])),unused=[r['pc'] for r in rows if r['unused']],address_search=address,
        conditions={NAMES[c]:dict(Counter(f"{r['select']}/{r['direct']}" for r in rows if r['command']==c and not r['unused'])) for c in range(8)},
        subroutines={str(t):walk(rows,t) for t in sorted({r['branch'] for r in rows if r['command']==4 and r['direct']})},
        outlier_01e=dict(explanation='01C calls 01E, pushing 01D. BLT consumes that return: true reaches PLP at 01D, false continues 01F. This is a valid loop entry, not an empty-stack access.',status='hypothesis',evidence='Decoded 01C BSR 01E; 01D PLP; 01E BLT; both paths balance the initial push'),
        dispatch=scenario['dispatch']['tables'],indirect_branches=dict(addresses=[r['pc'] for r in rows if r['command']==6 and not r['direct']],policy=scenario['indirect_branch']))
    save(args.out/'analysis.json',summary);save(args.out/'control-flow.json',cfg)
    listing(rows,args.out/'listing.csv')
    with (args.out/'control-flow.dot').open('w') as f:
        f.write('digraph microcode {\n')
        for a,b,kind in cfg['edges']: f.write(f' a{a:03x} -> a{b:03x} [label="{kind}"];\n')
        f.write('}\n')
    save(args.out/'ranking.json',rank_layouts(lanes,rows,args.out))
    print(summary['histogram']);print('Reachable',len(cfg['reached']),'unreachable',len(cfg['unreachable']))

if __name__=='__main__': main()
