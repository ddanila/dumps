"""Bounded-memory execution of real PROMs under explicit mapping/scenario assumptions."""
import argparse
import hashlib
import json
import random
from contextlib import ExitStack
from collections import Counter
from pathlib import Path
from common import HERE, decode, digest, load, read, save, unconditional_transfer, table_targets
from model import Am2901, X8X02, UnknownStack


class CarryInput:
    """Explicit constant or mapped/previous-carry input, shared with experiments."""
    def __init__(self,policy):
        self.policy=policy
        self.previous=policy['initial'] if isinstance(policy,dict) else policy
        self.counts=Counter()

    def resolve(self,row):
        if not isinstance(self.policy,dict):return self.policy
        if row[self.policy['select_field']]:
            value=self.previous;self.counts['feedback']+=1
            if value is None:
                value=self.policy['unknown'];self.counts['unknown_feedback']+=1
        else:
            value=row[self.policy['constant_field']];self.counts['mapped_constant']+=1
        self.counts[f'value_{value}']+=1
        return value

    def observe(self,result):
        self.previous=result['carry']


def validate_scenario(s):
    if s['status'] not in ('hypothesis','stub','recovered-from-data') or not s.get('evidence'):
        raise ValueError('scenario requires provenance')
    if s.get('stack_fallback') is not None:
        raise ValueError('stack repair is unsupported: diagnose mapping instead')
    c=s['condition'];d=s['dispatch']
    if c['mode'] not in ('constant','per-select','random','flags'):
        raise ValueError('unknown condition mode')
    if c['flag_timing'] not in ('current','previous'):
        raise ValueError('invalid flag timing')
    for key in ('per_select','polarity'):
        if len(c[key])!=8 or any(v not in (0,1) for v in c[key]):
            raise ValueError(f'invalid {key}')
    if len(c['sources'])!=8 or any(v not in ('constant','zero','sign','carry','overflow','external','random') for v in c['sources']):
        raise ValueError('invalid condition sources')
    if c['value'] not in (0,1) or c['unknown'] not in (0,1):
        raise ValueError('invalid condition defaults')
    indirect=s['indirect_branch']
    if indirect['source'] not in ('microword','constant','y','q') or indirect['status'] not in ('stub','hypothesis','recovered-from-data') or not indirect.get('evidence') or not 0<=indirect['value']<1024:
        raise ValueError('invalid indirect branch policy')
    if d['mode'] not in ('constant','sequence','random') or d['source'] not in ('scenario','y','q'):
        raise ValueError('invalid dispatch mode/source')
    if not d['sequence'] or any(not isinstance(v,int) or v<0 for v in d['sequence']):
        raise ValueError('invalid dispatch sequence')
    if not isinstance(c.get('unconditional_requires_direct', True), bool):
        raise ValueError('unconditional_requires_direct must be boolean')
    for pc,t in [*d['tables'].items(), *s.get('branch_tables',{}).items()]:
        if not 0<=int(pc)<1024:raise ValueError('invalid dispatch site')
        table_targets(t)
        if t['status'] not in ('hypothesis','stub','recovered-from-data') or not t.get('evidence'):
            raise ValueError('dispatch requires provenance')
    if s['io']['read']['mode'] not in ('immediate','constant','table','am27s31'):
        raise ValueError('unknown IO read mode')
    if c['unconditional_select'] is not None and c['unconditional_select'] not in range(8):
        raise ValueError('invalid unconditional select')
    if any(not isinstance(v,int) or not 0<=v<=255 for v in s['io']['read']['table']) or not 0<=s['io']['read']['value']<=255:
        raise ValueError('read values must be bytes')
    if d['value']<0:
        raise ValueError('negative dispatch index')
    for w in s['io']['writes']:
        if not 0<=int(w['pc'])<1024 or w['status'] not in ('hypothesis','stub','recovered-from-data') or not w.get('evidence') or w.get('source','y') not in ('y','f','carry','zero','sign','overflow'):
            raise ValueError('invalid write rule')
    if not s['io']['read']['table']:
        raise ValueError('empty read table')
    initial=s['initial']
    if not 0<=initial['pc']<1024 or len(initial['ram'])!=16 or any(not 0<=v<=255 for v in initial['ram']) or not 0<=initial['q']<=255:
        raise ValueError('invalid initial state')
    carry=s['inputs']['carry']
    if isinstance(carry,dict):
        if carry['mode']!='mapped-or-previous' or carry['initial'] not in (0,1) or carry['unknown'] not in (0,1) or carry['status'] not in ('hypothesis','stub','recovered-from-data') or not carry.get('evidence'):
            raise ValueError('invalid carry policy')
    elif carry not in (0,1):raise ValueError('invalid carry input')
    for key in ('ram_in','q_in','external'):
        if s['inputs'][key] not in (0,1): raise ValueError('invalid input bit')


def execute(mapping, scenario, cycles, seed=0, mode='sequencer', out=None, trace_limit=1000):
    with ExitStack() as stack:
        sinks={}
        if out:
            Path(out).mkdir(parents=True,exist_ok=True)
            sinks={name:stack.enter_context((Path(out)/name).open('w')) for name in ('trace.jsonl','io.jsonl')}
        return _execute(mapping,scenario,cycles,seed,mode,out,trace_limit,sinks)


def _execute(mapping, scenario, cycles, seed, mode, out, trace_limit, sinks):
    validate_scenario(scenario)
    if cycles<1 or trace_limit<0 or mode not in ('sequencer','integrated'):
        raise ValueError('invalid run limits/mode')
    lanes=load();rows=decode(mapping,lanes)
    if mode=='integrated' and any(k not in mapping['fields'] for k in ('i','a','b','d')):
        raise ValueError('integrated mode requires datapath fields')
    cond=scenario['condition'];dispatch=scenario['dispatch'];inputs=scenario['inputs']
    if mode=='sequencer' and (cond['mode']=='flags' or dispatch['source']!='scenario' or scenario['indirect_branch']['source'] in ('y','q')):
        raise ValueError('datapath source requires integrated mode')
    for row in rows:
        if row['command']==4 and not row['direct'] and str(row['pc']) not in dispatch['tables']:
            raise ValueError(f"missing dispatch site {row['pc']:03x}")
    for site in scenario.get('branch_tables',{}):
        if rows[int(site)]['command'] != 6: raise ValueError('branch table site must be BRT')
    if isinstance(inputs['carry'],dict):
        if mode!='integrated':raise ValueError('carry feedback requires integrated mode')
        for key in ('select_field','constant_field'):
            field=inputs['carry'][key]
            if any(row.get(field) not in (0,1) for row in rows):raise ValueError('missing one-bit carry field')
    dispatch_targets={pc:table_targets(t) for pc,t in dispatch['tables'].items()}
    branch_targets={pc:table_targets(t) for pc,t in scenario.get('branch_tables',{}).items()}
    carry_input=CarryInput(inputs['carry'])
    rng=random.Random(seed); initial=scenario['initial']
    seq=X8X02(pc=initial['pc']);cpu=Am2901(ram=initial['ram'][:],q=initial['q'])
    visited=Counter();edges=Counter();assumptions=Counter();events=[];depth=maximum=0
    stack_reads=stack_writes=underflows=overflows=unused=0
    source_read=scenario['io']['read'];table=source_read['table'];rom_hash=None
    if source_read['mode']=='am27s31':
        p=HERE.parents[3]/'unknown-modem-am27s31dc'/'nokia-modem-am27s31dc.bin'
        table=list(p.read_bytes());rom_hash=hashlib.sha256(bytes(table)).hexdigest()
        if not table: raise ValueError('empty Am27S31 dump')
    writes={int(w['pc']):w for w in scenario['io']['writes']}
    trace_count=0;io_count=0;dispatch_counts=Counter();register_changes=0
    routine_entries={r['branch'] for r in rows if r['command']==4 and r['direct']}
    routine_samples={}
    flags=dict(zero=None,sign=None,carry=None,overflow=None)
    h=hashlib.sha256(); stop='cycle limit'; completed=0
    # Hash compact transitions incrementally, without storing a full history.
    for cycle in range(cycles):
        pc=seq.pc;r=rows[pc];c=r['command'];select=r['select'];visited[pc]+=1
        old_ram=tuple(cpu.ram) if mode=='integrated' else ();old_q=cpu.q
        if r['unused']: unused+=1
        previous=flags
        result=None
        if mode=='integrated':
            d=r.get('d',source_read['value'])
            if 'd' not in r: assumptions['address-word D fallback']+=1
            if source_read['mode']=='constant': d=source_read['value'];assumptions['constant external read']+=1
            elif source_read['mode'] in ('table','am27s31'):
                d=table[d%len(table)]; assumptions['table external read']+=1
            carry=carry_input.resolve(r)
            result=cpu.step(r['i'],r['a'],r['b'],d,carry,inputs['ram_in'],inputs['q_in'])
            carry_input.observe(result)
            flags=result
            register_changes+=sum(a!=b for a,b in zip(old_ram,cpu.ram))+(old_q!=cpu.q)
        always=unconditional_transfer(r,scenario)
        if always:
            test=1;assumptions['unconditional direct transfer' if r['direct'] else 'unconditional computed transfer']+=1
        elif cond['mode']=='constant': test=cond['value']
        elif cond['mode']=='per-select': test=cond['per_select'][select]
        elif cond['mode']=='random': test=rng.getrandbits(1)
        else:
            source=cond['sources'][select]
            if source=='random': test=rng.getrandbits(1)
            elif source=='constant': test=cond['value']
            elif source=='external': test=inputs['external'];assumptions['external condition']+=1
            else: test=(flags if cond['flag_timing']=='current' else previous)[source]
            if test is None:
                test=cond['unknown'];assumptions['unknown '+source]+=1
                if len(events)<32: events.append(dict(cycle=cycle,pc=pc,event='unknown '+source,value=test))
        # Unconditional transfers are invariant under per-select test polarity.
        if not always:
            test ^= cond['polarity'][select]
        branch=r['branch'];entry=None
        branch_table=scenario.get('branch_tables',{}).get(str(pc)) if c==6 else None
        if c==6 and not r['direct'] and branch_table is None:
            policy=scenario['indirect_branch'];assumptions['indirect BRT '+policy['status']]+=1
            if policy['source']=='constant': branch=policy['value']
            elif policy['source']=='y': branch=result['y']
            elif policy['source']=='q': branch=cpu.q
        if test and ((c==4 and (not r['direct'] or str(pc) in dispatch_targets)) or branch_table is not None):
            t=branch_table if branch_table is not None else dispatch['tables'][str(pc)]
            targets=(branch_targets if branch_table is not None else dispatch_targets)[str(pc)];count=len(targets)
            if dispatch['source']=='y': index=result['y']
            elif dispatch['source']=='q': index=cpu.q
            elif dispatch['mode']=='constant': index=dispatch['value']
            elif dispatch['mode']=='sequence': index=dispatch['sequence'][dispatch_counts[pc]%len(dispatch['sequence'])]
            else: index=rng.randrange(count)
            entry=index%count;branch=targets[entry];dispatch_counts[pc]+=1
            assumptions['dispatch '+t['status']]+=1
        push=c==5 or (c==4 and test);pop=c in (2,3)
        before=dict(sp=seq.sp,depth=depth)
        if push:
            stack_writes+=1
            if depth>=4: overflows+=1
            depth+=1;maximum=max(maximum,depth)
        if pop:
            if c==3 or test: stack_reads+=1
            if depth<=0: underflows+=1
            depth-=1
        try: seq.step(c,branch,test)
        except UnknownStack as err:
            stop=str(err)
            if len(events)<32: events.append(dict(cycle=cycle,pc=pc,event=stop))
            break
        completed+=1;edges[(pc,seq.pc)]+=1
        if overflows or underflows:
            # Continue real circular-stack semantics; do not repair the model.
            if len(events)<32: events.append(dict(cycle=cycle,pc=pc,event='stack depth violation',depth=depth))
        h.update(bytes((pc&255,pc>>8,seq.pc&255,seq.pc>>8,test,cpu.q)))
        if result: h.update(bytes(cpu.ram))
        if isinstance(inputs['carry'],dict):h.update(bytes((2 if carry_input.previous is None else carry_input.previous,)))
        if pc in writes:
            w=writes[pc];value=result[w.get('source','y')] if result else w.get('value',0)
            io_count+=1
            if io_count<=trace_limit and 'io.jsonl' in sinks:
                record=dict(cycle=cycle,pc=pc,address=w['address'],value=value,status=w['status'],evidence=w['evidence'])
                sinks['io.jsonl'].write(json.dumps(record,sort_keys=True)+'\n')
        if trace_count<trace_limit or (pc in routine_entries and pc not in routine_samples):
            record=dict(cycle=cycle,pc=pc,raw=r['raw'],command=c,test=test,branch=branch,dispatch_entry=entry,
                stack_before=before,stack_after=dict(sp=seq.sp,depth=depth,values=seq.stack[:]),next_pc=seq.pc,
                registers={str(i):v for i,v in enumerate(cpu.ram) if mode=='integrated' and old_ram[i]!=v},q=cpu.q,alu=result)
            if isinstance(inputs['carry'],dict):record['carry_in']=carry
            if pc in routine_entries and pc not in routine_samples: routine_samples[pc]=record
            if trace_count<trace_limit:
                trace_count+=1
                if 'trace.jsonl' in sinks: sinks['trace.jsonl'].write(json.dumps(record,sort_keys=True)+'\n')
    used={r['pc'] for r in rows if not r['unused']};coverage=len(used&visited.keys())/len(used)
    summary=dict(mapping=mapping['name'],mapping_digest=digest(mapping),scenario=scenario['name'],scenario_digest=digest(scenario),
        rom_hashes={c:hashlib.sha256(data).hexdigest() for c,data in lanes.items()},am27s31_hash=rom_hash,mode=mode,seed=seed,
        requested_cycles=cycles,completed_cycles=completed,stop=stop,coverage=coverage,visited=sorted(visited),
        address_counts=dict(visited),uncovered=sorted(used-visited.keys()),edge_counts={f'{a:03x}->{b:03x}':n for (a,b),n in sorted(edges.items())},
        stack=dict(max_depth=maximum,final_depth=depth,reads=stack_reads,writes=stack_writes,underflows=underflows,overflows=overflows),
        unused_word_executions=unused,assumption_counts=dict(assumptions),events=events,dispatch_counts=dict(dispatch_counts),
        register_changes=register_changes,routine_samples=routine_samples,io_writes=io_count,trace_digest=h.hexdigest(),final_state=dict(pc=seq.pc,sp=seq.sp,stack=seq.stack,ram=cpu.ram,q=cpu.q),
        clean=completed==cycles and not(underflows or overflows),
        interpretation='Runs under declared assumptions; neither recovered wiring nor verified Nokia execution.')
    if isinstance(inputs['carry'],dict):
        summary['carry_model']=dict(previous=carry_input.previous,counts=dict(carry_input.counts))
    if out:
        out=Path(out);out.mkdir(parents=True,exist_ok=True);save(out/'summary.json',summary)
        save(out/'mapping.json',mapping);save(out/'scenario.json',scenario)

    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mapping',type=Path,required=True);p.add_argument('--scenario',type=Path,required=True)
    p.add_argument('--mode',choices=['sequencer','integrated'],default='sequencer')
    p.add_argument('--cycles',type=int,default=1000000);p.add_argument('--seed',type=int,default=0)
    p.add_argument('--trace-limit',type=int,default=1000);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();s=execute(read(a.mapping),read(a.scenario),a.cycles,a.seed,a.mode,a.out,a.trace_limit)
    print(json.dumps({k:s[k] for k in ('completed_cycles','coverage','stop','clean')}))

if __name__=='__main__': main()
