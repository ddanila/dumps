"""Run timer-paced AE-to-AF entry into the offset-PROM zero handoff."""

import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from receiver_ae_to_af_timer_probe import ae_source, execute_probe
from receiver_timer1_offset_handoff import (PRIOR, SOURCE, compile_probe,
                                            timer_source, unheld_source)
from receiver_timed_controller_handoff import BIT_TICKS
from zero_run_detector import CORE, ROM

RXC_START_CYCLE = 51200
PULSES = (63, 64, 65, 128)


def delayed_source(source):
    changes = [
        ('for(cycle=0;cycle<(128+10)*bit_ticks && !errors;cycle++) {',
         f'for(cycle=0;cycle<{RXC_START_CYCLE}+(128+10)*bit_ticks && !errors;cycle++) {{'),
        ('if(next_bit<128 && cycle==next_bit*bit_ticks) rxc_edge(next_bit++);',
         'if(next_bit<128 && '
         f'cycle>={RXC_START_CYCLE} && '
         f'cycle-{RXC_START_CYCLE}==next_bit*bit_ticks) rxc_edge(next_bit++);'),
    ]
    for old, new in changes:
        if source.count(old) != 1:
            raise ValueError(('paced source changed', old, source.count(old)))
        source = source.replace(old, new)
    return source


def run(out=HERE / 'results/receiver-ae-af-zero-handoff.json'):
    prior = json.loads(PRIOR.read_text())
    unique = {}
    for row in prior['cases']:
        unique.setdefault(row['polynomial_delay'], row)
    if set(unique) != {5, 18}:
        raise ValueError('offset PROM line streams changed')
    base = unheld_source(timer_source()[0])
    mode5_source = delayed_source(ae_source(base, 5))
    mode0_source = delayed_source(ae_source(base, 0))
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        mode5_exe = compile_probe(mode5_source, directory, 'mode5-ae-af')
        mode0_exe = compile_probe(mode0_source, directory, 'mode0-ae-control')
        for delay in (5, 18):
            source_case = unique[delay]
            values = [int(item, 16)
                      for item in source_case['recovered_line_bytes']]
            selector = 0x40 if delay == 5 else 0x60
            pulse_cases = [dict(pulse=pulse,
                                result=execute_probe(mode5_exe, values,
                                                     pulse, delay, selector))
                           for pulse in PULSES]
            opposite = execute_probe(mode5_exe, values, 64, delay,
                                     0x60 if selector == 0x40 else 0x40)
            wrong_mode = execute_probe(mode0_exe, values, 64, delay, selector)
            aligned = pulse_cases[1]['result']
            if (aligned['first_af'] == 0 or
                    aligned['first_af'] >= RXC_START_CYCLE + 64 * BIT_TICKS or
                    aligned['state'] != 0xB0 or
                    aligned['zero_octets'] != 8 or
                    aligned['consumed_bytes'] != values or
                    aligned['decoded_bytes'] != [0] * 8 or
                    aligned['overruns'] or aligned['errors'] or
                    any(item['result']['state'] != 0xAF or
                        item['result']['errors']
                        for index, item in enumerate(pulse_cases)
                        if index != 1) or
                    opposite['state'] != 0xAF or opposite['errors'] or
                    wrong_mode['state'] != 0xAE or
                    wrong_mode['first_af'] or wrong_mode['errors']):
                raise ValueError(('AE-AF zero handoff changed', delay))
            cases.append(dict(polynomial_delay=delay,
                              selected_prom_trace_digest=source_case['trace_digest'],
                              line_bytes=source_case['recovered_line_bytes'],
                              pulse_cases=pulse_cases,
                              opposite_selector=opposite,
                              mode0_control=wrong_mode))
            print(delay, 'AF', aligned['first_af'],
                  'AF countdown', aligned['ram15'], aligned['ram14'],
                  'B0', aligned['b0_cycle'],
                  'states', [(item['pulse'], item['result']['state'])
                             for item in pulse_cases],
                  'mode0', wrong_mode['state'], flush=True)
    paths = [Path(__file__), PRIOR, SOURCE,
             HERE / 'receiver_ae_to_af_timer_probe.py',
             HERE / 'receiver_timer1_offset_handoff.py',
             HERE.parents[1] / 'results/controller-linear.asm', ROM,
             *(CORE / item for item in
               ('core.c', 'opcodes.c', 'disasm.c', 'emu8051.h'))]
    report = dict(experiment='Timer-paced ROM AE-to-AF-to-B0 receive handoff',
                  fixture=dict(initial_state='AE',
                               initial_ram15_ram14='75:30',
                               initial_ram17_ram16='00:32',
                               decoded_dte_mode='05',
                               raw_dte_command_byte='02',
                               controller_bit_ticks=BIT_TICKS,
                               rxc_start_cycle=RXC_START_CYCLE,
                               pulse_indices=PULSES,
                               timer1_sfrs='TMOD=15 TH1=FC TL1=21 TCON=40 IE=88',
                               mode5_source_sha256=hashlib.sha256(
                                   mode5_source.encode()).hexdigest(),
                               mode0_source_sha256=hashlib.sha256(
                                   mode0_source.encode()).hexdigest()),
                  cases=cases,
                  limitations=[
                      'The AE state, 75:30 and 00:32 countdowns and remote RxC start are seeded fixtures, though their byte values and AE-to-AF branch are executed ROM behavior.',
                      'The line bytes come from saved real-PROM traces; DSC and controller are sequential rather than concurrent.',
                      'DTE serial completion, RxD/RxC/SYNDET, ADC capture and external readout remain hypothetical; this does not establish C3.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
