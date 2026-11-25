"""Join real-PROM receive traces to the ROM-executed AF zero detector."""

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from receiver_mask04_protocol_preamble import (HERE, MAPPINGS, candidate,
                                               capture, fixture, mapped,
                                               mapping_with_upper_source)
from receiver_mask04_serial_candidate import bytes_lsb_first, decode
from zero_run_detector import CORE, HISTORY, ROM, line_octets
from common import save

PREAMBLE_SYMBOLS = 32
DATA_BYTES = 8
DATA_SYMBOLS = DATA_BYTES * 4
OSCILLATOR_HZ = 14_400_000
BIT_CYCLES = 6000


def dibits_from_bytes(values):
    bits = [(value >> bit) & 1 for value in values for bit in range(8)]
    return [bits[index] | (bits[index + 1] << 1)
            for index in range(0, len(bits), 2)]


def controller_probe(exe, delay, values):
    process = subprocess.run([str(exe), str(ROM), str(delay), str(HISTORY),
                              *(str(value) for value in values)],
                             capture_output=True, text=True, check=True)
    return json.loads(process.stdout)


def run(out=HERE / 'results/receiver-mask04-controller-zero-handoff.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    rows = []
    with tempfile.TemporaryDirectory() as temporary:
        exe = Path(temporary) / 'zero-run-probe'
        subprocess.run(['cc', '-O2', '-Wall', '-Wno-unused-function',
                        '-DSAT_TRACE', '-I', str(CORE),
                        str(HERE / 'zero_run_probe.c'),
                        *(str(CORE / name) for name in
                          ('core.c', 'opcodes.c', 'disasm.c')),
                        '-o', str(exe)], check=True)
        for delay in (5, 18):
            offered = line_octets([0] * DATA_BYTES, delay)
            data_dibits = dibits_from_bytes(offered)
            if len(data_dibits) != DATA_SYMBOLS:
                raise ValueError('line data length changed')
            for degrees in (0, 45):
                case = capture(mapping, base, degrees, delay, data_dibits)
                decoded = decode(case)
                bits = [bit for dibit in decoded[PREAMBLE_SYMBOLS:]
                        for bit in (dibit & 1, (dibit >> 1) & 1)]
                recovered = bytes_lsb_first(bits)
                if (len(case['symbols']) != PREAMBLE_SYMBOLS + DATA_SYMBOLS or
                        recovered != offered or
                        case['gate_edges'].get('3F8->3F9') != 24000 or
                        case['nominal' if degrees == 0 else 'diagonal']
                            ['all_data'] != dict(checks=DATA_SYMBOLS,
                                                errors=0, unknown=0,
                                                dibits=data_dibits)):
                    raise ValueError(('real-PROM receive readout failed',
                                      delay, degrees))
                controller = controller_probe(exe, delay, recovered)
                if (controller['errors'] or not controller['reached_stop'] or
                        controller['state_after'] != 0xB0 or
                        [row['decoded'] for row in controller['octets']] !=
                        [0] * DATA_BYTES or
                        [row['zero_octets'] for row in controller['octets']] !=
                        list(range(1, DATA_BYTES + 1)) or
                        any(row['status_reads'] != 1 or row['data_reads'] != 1
                            for row in controller['octets']) or
                        controller['wire'] != [0xD0, 0x42, 0x81, 0x1A]):
                    raise ValueError(('controller handoff failed', delay, degrees))
                corrupted = recovered[:-1] + [recovered[-1] ^ 1]
                control = controller_probe(exe, delay, corrupted)
                if (control['errors'] or not control['reached_stop'] or
                        control['state_after'] != 0xAF or
                        control['zero_octets'] != 0 or
                        control['octets'][-1]['decoded'] == 0 or
                        control['wire'] != [0xD0, 0x42, 0x89, 0x9A]):
                    raise ValueError(('one-bit corruption control failed',
                                      delay, degrees))
                rows.append(dict(polynomial_delay=delay, degrees=degrees,
                                 real_prom_trace_digest=case['trace_digest'],
                                 recovered_line_bytes=[f'{value:02X}' for value in recovered],
                                 recovered_preamble_dibits=decoded[1:PREAMBLE_SYMBOLS],
                                 real_prom_capture_edges=case['gate_edges'],
                                 data_dibits=case['nominal' if degrees == 0 else 'diagonal']['all_data'],
                                 controller_decoded_bytes=[f'{row["decoded"]:02X}'
                                                           for row in controller['octets']],
                                 controller_zero_count=controller['zero_octets'],
                                 controller_state_after=f'{controller["state_after"]:02X}',
                                 controller_outgoing_frame=' '.join(
                                     f'{value:02X}' for value in controller['wire']),
                                 last_line_byte_lsb_flip_control=dict(
                                     last_decoded_byte=f'{control["octets"][-1]["decoded"]:02X}',
                                     state_after=f'{control["state_after"]:02X}',
                                     zero_count=control['zero_octets'],
                                     outgoing_frame=' '.join(
                                         f'{value:02X}' for value in control['wire']))))
    paths = [Path(__file__), HERE / 'receiver_mask04_protocol_preamble.py',
             HERE / 'receiver_mask04_serial_candidate.py',
             HERE / 'zero_run_detector.py', HERE / 'zero_run_probe.c',
             HERE.parents[1] / 'controller_scrambler.py', ROM,
             MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(experiment='conditional real-PROM receive to actual 8031 AF zero-run handoff',
                  fixture=dict(preamble_symbols=PREAMBLE_SYMBOLS,
                               data_symbols=DATA_SYMBOLS,
                               data_bytes=DATA_BYTES,
                               oscillator_hz=OSCILLATOR_HZ,
                               assumed_bit_cycles=BIT_CYCLES,
                               source='eight line bytes from verified V.26 ter scrambler of zero octets',
                               receiver='mask-04 complementary-ADC four-row real-PROM path, external frozen phase/readout logic',
                               controller='preserved 8031 ROM; modeled USART-01 status/data reads in state AF'),
                  cases=rows,
                  limitations=['The DSC-to-8251A RxD/RxC circuit, bit serialization, phase-class selection and byte alignment are labelled assumptions.',
                               'The 8031 probe supplies each recovered byte at a modeled USART-01 MOVX read; it does not clock an 8251A or show a physical receive event.',
                               'The controller AF dispatcher and state step are explicitly entered rather than naturally scheduled by the main loop.',
                               'A conditional co-simulation does not establish a C3 physical connection or prove C4 echo cancellation.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    for case in result['cases']:
        print(case['polynomial_delay'], case['degrees'],
              case['controller_state_after'],
              case['controller_outgoing_frame'], flush=True)
