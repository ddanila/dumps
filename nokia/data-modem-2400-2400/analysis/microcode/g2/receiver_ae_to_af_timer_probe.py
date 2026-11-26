"""Run the ROM AE-to-AF state step under Timer 1 and ROM-literal countdowns."""

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from receiver_timer1_offset_handoff import (PRIOR, SOURCE, compile_probe,
                                            timer_source, unheld_source)
from receiver_timed_controller_handoff import BIT_TICKS
from zero_run_detector import CORE, HISTORY, ROM

MODES = (0x00, 0x01, 0x04, 0x05)


def ae_source(base, mode):
    source = base
    changes = [
        ('static unsigned cycle, pc, errors, tx_due, bit_ticks, pulse_bit, timer1_irqs;',
         'static unsigned cycle, pc, errors, tx_due, bit_ticks, pulse_bit, timer1_irqs, '
         'first_af_cycle, first_af_ram15, first_af_ram14, first_af_irqs, ae_dispatches, '
         'ae_entries, ae_reloads, ae_checks, ae_increments, '
         'ae_flag2a, ae_flag24, ae_timer17, ae_timer16, '
         'first_ae_flag2a, first_ae_flag24, first_ae_timer17, first_ae_timer16, '
         'mov2a_count, mov2a_value;'),
        ('pc=c->mPC; if(pc==0x07d7) timer1_irqs++;',
         'pc=c->mPC; if(pc==0x07d7) timer1_irqs++; '
         'if(pc==0x1000 && c->mLowerData[0x34]==0xAE) ae_dispatches++; '
         'if(pc==0x0823) {mov2a_count++; mov2a_value=c->mLowerData[0x20];} '
         'if(pc==0x12ea) {if(!ae_entries) {first_ae_flag2a=c->mLowerData[0x2a]; '
         'first_ae_flag24=c->mLowerData[0x24]; '
         'first_ae_timer17=c->mLowerData[0x17]; '
         'first_ae_timer16=c->mLowerData[0x16];} '
         'ae_entries++; ae_flag2a=c->mLowerData[0x2a]; '
         'ae_flag24=c->mLowerData[0x24]; ae_timer17=c->mLowerData[0x17]; '
         'ae_timer16=c->mLowerData[0x16];} '
         'if(pc==0x12f3) ae_reloads++; if(pc==0x12ff) ae_checks++; '
         'if(pc==0x130a) ae_increments++; '
         'if(c->mLowerData[0x34]==0xAF && !first_af_cycle) {'
         'first_af_cycle=cycle; first_af_ram15=c->mLowerData[0x15]; '
         'first_af_ram14=c->mLowerData[0x14]; first_af_irqs=timer1_irqs;}'),
        ('c.mLowerData[0x34]=0xAF;c.mLowerData[0x22]=0x10;',
         'c.mLowerData[0x34]=0xAE;c.mLowerData[0x22]=0x10; '
         'c.mLowerData[0x15]=0x75;c.mLowerData[0x14]=0x30; '
         'c.mLowerData[0x17]=0x00;c.mLowerData[0x16]=0x32; '
         'c.mLowerData[0x2A]=0x00;'),
        ('unsigned char control_input[]={0,7,0,0,0,(unsigned char)selector,0};',
         'unsigned char control_input[]={0,'
         f'0x{mode ^ 7:02X},0,0,0,(unsigned char)selector,0}};'),
        ('return errors?3:0;',
         'fprintf(stderr,"FIRST_AF=%u RAM15=%u RAM14=%u IRQ=%u AE_DISPATCHES=%u\\n",'
         'first_af_cycle,first_af_ram15,first_af_ram14,first_af_irqs,ae_dispatches); '
         'fprintf(stderr,"AE_PATH=%u RELOADS=%u CHECKS=%u INCREMENTS=%u FLAG2A=%u FLAG24=%u TIMER17=%u TIMER16=%u\\n",'
         'ae_entries,ae_reloads,ae_checks,ae_increments,ae_flag2a,ae_flag24,ae_timer17,ae_timer16); '
         'fprintf(stderr,"AE_FIRST=%u FIRST_FLAG24=%u FIRST_TIMER17=%u FIRST_TIMER16=%u MOV2A_COUNT=%u MOV2A_VALUE=%u\\n",'
         'first_ae_flag2a,first_ae_flag24,first_ae_timer17,first_ae_timer16,mov2a_count,mov2a_value); '
         'return errors?3:0;'),
    ]
    for old, new in changes:
        if source.count(old) != 1:
            raise ValueError(('controller source changed', old, source.count(old)))
        source = source.replace(old, new)
    return source


def execute_probe(exe, values, pulse=128, delay=5, selector=64):
    process = subprocess.run(
        [str(exe), str(ROM), str(BIT_TICKS), str(pulse), str(delay),
         str(HISTORY), str(selector), *(str(value) for value in values)],
        capture_output=True, text=True)
    if not process.stdout:
        raise ValueError(('AE probe did not report', process.returncode,
                          process.stderr))
    result = json.loads(process.stdout)
    result['exit_code'] = process.returncode
    fields = {}
    for line in process.stderr.splitlines():
        if line.startswith('TIMER1_IRQS='):
            fields['timer1_irqs'] = int(line.split('=')[1])
        elif line.startswith('RAM15='):
            high, low = line.split()
            fields['final_ram15'] = int(high.split('=')[1])
            fields['final_ram14'] = int(low.split('=')[1])
        elif line.startswith('FIRST_AF='):
            for item in line.split():
                key, value = item.split('=')
                fields[key.lower()] = int(value)
        elif line.startswith('AE_PATH='):
            for item in line.split():
                key, value = item.split('=')
                fields[key.lower()] = int(value)
        elif line.startswith('AE_FIRST='):
            for item in line.split():
                key, value = item.split('=')
                fields[key.lower()] = int(value)
    if set(fields) != {'timer1_irqs', 'final_ram15', 'final_ram14',
                       'first_af', 'ram15', 'ram14', 'irq', 'ae_dispatches',
                       'ae_path', 'reloads', 'checks', 'increments',
                       'flag2a', 'flag24', 'timer17', 'timer16',
                       'ae_first', 'first_flag24', 'first_timer17',
                       'first_timer16', 'mov2a_count', 'mov2a_value'}:
        raise ValueError(('AE probe markers changed', process.stderr))
    result.update(fields)
    return result


def run(out=HERE / 'results/receiver-ae-to-af-timer-probe.json'):
    prior = json.loads(PRIOR.read_text())
    line = next(row for row in prior['cases']
                if row['polynomial_delay'] == 5)['recovered_line_bytes']
    values = [int(value, 16) for value in line]
    rom = ROM.read_bytes()
    if (rom[0x12F5:0x12FB] != bytes.fromhex('75 17 00 75 16 32') or
            rom[0x117C:0x1182] != bytes.fromhex('75 15 75 75 14 30')):
        raise ValueError('ROM countdown literals changed')
    base = unheld_source(timer_source()[0])
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        for mode in MODES:
            source = ae_source(base, mode)
            exe = compile_probe(source, directory, f'ae-mode-{mode:02x}')
            result = execute_probe(exe, values)
            if (result['errors'] or result['mov2a_value'] != mode or
                    (mode == 0x05 and
                     (not result['first_af'] or result['ram15'] >= 0x80 or
                      result['reloads'] or result['increments'] != 1)) or
                    (mode != 0x05 and
                     (result['first_af'] or result['reloads'] == 0 or
                      result['increments']))):
                raise ValueError(('AE mode branch changed', mode, result))
            cases.append(dict(decoded_ram2a_mode=f'{mode:02X}',
                              raw_dte_command_byte=f'{mode ^ 7:02X}',
                              source_sha256=hashlib.sha256(
                                  source.encode()).hexdigest(),
                              result=result))
            print(f'{mode:02X}',
                  'AF', result['first_af'],
                  'AF countdown', result['ram15'], result['ram14'],
                  'AF IRQ', result['irq'],
                  'final', result['state'],
                  'path', result['ae_path'], result['reloads'],
                  result['checks'], result['increments'],
                  'flags', result['flag2a'], result['flag24'],
                  'first', result['ae_first'], result['first_flag24'],
                  'mov2a', result['mov2a_count'], result['mov2a_value'],
                  'timer', result['timer17'], result['timer16'],
                  'errors', result['errors'], flush=True)
    paths = [Path(__file__), PRIOR, SOURCE,
             HERE / 'receiver_timer1_offset_handoff.py',
             HERE.parents[1] / 'results/controller-linear.asm', ROM,
             *(CORE / item for item in
               ('core.c', 'opcodes.c', 'disasm.c', 'emu8051.h'))]
    report = dict(experiment='Timer 1 ROM AE-to-AF transition with inherited countdown',
                  fixture=dict(initial_state='AE',
                               initial_ram15_ram14='75:30',
                               initial_ram17_ram16='00:32',
                               decoded_modes=[f'{value:02X}' for value in MODES],
                               raw_dte_command_bytes=[f'{value ^ 7:02X}'
                                                      for value in MODES],
                               ram24=0,
                               timer1_sfrs='TMOD=15 TH1=FC TL1=21 TCON=40 IE=88',
                               controller_bit_ticks=BIT_TICKS,
                               syndet_pulse='none',
                               line_bytes=line,
                               rom_short_timer_site='12F5',
                               rom_long_timer_site='117C'),
                  cases=cases,
                  limitations=[
                      'The AE state and two ROM-literal countdown values are seeded fixtures; their natural predecessors are not demonstrated. RAM2A is written by the ROM from the synthetic DTE command byte.',
                      'The DTE frame and mode-0 SBUF completion remain synthetic; no physical receive route is established.',
                      'A transition into AF under a flag fixture does not by itself prove a natural call sequence or C3.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
