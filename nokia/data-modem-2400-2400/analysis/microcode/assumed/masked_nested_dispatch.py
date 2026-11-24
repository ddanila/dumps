"""Drive both nested dispatches from a reset-loaded nonzero input mask under q3."""
import argparse
import copy
import hashlib
import shutil
import tempfile
from collections import Counter
from pathlib import Path
from common import HERE, read, save, decode, table_targets
from execute import execute
from defined_condition_fit import load_trace
from model import Am2901
from rom_study import load_rom


def scenario_for(config,a,b,outer='q',inner='q'):
    scenario=copy.deepcopy(read(HERE/config['scenario']))
    scenario['name']=f'masked nested dispatch {a:02x}&{b:02x} {outer}/{inner}'
    scenario['evidence']=config['evidence']
    scenario['io']['read']['pc_sequences'].update({str(0x107):[0],str(0x2e0):[a],str(0x2e1):[b]})
    scenario['io']['read']['evidence']=config['evidence']
    for pc,source in ((0x21f,outer),(0x2c4,inner)):
        scenario['dispatch']['tables'][str(pc)].update(index_source=source,evidence=config['evidence'])
    scenario['dispatch']['initial_y']=0
    return scenario


def check_mask(rows,a,b):
    cpu=Am2901(logic_flags=True);cpu.ram[0]=255
    before=cpu.ram[:]
    for pc,d in ((0x2e0,a),(0x2e1,b)):
        row=rows[pc];assert row['carry']==row['carry_select']==0
        cpu.step(row['i'],row['a'],row['b'],d,0,0,0)
    assert cpu.q==a&b and cpu.ram==before
    row=rows[0x2e2];assert row['carry']==row['carry_select']==0
    result=cpu.step(row['i'],row['a'],row['b'],0,0,0,0)
    assert (result['f'],result['y'],result['carry'])==(255,255,0)
    assert cpu.q==a&b and cpu.ram==before
    return cpu.q


def inspect(trace,scenario,mask):
    ram=[0]*16;q=0;events=[]
    for row in trace:
        pc=row['pc']
        if pc==0x2e1:assert row['q']==mask
        if pc==0x21f:
            assert q==mask and row['alu']['y']==0
            source=scenario['dispatch']['tables'][str(pc)]['index_source']
            expected=0 if source=='y' else mask
            assert row['dispatch_input']==expected
            assert row['next_pc']==table_targets(scenario['dispatch']['tables'][str(pc)])[expected%82]
        if pc==0x2c4:
            assert q==mask and ram[0]==mask>>1 and ram[2]==ram[5]==0
            assert ram[4]==((204+mask)&255)>>1
            source=scenario['dispatch']['tables'][str(pc)]['index_source']
            expected=0 if source=='y' else mask
            assert row['dispatch_input']==expected
            assert row['next_pc']==table_targets(scenario['dispatch']['tables'][str(pc)])[expected%64]
        if pc in (0x2e0,0x2e1,0x21e,0x21f,0x2bc,0x2c3,0x2c4,0x2c5,0x220,0x2ff):
            events.append(dict(pc=pc,cycle=row['cycle'],before=dict(ram=ram[:],q=q),
                y=row['alu']['y'],index=row.get('dispatch_input'),entry=row['dispatch_entry'],
                next_pc=row['next_pc'],depth=row['stack_before']['depth']))
        for register,value in row['registers'].items():ram[int(register)]=value
        q=row['q']
    assert len([e for e in events if e['pc']==0x21f])==1
    return events


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/masked-nested-dispatch')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'masked-nested-dispatch.json');mapping=read(HERE/config['mapping']);rows=decode(mapping)
    rom=load_rom(config);template=scenario_for(config,0,255)
    for pc in (0x21f,0x2c4):
        table=template['dispatch']['tables'][str(pc)];lookup=table['lookup']
        assert table_targets(table)==[lookup['bank']+v for v in rom[lookup['offset']:lookup['offset']+lookup['count']]]
    targets=table_targets(template['dispatch']['tables'][str(0x21f)])
    mask_counts=Counter();nested_masks=[m for m in range(256) if targets[m%82]==0x2bc]
    for a in range(256):
        for b in range(256):mask_counts[check_mask(rows,a,b)]+=1
    assert nested_masks==[81,163,245]
    runs=[];controls=[];witnesses=[]
    with tempfile.TemporaryDirectory() as temporary:
        out=Path(temporary)/'run'
        cases=[(m,'q','q') for m in range(256)]
        cases += [(m,outer,inner) for m in nested_masks for outer,inner in (('previous_y','q'),('y','q'),('q','previous_y'),('q','y'))]
        for mask,outer,inner in cases:
            scenario=scenario_for(config,mask,255,outer,inner)
            summary=execute(mapping,scenario,config['cycles'],seed=config['seed'],mode='integrated',out=out,trace_limit=config['cycles'])
            assert summary['clean'] and not summary['unused_word_executions']
            trace=load_trace(out);events=inspect(trace,scenario,mask)
            nested=any(e['pc']==0x2bc for e in events)
            assert nested==(mask in nested_masks and outer!='y')
            case=dict(mask=mask,outer=outer,inner=inner,nested=nested,events=events,
                      first_terminal=next((r['cycle'] for r in trace if r['pc']==0x84),None),
                      max_depth=summary['stack']['max_depth'],trace_digest=summary['trace_digest'])
            assert case['first_terminal'] is not None
            (runs if outer==inner=='q' else controls).append(case)
            if mask in nested_masks:
                name=f'mask-{mask:02x}-{outer}-{inner}'
                shutil.copytree(out,args.out/name,dirs_exist_ok=True)
                witnesses.append(dict(path=name,mask=mask,outer=outer,inner=inner,trace_digest=summary['trace_digest']))
    sources=[Path(__file__),HERE/'masked-nested-dispatch.json',HERE/config['scenario'],HERE/config['mapping'],HERE/'execute.py',HERE/'common.py',HERE/'defined_condition_fit.py',HERE/'rom_study.py',HERE.parent/'model.py']
    save(args.out/'report.json',dict(configuration=config,mask_checks=65536,mask_counts=dict(mask_counts),nested_masks=nested_masks,
        independent_pairs_selecting_nested=sum(mask_counts[m] for m in nested_masks),runs=runs,controls=controls,witnesses=witnesses,
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}))
    print(dict(reset_runs=len(runs)+len(controls),nested_masks=nested_masks,independent_pairs=sum(mask_counts[m] for m in nested_masks)))


if __name__=='__main__':main()
