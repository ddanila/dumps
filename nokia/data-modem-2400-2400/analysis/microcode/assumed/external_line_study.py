"""Exercise cycle-timed selector input from reset without PC-specific branch patches."""
import argparse
import hashlib
import shutil
import tempfile
from collections import Counter
from pathlib import Path
from common import HERE,read,save,decode
from execute import execute
from defined_condition_fit import load_trace
from handler_timing_study import scenario_for_case,classify


def scenario_for(config,timing,code,fall_cycle):
    h=read(HERE/config['handler_configuration'])
    scenario=scenario_for_case(h,'q3',timing,'plp' if timing=='previous' else 'blt',code)
    scenario['condition']['sources'][5]='external';scenario['condition']['polarity'][5]=0
    scenario['inputs']['external']=dict(mode='cycle-events',initial=1,events=[[fall_cycle,0]],status='stub',evidence=config['evidence'])
    scenario.update(name=f'q3 handler 3 external line {timing} code {code:02x} falls {fall_cycle}',evidence=config['evidence'])
    return scenario


def inspect(trace,scenario,fall_cycle,timing):
    finding=classify(trace,scenario);pcs={row['pc'] for row in trace}
    assert 0x1ef not in pcs
    tests=[row for row in trace if row['pc']==0x302]
    if 4<=fall_cycle<=43:
        assert len(tests)==1 and tests[0]['cycle']==43 and tests[0]['test']==0
        branch=next(row for row in trace if row['pc']==0x303)
        assert branch['cycle']==44 and branch['test']==0 and branch['alu']['carry']==1
        assert next(row['cycle'] for row in trace if row['pc']==0x370)==74
        assert finding['first_terminal']==109
        ram=scenario['initial']['ram'][:]
        for row in trace:
            for k,v in row['registers'].items():ram[int(k)]=v
        expected=[0]*16;expected[4]=expected[13]=1
        if timing=='current':expected[6]=expected[7]=255
        assert ram==expected and trace[-1]['q']==0
    elif fall_cycle<=3:assert not tests and 0x109 not in pcs
    else:assert len(tests)==1 and tests[0]['test']==1
    for row in trace:
        if 'external_condition' in row:
            event=row['external_condition']
            assert event['value']==int(row['cycle']<fall_cycle)
            assert event['event_index']==(-1 if row['cycle']<fall_cycle else 0)
    return dict(finding=finding,entered_370=0x370 in pcs,entered_1ef=False,
        selector_reads=sum('external_condition' in row for row in trace))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/external-line-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'external-line-study.json');h=read(HERE/config['handler_configuration'])
    mapping=read(HERE/h['profiles']['q3']);rows=decode(mapping);runs=[];witnesses=[];counts=Counter()
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)
        for timing in ('previous','current'):
            for code in range(3,256,8):
                baseline=scenario_for_case(h,'q3',timing,'plp' if timing=='previous' else 'blt',code)
                execute(mapping,baseline,config['cycles'],mode='integrated',out=root/'base',trace_limit=config['cycles'])
                base_trace=load_trace(root/'base')
                assert [(r['cycle'],r['pc']) for r in base_trace[:44] if rows[r['pc']]['select']==5
                    and r['command'] in (0,2,4,6)]==[(3,3),(43,0x302)]
                for fall in config['fall_cycles']:
                    scenario=scenario_for(config,timing,code,fall)
                    summary=execute(mapping,scenario,config['cycles'],mode='integrated',out=root/'run',trace_limit=config['cycles'])
                    assert summary['clean'] and not summary['unused_word_executions']
                    trace=load_trace(root/'run');observed=inspect(trace,scenario,fall,timing)
                    for a,b in zip(trace[:fall],base_trace[:fall]):
                        a=a.copy();a.pop('external_condition',None)
                        assert a==b,(timing,code,fall,a,b)
                    counts[f'{timing}:{fall}:{observed["finding"]["outcome"]}']+=1
                    case=dict(timing=timing,code=code,fall_cycle=fall,trace_digest=summary['trace_digest'],**observed);runs.append(case)
                    if (code==3 and fall in (3,4,43,44)) or (code==251 and fall==40):
                        name=f'{timing}-{code:02x}-fall-{fall:03d}'
                        shutil.copytree(root/'run',args.out/name,dirs_exist_ok=True);witnesses.append(dict(path=name,**case))
            print(timing,'224 reset scenarios verified',flush=True)
    sources=[Path(__file__),HERE/'external-line-study.json',HERE/'external_line.py',HERE/'execute.py',HERE/'common.py',
        HERE/'defined_condition_fit.py',HERE/'handler_timing_study.py',HERE/'selector_prefix_study.py',HERE.parent/'model.py',
        HERE/config['handler_configuration'],HERE/h['profiles']['q3']]
    save(args.out/'report.json',dict(configuration=config,counts=dict(counts),runs=runs,witnesses=witnesses,
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='Timed external selector 5 preserves boot and admits handler-3 double preparation and paired wait from reset. All tested code-3 inputs exclude 1EF through carry at 303. Constant-input histories match before the scheduled edge; no physical timing or port assignment inferred.'))


if __name__=='__main__':main()
