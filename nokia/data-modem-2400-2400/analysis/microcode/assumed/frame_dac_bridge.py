"""Compose actual controller output execution with an explicitly hypothetical DSP/DAC bridge."""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from common import HERE,read,save
from execute import execute
from defined_condition_fit import load_trace
from handler_timing_study import classify
from sine_operand_study import scenario_for_phase
from rom_study import load_rom
from dac0830 import replay
ANALYSIS=HERE.parent.parent
sys.path.insert(0,str(ANALYSIS))
from interface_study import CORE,ROM,SHA


def latched_frame(result,initial_p1):
    """A submitted fourth byte is insufficient: require completion before the edge."""
    wire=[];completed=[];p1=initial_p1;latched=None
    for event in result['events']:
        if event['kind']=='tx':wire.append(event['value'])
        elif event['kind']=='tx_complete':
            completed.append(event)
            if event['value']!=len(completed) or len(completed)>len(wire):
                raise ValueError('invalid transmit completion ordering')
        elif event['kind']=='p1':
            rising=not p1&4 and event['value']&4;p1=event['value']
            if rising:
                if len(wire)!=4 or len(completed)!=4 or event['cycle']<=completed[-1]['cycle']:
                    raise ValueError('frame latch preceded complete four-byte transfer')
                if latched is not None:raise ValueError('multiple frames outside single-transaction contract')
                latched=dict(wire=wire[:],controller_tick=event['cycle'],latch_pc=event['pc'])
    return latched


def scenario_for_frame(config,wire):
    if config.get('status')!='hypothesis' or not config.get('evidence'):raise ValueError('bridge needs hypothesis provenance')
    if len(wire)!=4 or any(type(v) is not int or not 0<=v<=255 for v in wire) or wire[0]%8!=5:
        raise ValueError('bridge study supports four-byte handler-5 frames')
    sine=read(HERE/config['sine_config']);scenario=scenario_for_phase(sine,'q3',0)
    scenario.update(name='latched controller frame '+bytes(wire).hex(),evidence=config['evidence'])
    policy=scenario['io']['read'];policy['evidence']=config['evidence'];policy['address']['evidence']=config['evidence']
    for pc,index in config['bindings'].items():policy['pc_sequences'][pc]=[wire[index]]
    for pc,value in config['constant_reads'].items():policy['pc_sequences'][pc]=[value]
    return scenario


def inspect_micro(trace,scenario,wire,rom):
    code=wire[0];phase=(code+wire[1])&255;byte=rom[256+phase];u=(byte+code)&255
    v=((wire[2]-1)&255)+(((wire[3]-1)&255)<<8)
    output=[(2*u)&255,(2*u)>>8,(2*v)&255,((2*v)&65535)>>8]
    reads=[r for r in trace if 'address' in r.get('external_read',{})]
    assert len(reads)==1
    assert (reads[0]['pc'],reads[0]['cycle'],reads[0]['external_read']['address'],reads[0]['external_read']['value'])==(0x317,45,256+phase,byte)
    assert reads[0]['external_read']['selected_by_alu'] and reads[0]['alu']['f']==u
    ram=[0]*16;dispatches=0;updates=[]
    for row in trace:
        if row['pc']==0x38f:
            assert ram[4:12]==[u,0,v&255,v>>8,u,0,v&255,v>>8]
            assert row['dispatch_input']==0 and row['next_pc']==0x392 and row['q']==code
            dispatches+=1
        if 0x392<=row['pc']<=0x395:
            assert row['alu']['y']==output[row['pc']-0x392] and not row['registers']
            if row['pc']==0x392:updates.append(row['cycle'])
        for k,value in row['registers'].items():ram[int(k)]=value
    finding=classify(trace,scenario)
    assert output[-1]!=0 and finding['outcome']=='repeat' and finding['repeat']['period']==12
    assert updates==list(range(55,len(trace),12)) and dispatches==len(updates)
    return dict(code=code,phase=phase,quarter_sine=phase<=64,rom_address=256+phase,rom_byte=byte,
        first_component=u,second_component=v,output_bytes=output,update_cycles=updates,classification=finding)


def controller_line(case,delay,completions):
    c=case['fixture']
    payload=bytes([c['state'],*c['previous'],*c['payload'],*c['counters'],*c['patterns'],c['prior_mode']]).hex()
    return f"send {payload} {bytes(c['flags']).hex()} {delay} {completions}\n"


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'results/frame-dac-bridge')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    config=read(HERE/'frame-dac-bridge.json');cc=read(HERE/config['controller_config'])
    sine=read(HERE/config['sine_config']);mapping=read(HERE/sine['profiles']['q3']);rom=load_rom(sine)
    dac_config=read(HERE/config['dac_config']);runs=[];digests={}
    assert hashlib.sha256(ROM.read_bytes()).hexdigest()==SHA
    sources=[ANALYSIS/'interface_probe.c',*(CORE/n for n in ('core.c','opcodes.c','disasm.c'))]
    with tempfile.TemporaryDirectory() as tmp:
        exe=Path(tmp)/'controller-probe'
        subprocess.run(['cc','-O2','-Wall','-DSAT_TRACE','-I',str(CORE),*[str(p) for p in sources],'-o',str(exe)],check=True)
        for case in config['frames']:
            schedules=[(delay,4) for delay in config['completion_delays']]+[(8,n) for n in config['incomplete_counts']]
            for delay,completions in schedules:
                line=controller_line(case,delay,completions)
                result=json.loads(subprocess.run([str(exe),str(ROM),str(cc['initial_p1']),'0',str(cc['cycle_limit']),
                    str(cc['return_sentinel']),str(cc['initial_sp'])],input=line,text=True,capture_output=True,check=True).stdout)
                assert result['errors']==0
                latch=latched_frame(result,cc['initial_p1'])
                run=dict(frame=case['name'],delay=delay,completions=completions,controller=result,latch=latch)
                if completions<4:
                    assert latch is None and not result['reached_stop']
                    assert result['pc']=={0:0x8b0,3:0x8d4}[completions]
                    run.update(microcode_started=False,dac_register=None);runs.append(run);continue
                assert result['reached_stop'] and result['pc']==0x1ee8 and result['sp']==cc['initial_sp']
                assert latch['wire']==case['expected_wire'] and latch['latch_pc']==0x8d7
                wire=latch['wire'];scenario=scenario_for_frame(config,wire);out=args.out/case['name']
                summary=execute(mapping,scenario,config['microcode_cycles'],mode='integrated',out=out,trace_limit=config['microcode_cycles'])
                assert summary['clean'] and not summary['unused_word_executions']
                trace=load_trace(out);finding=inspect_micro(trace,scenario,wire,rom)
                if case['name'] in digests:assert summary['trace_digest']==digests[case['name']]
                digests[case['name']]=summary['trace_digest']
                dac=replay(trace,dac_config,'first_low','per_load')
                transfers=[e for e in dac['events'] if e['action']=='transfer-open']
                assert [e['cycle'] for e in transfers]==finding['update_cycles']
                assert all(e['dac_register']==finding['output_bytes'][0] for e in transfers)
                start=latch['controller_tick']*config['timing']['microcycles_per_controller_tick']+config['timing']['start_latency']
                times=[start+e['cycle'] for e in transfers]
                save(out/'dac.json',dac)
                run.update(microcode_started=True,microcode_path=case['name'],microcode_digest=summary['trace_digest'],
                    microcode_start_time=start,update_times=times,dac_register=dac['dac_register'],finding=finding)
                runs.append(run)
    root=ANALYSIS.parents[2]
    sources += [CORE/'emu8051.h',Path(__file__),HERE/'frame-dac-bridge.json',HERE/'dac0830.py',HERE/config['dac_config'],
        HERE/config['controller_config'],HERE/config['controller_evidence'],HERE/'execute.py',HERE/'external_line.py',HERE/'common.py',
        HERE/'handler_timing_study.py',HERE/'defined_condition_fit.py',HERE/'selector_prefix_study.py',HERE/'paired_components_study.py',
        HERE/'sine_operand_study.py',HERE/config['sine_config'],HERE/'rom_study.py',HERE/sine['profiles']['q3'],HERE.parent/'model.py',ROM]
    save(args.out/'report.json',dict(configuration=config,runs=runs,controller_rom_sha256=SHA,
        source_sha256={str(p.resolve().relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        interpretation='Explicit one-way diagnostic connection, not recovered board wiring: actual controller build/transmit, completion-qualified latch, one zero-reset microcode run, actual ROM operand, recurring paired-output loop and hypothetical DAC load/transfer. Constant held output codes, no phase advance or controller feedback.'))
    print('6 completed controller-to-DAC hypotheses and 4 incomplete-transfer controls verified')


if __name__=='__main__':main()
