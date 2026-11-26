"""Check whether executed AD-AE-AF receive handling reinitializes USART 01."""

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from receiver_ad_ae_af_zero_handoff import ad_source
from receiver_timer1_offset_handoff import PRIOR, compile_probe
from receiver_timed_controller_handoff import BIT_TICKS
from zero_run_detector import CORE, HISTORY, ROM

LOG = 'fprintf(stderr,"XWRITE cycle=%u pc=%04X address=%u value=%u\\n",cycle,pc,address,value);'
SITE = '    if(address!=1 && address!=2 && address!=5 && address!=6) {'


def instrument(source):
    if source.count(SITE) != 1:
        raise ValueError('controller external-write hook changed')
    return source.replace(SITE, '    ' + LOG + '\n' + SITE)


def execute(exe, delay, selector, values, pulse):
    process = subprocess.run(
        [str(exe), str(ROM), str(BIT_TICKS), str(pulse), str(delay),
         str(HISTORY), str(selector), *(str(value) for value in values)],
        capture_output=True, text=True, check=True)
    state = json.loads(process.stdout)
    writes = []
    for line in process.stderr.splitlines():
        if line.startswith('FIRST_AF='):
            state['first_af'] = int(line.split()[0].split('=')[1])
        elif line.startswith('FIRST_AE_STATE='):
            state['first_ae'] = int(line.split()[0].split('=')[1])
        if line.startswith('XWRITE '):
            fields = dict(item.split('=') for item in line.split()[1:])
            writes.append(dict(cycle=int(fields['cycle']),
                               pc=fields['pc'], address=int(fields['address']),
                               value=int(fields['value'])))
    return state, writes


def summarize(writes):
    return dict(counts={str(address): sum(row['address'] == address
                                         for row in writes)
                        for address in (1, 2, 5, 6)},
                control_port_05=[row for row in writes if row['address'] == 5],
                control_port_06=[row for row in writes if row['address'] == 6],
                first_line_data_cycle=next((row['cycle'] for row in writes
                                            if row['address'] == 1), None),
                last_line_data_cycle=next((row['cycle'] for row in reversed(writes)
                                           if row['address'] == 1), None))


def run(out=HERE / 'results/receiver-usart-reinit-screen.json'):
    prior = json.loads(PRIOR.read_text())
    unique = {row['polynomial_delay']: row for row in prior['cases']}
    if set(unique) != {5, 18}:
        raise ValueError('saved PROM receive cases changed')
    source = instrument(ad_source(5))
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        exe = compile_probe(source, Path(temporary), 'controller-usart-write-screen')
        for delay in (5, 18):
            values = [int(item, 16) for item in
                      unique[delay]['recovered_line_bytes']]
            selector = 0x40 if delay == 5 else 0x60
            aligned, writes = execute(exe, delay, selector, values, 64)
            absent, absent_writes = execute(exe, delay, selector, values, 128)
            if (aligned['state'] != 0xB0 or absent['state'] != 0xAF or
                    aligned['consumed_bytes'] != values or aligned['errors'] or
                    absent['errors']):
                raise ValueError('AD-AE-AF receive control changed')
            aligned_summary = summarize(writes)
            absent_summary = summarize(absent_writes)
            if (aligned_summary != absent_summary or
                    aligned_summary['control_port_05'] or
                    aligned_summary['counts'] != {'1': 67, '2': 0,
                                                  '5': 0, '6': 5}):
                raise ValueError('controller write-route observation changed')
            cases.append(dict(delay=delay, selector=f'{selector:02X}',
                              aligned_state=aligned['state'],
                              absent_state=absent['state'],
                              first_ae=aligned['first_ae'],
                              first_af=aligned['first_af'],
                              first_receive_byte=aligned['consumed_cycles'][0],
                              aligned_writes=aligned_summary,
                              absent_writes=absent_summary))
            print(delay, aligned_summary, flush=True)
    paths = [Path(__file__), PRIOR,
             HERE / 'receiver_ad_ae_af_zero_handoff.py',
             HERE / 'receiver_ae_af_zero_handoff.py',
             HERE / 'receiver_ae_to_af_timer_probe.py',
             HERE / 'receiver_timer1_offset_handoff.py',
             HERE / 'receiver_timed_controller_probe.c', ROM,
             *(CORE / item for item in ('core.c', 'opcodes.c', 'disasm.c',
                                       'emu8051.h'))]
    report = dict(experiment='executed controller AD-AE-AF line-USART reinitialization screen',
                  fixture=dict(initial_state='AD', timer1='enabled',
                               rxc_start_cycle=85000,
                               bit_ticks=BIT_TICKS,
                               pulse_bits=(64, 128)),
                  cases=cases,
                  limitations=['The AD entry and countdown, external receive bits, SYNDET and serial completions are fixture assumptions.',
                               'The 8251 behavior remains a narrow model; external writes are observed from the real 8031 ROM.'],
                  instrumented_source_sha256=hashlib.sha256(source.encode()).hexdigest(),
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
