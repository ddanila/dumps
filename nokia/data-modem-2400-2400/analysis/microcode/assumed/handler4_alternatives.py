"""Explain handler-4 alternate preparation, Q additions and direct terminal path."""
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


def scenario_for(config,code,index,alternate,d,u,v):
    h=read(HERE/config['handler_configuration']);s=scenario_for_case(h,'q3','previous','plp',code)
    s.update(name=f'handler4 alternatives c={code:02x} i={index} alt={int(alternate)} d={d:02x} u={u:02x} v={v:02x}',evidence=config['evidence'])
    s['dispatch']['value']=index
    s['condition']['sources'][5]='external';s['condition']['polarity'][5]=0
    s['inputs']['external']=dict(mode='cycle-events',initial=1,events=[[70,0]] if alternate else [],status='stub',evidence=config['evidence'])
    s['io']['read']['pc_sequences'].update({str(pc):[value] for pc,value in ((0x25d,d),(0x235,u),(0xed,v))})
    return s


def prediction(code,index,alternate,d,u,v):
    assert code%8==4 and index in (3,4,5,6)
    adds=index in (3,6);q=d if alternate else 1;p=(q+u+v)&255 if adds else q
    entry=[0]*16;entry[0]=255;entry[3]=code+1 if alternate else (-code-2)&255
    entry[4]=(q+1)&255;entry[12]=code+1;entry[14]=(-code)&255 if alternate else 1;entry[15]=0 if alternate else 2
    ram=entry[:];ram[0]=p>>1;ram[2]=(p+1)&255;ram[5]=((-p)&255)>>1
    if adds:ram[3]=255;ram[15]=0
    ram[index]=p>>1
    return dict(ram=ram,q=p,entry_ram=entry,entry_q=q,entry_cycle=81 if alternate else 92,
        first_terminal=(148 if adds else 118)-11*alternate-int(p==0),adds=adds)


def inspect(trace,summary,code,index,alternate,d,u,v):
    want=prediction(code,index,alternate,d,u,v)
    assert summary['clean'] and not summary['unused_word_executions']
    assert summary['final_state']['ram']==want['ram'],(code,index,alternate,d,u,v,summary['final_state'],want)
    assert summary['final_state']['q']==want['q']
    entry=prestate(trace,0x26f)
    assert entry['ram']==want['entry_ram'] and entry['q']==want['entry_q'] and entry['cycle']==want['entry_cycle']
    assert entry['stack']['depth']==0
    at={r['pc']:r for r in trace if r['pc']!=0x84}
    assert at[0x264]['cycle']==70 and at[0x264]['next_pc']==(0x265 if alternate else 0x2a0)
    assert (0x265 in at)==alternate
    if alternate:
        assert at[0x265]['alu']['f']==code+1
        assert at[0x266]['alu']['f']==code and at[0x266]['alu']['carry']==1
        assert at[0x267]['alu']['f']==(-code)&255 and at[0x268]['alu']['f']==1
    if want['adds']:
        assert at[0x26f]['next_pc']==0x230 and at[0x237]['next_pc']==0x251
        assert at[0x235]['q']==(want['entry_q']+u)&255
        assert at[0x255]['next_pc']==0xeb and at[0xeb]['alu']['f']==255 and at[0xec]['alu']['f']==0
        assert at[0xed]['q']==want['q']
        assert at[0xf2]['next_pc']==0xf3 and at[0xf5]['next_pc']==0xf6 and at[0xf9]['next_pc']==0x28b
        assert at[0x28b]['alu']['f']==255 and at[0x28d]['next_pc']==0x78
    else:
        assert at[0x26f]['next_pc']==0x280 and at[0x280]['next_pc']==0x78 and 0x235 not in at and 0xed not in at
    assert (0x79 in at)==(want['q']!=0)
    assert all(at[pc]['next_pc']==0x8a+index for pc in (0x7e,0x81))
    assert next(r['cycle'] for r in trace if r['pc']==0x84)==want['first_terminal']
    assert summary['stack']['max_depth']==3 and summary['stack']['final_depth']==0
    return want


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,default=HERE/'results/handler4-alternatives');args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'handler4-alternatives.json');h=read(HERE/config['handler_configuration']);mapping=read(HERE/h['profiles']['q3']);runs=[];witnesses=[]
    triples=((0,0,0),(1,0,0),(255,1,0),(128,255,128),(255,255,255),(0,255,0),(255,0,1),(1,127,128))
    with tempfile.TemporaryDirectory() as temp:
        out=Path(temp)
        for code in range(4,256,8):
            for index in (3,4,5,6):
                for d,u,v in triples:
                    prefix=None
                    for alternate in (False,True):
                        values=(code,index,alternate,d,u,v);s=scenario_for(config,*values)
                        summary=execute(mapping,s,config['cycles'],mode='integrated',out=out,trace_limit=config['cycles']);trace=load_trace(out)
                        want=inspect(trace,summary,*values)
                        if prefix is None:prefix=trace[:70]
                        else:
                            for actual,old in zip(trace[:70],prefix):
                                for k in ('pc','next_pc','alu','q','registers','stack_after'):assert actual[k]==old[k]
                        case=dict(code=code,index=index,alternate=alternate,d=d,u=u,v=v,prediction=want,trace_digest=summary['trace_digest']);runs.append(case)
                        if code==4 and ((d,u,v)==(0,0,0) and index in (3,4)) or code==252 and (d,u,v)==(255,0,1) and index in (5,6):
                            name=f'{code:02x}-{index}-alt-{int(alternate)}';shutil.copytree(out,args.out/name,dirs_exist_ok=True);witnesses.append(dict(path=name,**case))
            if code in (4,252):print(f'{code:02x}: four indices and both preparation paths checked',flush=True)
    sources=[Path(__file__),HERE/'handler4-alternatives.json',HERE/'handler_reply_study.py',HERE/'execute.py',HERE/'external_line.py',HERE/'common.py',HERE/'defined_condition_fit.py',HERE/'handler_timing_study.py',HERE/'selector_prefix_study.py',HERE.parent/'model.py',HERE/config['handler_configuration'],HERE/h['profiles']['q3'],HERE/h['scenario'],HERE/h['tables']]
    save(args.out/'report.json',dict(configuration=config,reset_cases=len(runs),paired_prefix_checks=len(runs)//2,runs=runs,witnesses=witnesses,source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}))
    print(len(runs),'reset cases;',len(witnesses),'witnesses',flush=True)


if __name__=='__main__':main()
