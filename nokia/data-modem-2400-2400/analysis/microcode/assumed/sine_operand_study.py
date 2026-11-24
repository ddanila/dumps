"""Trace a site-selected actual quarter-sine ROM read through paired arithmetic."""
import argparse
import copy
import hashlib
import math
import shutil
import tempfile
from pathlib import Path
from common import HERE, read, save
from execute import execute
from defined_condition_fit import load_trace
from paired_components_study import scenario_for, inspect
from rom_study import load_rom


def scenario_for_phase(config,profile,phase):
    scenario=scenario_for(config,profile,5,1,0)
    scenario['name']=f'site-selected sine operand {profile} phase={phase}'
    policy=scenario['io']['read']
    del policy['pc_sequences'][str(0x317)]
    policy['pc_sequences'][str(0x316)]=[(phase-5)&255]
    policy.update(expected_sha256=config['rom_sha256'],address=dict(source='previous_y',bank=256,
        initial_y=0,pcs=[0x317],status='hypothesis',evidence=config['evidence']))
    return scenario


def inspect_phase(trace,scenario,profile,phase,rom):
    index=phase if profile=='q3' else 0
    byte=rom[256+index]
    finding=inspect(trace,scenario,profile,byte+5,1,0)
    reads=[r for r in trace if 'address' in r.get('external_read',{})]
    assert len(reads)==1
    row=reads[0];read_event=row['external_read']
    assert row['pc']==0x317 and read_event['address']==256+index and read_event['value']==byte
    assert read_event['selected_by_alu']==(profile=='q3')
    previous=trace[row['cycle']-1]
    assert previous['pc']==0x316 and previous['alu']['y']==index
    assert finding['outcome']=='terminal' and finding['first_terminal']==110
    return dict(phase=phase,rom_address=256+index,rom_byte=byte,rom_read_cycle=row['cycle'],
        address_load_cycle=previous['cycle'],first_output_cycle=finding['outputs'][0]['cycle'],
        expected_pairs=finding['expected_pairs'],preserved_components=finding['preserved_components'],
        first_terminal=finding['first_terminal'],selected_by_alu=read_event['selected_by_alu'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/sine-operand-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'sine-operand-study.json');rom=load_rom(config)
    assert list(rom[256:321])==[round(127*math.sin(math.pi*i/128)) for i in range(65)]
    runs=[];witnesses=[];controls=[]
    with tempfile.TemporaryDirectory() as temporary:
        out=Path(temporary)/'run'
        for profile,path in config['profiles'].items():
            mapping=read(HERE/path)
            for phase in (range(65) if profile=='q3' else (0,32,64)):
                scenario=scenario_for_phase(config,profile,phase)
                result=execute(mapping,scenario,160,mode='integrated',out=out,trace_limit=160)
                assert result['clean'] and not result['unused_word_executions']
                trace=load_trace(out);finding=inspect_phase(trace,scenario,profile,phase,rom)
                assert result['rom_reads']['address_counts']=={finding['rom_address']:1}
                assert result['rom_reads']['selected_by_alu']==int(profile=='q3')
                case=dict(profile=profile,trace_digest=result['trace_digest'],**finding)
                runs.append(case)
                if phase in (0,32,64):
                    name=f'{profile}-{phase:02x}'
                    shutil.copytree(out,args.out/name,dirs_exist_ok=True)
                    witnesses.append(dict(path=name,**case))
                    if profile=='q3':
                        stub=copy.deepcopy(scenario);policy=stub['io']['read']
                        del policy['address'];del policy['expected_sha256']
                        policy['pc_sequences'][str(0x317)]=[0]
                        stub['name']=f'zero input counterfactual phase={phase}'
                        check=execute(mapping,stub,160,mode='integrated',out=out,trace_limit=160)
                        assert check['clean'] and not check['unused_word_executions']
                        alternative=load_trace(out);other=inspect(alternative,stub,profile,5,1,0)
                        assert alternative[:finding['rom_read_cycle']]==trace[:finding['rom_read_cycle']]
                        assert finding['expected_pairs'][0]-other['expected_pairs'][0]==2*finding['rom_byte']
                        name=f'zero-control-{phase:02x}'
                        shutil.copytree(out,args.out/name,dirs_exist_ok=True)
                        controls.append(dict(path=name,phase=phase,expected_pairs=other['expected_pairs'],
                            trace_digest=check['trace_digest'],output_difference=2*finding['rom_byte']))
    sources=[Path(__file__),HERE/'sine-operand-study.json',HERE/'paired_components_study.py',HERE/'handler_timing_study.py',HERE/'selector_prefix_study.py',HERE/'rom_study.py',HERE/'execute.py',HERE/'common.py',HERE/'defined_condition_fit.py',HERE.parent/'model.py',HERE/config['scenario'],HERE/config['tables'],*(HERE/p for p in config['profiles'].values())]
    save(args.out/'report.json',dict(configuration=config,runs=runs,witnesses=witnesses,zero_controls=controls,
        rom_sha256=hashlib.sha256(rom).hexdigest(),source_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}))
    print('68 ROM scenarios and 3 zero-input controls verified',flush=True)


if __name__=='__main__':main()
