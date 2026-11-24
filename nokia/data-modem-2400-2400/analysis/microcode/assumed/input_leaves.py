"""Connect outer input-load and comparison-return leaves to complete reset paths."""
import argparse
import hashlib
import shutil
import tempfile
from pathlib import Path
from common import HERE,read,save,decode,table_targets
from execute import execute
from defined_condition_fit import load_trace
from handler_timing_study import scenario_for_case
from handler_reply_study import prestate
from rom_study import load_rom
from model import Am2901

LOAD_INDICES=(0,82,164,246)
PRESERVE_INDICES=(16,32,48,64,80,98,114,130,146,162,180,196,212,228,244)


def prediction(code,d,u,p,source='previous_y'):
    assert code%8==4 and d in LOAD_INDICES+PRESERVE_INDICES and source in ('q','previous_y','y')
    load=source=='y' or d in LOAD_INDICES;q=p if load else d
    ram=[0]*16;ram[0]=ram[11]=q>>1;ram[2]=(q+1)&255;ram[3]=ram[12]=code+1
    ram[4]=(d+2)&255;ram[5]=((-q)&255)>>1;ram[14]=(-code)&255
    return dict(ram=ram,q=q,load=load,target=0x221 if load else 0x2b3,first_terminal=126-int(p==0) if load else 125)


def scenario_for(config,code,d,u,p,source='previous_y'):
    h=read(HERE/config['handler_configuration']);s=scenario_for_case(h,'q3','previous','plp',code)
    s.update(name=f'input leaves {code:02x}/{d:02x}/{u:02x}/{p:02x}/{source}',evidence=config['evidence'])
    s['dispatch']['value']=11;s['dispatch']['tables'][str(0x21f)]['index_source']=source
    s['condition']['sources'][5]='external';s['condition']['polarity'][5]=0
    s['inputs']['external']=dict(mode='cycle-events',initial=1,events=[[70,0]],status='stub',evidence=config['evidence'])
    s['io']['read']['pc_sequences'].update({str(pc):[value] for pc,value in ((0x25d,d),(0x221,u),(0x225,p))})
    return s


def inspect(trace,summary,code,d,u,p,source='previous_y'):
    want=prediction(code,d,u,p,source)
    assert summary['clean'] and not summary['unused_word_executions']
    assert summary['final_state']['ram']==want['ram'] and summary['final_state']['q']==want['q']
    at={r['pc']:r for r in trace if r['pc']!=0x84};entry=prestate(trace,0x21f)
    assert at[0x264]['next_pc']==0x265 and at[0x26f]['next_pc']==0x217
    assert entry['cycle']==88 and entry['q']==d and entry['ram'][0]==255 and entry['ram'][2]==0 and entry['ram'][4]==(d+2)&255
    assert at[0x21f]['dispatch_input']==(0 if source=='y' else d) and at[0x21f]['next_pc']==want['target']
    assert at[0x21f]['stack_before']['depth']==1 and at[0x21f]['stack_after']['depth']==2
    if want['load']:
        assert at[0x221]['q']==u and at[0x225]['q']==p
        assert at[0x223]['next_pc']==0x228 and at[0x223]['stack_after']['depth']==3
        assert [at[pc]['alu']['y'] for pc in (0x228,0x229,0x22a)]==[u,(u+1)&255,(u-1)&255]
        assert at[0x22a]['next_pc']==0x224 and at[0x227]['next_pc']==0x220
        assert 0x2b9 not in at
    else:
        assert at[0x2b7]['alu']['carry']==0 and at[0x2b8]['next_pc']==0x2b9
        assert [at[pc]['alu']['y'] for pc in (0x2b9,0x2ba,0x2bb)]==[0,0,0]
        assert at[0x2bb]['next_pc']==0x220 and at[0x2bb]['stack_before']['depth']==2 and at[0x2bb]['stack_after']['depth']==1
        assert 0x225 not in at and 0x227 not in at
    assert at[0x220]['next_pc']==0x218 and at[0x219]['next_pc']==0x78
    assert (0x79 in at)==(want['q']!=0)
    assert next(r['cycle'] for r in trace if r['pc']==0x84)==want['first_terminal']
    assert summary['stack']['max_depth']==3 and summary['stack']['final_depth']==0
    return want


def check_guard(mapping):
    rows=decode(mapping);fallthrough=0
    for a in range(256):
        for q in range(256):
            ram=[(i*37+11)&255 for i in range(16)];ram[0]=a;ram[2]=a^q
            cpu=Am2901(ram=ram[:],q=q,logic_flags=True)
            row=rows[0x2b7];guard=cpu.step(row['i'],row['a'],row['b'],1,1,0,0)
            assert guard['carry']==int(q>=a)
            row=rows[0x2b8];cpu.step(row['i'],row['a'],row['b'],1,guard['carry'],0,0)
            if not guard['carry']:
                fallthrough+=1
                for pc in (0x2b9,0x2ba,0x2bb):
                    row=rows[pc];value=cpu.step(row['i'],row['a'],row['b'],1,0,0,0)
                    assert value['y']==ram[2]
            assert cpu.ram==ram and cpu.q==q
    assert fallthrough==32640
    return dict(guard_pairs=65536,fallthrough_pairs=fallthrough)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,default=HERE/'results/input-leaves');args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'input-leaves.json');h=read(HERE/config['handler_configuration']);mapping=read(HERE/h['profiles']['q3']);runs=[];witnesses=[];controls=[]
    table=scenario_for(config,4,0,0,0)['dispatch']['tables'][str(0x21f)];rom=load_rom(config);lookup=table['lookup'];targets=table_targets(table)
    assert targets==[lookup['bank']+v for v in rom[lookup['offset']:lookup['offset']+lookup['count']]]
    assert tuple(d for d in range(256) if targets[d%len(targets)]==0x221)==LOAD_INDICES
    assert tuple(d for d in range(256) if targets[d%len(targets)]==0x2b3)==PRESERVE_INDICES
    arithmetic=check_guard(mapping);print(arithmetic,flush=True)
    with tempfile.TemporaryDirectory() as temp:
        out=Path(temp)
        for code in range(4,256,8):
            for d in LOAD_INDICES+PRESERVE_INDICES:
                for u,p in ((0,0),(1,255),(255,1),(128,128)):
                    s=scenario_for(config,code,d,u,p);result=execute(mapping,s,config['cycles'],mode='integrated',out=out,trace_limit=config['cycles']);want=inspect(load_trace(out),result,code,d,u,p)
                    case=dict(code=code,d=d,u=u,p=p,prediction=want,trace_digest=result['trace_digest']);runs.append(case)
                    selected=(code==4 and ((d in (0,246) and (u,p) in ((0,0),(255,1))) or (d in (16,244) and u==0))) or (code==252 and ((d==246 and u==255) or (d==244 and u==0)))
                    if selected:
                        name=f'{code:02x}-d-{d:02x}-u-{u:02x}';shutil.copytree(out,args.out/name,dirs_exist_ok=True);witnesses.append(dict(path=name,**case))
            if code in (4,252):print(f'{code:02x}: all nineteen selecting bytes checked',flush=True)
        for d in (0,16,82,244,246):
            for source in ('q','y'):
                s=scenario_for(config,4,d,255,128,source);result=execute(mapping,s,config['cycles'],mode='integrated',out=out,trace_limit=config['cycles']);want=inspect(load_trace(out),result,4,d,255,128,source)
                controls.append(dict(d=d,source=source,prediction=want,trace_digest=result['trace_digest']))
    sources=[Path(__file__),HERE/'input-leaves.json',HERE/'rom_study.py',HERE/'handler_reply_study.py',HERE/'execute.py',HERE/'external_line.py',HERE/'common.py',HERE/'defined_condition_fit.py',HERE/'handler_timing_study.py',HERE/'selector_prefix_study.py',HERE.parent/'model.py',HERE/config['handler_configuration'],HERE/h['profiles']['q3'],HERE/h['scenario'],HERE/h['tables']]
    save(args.out/'report.json',dict(configuration=config,arithmetic=arithmetic,reset_cases=len(runs),index_source_controls=controls,runs=runs,witnesses=witnesses,source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}))
    print(len(runs),'reset cases;',len(controls),'source controls;',len(witnesses),'witnesses',flush=True)


if __name__=='__main__':main()
