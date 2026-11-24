"""Probe one-cycle 8X02 address-bus takeover using real control-store words."""

import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path.insert(0, str(ASSUMED))
from common import decode, read, save, unconditional_transfer
from model import X8X02

MAPPING = ASSUMED / 'sequencer.json'
SCENARIO = ASSUMED / 'results/rotation-study/scenario-3.json'
DATASHEET = ('https://bms.isjtr.ro/other/sos/'
             'Philips_elcoma_Signetics_Bipolar%26MOSMicroprocessors_1978.pdf')


def execute_fetch(rows, scenario, sequencer, *, en_high, external_address=None):
    internal_pc = sequencer.pc
    if en_high and external_address is None:
        return dict(internal_pc=f'{internal_pc:03X}', en_high=True,
                    external_address=None, fetch=None, next_pc=None,
                    outcome='unknown control-store address: U9 outputs high-Z, no driver')
    fetch_pc = external_address if en_high else internal_pc
    if fetch_pc is None or not 0 <= fetch_pc < 1024:
        raise ValueError('external control-store address must be ten bits')
    row = rows[fetch_pc]
    if not unconditional_transfer(row, scenario):
        raise ValueError('probe requires an unconditionally executed control word')
    old_stack = sequencer.stack[:]
    old_sp = sequencer.sp
    sequencer.step(row['command'], row['branch'], True)
    return dict(internal_pc=f'{internal_pc:03X}', en_high=en_high,
                external_address=f'{external_address:03X}' if en_high else None,
                fetch=dict(pc=f'{fetch_pc:03X}', raw=row['raw'],
                           command=row['command_name'], branch=f'{row["branch"]:03X}',
                           select=row['select'], direct=row['direct']),
                next_pc=f'{sequencer.pc:03X}',
                stack_unchanged=sequencer.stack == old_stack and sequencer.sp == old_sp)


def run(out=HERE / 'results/enable-takeover-probe.json'):
    rows = decode(read(MAPPING))
    scenario = read(SCENARIO)
    if rows[0x084]['command_name'] != 'BRT' or rows[0x084]['branch'] != 0x084:
        raise ValueError('084 self-branch decode changed')
    if rows[0x036]['command_name'] != 'BRT' or rows[0x036]['branch'] != 0x300:
        raise ValueError('036 vector-word decode changed')
    off = execute_fetch(rows, scenario, X8X02(pc=0x084), en_high=False)
    floating = execute_fetch(rows, scenario, X8X02(pc=0x084), en_high=True)
    sequencer = X8X02(pc=0x084)
    vector = execute_fetch(rows, scenario, sequencer, en_high=True,
                           external_address=0x036)
    resumed_pc = sequencer.pc
    # Once EN is low again, the next fetch comes from the internal address.
    resumed_fetch = rows[resumed_pc]
    if (off['next_pc'] != '084' or vector['next_pc'] != '300' or
            resumed_fetch['pc'] != 0x300 or not vector['stack_unchanged']):
        raise ValueError('address-bus takeover invariant changed')
    available = [dict(fetch_pc=f'{row["pc"]:03X}', target=f'{row["branch"]:03X}')
                 for row in rows if row['command'] == 6 and row['direct']
                 and unconditional_transfer(row, scenario)
                 and row['branch'] != 0x084]
    report = dict(status='diagnostic external-address hypothesis, not Nokia wiring',
                  component='N8X02AN at U9, pin 2 EN-bar',
                  manufacturer_reference=DATASHEET,
                  datasheet_behavior='EN high tri-states address outputs; an external driver may address control-store PROMs while the internal address register retains its state.',
                  cases=dict(en_low=off, en_high_no_driver=floating,
                             en_high_external_036=vector,
                             next_internal_fetch=dict(pc=f'{resumed_pc:03X}',
                                                      command=resumed_fetch['command_name'])),
                  unconditional_direct_brt_vectors_excluding_084=available,
                  limitations=[
                      'No connection to U9 EN-bar or an external ten-bit address driver is established on the Nokia board.',
                      'The 036 address is a diagnostic choice from real PROM contents, not a recovered controller vector.',
                      'Only the 8X02 next-address and stack operation is modeled; no Am2901, controller, DAC or ADC participates.',
                      'Driving EN high without an external PROM address leaves the control word unknown, not a restart.',
                      'The Signetics source describes 8X02; the photographed part is marked N8X02AN.'],
                  source_sha256={str(p.relative_to(HERE.parent)):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (Path(__file__), MAPPING, SCENARIO,
                                           ASSUMED / 'common.py', HERE.parent / 'model.py')})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    print(report['cases'])
    print('candidate direct vectors', len(report['unconditional_direct_brt_vectors_excluding_084']))
