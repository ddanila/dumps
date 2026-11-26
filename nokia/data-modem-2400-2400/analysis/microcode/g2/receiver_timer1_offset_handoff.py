"""Enable 8031 Timer 1 during the saved offset-PROM receive handoff."""

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from receiver_timed_controller_handoff import BIT_TICKS
from zero_run_detector import CORE, HISTORY, ROM

PRIOR = HERE / 'results/receiver-mask04-margin-zero-handoff.json'
SOURCE = HERE / 'receiver_timed_controller_probe.c'
PULSES = (63, 64, 65, 128)


def timer_source():
    source = SOURCE.read_text()
    changes = [
        ('static unsigned cycle, pc, errors, tx_due, bit_ticks, pulse_bit;',
         'static unsigned cycle, pc, errors, tx_due, bit_ticks, pulse_bit, timer1_irqs;'),
        ('pc=c->mPC;',
         'pc=c->mPC; if(pc==0x07d7) timer1_irqs++;'),
        ('c.mSFR[REG_SP]=113;c.mSFR[REG_IE]=0;',
         'c.mSFR[REG_SP]=113;c.mSFR[REG_IE]=0x88; '
         'c.mSFR[REG_TMOD]=0x15; c.mSFR[REG_TH1]=0xFC; '
         'c.mSFR[REG_TL1]=0x21; c.mSFR[REG_TCON]=0x40;'),
        ('return errors?3:0;',
         'fprintf(stderr,"TIMER1_IRQS=%u\\n",timer1_irqs); '
         'return errors?3:0;'),
    ]
    for old, new in changes:
        if source.count(old) != 1:
            raise ValueError(('controller source changed', old, source.count(old)))
        source = source.replace(old, new)
    return source, [old for old, _ in changes]


def unheld_source(source):
    old = 'if(pc==0x1000) c->mLowerData[0x15]=1;'
    if source.count(old) != 1:
        raise ValueError('RAM15 gate hook changed')
    return source.replace(old, '/* RAM15 retains its preserved value */')


def compile_probe(source, directory, name):
    path = directory / f'{name}.c'
    exe = directory / name
    path.write_text(source)
    subprocess.run(['cc', '-O2', '-Wall', '-Wno-unused-parameter',
                    '-DSAT_TRACE', '-I', str(CORE), str(path),
                    *(str(CORE / item) for item in
                      ('core.c', 'opcodes.c', 'disasm.c')),
                    '-o', str(exe)], check=True)
    return exe


def probe(exe, delay, selector, pulse, values, timer):
    process = subprocess.run(
        [str(exe), str(ROM), str(BIT_TICKS), str(pulse),
         str(delay), str(HISTORY), str(selector),
         *(str(value) for value in values)],
        capture_output=True, text=True)
    if not process.stdout:
        raise ValueError(('controller produced no report', process.returncode,
                          process.stderr))
    result = json.loads(process.stdout)
    result['exit_code'] = process.returncode
    if timer:
        marker = 'TIMER1_IRQS='
        lines = [line for line in process.stderr.splitlines()
                 if line.startswith(marker)]
        if len(lines) != 1:
            raise ValueError(('timer interrupt count missing', process.stderr))
        result['timer1_irqs'] = int(lines[0][len(marker):])
    else:
        if process.returncode or process.stderr:
            raise ValueError(('baseline controller failed', process.stderr))
        result['timer1_irqs'] = 0
    return result


def run(out=HERE / 'results/receiver-timer1-offset-handoff.json'):
    prior = json.loads(PRIOR.read_text())
    source, keys = timer_source()
    unheld = unheld_source(source)
    unique = {}
    for row in prior['cases']:
        unique.setdefault(row['polynomial_delay'], row)
    if set(unique) != {5, 18}:
        raise ValueError('offset PROM handoff cases changed')
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        baseline_exe = compile_probe(SOURCE.read_text(), directory, 'baseline')
        timer_exe = compile_probe(source, directory, 'timer1')
        unheld_exe = compile_probe(unheld, directory, 'timer1-unheld-ram15')
        for delay in (5, 18):
            prior_row = unique[delay]
            values = [int(value, 16)
                      for value in prior_row['recovered_line_bytes']]
            selector = 0x40 if delay == 5 else 0x60
            pulse_cases = []
            for pulse in PULSES:
                old = probe(baseline_exe, delay, selector, pulse, values, False)
                new = probe(timer_exe, delay, selector, pulse, values, True)
                saved = next(item['result'] for item in prior_row['pulse_cases']
                             if item['pulse'] == pulse)
                if {key: old[key] for key in saved} != saved:
                    raise ValueError(('baseline differs from saved handoff',
                                      delay, pulse))
                pulse_cases.append(dict(pulse=pulse,
                                        baseline=old, timer1=new))
            opposite = probe(timer_exe, delay,
                             0x60 if selector == 0x40 else 0x40,
                             64, values, True)
            unheld_gate = probe(unheld_exe, delay, selector,
                                64, values, True)
            aligned = pulse_cases[1]['timer1']
            if (aligned['state'] != 0xB0 or
                    aligned['zero_octets'] != 8 or
                    aligned['consumed_bytes'] != values or
                    aligned['decoded_bytes'] != [0] * 8 or
                    aligned['overruns'] or aligned['errors'] or
                    aligned['timer1_irqs'] != 57 or
                    any(item['timer1']['state'] != 0xAF or
                        item['timer1']['errors'] or
                        item['timer1']['timer1_irqs'] != 57
                        for index, item in enumerate(pulse_cases)
                        if index != 1) or
                    opposite['state'] != 0xAF or opposite['errors'] or
                    unheld_gate['state'] != 0 or
                    unheld_gate['consumed'] != 0 or
                    unheld_gate['overruns'] != 7 or
                    unheld_gate['timer1_irqs'] != 57):
                raise ValueError(('Timer 1 handoff controls changed', delay))
            cases.append(dict(polynomial_delay=delay,
                              selected_prom_trace_digest=prior_row['trace_digest'],
                              line_bytes=prior_row['recovered_line_bytes'],
                              pulse_cases=pulse_cases,
                              opposite_selector_timer1=opposite,
                              unheld_ram15_control=unheld_gate))
            print(delay,
                  [(item['pulse'], item['timer1']['state'],
                    item['timer1']['zero_octets'],
                    item['timer1']['timer1_irqs'],
                    item['timer1']['errors']) for item in pulse_cases],
                  'opposite', opposite['state'], flush=True)
    paths = [Path(__file__), PRIOR, SOURCE,
             HERE / 'receiver_mask04_margin_zero_handoff.py',
             HERE / 'receiver_timed_controller_handoff.py',
             HERE / 'zero_run_detector.py', ROM,
             *(CORE / item for item in
               ('core.c', 'opcodes.c', 'disasm.c', 'emu8051.h'))]
    report = dict(experiment='Timer 1 effect on paced offset-PROM receive handoff',
                  fixture=dict(controller_rom='unchanged 8031 ROM',
                               initial_state='AF',
                               timer1_sfrs='TMOD=15 TH1=FC TL1=21 TCON=40 IE=88',
                               ram15_gate='held positive at PC1000',
                               dte_input='synthetic selector frame',
                               serial_completion='synthetic eight-tick SBUF completion',
                               receive='narrow external-sync 8251A model',
                               bit_ticks=BIT_TICKS,
                               pulse_indices=PULSES,
                               generated_source_replacement_keys=keys,
                               generated_source_sha256=hashlib.sha256(
                                   source.encode()).hexdigest(),
                               unheld_source_sha256=hashlib.sha256(
                                   unheld.encode()).hexdigest()),
                  cases=cases,
                  limitations=[
                      'The data bytes come from saved offset-PROM executions; DSC and 8031 are not run simultaneously.',
                      'Timer 1 is enabled from a synthetic preserved AF state, without reconstructing the full entry countdown.',
                      'DTE receive, mode-0 serial completion, RxD/RxC/SYNDET and the RAM15 gate remain fixtures or wiring hypotheses.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
