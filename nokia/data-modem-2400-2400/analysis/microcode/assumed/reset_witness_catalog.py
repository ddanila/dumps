"""Replay and index reset witnesses for words outside the default graph."""
import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from common import HERE, decode, digest, read, save
from analyze import graph
from execute import execute

ARTIFACTS=('mapping.json','scenario.json','summary.json','trace.jsonl','io.jsonl')


def verify_witness(entry, profiles):
    """Reject stale/mixed artifacts and replay all register, flag, stack and I/O data."""
    if entry['status']!='hypothesis' or not entry.get('limitations') or not (HERE/entry['evidence']).is_file():
        raise ValueError('witness lacks hypothesis provenance or limitations')
    if entry['profile'] not in profiles:
        raise ValueError('unknown witness profile')
    directory=HERE/entry['path']
    mapping=read(directory/'mapping.json');scenario=read(directory/'scenario.json');summary=read(directory/'summary.json')
    if mapping!=read(HERE/profiles[entry['profile']]):
        raise ValueError('witness mapping differs from named profile')
    if scenario.get('initial')!=dict(pc=0,ram=[0]*16,q=0):
        raise ValueError('witness must start from zero reset')
    if (not summary['clean'] or summary['mode']!='integrated' or summary['unused_word_executions']
        or summary['stack']['underflows'] or summary['stack']['overflows']):
        raise ValueError('witness must be a clean integrated run')
    if summary['mapping_digest']!=digest(mapping) or summary['scenario_digest']!=digest(scenario):
        raise ValueError('witness input digests disagree')
    trace=[json.loads(line) for line in (directory/'trace.jsonl').read_text().splitlines()]
    cycles=summary['completed_cycles']
    if cycles!=summary['requested_cycles'] or len(trace)!=cycles:
        raise ValueError('incomplete witness trace')
    if not trace or trace[0]['pc']!=0 or [t['cycle'] for t in trace]!=list(range(cycles)):
        raise ValueError('witness trace is not continuous from reset')
    with tempfile.TemporaryDirectory() as temporary:
        out=Path(temporary)
        execute(mapping,scenario,cycles,seed=summary['seed'],mode='integrated',out=out,trace_limit=cycles)
        for filename in ARTIFACTS:
            if (out/filename).read_bytes()!=(directory/filename).read_bytes():
                raise ValueError(f'witness replay mismatch: {filename}')
    return summary,trace


def build_catalog(manifest_path=HERE/'reset-witnesses.json'):
    manifest_path=Path(manifest_path);config=read(manifest_path)
    rows=decode(read(HERE/'sequencer.json'));cfg=graph(rows,read(HERE/config['baseline_scenario']))
    if cfg['exceptions']:raise ValueError('baseline graph has exceptions')
    targets={r['pc'] for r in cfg['unreachable']};entries={f'{p:03X}':[] for p in sorted(targets)}
    summaries=[];ids=set()
    sources={manifest_path,HERE/'reset_witness_catalog.py',HERE/'execute.py',HERE/'common.py',HERE/'analyze.py',HERE.parent/'model.py',HERE/'sequencer.json',HERE/config['baseline_scenario']}
    for entry in config['witnesses']:
        if entry['id'] in ids:raise ValueError('duplicate witness id')
        ids.add(entry['id']);summary,trace=verify_witness(entry,config['profiles'])
        ram=[0]*16;q=0;first={}
        for t in trace:
            pc=t['pc']
            if pc in targets and pc not in first:
                first[pc]=dict(witness=entry['id'],profile=entry['profile'],cycle=t['cycle'],
                    before=dict(ram=ram[:],q=q,stack_depth=t['stack_before']['depth']),
                    next_pc=f"{t['next_pc']:03X}",test=t['test'])
                entries[f'{pc:03X}'].append(first[pc])
            for k,v in t['registers'].items():ram[int(k)]=v
            q=t['q']
        if not first:raise ValueError('witness covers no target words')
        if ram!=summary['final_state']['ram'] or q!=summary['final_state']['q']:
            raise ValueError('trace state reconstruction disagrees with summary')
        if {t['pc'] for t in trace}!=set(summary['visited']):
            raise ValueError('trace and summary coverage disagree')
        witness_graph=graph(decode(read(HERE/entry['path']/'mapping.json')),read(HERE/entry['path']/'scenario.json'))
        summaries.append(dict(**entry,cycles=summary['completed_cycles'],max_stack_depth=summary['stack']['max_depth'],
            conservative_graph_words=len(witness_graph['reached']),conservative_graph_exceptions=witness_graph['exceptions'],
            first_084_cycle=next((t['cycle'] for t in trace if t['pc']==0x84),None),
            final_pc=f"{summary['final_state']['pc']:03X}",targets=[f'{p:03X}' for p in sorted(first)],
            trace_digest=summary['trace_digest'],mapping_digest=summary['mapping_digest'],scenario_digest=summary['scenario_digest']))
        sources.update(HERE/entry['path']/name for name in ARTIFACTS)
        sources.update((HERE/entry['evidence'],HERE/config['profiles'][entry['profile']]))
    missing=[pc for pc,visits in entries.items() if not visits]
    if missing:raise ValueError('missing reset witnesses: '+', '.join(missing))
    return dict(configuration=config,baseline_words=len(cfg['reached']),target_words=len(targets),
        witness_count=len(summaries),entries=entries,witnesses=summaries,
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(sources)},
        interpretation='Every default-graph gap has a replayed clean zero-reset witness under a named mapping and scenario. This is a union of incompatible hypotheses, not single-model coverage, a safe default gate, physical wiring recovery or full-plan completion.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/reset-witness-catalog')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    report=build_catalog();save(args.out/'report.json',report)
    print('verified witnesses',report['witness_count'],'default gaps covered',report['target_words'])


if __name__=='__main__':main()
