"""Time the controller frame-bit gate against the candidate DAC sample clock."""

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from main_loop_timer1_segment2 import CORE, HERE, ROM, ROOT, compile_probe, generated_source

GATE = HERE / 'results/controller-a2-latch-gate.json'
CONTROLLER_TICKS_PER_DAC_SAMPLE = 104


def instrument(source):
    old = 'static void sfr_write(struct em8051 *c,uint8_t address) {'
    new = (old + '\n'
           '    static unsigned frame_byte_index, previous_third=256, pending, old_third, new_third, p1_bit;')
    if source.count(old) != 1:
        raise ValueError(('sfr callback changed', source.count(old)))
    source = source.replace(old, new)
    old = 'if(address==0x99) {'
    new = (old + '\n'
           '        if(frame_byte_index++%4==2) {\n'
           '            unsigned value=c->mSFR[REG_SBUF];\n'
           '            if(previous_third!=256 && ((previous_third^value)&1))\n'
           '                {pending=1;old_third=previous_third;new_third=value;}\n'
           '            previous_third=value;\n'
           '        }')
    if source.count(old) != 1:
        raise ValueError(('SBUF callback changed', source.count(old)))
    source = source.replace(old, new)
    old = '        tx_due=cycle+8;'
    new = (old + '\n'
           '    } else if(address==0x90) {\n'
           '        unsigned now=(c->mSFR[REG_P1]>>2)&1;\n'
           '        if(now && !p1_bit && pending) {\n'
           '            fprintf(stderr,"L %u %02X %02X %02X\\n",'
           'cycle,c->mLowerData[0x34],old_third,new_third);\n'
           '            pending=0;\n'
           '        }\n'
           '        p1_bit=now;')
    if source.count(old) != 1:
        raise ValueError(('completion callback changed', source.count(old)))
    source = source.replace(old, new)
    return source


def run(out=HERE / 'results/controller-a2-latch-gate-timing.json'):
    gate = json.loads(GATE.read_text())
    if any(row['active_high_A1_A3_A4_low_A2_frame_bits'] != [[2, 0]]
           for row in gate['controller_cases']):
        raise ValueError('A2 bit gate changed')
    source, _ = generated_source()
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        exe = compile_probe(instrument(source), Path(temporary), True)
        for selector in (0x40, 0x60):
            process = subprocess.run(
                [str(exe), str(ROM), str(selector), '10000', '1'],
                capture_output=True, text=True, check=True)
            execution = json.loads(process.stdout)
            if execution['errors']:
                raise ValueError(('controller run errors', selector))
            events = []
            for line in process.stderr.splitlines():
                kind, cycle, state, old, new = line.split()
                if kind != 'L':
                    raise ValueError(('unexpected controller event', line))
                events.append(dict(cycle=int(cycle), state=state,
                                   old_third=old, new_third=new,
                                   gate_before=int(old, 16) & 1,
                                   gate_after=int(new, 16) & 1))
            falls = [event for event in events
                     if event['state'] == 'A2' and event['gate_after'] == 0]
            rises = [event for event in events
                     if event['state'] == 'A3' and event['gate_after'] == 1]
            if len(falls) != 1 or len(rises) != 1:
                raise ValueError(('A2 latch transitions changed', selector, events))
            fall, rise = falls[0], rises[0]
            ticks = rise['cycle'] - fall['cycle']
            if ticks < 50000 or ticks > 70000:
                raise ValueError(('A2 gate duration changed', selector, ticks))
            cases.append(dict(selector=f'{selector:02X}',
                              gate_events=events,
                              a2_gate_fall=fall,
                              a3_gate_rise=rise,
                              held_controller_ticks=ticks,
                              held_candidate_dac_samples=ticks /
                              CONTROLLER_TICKS_PER_DAC_SAMPLE,
                              tested_short_dac_hold_samples=64))
    paths = [Path(__file__), GATE, HERE / 'main_loop_timer1_segment2.py',
             HERE / 'main_loop_probe.c', ROM,
             *(CORE / name for name in ('core.c', 'opcodes.c', 'disasm.c', 'emu8051.h'))]
    report = dict(
        status='The candidate controller latch-enable bit stays low across the A2 interval for hundreds of modeled DAC sample periods.',
        fixture=dict(controller='unchanged 8031 ROM under Timer1 harness',
                     frame_latch_event='P1.2 rising edge after fourth mode-0 SBUF byte under synthetic eight-tick serial completion',
                     clock_ratio='14.4 MHz / 1500 DAC cycles per sample = 9600 samples/s; 11.9808 MHz / 12 = 998400 controller ticks/s; exactly 104 controller ticks per DAC sample',
                     controller_ticks_per_candidate_dac_sample=CONTROLLER_TICKS_PER_DAC_SAMPLE,
                     ram15='held positive at PC1000; source untraced'),
        cases=cases,
        limitations=[
            'The CD4094 cascade-to-74LS373 C/LE connection is untraced.',
            'The controller and DSC clocks are related by assumed dividers; the probe does not co-simulate both devices.',
            'Eight-tick SBUF completion is synthetic, so physical frame-latch timing and sample phase remain unverified.',
            'The earlier DAC screen held the output for only 64 samples; this event screen projects the controller interval under the clock hypothesis, not a new long PROM execution.'],
        source_sha256={str(path.relative_to(ROOT)):
                       hashlib.sha256(path.read_bytes()).hexdigest() for path in paths})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    return report


if __name__ == '__main__':
    for case in run()['cases']:
        print(case['selector'], case['a2_gate_fall'], case['a3_gate_rise'],
              case['held_controller_ticks'], case['held_candidate_dac_samples'])
