"""Replay A3/A4 under Timer 1 interrupts with the separate R5 gate held positive."""

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from state_transitions import CORE, HERE, ROM, ROM_SHA, ROOT

sys.path.insert(0, str(HERE.parents[1]))
from controller_scrambler import transform
from controller_segment2_pattern import source_windows, standard_bits

FORCED = HERE / 'results/main-loop-long.json'


def generated_source():
    source = (HERE / 'main_loop_probe.c').read_text()
    changes = [
        ('wanted>12', 'wanted>10000'),
        ('cycle<200000', 'cycle<10000000'),
        ('static unsigned cycle, pc, errors, tx_due, tx_count, write_count, status_value;',
         'static unsigned cycle, pc, errors, tx_due, tx_count, write_count, status_value, timer1_irqs;'),
        ('pc=c->mPC;',
         'pc=c->mPC; if(pc==0x07d7) timer1_irqs++; if(HOLD_GATE && pc==0x1000) c->mLowerData[0x15]=1;'),
        ('c.mSFR[REG_SP]=113;c.mSFR[REG_IE]=0;',
         'c.mSFR[REG_SP]=113;c.mSFR[REG_IE]=0x88; '
         'c.mSFR[REG_TMOD]=0x15; c.mSFR[REG_TH1]=0xFC; '
         'c.mSFR[REG_TL1]=0x21; c.mSFR[REG_TCON]=0x40;'),
        ('printf("{\\"cycle\\":%u,\\"state\\":%u,\\"timer\\":%u,\\"rx\\":%u,\\"tx\\":[",',
         'printf("{\\"cycle\\":%u,\\"state\\":%u,\\"timer\\":%u,\\"timer1_irqs\\":%u,\\"p1\\":%u,\\"rx\\":%u,\\"tx\\":[",'),
        ('cycle,c.mLowerData[0x34],256*c.mLowerData[0x17]+c.mLowerData[0x16],rx);',
         'cycle,c.mLowerData[0x34],256*c.mLowerData[0x17]+c.mLowerData[0x16],timer1_irqs,c.mSFR[REG_P1],rx);'),
        ('c.mLowerData[0x17]=0x80; /* externally supplied timer-underflow condition */',
         '/* Timer 1 interrupt advances RAM17:16 after the initial A0 expiry. */'),
        ('if(completed==wanted) break;',
         'if(completed==wanted || (HOLD_GATE && c.mLowerData[0x34]==0xa5 && completed>10)) '
         '{wanted=completed; break;}'),
    ]
    for old, new in changes:
        if source.count(old) != 1:
            raise ValueError(('controller probe source changed', old, source.count(old)))
        source = source.replace(old, new)
    return source, [old for old, _ in changes]


def compile_probe(source, directory, gate_hold):
    path = directory / ('timer-gate.c' if gate_hold else 'timer-control.c')
    exe = path.with_suffix('')
    path.write_text(source)
    subprocess.run(['cc', '-O2', '-Wall', '-Wno-unused-parameter', '-DSAT_TRACE',
                    f'-DHOLD_GATE={int(gate_hold)}', '-I', str(CORE), str(path),
                    *(str(CORE / name) for name in ('core.c', 'opcodes.c', 'disasm.c')),
                    '-o', str(exe)], check=True)
    return exe


def state_groups(rows):
    groups = []
    for index, row in enumerate(rows):
        state = f"{row['state']:02X}"
        if not groups or groups[-1]['state'] != state:
            groups.append(dict(state=state, first_iteration=index, iterations=0,
                               first_cycle=row['cycle'], first_timer1_irq=row['timer1_irqs'],
                               first_firmware_timer=row['timer']))
        groups[-1]['iterations'] += 1
        groups[-1]['last_cycle'] = row['cycle']
        groups[-1]['last_timer1_irq'] = row['timer1_irqs']
        groups[-1]['last_firmware_timer'] = row['timer']
        groups[-1]['p1_values'] = sorted(set(groups[-1].get('p1_values', [])) | {row['p1']})
    return groups


def run(out=HERE / 'results/main-loop-timer1-segment2.json'):
    if hashlib.sha256(ROM.read_bytes()).hexdigest() != ROM_SHA:
        raise ValueError('controller ROM changed')
    forced = json.loads(FORCED.read_text())
    source, changes = generated_source()
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        gate = compile_probe(source, directory, True)
        control = compile_probe(source, directory, False)
        negative = json.loads(subprocess.run(
            [str(control), str(ROM), '64', '4', '1'],
            capture_output=True, text=True, check=True).stdout)
        if ([row['state'] for row in negative['iterations']] !=
                [0xA1, 0x00, 0x00, 0x00] or negative['errors']):
            raise ValueError('unheld-R5 timer control changed')
        for selector, polynomial in ((0x40, 'GPC'), (0x60, 'GPA')):
            execution = json.loads(subprocess.run(
                [str(gate), str(ROM), str(selector), '10000', '1'],
                capture_output=True, text=True, check=True).stdout)
            rows = execution['iterations']
            groups = state_groups(rows)
            if (execution['errors'] or execution['completed'] != len(rows) or
                    [group['state'] for group in groups] !=
                    ['A1', 'A2', 'A3', 'A4', 'A5'] or
                    groups[2]['iterations'] < 23 or groups[3]['iterations'] != 8 or
                    groups[4]['iterations'] != 1):
                raise ValueError(('Timer1 state sequence changed', selector, groups))
            checks = 0
            for row in rows:
                line = [value for address, value in zip(
                    row['write_addresses'], row['writes']) if address == 1]
                expected = [transform(event['history'], event['input'], event['delay'])[1]
                            for event in row['scramble']]
                if line != expected:
                    raise ValueError(('port-01 scrambler mismatch', selector, row))
                checks += len(line)
            a3 = rows[groups[2]['first_iteration']:groups[3]['first_iteration']]
            a4 = rows[groups[3]['first_iteration']:groups[4]['first_iteration']]
            a5 = rows[groups[4]['first_iteration']]
            if {row['p1'] for row in a3 + a4} != {0xD8}:
                raise ValueError(('A3/A4 P1 boundary changed', selector))
            if (any(row['write_addresses'].count(1) for row in a3) or
                    any(row['write_sources'] != [0xFF] for row in a4) or
                    a5['write_sources'] != [0x03]):
                raise ValueError(('A3/A4/A5 port-01 source changed', selector))
            a4_bytes = [row['writes'][0] for row in a4]
            if any(row['write_addresses'] != [1] for row in a4) or a5['write_addresses'] != [1]:
                raise ValueError(('A4/A5 write address changed', selector))
            serial = [(value >> bit) & 1 for value in a4_bytes + a5['writes']
                      for bit in range(8)]
            if serial[1:65] != standard_bits(polynomial):
                raise ValueError(('interrupt-paced segment-2 pattern changed', selector))
            earlier = next(row for row in forced['runs']
                           if row['selector'] == f'{selector:02X}')
            if ([f'{value:02X}' for value in a4_bytes + a5['writes']] !=
                    source_windows(earlier)[0]['bytes']):
                raise ValueError(('interrupt-paced bytes differ from prior PROM source', selector))
            cases.append(dict(selector=f'{selector:02X}', polynomial=polynomial,
                              completed_iterations=len(rows),
                              state_groups=groups,
                              a3_unique_frames=sorted({' '.join(f'{v:02X}' for v in row['tx'])
                                                       for row in a3}),
                              a4_unique_frames=sorted({' '.join(f'{v:02X}' for v in row['tx'])
                                                       for row in a4}),
                              a3_p1_values=sorted({f"{row['p1']:02X}" for row in a3}),
                              a4_p1_values=sorted({f"{row['p1']:02X}" for row in a4}),
                              a3_port01_writes=0,
                              a4_port01_bytes=[f'{value:02X}' for value in a4_bytes],
                              first_a5_port01_byte=f"{a5['writes'][0]:02X}",
                              standard_segment2_matching_bits=64,
                              controller_bytes_match_prior_prom_fixture=True,
                              a3_to_a4_timer1_interrupts=(groups[3]['first_timer1_irq'] -
                                                            groups[2]['first_timer1_irq']),
                              a3_to_a4_emulator_ticks=(groups[3]['first_cycle'] -
                                                        groups[2]['first_cycle']),
                              independently_checked_port01_bytes=checks))
    paths = [Path(__file__), HERE / 'main_loop_probe.c', FORCED,
             HERE / 'controller_segment2_pattern.py', ROM,
             HERE.parents[1] / 'controller_scrambler.py',
             *(CORE / name for name in ('core.c', 'opcodes.c', 'disasm.c', 'emu8051.h'))]
    report = dict(
        status='A3 silence-at-port01 followed by exact A4 segment-2 digital pattern survives interrupt-paced controller execution with positive R5 gate',
        fixture=dict(entry_pc='1ED3', initial_state='A0', initial_timer17='80 to enter A1',
                     after_initial_expiry='Timer 1 SFRs TMOD=15 TH1=FC TL1=21 TCON=40 IE=88; no forced RAM17 expiry at polling boundaries',
                     ram15_gate='set RAM15=01 at each PC1000 state dispatch; external gate hypothesis, not observed hardware behavior',
                     rx_bytes='00 07 00 00 00 selector 00 every polling iteration',
                     external_reads='status 01 at PC0539/1D9D/1DBD, data 00 at PC1DC6; all synthetic',
                     serial_completion_delay_emulator_ticks=8,
                     timer_caveat='emu8051 timer_tick advances once per tick() instruction call, not calibrated to varying 8031 machine cycles',
                     generated_source_replacement_keys=changes),
        unheld_ram15_control=dict(first_states=[f"{row['state']:02X}" for row in negative['iterations']],
                                  first_timer1_interrupt_counts=[row['timer1_irqs'] for row in negative['iterations']]),
        cases=cases,
        limitations=['RAM15 is held positive at state dispatch to bypass the separate sign gate; the source of that gate is unknown.',
                     'The 8031 instruction-tick timer model and synthetic USART completion/receive events do not establish physical milliseconds or line symbol timing.',
                     'The exact port-01 pattern is a controller digital signal, not a traced DSC2847 input or DAC/line output.'],
        source_sha256={str(path.relative_to(ROOT)):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path,
                        default=HERE / 'results/main-loop-timer1-segment2.json')
    args = parser.parse_args()
    report = run(args.out)
    for case in report['cases']:
        print(case['selector'],
              [(g['state'], g['iterations']) for g in case['state_groups']],
              case['a3_to_a4_timer1_interrupts'],
              case['standard_segment2_matching_bits'])
