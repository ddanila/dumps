"""Replay A3/A4 with a one-byte 8251A Tx buffer and 2400-bit/s Tx clock."""

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from main_loop_timer1_segment2 import (HERE, ROM, compile_probe,
                                      generated_source, state_groups)
from controller_segment2_pattern import standard_bits

TIMER_REPORT = HERE / 'results/main-loop-timer1-segment2.json'

OSCILLATOR_HZ = 11980800
MACHINE_DIVISOR = 12
LINE_BIT_RATE = 2400
BIT_TICKS = OSCILLATOR_HZ // MACHINE_DIVISOR // LINE_BIT_RATE
BYTE_TICKS = 8 * BIT_TICKS
PHASES = tuple(range(0, BYTE_TICKS, BIT_TICKS))


def probe_source():
    source, _ = generated_source()
    changes = [
        ('static unsigned cycle, pc, errors, tx_due, tx_count, write_count, status_value, timer1_irqs;',
         '''static unsigned cycle, pc, errors, tx_due, tx_count, write_count, status_value, timer1_irqs;
static unsigned a3_start, a5_seen, serial_char=255, serial_bitpos, serial_next;
static unsigned serial_pending_valid, serial_pending, serial_source;
static void serial_tick(void) {
    if(cycle!=serial_next) return;
    if(serial_bitpos==8) {
        if(serial_pending_valid) {
            serial_char=serial_pending; serial_pending_valid=0; serial_source=1;
            if(a3_start) fprintf(stderr,"TXRDY_RISE %u\\n",cycle);
        } else {serial_char=255; serial_source=0;}
        serial_bitpos=0;
    }
    if(a3_start)
        fprintf(stderr,"BIT %u %u %u\\n",cycle,(serial_char>>serial_bitpos)&1,serial_source);
    serial_bitpos++; serial_next+=416;
}'''),
        ('pc=c->mPC; if(pc==0x07d7) timer1_irqs++; if(HOLD_GATE && pc==0x1000) c->mLowerData[0x15]=1;',
         '''pc=c->mPC; if(pc==0x07d7) timer1_irqs++;
    if(HOLD_GATE && pc==0x1000) c->mLowerData[0x15]=1;
    if(pc==0x1ed3 && c->mLowerData[0x34]==0xa3 && !a3_start) {
        a3_start=cycle; fprintf(stderr,"A3_START %u\\n",cycle);
    }'''),
        ('if(pc==0x0539 || pc==0x1d9d || pc==0x1dbd) return (unsigned char)status_value;',
         'if(pc==0x0539 || pc==0x1d9d || pc==0x1dbd) return serial_pending_valid?0:1;'),
        ('if(address==1 || address==2 || address==5 || address==6) {',
         '''if(address==1) {
        if(serial_pending_valid) errors++;
        serial_pending=value; serial_pending_valid=1;
        fprintf(stderr,"WRITE %u %02X %02X %02X\\n",cycle,c->mLowerData[0x34],value,c->mLowerData[0x37]);
    }
    if(address==1 || address==2 || address==5 || address==6) {'''),
        ('tick(&c);', 'serial_tick(); tick(&c);'),
        ('status_value>3', 'status_value>3327'),
        ('unsigned char input[]={0,7,0,0,0,(unsigned char)selector,0};',
         'serial_next=status_value; unsigned char input[]={0,7,0,0,0,(unsigned char)selector,0};'),
        ('if(completed==wanted || (HOLD_GATE && c.mLowerData[0x34]==0xa5 && completed>10))',
         'if(completed==wanted || (HOLD_GATE && c.mLowerData[0x34]==0xa5 && completed>10 && ++a5_seen>=45))'),
    ]
    for old, new in changes:
        if source.count(old) != 1:
            raise ValueError(('controller probe source changed', old, source.count(old)))
        source = source.replace(old, new)
    return source


def parse_events(stderr):
    start = None
    writes, bits, ready_rises = [], [], []
    for line in stderr.splitlines():
        fields = line.split()
        if fields[0] == 'A3_START':
            if start is not None:
                raise ValueError('multiple A3 entries')
            start = int(fields[1])
        elif fields[0] == 'WRITE':
            writes.append(dict(cycle=int(fields[1]), state=fields[2],
                               value=fields[3], source=fields[4]))
        elif fields[0] == 'BIT':
            bits.append(dict(cycle=int(fields[1]), bit=int(fields[2]),
                             data_character=bool(int(fields[3]))))
        elif fields[0] == 'TXRDY_RISE':
            ready_rises.append(int(fields[1]))
        else:
            raise ValueError(('unexpected probe event', line))
    if start is None:
        raise ValueError('A3 start not observed')
    return start, writes, bits, ready_rises


def run(out=HERE / 'results/main-loop-usart-txready.json'):
    if OSCILLATOR_HZ % MACHINE_DIVISOR or (OSCILLATOR_HZ // MACHINE_DIVISOR) % LINE_BIT_RATE:
        raise ValueError('clock no longer gives integer machine ticks per bit')
    source = probe_source()
    timer = json.loads(TIMER_REPORT.read_text())
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        exe = compile_probe(source, Path(temporary), True)
        for selector in (0x40, 0x60):
            for phase in PHASES:
                process = subprocess.run([str(exe), str(ROM), str(selector),
                                          '10000', str(phase)],
                                         capture_output=True, text=True, check=True)
                execution = json.loads(process.stdout)
                groups = state_groups(execution['iterations'])
                if (execution['errors'] or
                        [group['state'] for group in groups] !=
                        ['A1', 'A2', 'A3', 'A4', 'A5']):
                    raise ValueError(('paced controller states changed', selector, phase))
                start, writes, bits, ready_rises = parse_events(process.stderr)
                a4 = [write for write in writes if write['state'] == 'A4']
                a5 = [write for write in writes if write['state'] == 'A5']
                if (len(a4) != 7 or [write['source'] for write in a4] != ['FF'] * 7 or
                        len(a5) < 2 or [write['source'] for write in a5[:2]] != ['FF', '03']):
                    raise ValueError(('paced A4/A5 write count changed', selector, phase,
                                      a4, a5))
                baseline = next(case for case in timer['cases']
                                if case['selector'] == f'{selector:02X}')
                first_nine = a4 + a5[:2]
                if ([write['value'] for write in first_nine] !=
                        baseline['a4_port01_bytes'] + [baseline['first_a5_port01_byte']]):
                    raise ValueError(('paced serial bytes changed', selector, phase,
                                      first_nine))
                if any(write['cycle'] <= start for write in writes):
                    raise ValueError(('unexpected A3 data write', selector, phase))
                first_data_bit = next(bit for bit in bits if bit['data_character'])
                if not ready_rises or ready_rises[0] != first_data_bit['cycle']:
                    raise ValueError(('TxRDY rise differs from data shift start',
                                      selector, phase, ready_rises))
                fill_bits_since_a3 = sum(not bit['data_character'] for bit in bits
                                         if bit['cycle'] < first_data_bit['cycle'])
                data_bits = [bit['bit'] for bit in bits if bit['data_character']]
                if len(data_bits) < 72:
                    raise ValueError(('nine USART bytes not shifted out', selector, phase))
                transmitted = [sum(data_bits[index + bit] << bit for bit in range(8))
                               for index in range(0, 72, 8)]
                if transmitted != [int(write['value'], 16) for write in first_nine]:
                    raise ValueError(('USART shifted bytes differ from CPU writes',
                                      selector, phase, transmitted))
                polynomial = 'GPC' if selector == 0x40 else 'GPA'
                if data_bits[1:65] != standard_bits(polynomial):
                    raise ValueError(('paced TxD segment-2 pattern changed',
                                      selector, phase))
                cases.append(dict(selector=f'{selector:02X}', tx_clock_phase_ticks=phase,
                                  a3_start_cycle=start,
                                  first_a4_write_cycle=a4[0]['cycle'],
                                  a3_to_first_a4_write_ticks=a4[0]['cycle'] - start,
                                  a3_to_first_a4_write_ms=round(
                                      (a4[0]['cycle'] - start) * MACHINE_DIVISOR /
                                      OSCILLATOR_HZ * 1000, 6),
                                  a4_source_ff_writes=len(a4),
                                  a4_output_bytes=[write['value'] for write in a4],
                                  first_a5_source=a5[0]['source'],
                                  first_a5_output_byte=a5[0]['value'],
                                  second_a5_source=a5[1]['source'],
                                  second_a5_output_byte=a5[1]['value'],
                                  first_nine_output_bytes=[write['value'] for write in first_nine],
                                  first_nine_transmitted_bytes=[f'{value:02X}' for value in transmitted],
                                  exact_standard_segment2_bits_on_txd=64,
                                  segment2_start_bit_in_first_data_byte=1,
                                  first_data_bit_cycle=first_data_bit['cycle'],
                                  first_txrdy_rise_cycle=ready_rises[0],
                                  txempty_fall_to_txrdy_rise_ticks=(
                                      ready_rises[0] - a4[0]['cycle']),
                                  sync_fill_bits_since_a3_entry=fill_bits_since_a3,
                                  first_data_bit_after_a3_entry_ticks=first_data_bit['cycle'] - start,
                                  a4_state_iterations=groups[3]['iterations'],
                                  bit_events_after_a3=len(bits),
                                  first_16_serial_bits=''.join(str(bit['bit']) for bit in bits[:16]),
                                  first_a4_write_after_seventh_ff_byte=(
                                      7 * BYTE_TICKS < a4[0]['cycle'] - start <
                                      8 * BYTE_TICKS)))
    paths = [Path(__file__), HERE / 'main_loop_timer1_segment2.py', TIMER_REPORT,
             HERE / 'main_loop_probe.c', HERE / 'controller_segment2_pattern.py', ROM]
    report = dict(
        status='nominal 2400-bit/s one-byte 8251A TxRDY pacing shifts the eighth FF-source byte into A5, then shifts all nine bytes through TxD with the exact 64-bit standard segment-2 window in eight clock phases per selector',
        fixture=dict(controller='unchanged 8031 ROM; Timer 1 interrupt with RAM15=01 hold at PC1000',
                     usart='single-byte transmit buffer and FF sync fill; TxRDY bit0 high only when buffer empty',
                     tx_clock_hz=LINE_BIT_RATE, oscillator_hz=OSCILLATOR_HZ,
                     machine_cycle_divisor=MACHINE_DIVISOR,
                     machine_ticks_per_bit=BIT_TICKS,
                     machine_ticks_per_byte=BYTE_TICKS,
                     clock_phases_ticks=list(PHASES),
                     external_receive_and_cd4094='same synthetic receive/status and serial-completion fixtures as main_loop_timer1_segment2.py'),
        cases=cases,
        limitations=['The controller starts after its USART startup programming; CTS and TxD routing are assumed.',
                     'Tx clock at 2400 Hz, one-byte buffer, initial FF shifter and sampled clock phases are explicit hypotheses; sub-bit and all 3328 byte-clock phases are not swept.',
                     'RAM15 hold, synthetic receive events and CD4094 serial completion remain controller fixture assumptions.',
                     'The eight sampled initial Tx clock phases do not establish the board phase or actual TxD-to-DSC wiring.',
                     'The modeled TxD stream and nine controller bytes are digital results, not a complete analog line waveform or DSC receiver.'],
        source_sha256={str(path.relative_to(HERE.parents[2])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path,
                        default=HERE / 'results/main-loop-usart-txready.json')
    args = parser.parse_args()
    report = run(args.out)
    for case in report['cases']:
        print(case['selector'], case['tx_clock_phase_ticks'],
              case['a4_source_ff_writes'], case['first_a5_output_byte'])
