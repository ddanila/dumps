"""Compare declared DAC byte-routing/buffering hypotheses on actual sine traces."""
import argparse
import csv
import hashlib
import itertools
import shutil
import tempfile
from pathlib import Path
from common import HERE,read,save
from execute import execute
from defined_condition_fit import load_trace
from sine_operand_study import scenario_for_phase,inspect_phase
from rom_study import load_rom
from dac0830 import DAC0830,replay


def check_controls():
    cases=0
    for levels in itertools.product((0,1),repeat=5):
        pins=dict(zip(('ile','cs_n','wr1_n','wr2_n','xfer_n'),levels))
        for data in range(256):
            dac=DAC0830(165,90);result=dac.drive(data,**pins)
            expected_input=data if levels[:3]==(1,0,0) else 165
            expected_dac=expected_input if levels[3:]==(0,0) else 90
            assert result['input_register']==expected_input and result['dac_register']==expected_dac
            cases+=1
    return cases


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/dac-output-study')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'dac-output-study.json');sine=read(HERE/config['sine_config']);rom=load_rom(sine)
    baseline=read(HERE/config['baseline_report'])
    expected_digests={r['phase']:r['trace_digest'] for r in baseline['runs'] if r['profile']=='q3'}
    mapping=read(HERE/sine['profiles']['q3']);cases=check_controls();runs=[];phase_rows=[];witnesses=[]
    with tempfile.TemporaryDirectory() as temporary:
        for phase in range(65):
            out=Path(temporary)/'run';scenario=scenario_for_phase(sine,'q3',phase)
            result=execute(mapping,scenario,160,mode='integrated',out=out,trace_limit=160)
            assert result['clean'] and result['trace_digest']==expected_digests[phase]
            trace=load_trace(out);finding=inspect_phase(trace,scenario,'q3',phase,rom)
            byte=finding['rom_byte'];word=2*(byte+5)
            expected=dict(rom_sum=byte+5,first_low=word&255,first_high=word>>8,all_four=0)
            phase_rows.append(dict(phase=phase,rom_byte=byte,paired_word=word,**expected))
            if phase in config['witness_phases']:
                name=f'phase-{phase:02d}';shutil.copytree(out,args.out/name,dirs_exist_ok=True);witnesses.append(name)
            for route in config['routes']:
                for mode in config['transfer_modes']:
                    got=replay(trace,config,route,mode)
                    assert got['input_register']==expected[route]
                    assert got['dac_register']==(None if mode=='load_only' else expected[route])
                    updates=[e for e in got['events'] if e['action']=='transfer-open']
                    if mode=='terminal':assert len(updates)==1 and updates[0]['cycle']==110
                    elif mode=='load_only':assert not updates
                    else:
                        assert [e['cycle'] for e in updates]==([45] if route=='rom_sum' else [55] if route=='first_low' else [56] if route=='first_high' else [55,56,57,58])
                    runs.append(dict(phase=phase,route=route,transfer=mode,input_register=got['input_register'],
                        dac_register=got['dac_register'],updates=[dict(cycle=e['cycle'],code=e['dac_register']) for e in updates]))
                    if phase in config['witness_phases']:
                        save(args.out/f'phase-{phase:02d}'/f'dac-{route}-{mode}.json',got)
    drops=[dict(from_phase=a['phase'],to_phase=b['phase'],before=a['first_low'],after=b['first_low'])
           for a,b in zip(phase_rows,phase_rows[1:]) if b['first_low']<a['first_low']]
    assert drops==[dict(from_phase=53,to_phase=54,before=254,after=0)]
    with (args.out/'phase-codes.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(phase_rows[0]));writer.writeheader();writer.writerows(phase_rows)
    sources=[Path(__file__),HERE/'dac0830.py',HERE/'dac-output-study.json',HERE/config['sine_config'],
        HERE/config['baseline_report'],HERE/config['photo'],HERE/'sine_operand_study.py',HERE/'paired_components_study.py',
        HERE/'handler_timing_study.py',HERE/'selector_prefix_study.py',HERE/'rom_study.py',HERE/'execute.py',HERE/'common.py',
        HERE/'defined_condition_fit.py',HERE.parent/'model.py',HERE/sine['scenario'],HERE/sine['tables'],HERE/sine['profiles']['q3']]
    save(args.out/'report.json',dict(configuration=config,control_cases=cases,core_replays=65,sink_cases=len(runs),
        first_low_drops=drops,runs=runs,witnesses=witnesses,
        source_sha256={str(p.relative_to(HERE.parent.parent.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='Explicit hypothetical DAC sink, not recovered wiring. First-low route drops 254 to 0 at phase 54; first-high is only 0/1; all-four ends at 0; ROM-sum route retains S+5. Loading alone leaves output unknown. Transfer timing changes when DAC code updates without altering any microcode trace.'))
    print(f'{cases} control cases, 65 unchanged core traces, {len(runs)} hypothetical sink cases verified',flush=True)


if __name__=='__main__':main()
