"""Compare timed-condition handler-2 continuations and carry-biased Q drains."""
import argparse
import hashlib
import shutil
import tempfile
from pathlib import Path
from common import HERE,read,save
from execute import execute
from defined_condition_fit import load_trace
from handler2_body import scenario_for as body_scenario,prediction as body_prediction

OFFSETS={'prepare-1b8':0,'prepare-1b9':1,'prepare-1bc':4,'prepare-1bd':5}


def prediction(a,b,payload,delay,u,v,route):
    want=body_prediction(a,b,payload,delay);length=want['qsum'].bit_length()
    first=((u+1)&255) if route=='detour' else u
    poll=(179 if route=='detour' else 180)+2*length+2*(first>>1).bit_length()+2*(v>>1).bit_length()
    if route in OFFSETS:poll+=OFFSETS[route]-4
    want.update(first_poll=poll,first_terminal=poll+32+2*delay,first_drain_input=first,second_drain_input=v)
    return want


def scenario_for(config,code,a,b,payload,delay,u,v,route):
    body=read(HERE/config['body_configuration']);s=body_scenario(body,code,a,b,payload,delay)
    first_branch=134+2*((a+b)&255).bit_length()
    selector=1 if route in OFFSETS else 5
    transition=first_branch+OFFSETS[route] if selector==1 else first_branch+10+int(route=='detour')
    initial=0 if selector==1 else 1
    s.update(name=f'handler2 {route} {code:02x}/{a:02x}/{b:02x}/{payload:02x}/{delay}/{u:02x}/{v:02x}',evidence=config['evidence'])
    s['condition']['sources'][selector]='external';s['condition']['polarity'][selector]=0
    s['inputs']['external']=dict(mode='cycle-events',initial=initial,events=[[transition,1-initial]],status='stub',evidence=config['evidence'])
    s['io']['read']['pc_sequences'].update({str(pc):[value] for pc,value in ((0x1c5,u),(0x2d0,u),(0x1ca,v),(0x2d5,v))})
    return s


def inspect(trace,summary,scenario,a,b,payload,delay,u,v,route):
    want=prediction(a,b,payload,delay,u,v,route)
    assert summary['clean'] and not summary['unused_word_executions']
    assert summary['final_state']['ram']==want['ram'] and summary['final_state']['q']==want['q']
    assert next(r['cycle'] for r in trace if r['pc']==0x1ec)==want['first_poll']
    assert next(r['cycle'] for r in trace if r['pc']==0x84)==want['first_terminal']
    at={r['pc']:r for r in trace if r['pc']!=0x84}
    first,second=(0x2d0,0x2d5) if route=='detour' else (0x1c5,0x1ca)
    assert at[first]['q']==want['first_drain_input'] and at[second]['q']==v
    assert at[first+1]['q']==want['first_drain_input']>>1 and at[second+1]['q']==v>>1
    assert (0x2d0 in at)==(route=='detour') and (0x1c3 in at)==(route!='detour')
    if route in OFFSETS:
        branch=int(route.split('-')[1],16)
        assert at[branch]['next_pc']==0x1da and at[0x1da]['next_pc']==0x341 and at[0x1db]['next_pc']==0x1c3
        assert len([r for r in trace if r['pc']==0x341])==2
    else:
        assert at[0x1c2]['next_pc']==(0x2d0 if route=='detour' else 0x1c3)
        assert 0x1da not in at
    event=scenario['inputs']['external'];cycle,value=event['events'][0]
    for row in trace:
        if 'external_condition' in row:assert row['external_condition']['value']==(event['initial'] if row['cycle']<cycle else value)
    assert summary['stack']['max_depth']==3 and summary['stack']['final_depth']==0
    return want


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,default=HERE/'results/handler2-routes');args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'handler2-routes.json');body=read(HERE/config['body_configuration']);h=read(HERE/body['handler_configuration']);mapping=read(HERE/h['profiles']['q3'])
    runs=[];witnesses=[]
    with tempfile.TemporaryDirectory() as temp:
        out=Path(temp)
        for code in range(2,256,8):
            for route in config['routes']:
                for u in (0,1,128,255):
                    for v in (0,1,128,255):
                        a=code^u;b=v;payload=u^v;delay=(u+v)%3;s=scenario_for(config,code,a,b,payload,delay,u,v,route)
                        result=execute(mapping,s,config['cycles'],mode='integrated',out=out,trace_limit=config['cycles'])
                        want=inspect(load_trace(out),result,s,a,b,payload,delay,u,v,route)
                        case=dict(code=code,route=route,a=a,b=b,payload=payload,delay=delay,u=u,v=v,prediction=want,trace_digest=result['trace_digest']);runs.append(case)
                        if code==2 and u==255 and v==128:
                            shutil.copytree(out,args.out/route,dirs_exist_ok=True);witnesses.append(dict(path=route,**case))
            if code in (2,250):print(f'{code:02x}: six continuations verified',flush=True)
    sources=[Path(__file__),HERE/'handler2-routes.json',HERE/'handler2_body.py',HERE/config['body_configuration'],HERE/'execute.py',HERE/'external_line.py',HERE/'common.py',HERE/'defined_condition_fit.py',HERE/'handler_timing_study.py',HERE/'selector_prefix_study.py',HERE.parent/'model.py',HERE/body['handler_configuration'],HERE/h['profiles']['q3'],HERE/h['scenario'],HERE/h['tables']]
    save(args.out/'report.json',dict(configuration=config,reset_cases=len(runs),runs=runs,witnesses=witnesses,source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}))
    print(len(runs),'reset cases;',len(witnesses),'witnesses',flush=True)


if __name__=='__main__':main()
