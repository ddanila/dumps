"""Connect handler-4 bank-200 continuations to nested input and terminal stores."""
import argparse
import hashlib
import shutil
import tempfile
from pathlib import Path
from common import HERE,read,save
from execute import execute
from defined_condition_fit import load_trace
from handler_timing_study import scenario_for_case
from handler_reply_study import prestate


def scenario_for(config,code,index,payload,load,add,subtract):
    h=read(HERE/config['handler_configuration']);s=scenario_for_case(h,'q3','previous','plp',code)
    s.update(name=f'handler4 bank c={code:02x} i={index} p={payload:02x} l={load:02x} a={add:02x} b={subtract:02x}',evidence=config['evidence'])
    s['dispatch']['value']=index
    s['io']['read']['pc_sequences'].update({str(pc):[v] for pc,v in ((0x225,payload),(0x2ec,load),(0x28e,add),(0x293,subtract))})
    return s


def prediction(code,index,payload,load,add,subtract):
    assert code%8==4 and 7<=index<=15
    short=index==11
    ram=[0]*16;ram[0]=payload>>1;ram[2]=(payload+1)&255
    ram[3]=(-code-2)&255 if short else (payload+add)&255
    ram[4]=3 if short else (load+1)&255
    ram[5]=((-payload)&255)>>1;ram[12]=code+1 if short else 0
    ram[14]=1;ram[15]=2 if short else (payload-subtract+1)&255
    ram[index]=payload>>1
    return dict(ram=ram,q=payload,first_terminal=(130-int(payload==0) if short else 174 if index==12 else 183),
        target=0x217 if short else 0x2cb if index==12 else 0x200)


def inspect(trace,summary,code,index,payload,load,add,subtract):
    want=prediction(code,index,payload,load,add,subtract)
    assert summary['clean'] and not summary['unused_word_executions']
    assert summary['final_state']['ram']==want['ram'],(code,index,payload,summary['final_state'],want)
    assert summary['final_state']['q']==want['q']
    before=prestate(trace,0x26f);ram=[0]*16
    ram[0]=255;ram[3]=(-code-2)&255;ram[4]=2;ram[12]=code+1;ram[14]=1;ram[15]=2
    assert before['cycle']==92 and before['ram']==ram and before['q']==1 and before['stack']['depth']==0
    at={r['pc']:r for r in trace if r['pc']!=0x84}
    assert at[0x26f]['next_pc']==want['target'] and at[0x21f]['next_pc']==0x225
    assert at[0x225]['q']==payload
    assert next(r['cycle'] for r in trace if r['pc']==0x84)==want['first_terminal']
    assert all(at[pc]['next_pc']==0x8a+index for pc in (0x7e,0x81))
    if index==11:
        assert at[0x217]['next_pc']==0x21a and at[0x219]['next_pc']==0x78
        assert 0x204 not in at and 0x2ec not in at and 0x28e not in at
        assert (0x79 in at)==(payload!=0)
    else:
        assert (0x281 in at)==(index!=12)
        if index!=12:assert at[0x281]['alu']['f']==1 and at[0x286]['next_pc']==0x201
        assert at[0x2cb]['next_pc']==(0x2cc if index==12 else 0x2cd)
        assert (0x2cc in at)==(index==12)
        if index==12:assert at[0x2cc]['next_pc']==0x2cd and at[0x2cc]['alu']['f']==0
        assert at[0x2ce]['next_pc']==0x204
        assert at[0x204]['alu']['f']==0 and at[0x212]['next_pc']==0x2ec
        assert at[0x2f6]['next_pc']==0x3bb and at[0x2ff]['next_pc']==0x213
        assert at[0x21a]['alu']['f']==(load+1)&255
        assert at[0x28e]['alu']['f']==(payload+add)&255
        assert at[0x295]['alu']['f']==(payload-subtract+1)&255
        assert at[0x291]['alu']['f']==payload and at[0x216]['alu']['f']==255
        assert 0x79 in at
    assert summary['stack']['max_depth']==3 and summary['stack']['final_depth']==0
    return want


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,default=HERE/'results/handler4-bank');args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'handler4-bank.json');h=read(HERE/config['handler_configuration']);mapping=read(HERE/h['profiles']['q3']);runs=[];witnesses=[]
    with tempfile.TemporaryDirectory() as temp:
        out=Path(temp)
        for code in range(4,256,8):
            for index in range(7,16):
                for payload in (0,1,128,255):
                    for load,add,subtract in ((0,0,0),(1,255,128),(255,128,255)):
                        values=(code,index,payload,load,add,subtract);s=scenario_for(config,*values)
                        summary=execute(mapping,s,config['cycles'],mode='integrated',out=out,trace_limit=config['cycles'])
                        want=inspect(load_trace(out),summary,*values)
                        case=dict(code=code,index=index,payload=payload,load=load,add=add,subtract=subtract,prediction=want,trace_digest=summary['trace_digest']);runs.append(case)
                        if load==0 and ((code==4 and index in (7,11,12) and payload in (0,255)) or (code==252 and index in (14,15) and payload==255)):
                            name=f'{code:02x}-{index}-p-{payload:02x}';shutil.copytree(out,args.out/name,dirs_exist_ok=True);witnesses.append(dict(path=name,**case))
            if code in (4,252):print(f'{code:02x}: nine dispatch indices checked',flush=True)
    sources=[Path(__file__),HERE/'handler4-bank.json',HERE/'handler_reply_study.py',HERE/'execute.py',HERE/'external_line.py',HERE/'common.py',HERE/'defined_condition_fit.py',HERE/'handler_timing_study.py',HERE/'selector_prefix_study.py',HERE.parent/'model.py',HERE/config['handler_configuration'],HERE/h['profiles']['q3'],HERE/h['scenario'],HERE/h['tables']]
    save(args.out/'report.json',dict(configuration=config,reset_cases=len(runs),runs=runs,witnesses=witnesses,source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}))
    print(len(runs),'reset cases;',len(witnesses),'witnesses',flush=True)


if __name__=='__main__':main()
