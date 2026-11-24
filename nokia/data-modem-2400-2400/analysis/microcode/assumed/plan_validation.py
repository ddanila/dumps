"""Refresh execution acceptance while reporting remaining plan interpretation work."""
import argparse
import hashlib
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor,as_completed
from pathlib import Path
from common import HERE,read,save,decode
from execute import execute
from defined_condition_fit import load_trace


def preserved_inputs(config):
    verified={}
    for location in config['input_manifests']:
        manifest=HERE/location;content=read(manifest)
        entries=content.get('chips',content.get('images',[content]))
        for entry in entries:
            path=manifest.parent/entry['file']
            actual=hashlib.sha256(path.read_bytes()).hexdigest()
            assert actual==entry['sha256'],str(path)
            verified[str(path.resolve().relative_to(HERE.parents[3]))]=actual
    return verified


def long_job(job,out):
    base=HERE/job['base'] if 'base' in job else None
    mapping_path=base/'mapping.json' if base else HERE/job['mapping']
    scenario_path=base/'scenario.json' if base else HERE/job['scenario']
    mapping,scenario=read(mapping_path),read(scenario_path)
    path=out/job['name']
    result=execute(mapping,scenario,job['cycles'],job['seed'],job['mode'],path,256)
    replay=execute(mapping,scenario,job['cycles'],job['seed'],job['mode'],trace_limit=256)
    prefix_equal=None
    if base:
        prefix_equal=load_trace(path)==load_trace(base)[:256]
    return dict(name=job['name'],summary=result,replay_equal=replay==result,
                saved_prefix_equal=prefix_equal,
                source_sha256={str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (mapping_path,scenario_path)})


def acceptance(long_runs,sweep,minimum_coverage):
    clean=all(r['summary']['clean'] and r['summary']['completed_cycles']==r['summary']['requested_cycles']
              and r['summary']['stack']['max_depth']<=4 and r['summary']['unused_word_executions']==0 for r in long_runs)
    stable=all(r['replay_equal'] and r['saved_prefix_equal'] is not False for r in long_runs)
    seq=sum(r['summary']['completed_cycles'] for r in long_runs if r['summary']['mode']=='sequencer')
    integrated=sum(r['summary']['completed_cycles'] for r in long_runs if r['summary']['mode']=='integrated')
    coverage=len(sweep['visited'])/1021
    return dict(long_runs_clean=clean,full_replays_equal=stable,sequencer_cycles=seq,integrated_cycles=integrated,
        sweep_coverage=coverage,execution_acceptance_met=bool(long_runs) and clean and stable and seq>=1000000
        and integrated>=2000000 and sweep['all_clean'] and coverage>=minimum_coverage)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/plan-validation')
    parser.add_argument('--workers',type=int,default=3)
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    if args.workers<1:parser.error('workers must be positive')
    config=read(HERE/'plan-validation.json')
    preserved=preserved_inputs(config)
    # Re-run the actual field/window/scoring code, not just a cached manifest.
    analysis_out=args.out/'analysis-replay'
    subprocess.run([sys.executable,str(HERE/'analyze.py'),'--out',str(analysis_out)],check=True)
    analysis_files=sorted(p.name for p in analysis_out.iterdir() if p.is_file())
    assert all((analysis_out/name).read_bytes()==(HERE/'results'/name).read_bytes() for name in analysis_files)
    # Re-generate the annotated listing; this also replays its five gap witnesses.
    reading_out=args.out/'reading-replay'
    subprocess.run([sys.executable,str(HERE/'program_reading.py'),'--out',str(reading_out)],check=True)
    for name in ('listing.csv','catalog.json'):
        assert (reading_out/name).read_bytes()==(HERE/'results/program-reading'/name).read_bytes()
    catalog=read(reading_out/'catalog.json')
    interface_out=args.out/'interface-replay'
    subprocess.run([sys.executable,str(HERE/'frame_dac_bridge.py'),'--out',str(interface_out)],check=True)
    interface_base=(HERE/config['interface_report']).parent
    interface_files=sorted(str(p.relative_to(interface_out)) for p in interface_out.rglob('*') if p.is_file())
    assert interface_files==sorted(str(p.relative_to(interface_base)) for p in interface_base.rglob('*') if p.is_file())
    for name in interface_files:assert (interface_out/name).read_bytes()==(interface_base/name).read_bytes(),name
    interface=read(interface_out/'report.json')
    complete=[r for r in interface['runs'] if r['microcode_started']]
    incomplete=[r for r in interface['runs'] if not r['microcode_started']]
    assert len(complete)==6 and len(incomplete)==4 and all(r['latch'] is None for r in incomplete)
    interface_evidence=dict(files_reproduced=interface_files,completed_transactions=len(complete),
        rejected_incomplete_transfers=len(incomplete),diagnostic_connection_only=True,
        recurring_dac_periods=sorted({r['finding']['classification']['repeat']['period'] for r in complete}),
        autonomous_phase_advance=False,controller_feedback=False)
    variants={}
    for name,path in read(HERE/'program-reading.json')['profiles'].items():
        mapping=read(HERE/path);rows=decode(mapping)
        assert len(rows)==1024 and all(0<=r['i']<512 and 0<=r['a']<16 and 0<=r['b']<16 for r in rows)
        assert all(f['status'] in ('hypothesis','stub','recovered-from-data') and f.get('evidence') for f in mapping['fields'].values())
        variants[name]=dict(words=len(rows),mapping=path,source_sha256=hashlib.sha256((HERE/path).read_bytes()).hexdigest())
    mapping,scenario=read(HERE/config['sequencer_mapping']),read(HERE/config['sequencer_scenario'])
    reference=read(HERE/config['sweep_reference']);visited=set();sweep_runs=[]
    for seed in range(config['sweep_seeds']):
        result=execute(mapping,scenario,config['sweep_cycles'],seed,'sequencer',trace_limit=0)
        expected=next(r for r in reference['runs'] if r['seed']==seed)
        assert result['trace_digest']==expected['trace_digest'] and result['stack']==expected['stack']
        visited.update(result['visited']);sweep_runs.append(dict(seed=seed,clean=result['clean'],trace_digest=result['trace_digest']))
    assert sorted(visited)==reference['reached']
    sweep=dict(visited=sorted(visited),all_clean=all(r['clean'] for r in sweep_runs),runs=sweep_runs)
    print('Analysis, six layouts, annotated listing and 128-seed sweep verified',flush=True)
    results={}
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures=[pool.submit(long_job,job,args.out) for job in config['long_runs']]
        for future in as_completed(futures):
            result=future.result();results[result['name']]=result
            print(result['name'],result['summary']['completed_cycles'],'replay equal',result['replay_equal'],flush=True)
    ordered=[results[job['name']] for job in config['long_runs']]
    finding=acceptance(ordered,sweep,config['minimum_coverage'])
    missing=[dict(entry=e['entry'],callers=e['callers']) for e in catalog['direct_call_entries'] if not e['annotations']]
    historical=read(HERE/'results/suite.json')
    sources=[Path(__file__),HERE/'plan-validation.json',HERE/'frame_dac_bridge.py',HERE/'frame-dac-bridge.json',HERE/config['interface_report'],HERE.parent/'PLAN.md',HERE/'analyze.py',HERE/'program_reading.py',
        HERE/'program-reading.json',HERE/config['catalog'],HERE/config['sequencer_mapping'],HERE/config['sequencer_scenario'],
        HERE/config['sweep_reference'],HERE/'results/suite.json',HERE/'execute.py',HERE/'external_line.py',HERE/'common.py',
        HERE/'defined_condition_fit.py',HERE.parent/'model.py',*(HERE/p for p in config['input_manifests'])]
    save(args.out/'report.json',dict(configuration=config,preserved_inputs=preserved,analysis_files_reproduced=analysis_files,variants=variants,
        long_runs=ordered,sweep=sweep,execution_acceptance=finding,interface_evidence=interface_evidence,
        interpretation_audit=dict(annotated_used_words=catalog['counts']['annotated_used_words'],
            used_words=1021,direct_call_entries=len(catalog['direct_call_entries']),unannotated_direct_entries=missing,
            full_plan_complete=False,reason='Routine and branch/case interpretation remains incomplete. The verified controller-to-DAC transaction is an explicit one-way diagnostic hypothesis, not recovered board function.'),
        historical_suite=dict(acceptance_met=historical['acceptance_met'],coverage=historical['aggregate_sequencer_coverage'],
                              completed_cycles=sum(r['completed_cycles'] for r in historical['runs'].values())),
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}))
    assert finding['execution_acceptance_met'],finding
    print('Current execution acceptance passed; full plan remains incomplete',flush=True)


if __name__=='__main__':main()
