"""Check whether first non-11 data dibit can drive external SYNDET."""

import hashlib
import json
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from receiver_mask04_dual_zero_handoff import DATA_BYTES, controller
from receiver_timed_controller_handoff import BIT_TICKS
from zero_run_detector import CORE, ROM, line_octets

PREAMBLE_BITS = 64
DELAYS = (5, 18)


def first_non_reversal(bytes_):
    for bit_index in range(0, len(bytes_) * 8, 2):
        byte = bytes_[bit_index // 8]
        pair = (byte >> (bit_index % 8)) & 3
        if pair != 3:
            return bit_index // 2
    return None


def run(out=HERE / 'results/receiver-syndet-preamble-transition.json'):
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        exe = Path(temporary) / 'receiver-timed-controller-probe'
        subprocess.run(['cc', '-O2', '-Wall', '-Wno-unused-parameter',
                        '-DSAT_TRACE', '-I', str(CORE),
                        str(HERE / 'receiver_timed_controller_probe.c'),
                        *(str(CORE / name) for name in
                          ('core.c', 'opcodes.c', 'disasm.c')),
                        '-o', str(exe)], check=True)
        for delay in DELAYS:
            selector = 0x40 if delay == 5 else 0x60
            offsets = Counter()
            representative = None
            zero_line = line_octets([0] * DATA_BYTES, delay)
            if first_non_reversal(zero_line) != 0:
                raise ValueError('zero-run fixture does not start with non-11 dibit')
            for first_payload in range(256):
                line = line_octets([first_payload] + [0] * (DATA_BYTES - 1), delay)
                offset = first_non_reversal(line)
                offsets[offset] += 1
                if offset == 1 and representative is None:
                    representative = dict(first_payload=first_payload,
                                          line=line, offset=offset)
            if sum(offsets.values()) != 256 or offsets[0] != 192 or representative is None:
                raise ValueError('first-dibit distribution changed')
            zero_aligned = controller(exe, delay, selector, PREAMBLE_BITS, zero_line)
            candidate = representative
            exact = controller(exe, delay, selector, PREAMBLE_BITS,
                               candidate['line'])
            shifted = controller(exe, delay, selector,
                                 PREAMBLE_BITS + 2 * candidate['offset'],
                                 candidate['line'])
            if (zero_aligned['state'] != 0xB0 or
                    exact['consumed_bytes'] != candidate['line'] or
                    shifted['consumed_bytes'] == candidate['line']):
                raise ValueError('SYNDET transition control changed')
            row = dict(delay=delay, selector=f'{selector:02X}',
                       offset_distribution={str(k): v for k, v in
                                            sorted(offsets.items())},
                       zero_line=[f'{x:02X}' for x in zero_line],
                       representative=dict(first_payload=candidate['first_payload'],
                                           line=[f'{x:02X}' for x in candidate['line']],
                                           first_non_11_dibit=candidate['offset'],
                                           exact_pulse_before_bit=PREAMBLE_BITS,
                                           transition_pulse_before_bit=
                                           PREAMBLE_BITS + 2 * candidate['offset'],
                                           exact_result=exact,
                                           transition_result=shifted),
                       zero_aligned=zero_aligned)
            cases.append(row)
            print(delay, dict(offsets), candidate['line'][0],
                  exact['consumed_bytes'][:2], shifted['consumed_bytes'][:2],
                  flush=True)
    paths = [Path(__file__), HERE / 'receiver_mask04_dual_zero_handoff.py',
             HERE / 'receiver_timed_controller_handoff.py',
             HERE / 'receiver_timed_controller_probe.c',
             HERE / 'zero_run_detector.py',
             HERE.parents[1] / 'controller_scrambler.py',
             HERE.parent / 'assumed/execute.py', ROM,
             *(CORE / name for name in ('core.c', 'opcodes.c', 'disasm.c',
                                       'emu8051.h'))]
    report = dict(experiment='first non-11 data dibit as an external SYNDET source',
                  fixture=dict(preamble_bits=PREAMBLE_BITS,
                               data_bytes=DATA_BYTES,
                               delays=DELAYS, bit_ticks=BIT_TICKS,
                               payloads='all 256 first octets followed by seven zero octets'),
                  cases=cases,
                  limitations=['The detector is a hypothetical external circuit; no receiver output or SYNDET net is traced.',
                               'Only the first payload byte is exhaustively varied, with fixed scrambler history and later zero bytes.',
                               'The 8251 model is narrow and controller serial completion is synthetic.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
