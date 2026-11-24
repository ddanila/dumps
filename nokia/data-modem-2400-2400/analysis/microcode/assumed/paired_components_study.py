"""Follow independently supplied nonzero components through handler 5 from reset."""
import argparse
import copy
import hashlib
import shutil
import tempfile
from pathlib import Path
from common import HERE, read, save
from execute import execute
from defined_condition_fit import load_trace
from handler_timing_study import scenario_for_case, classify


def scenario_for(config,profile,u,v,entry):
    scenario=scenario_for_case(config,profile,'previous','plp',5)
    scenario['name']=f'paired components {profile} U={u:02X} V={v:04X} entry={entry}'
    scenario['io']['read']['pc_sequences'].update({str(0x317):[(u-5)&255],
        str(0x118):[(v+1)&255],str(0x107):[((v>>8)+1)&255],
        str(0x38e):[entry],str(0x36d):[0]})
    scenario['dispatch']['tables'][str(0x38f)]['index_source']='previous_y'
    return scenario


def inspect(trace,scenario,profile,u,v,entry):
    first=u if profile=='q3' else 0
    expected=[2*first if entry in (0,3) else 0,(2*v)&65535 if entry in (0,1) else 0]
    output=[expected[0]&255,expected[0]>>8,expected[1]&255,expected[1]>>8]
    start=0x392+4*entry
    ram=[0]*16;outputs=[];dispatches=0;entry_state=None;loads=[]
    for row in trace:
        pc=row['pc']
        if pc==0x317:
            assert row['external_read']['value']==(u-5)&255
            assert row['external_read']['selected_by_alu']==(profile=='q3')
            assert row['alu']['f']==first
            loads.append(dict(cycle=row['cycle'],pc=pc,input=row['external_read']['value'],value=first))
        if pc==0x38f:
            assert ram[4:12]==[first,0,v&255,v>>8,first,0,v&255,v>>8]
            assert row['dispatch_input']==entry and row['next_pc']==start
            assert row['q']==5
            dispatches+=1
            if entry_state is None:entry_state=dict(cycle=row['cycle'],ram=ram[:],q=row['q'])
        if start<=pc<start+4:
            assert row['alu']['f']==row['alu']['y']==output[pc-start]
            assert not row['registers'] and row['q']==5
            if len(outputs)<4:outputs.append(dict(pc=pc,cycle=row['cycle'],value=row['alu']['y'],carry=row['alu']['carry']))
        if pc==0x390:
            assert row['test']==int(expected[1]>>8!=0)
        for register,value in row['registers'].items():ram[int(register)]=value
    assert len(loads)==1 and dispatches and len(outputs)==4
    assert ram[8:12]==[first,0,v&255,v>>8]
    finding=classify(trace,scenario)
    releases=expected[1]>>8==0
    assert (finding['outcome']=='terminal')==releases
    assert finding['repeat']['period']==(1 if releases else 12)
    if releases:assert finding['first_terminal']==110
    return dict(expected_pairs=expected,outputs=outputs,input_load=loads[0],entry_state=entry_state,
                preserved_components=ram[8:12],**finding)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/paired-components-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'paired-components-study.json');runs=[];witnesses=[];controls=[]
    with tempfile.TemporaryDirectory() as temporary:
        out=Path(temporary)/'run'
        for profile,path in config['profiles'].items():
            mapping=read(HERE/path)
            for u in (range(256) if profile=='q3' else config['control_u']):
                for v in config['v_values']:
                    for entry in range(4):
                        scenario=scenario_for(config,profile,u,v,entry)
                        result=execute(mapping,scenario,config['cycles'],mode='integrated',out=out,trace_limit=config['cycles'])
                        assert result['clean'] and not result['unused_word_executions']
                        trace=load_trace(out);finding=inspect(trace,scenario,profile,u,v,entry)
                        case=dict(profile=profile,u=u,v=v,entry=entry,trace_digest=result['trace_digest'],
                            expected_pairs=finding['expected_pairs'],outcome=finding['outcome'],
                            first_terminal=finding['first_terminal'],period=finding['repeat']['period'])
                        runs.append(case)
                        if u==255 and v in (1,128):
                            name=f'{profile}-{u:02x}-{v:04x}-{entry}'
                            shutil.copytree(out,args.out/name,dirs_exist_ok=True)
                            witnesses.append(dict(path=name,**case,details=finding))
                        if profile=='q3' and u==255 and v==1 and entry==0:
                            # Earlier D reads cannot substitute for the surviving 317 load.
                            for value in (0,255):
                                altered=copy.deepcopy(scenario)
                                for pc in (0x115,0x315):altered['io']['read']['pc_sequences'][str(pc)]=[value]
                                check=execute(mapping,altered,config['cycles'],mode='integrated',out=out,trace_limit=config['cycles'])
                                assert check['clean'] and not check['unused_word_executions']
                                alternative=load_trace(out);again=inspect(alternative,altered,profile,u,v,entry)
                                after=next(i for i,r in enumerate(trace) if r['pc']==0x318)
                                assert alternative[after:]==trace[after:]
                                controls.append(dict(earlier_input=value,unchanged_suffix_cycle=after,trace_digest=check['trace_digest'],expected_pairs=again['expected_pairs']))
            print(profile,'component sweep complete',flush=True)
    sources=[Path(__file__),HERE/'paired-components-study.json',HERE/'handler_timing_study.py',HERE/'selector_prefix_study.py',HERE/'execute.py',HERE/'common.py',HERE/'defined_condition_fit.py',HERE.parent/'model.py',HERE/config['scenario'],HERE/config['tables'],*(HERE/p for p in config['profiles'].values())]
    save(args.out/'report.json',dict(configuration=config,runs=runs,witnesses=witnesses,overwrite_controls=controls,
        source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}))


if __name__=='__main__':main()
