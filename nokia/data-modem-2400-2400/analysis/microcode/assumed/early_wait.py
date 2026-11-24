"""Explain the fixed-register early wait and its completing reset entry."""
import argparse
import hashlib
import shutil
import tempfile
from pathlib import Path
from common import HERE,read,save,decode
from execute import execute,CarryInput
from defined_condition_fit import load_trace
from handler_timing_study import scenario_for_case,classify
from model import Am2901


def scenario_for(config,entry,a,b,capture,tail):
    h=read(HERE/config['handler_configuration']);s=scenario_for_case(h,'q3','previous','plp',2)
    s.update(name=f'early boot {entry}/{a:02x}/{b:02x}/{capture:02x}/{tail:02x}',evidence=config['evidence'])
    s['condition']['polarity'][5]=0;s['dispatch']['value']=entry;s['branch_tables']['8']['index_source']='scenario'
    s['io']['read']['pc_sequences'].update({str(pc):[value] for pc,value in ((2,a),(0x76,b),(0x5b,capture),(0x64,tail))})
    return s


def prediction(entry,capture,tail):
    ram=[0]*16;q=[255,255,255,1,127,0,1,255][entry]
    ram[0]=(q+1)&255;ram[4]=(q+capture)&255
    if entry==3:ram[14]=253
    if entry==4:ram[1]=255
    if entry==7:ram[15]=255
    if entry==5:ram[2]=1;ram[3]=(tail-1)&255
    return dict(ram=ram,q=q,first_wait=[24,24,22,38,32,26,30,25][entry],terminal=entry==5)


def inspect(trace,summary,scenario,entry,capture,tail):
    want=prediction(entry,capture,tail)
    assert summary['clean'] and not summary['unused_word_executions']
    assert summary['final_state']['ram']==want['ram'] and summary['final_state']['q']==want['q']
    assert next(r['cycle'] for r in trace if r['pc']==0x5d)==want['first_wait']
    dispatch=next(r for r in trace if r['pc']==8)
    assert dispatch['next_pc']==[9,15,11,19,34,13,50,84][entry]
    finding=classify(trace,scenario)
    if entry==5:
        assert next(r['cycle'] for r in trace if r['pc']==0x84)==44
        assert len([r for r in trace if r['pc']==0x63])==1
        assert summary['stack']['final_depth']==0
    else:
        assert not any(r['pc']==0x64 or r['pc']==0x84 for r in trace)
        assert finding['repeat']['period']==7
    return dict(**want,classification=finding)


def loop_pass(rows,ram,q,d,policy):
    cpu=Am2901(ram=ram[:],q=q,logic_flags=True);carry=CarryInput(policy)
    results=[]
    for pc in range(0x5d,0x64):
        row=rows[pc];result=cpu.step(row['i'],row['a'],row['b'],d,carry.resolve(row),0,0);carry.observe(result);results.append(result)
    expected=ram[:];expected[0]=(q+1)&255;expected[2]=ram[3]
    assert cpu.ram==expected and cpu.q==q
    assert results[-2]['zero']==int(q==ram[3])
    assert results[-1]['zero']==int(((q+ram[3])&255)==0)
    return dict(ram=cpu.ram,q=cpu.q,previous_returns=bool(results[-2]['zero']),current_returns=bool(results[-1]['zero']))


def check_loop(mapping):
    rows=decode(mapping);counts={'previous':0,'current':0}
    config=read(HERE/'early-wait.json');policy=scenario_for(config,0,1,1,1,1)['inputs']['carry']
    for q in range(256):
        for r3 in range(256):
            ram=[(q+13*i)&255 for i in range(16)];ram[3]=r3
            result=loop_pass(rows,ram,q,q^r3,policy)
            counts['previous']+=result['previous_returns'];counts['current']+=result['current_returns']
    assert counts==dict(previous=256,current=256)
    return dict(pairs=65536,returns=counts)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,default=HERE/'results/early-wait');args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'early-wait.json');h=read(HERE/config['handler_configuration']);mapping=read(HERE/h['profiles']['q3'])
    local=check_loop(mapping);print('65536 loop comparisons checked',flush=True)
    runs=[];witnesses=[]
    with tempfile.TemporaryDirectory() as temp:
        out=Path(temp)
        for entry in range(8):
            for a in (0,1,128,255):
                for b in (0,1,128,255):
                    for capture in (0,1,128,255):
                        for tail in (0,1,128,255):
                            s=scenario_for(config,entry,a,b,capture,tail);result=execute(mapping,s,config['cycles'],mode='integrated',out=out,trace_limit=config['cycles'])
                            want=inspect(load_trace(out),result,s,entry,capture,tail)
                            case=dict(entry=entry,a=a,b=b,capture=capture,tail=tail,prediction=want,trace_digest=result['trace_digest']);runs.append(case)
                            if a==255 and b==128 and capture==255 and tail==0:
                                name=f'entry-{entry}';shutil.copytree(out,args.out/name,dirs_exist_ok=True);witnesses.append(dict(path=name,**case))
            print('entry',entry,'verified',flush=True)
    sources=[Path(__file__),HERE/'early-wait.json',HERE/'execute.py',HERE/'external_line.py',HERE/'common.py',HERE/'defined_condition_fit.py',HERE/'handler_timing_study.py',HERE/'selector_prefix_study.py',HERE.parent/'model.py',HERE/config['handler_configuration'],HERE/h['profiles']['q3'],HERE/h['scenario'],HERE/h['tables']]
    save(args.out/'report.json',dict(configuration=config,local=local,reset_cases=len(runs),runs=runs,witnesses=witnesses,source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}))
    print(len(runs),'reset cases;',len(witnesses),'witnesses',flush=True)


if __name__=='__main__':main()
