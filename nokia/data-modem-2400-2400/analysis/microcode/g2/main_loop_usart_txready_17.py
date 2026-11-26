"""Check the first 17 paced 8251 TxD bytes against the joined DSC input."""

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from main_loop_timer1_segment2 import HERE, ROM, compile_probe, state_groups
from main_loop_usart_txready import PHASES, parse_events, probe_source

CONTROLLER = HERE / 'results/main-loop-long.json'
DSC = HERE / 'results/joint-mask04-12a-controller-continuation.json'
DATA_BYTES = 17
A5_PASSES = 70


def run(out=HERE / 'results/main-loop-usart-txready-17.json'):
    source = probe_source()
    old = 'a5_seen>=45'
    if source.count(old) != 1:
        raise ValueError('paced controller stop point changed')
    source = source.replace(old, f'a5_seen>={A5_PASSES}')
    controller = json.loads(CONTROLLER.read_text())
    dsc = json.loads(DSC.read_text())
    cases = []
    with tempfile.TemporaryDirectory() as temp:
        exe = compile_probe(source, Path(temp), True)
        for selector in (0x40, 0x60):
            name = f'{selector:02X}'
            earlier = next(row for row in controller['runs']
                           if row['selector'] == name)
            expected = [int(byte, 16) for row in earlier['iterations']
                        for byte in row['line_bytes']][:DATA_BYTES]
            joined = next(row for row in dsc['cases']
                          if row['selector'] == name)
            joined_bytes = [int(value, 16) for value in
                            joined['training_line_bytes'] +
                            joined['payload_line_bytes']]
            if len(expected) != DATA_BYTES or len(joined_bytes) != 16:
                raise ValueError(('saved controller/DSC stream changed', name))
            for phase in PHASES:
                process = subprocess.run([str(exe), str(ROM), str(selector),
                                          '10000', str(phase)],
                                         capture_output=True, text=True, check=True)
                execution = json.loads(process.stdout)
                start, writes, bits, ready_rises = parse_events(process.stderr)
                groups = state_groups(execution['iterations'])
                if (execution['errors'] or
                        [group['state'] for group in groups] !=
                        ['A1', 'A2', 'A3', 'A4', 'A5'] or
                        groups[-1]['iterations'] != A5_PASSES):
                    raise ValueError(('paced controller did not sustain A5',
                                      name, phase, groups))
                data_bits = [event['bit'] for event in bits
                             if event['data_character']]
                if len(data_bits) < DATA_BYTES * 8:
                    raise ValueError(('too few paced TxD bits', name, phase))
                shifted = [sum(data_bits[8 * index + bit] << bit
                               for bit in range(8))
                           for index in range(DATA_BYTES)]
                if shifted != expected:
                    raise ValueError(('paced TxD differs from controller writes',
                                      name, phase, shifted, expected))
                aligned = data_bits[1:129]
                packed = [sum(aligned[8 * index + bit] << bit
                              for bit in range(8))
                          for index in range(16)]
                if packed != joined_bytes:
                    raise ValueError(('paced TxD differs from joined DSC input',
                                      name, phase, packed, joined_bytes))
                first_data = next(event for event in bits
                                  if event['data_character'])
                if not ready_rises or ready_rises[0] != first_data['cycle']:
                    raise ValueError(('TxRDY/data start mismatch', name, phase))
                cases.append(dict(selector=name, tx_clock_phase_ticks=phase,
                                  completed_iterations=execution['completed'],
                                  a5_passes=groups[-1]['iterations'],
                                  port01_writes=len(writes),
                                  shifted_data_bits=len(data_bits),
                                  first_17_txd_bytes=[f'{value:02X}' for value in shifted],
                                  aligned_dsc_bytes=[f'{value:02X}' for value in packed],
                                  controller_writes_match=True,
                                  joined_dsc_input_match=True,
                                  first_data_bit_cycle=first_data['cycle'],
                                  first_txrdy_rise_cycle=ready_rises[0],
                                  a3_start_cycle=start))
    paths = (Path(__file__), HERE / 'main_loop_usart_txready.py',
             HERE / 'main_loop_timer1_segment2.py', CONTROLLER, DSC, ROM)
    report = dict(experiment='17 paced 8251 TxD characters through A4/A5',
                  fixture=dict(selectors=['40', '60'],
                               phases_ticks=list(PHASES),
                               a5_passes=A5_PASSES,
                               shifted_characters_checked=DATA_BYTES,
                               model='single-byte 8251 transmit buffer, 2400-bit/s clock, FF sync fill',
                               alignment='bit 1 of first A4 data character'),
                  cases=cases,
                  limitations=['RAM15 positive hold and synthetic receive/status input remain controller assumptions.',
                               'Tx clock, initial FF shifter, CTS, and TxD-to-DSC wiring remain photo-compatible hypotheses.',
                               'Eight sampled clock phases do not establish every possible physical phase.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    print('paced cases', len(cases), 'all match first 17 controller bytes and DSC input',
          flush=True)
    return report


if __name__ == '__main__':
    run()
