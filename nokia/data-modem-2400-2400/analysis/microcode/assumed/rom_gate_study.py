"""Fit small ROM-read predicates to explicit labels, then execute their global effects."""
import argparse
import hashlib
import shutil
import tempfile
from collections import Counter
from pathlib import Path
from common import HERE, decode, load, read, save
from execute import execute
from defined_condition_fit import load_trace
from output_control_study import candidates, activates
from sine_operand_study import scenario_for_phase
from rom_study import load_rom


def search(config,lanes):
    tested=0;fits=[]
    for terms in candidates(config):
        tested+=1
        if all(activates(terms,lanes,p) for p in config['positive']) and not any(activates(terms,lanes,p) for p in config['negative']):
            fits.append(dict(terms=list(terms),pcs=[p for p in range(1024) if activates(terms,lanes,p)]))
    for fit in fits:
        fit['minimal']=not any(set(map(tuple,other['terms']))<set(map(tuple,fit['terms'])) for other in fits)
    return tested,fits


def observe(trace,summary,rom,phase):
    output=[];first_terminal=None;reads=[]
    for row in trace:
        if 0x392<=row['pc']<=0x395 and len(output)<4:output.append(row['alu']['y'])
        if row['pc']==0x84 and first_terminal is None:first_terminal=row['cycle']
        event=row.get('external_read',{})
        if 'address' in event and event['selected_by_alu']:
            reads.append(dict(cycle=row['cycle'],pc=row['pc'],address=event['address'],value=event['value']))
    first=2*(5+rom[256+phase]);expected=[first&255,first>>8,2,0]
    return dict(clean=summary['clean'],stop=summary['stop'],unused=summary['unused_word_executions'],
        expected_output=expected,first_output=output,output_matches=output==expected,
        first_terminal=first_terminal,selected_rom_reads=reads,
        total_rom_reads=sum(summary['rom_reads']['address_counts'].values()),
        final_state=summary['final_state'],trace_digest=summary['trace_digest'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/rom-gate-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'rom-gate-study.json');lanes=load();rom=load_rom(config)
    mapping=read(HERE/config['profiles']['q3']);rows=decode(mapping)
    tested,fits=search(config,lanes);runs=[];witnesses=[];counts=Counter()
    owners={bit:[name for name,field in mapping['fields'].items() if isinstance(field['bits'],list) and bit in [token.lstrip('!') for token in field['bits']]] for bit in ('11.4','18.5')}
    with tempfile.TemporaryDirectory() as temporary:
        out=Path(temporary)/'run'
        for i,fit in enumerate(fits):
            fit['id']=i
            fit['d_selected_pcs']=[p for p in fit['pcs'] if rows[p]['i']&7 in (5,6,7)]
            for phase in (range(65) if len(fit['terms'])<=2 else config['probe_phases']):
                scenario=scenario_for_phase(config,'q3',phase)
                assert set(map(int,scenario['io']['read']['pc_sequences']))==set(config['negative'])
                scenario['name']=f'raw-bit ROM gate {i} phase {phase}'
                scenario['io']['read']['address'].update(pcs=fit['pcs'],evidence=config['evidence']+f' Compiled terms: {fit["terms"]}')
                summary=execute(mapping,scenario,config['cycles'],mode='integrated',out=out,trace_limit=config['cycles'])
                trace=load_trace(out);finding=observe(trace,summary,rom,phase)
                case=dict(gate=i,phase=phase,**finding);runs.append(case)
                outcome='terminal_match' if finding['clean'] and finding['output_matches'] and finding['first_terminal'] is not None else 'other'
                counts[outcome]+=1
                if phase in config['probe_phases'] and (len(fit['terms'])<=2 or i in config['witness_gate_ids']):
                    name=f'gate-{i}-phase-{phase}'
                    shutil.copytree(out,args.out/name,dirs_exist_ok=True)
                    witnesses.append(dict(path=name,gate=i,phase=phase,trace_digest=summary['trace_digest']))
            print('gate',i,'checked',flush=True) if i%32==0 else None
    phase32=[r for r in runs if r['phase']==32]
    runtime_diversity=dict(phase=32,selected_read_signatures=len({tuple((e['pc'],e['address'],e['value']) for e in r['selected_rom_reads']) for r in phase32}),
        final_ram_states=len({tuple(r['final_state']['ram']) for r in phase32}))
    sources=[Path(__file__),HERE/'rom-gate-study.json',HERE/'output_control_study.py',HERE/'sine_operand_study.py',HERE/'paired_components_study.py',HERE/'handler_timing_study.py',HERE/'selector_prefix_study.py',HERE/'rom_study.py',HERE/'execute.py',HERE/'common.py',HERE/'defined_condition_fit.py',HERE.parent/'model.py',HERE/config['scenario'],HERE/config['tables'],HERE/config['profiles']['q3']]
    save(args.out/'report.json',dict(configuration=config,tested=tested,fits=fits,runs=runs,witnesses=witnesses,
        counts=dict(counts),runtime_diversity=runtime_diversity,field_owners=owners,distinct_activation_sets=len({tuple(f['pcs']) for f in fits}),
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}))
    print(dict(tested=tested,fits=len(fits),counts=dict(counts)))


if __name__=='__main__':main()
