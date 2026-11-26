"""Run the ROM's AD-to-AE-to-AF-to-B0 path with timed receive bits."""

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from receiver_ae_af_zero_handoff import delayed_source
from receiver_ae_to_af_timer_probe import ae_source, execute_probe
from receiver_timer1_offset_handoff import (PRIOR, SOURCE, compile_probe,
                                            timer_source, unheld_source)
from receiver_timed_controller_handoff import BIT_TICKS
from zero_run_detector import CORE, HISTORY, ROM

RXC_START_CYCLE = 85000
PULSES = (63, 64, 65, 128)


def ad_source(mode):
    source = ae_source(unheld_source(timer_source()[0]), mode)
    changes = [
        ('c.mLowerData[0x34]=0xAE;c.mLowerData[0x22]=0x10;',
         'c.mLowerData[0x34]=0xAD;c.mLowerData[0x22]=0x10;'),
        ('c.mLowerData[0x17]=0x00;c.mLowerData[0x16]=0x32;', ''),
        ('void sat_trace(struct em8051 *c) {',
         'static unsigned first_ae_cycle, first_ae_ram64, first_ae_ram24, '
         'first_ae_ram15, first_ae_ram14, first_ae_irqs, ad_increment;\n'
         'void sat_trace(struct em8051 *c) {'),
        ('if(pc==0x130a) ae_increments++;',
         'if(pc==0x130a) ae_increments++; if(pc==0x1227) ad_increment++;'),
        ('tick(&c);',
         'tick(&c); if(c.mLowerData[0x34]==0xAE && !first_ae_cycle) {'
         'first_ae_cycle=cycle; first_ae_ram64=c.mLowerData[0x64]; '
         'first_ae_ram24=c.mLowerData[0x24]; '
         'first_ae_ram15=c.mLowerData[0x15]; '
         'first_ae_ram14=c.mLowerData[0x14]; '
         'first_ae_irqs=timer1_irqs;}'),
        ('return errors?3:0;',
         'fprintf(stderr,"FIRST_AE_STATE=%u RAM64=%u RAM24=%u RAM15=%u '
         'RAM14=%u IRQ=%u AD_INCREMENT=%u\\n",first_ae_cycle, '
         'first_ae_ram64,first_ae_ram24,first_ae_ram15,first_ae_ram14, '
         'first_ae_irqs,ad_increment); return errors?3:0;'),
    ]
    for old, new in changes:
        if source.count(old) != 1:
            raise ValueError(('controller source changed', old, source.count(old)))
        source = source.replace(old, new)
    return delayed_source(source, RXC_START_CYCLE)


def first_ae_marker(exe, values, delay, selector):
    process = subprocess.run(
        [str(exe), str(ROM), str(BIT_TICKS), '64', str(delay),
         str(HISTORY), str(selector), *(str(value) for value in values)],
        capture_output=True, text=True, check=True)
    marker = next((line for line in process.stderr.splitlines()
                   if line.startswith('FIRST_AE_STATE=')), None)
    if marker is None:
        raise ValueError('missing AD-to-AE marker')
    return {key.lower(): int(value)
            for key, value in (item.split('=') for item in marker.split())}


def run(out=HERE / 'results/receiver-ad-ae-af-zero-handoff.json'):
    prior = json.loads(PRIOR.read_text())
    unique = {}
    for row in prior['cases']:
        unique.setdefault(row['polynomial_delay'], row)
    if set(unique) != {5, 18}:
        raise ValueError('offset PROM line streams changed')
    source5 = ad_source(5)
    source0 = ad_source(0)
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        exe5 = compile_probe(source5, directory, 'ad-mode5')
        exe0 = compile_probe(source0, directory, 'ad-mode0')
        for delay in (5, 18):
            source_case = unique[delay]
            values = [int(item, 16)
                      for item in source_case['recovered_line_bytes']]
            selector = 0x40 if delay == 5 else 0x60
            pulse_cases = [dict(pulse=pulse,
                                result=execute_probe(exe5, values, pulse,
                                                     delay, selector))
                           for pulse in PULSES]
            aligned = pulse_cases[1]['result']
            edge = first_ae_marker(exe5, values, delay, selector)
            opposite = execute_probe(exe5, values, 64, delay,
                                     0x60 if selector == 0x40 else 0x40)
            wrong_mode = execute_probe(exe0, values, 64, delay, selector)
            if (edge['first_ae_state'] == 0 or edge['ram64'] != 8 or
                    edge['ad_increment'] != 1 or
                    edge['first_ae_state'] >= aligned['first_af'] or
                    aligned['first_af'] >= RXC_START_CYCLE or
                    aligned['ram15'] >= 0x80 or
                    aligned['reloads'] != 1 or
                    aligned['state'] != 0xB0 or
                    aligned['zero_octets'] != 8 or
                    aligned['consumed_bytes'] != values or
                    aligned['decoded_bytes'] != [0] * 8 or
                    aligned['errors'] or aligned['overruns'] or
                    any(item['result']['state'] != 0xAF or
                        item['result']['errors']
                        for item in pulse_cases if item['pulse'] != 64) or
                    opposite['state'] != 0xAF or opposite['errors'] or
                    wrong_mode['state'] != 0xAE or
                    wrong_mode['first_af'] or wrong_mode['errors']):
                raise ValueError(('AD-to-B0 replay changed', delay, edge,
                                  aligned, wrong_mode))
            cases.append(dict(polynomial_delay=delay,
                              selected_prom_trace_digest=source_case['trace_digest'],
                              line_bytes=source_case['recovered_line_bytes'],
                              first_ae=edge,
                              pulse_cases=pulse_cases,
                              opposite_selector=opposite,
                              mode0_control=wrong_mode))
            print(delay, 'AE', edge['first_ae_state'], 'RAM64', edge['ram64'],
                  'AF', aligned['first_af'], 'B0', aligned['b0_cycle'],
                  'controls', [item['result']['state']
                              for item in pulse_cases],
                  'mode0', wrong_mode['state'], flush=True)
    paths = [Path(__file__), PRIOR, SOURCE,
             HERE / 'receiver_ae_af_zero_handoff.py',
             HERE / 'receiver_ae_to_af_timer_probe.py',
             HERE / 'receiver_timer1_offset_handoff.py',
             HERE.parents[1] / 'results/controller-linear.asm', ROM,
             *(CORE / item for item in
               ('core.c', 'opcodes.c', 'disasm.c', 'emu8051.h'))]
    report = dict(experiment='Timer-paced ROM AD-AE-AF-B0 receive handoff',
                  fixture=dict(initial_state='AD',
                               initial_ram15_ram14='75:30',
                               initial_ram17_ram16='00:00',
                               initial_ram64='00',
                               decoded_dte_mode='05',
                               raw_dte_command_byte='02',
                               controller_bit_ticks=BIT_TICKS,
                               rxc_start_cycle=RXC_START_CYCLE,
                               pulse_indices=PULSES,
                               timer1_sfrs='TMOD=15 TH1=FC TL1=21 TCON=40 IE=88',
                               mode5_source_sha256=hashlib.sha256(
                                   source5.encode()).hexdigest(),
                               mode0_source_sha256=hashlib.sha256(
                                   source0.encode()).hexdigest()),
                  cases=cases,
                  limitations=[
                      'State AD and long countdown 75:30 are seeded fixtures; their natural predecessor and countdown loading path are not demonstrated.',
                      'The short countdown is not seeded; the ROM loads it upon entering AE.',
                      'DTE serial completion, RxD/RxC/SYNDET, ADC capture and external readout remain hypothetical; this does not establish C3.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
