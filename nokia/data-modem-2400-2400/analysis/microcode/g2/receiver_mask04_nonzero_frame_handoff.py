"""Challenge the long frame-mode PROM/USART handoff with nonzero first bytes."""

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from receiver_mask04_dual_feature_consensus import consensus, decisions, metrics
from receiver_mask04_dual_zero_handoff import (DATA_BYTES, PREAMBLE,
                                               VISITS_PER_SYMBOL, capture_zero_stream,
                                               controller, frozen_tables)
from receiver_mask04_feature_choice import alternative_states
from receiver_mask04_four_bit_transition import states_from_symbols
from receiver_mask04_protocol_preamble import (MAPPINGS, candidate, fixture,
                                               mapped, mapping_with_upper_source)
from receiver_mask04_serial_candidate import bytes_lsb_first
from receiver_mask04_controller_zero_handoff import dibits_from_bytes
from receiver_syndet_preamble_transition import first_non_reversal
from zero_run_detector import CORE, ROM, line_octets

PAYLOADS = ((5, 75, 1), (18, 165, 2))
FRAME_EDGE = PREAMBLE * VISITS_PER_SYMBOL * 4
MODE_READS = (PREAMBLE + DATA_BYTES * 4) * VISITS_PER_SYMBOL * 4 + 1


def run(out=HERE / 'results/receiver-mask04-nonzero-frame-handoff.json'):
    primary, alternative = frozen_tables()
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    modes = [0x81] * FRAME_EDGE + [0xA1] * (MODE_READS - FRAME_EDGE)
    rows = []
    with tempfile.TemporaryDirectory() as temporary:
        exe = Path(temporary) / 'receiver-timed-controller-probe'
        subprocess.run(['cc', '-O2', '-Wall', '-Wno-unused-parameter',
                        '-DSAT_TRACE', '-I', str(CORE),
                        str(HERE / 'receiver_timed_controller_probe.c'),
                        *(str(CORE / name) for name in
                          ('core.c', 'opcodes.c', 'disasm.c')),
                        '-o', str(exe)], check=True)
        for delay, degrees, first in PAYLOADS:
            payload = [first] + [0] * (DATA_BYTES - 1)
            offered = line_octets(payload, delay)
            if first_non_reversal(offered) != 1:
                raise ValueError('the first non-11 dibit is no longer late')
            trace = capture_zero_stream(mapping, base, degrees,
                                        dibits_from_bytes(offered), mode_values=modes)
            symbols = trace['symbols']
            expected = [row['dibit'] for row in symbols]
            p = decisions(states_from_symbols(symbols), primary)
            a = decisions(alternative_states(symbols), alternative)
            decoded = consensus(p, a)
            scores = metrics(decoded, expected)
            if scores['errors'] or scores['unknown']:
                raise ValueError(('PROM decision failure', delay, scores))
            bits = [bit for dibit in decoded[PREAMBLE:]
                    for bit in (dibit & 1, (dibit >> 1) & 1)]
            recovered = bytes_lsb_first(bits)
            if (recovered != offered or decoded[1:PREAMBLE] !=
                    [3] * (PREAMBLE - 1) or trace['mode_reads'] != MODE_READS):
                raise ValueError('PROM byte/edge recovery changed')
            selector = 0x40 if delay == 5 else 0x60
            aligned = controller(exe, delay, selector, 64, recovered)
            shifted = controller(exe, delay, selector, 66, recovered)
            if (aligned['state'] != 0xAF or aligned['consumed_bytes'] != offered or
                    aligned['decoded_bytes'] != payload or aligned['errors'] or
                    aligned['overruns'] or shifted['consumed_bytes'] == offered):
                raise ValueError('paced USART/8031 byte control changed')
            rows.append(dict(delay=delay, degrees=degrees, payload=payload,
                             offered_line_bytes=[f'{x:02X}' for x in offered],
                             recovered_line_bytes=[f'{x:02X}' for x in recovered],
                             first_non_11_dibit=1, score=scores,
                             prom_cycles=trace['cycles'],
                             trace_digest=trace['trace_digest'],
                             adc_stream_sha256=trace['adc_stream_sha256'],
                             mode_reads=trace['mode_reads'],
                             aligned=aligned, shifted=shifted))
            print(delay, degrees, scores, recovered, flush=True)
    paths = [Path(__file__), HERE / 'receiver_mask04_dual_zero_handoff.py',
             HERE / 'receiver_mask04_dual_feature_consensus.py',
             HERE / 'receiver_mask04_feature_choice.py',
             HERE / 'receiver_mask04_four_bit_transition.py',
             HERE / 'receiver_mask04_protocol_preamble.py',
             HERE / 'receiver_mask04_controller_zero_handoff.py',
             HERE / 'receiver_mask04_serial_candidate.py',
             HERE / 'receiver_syndet_preamble_transition.py',
             HERE / 'receiver_timed_controller_probe.c',
             HERE / 'zero_run_detector.py',
             HERE.parents[1] / 'controller_scrambler.py',
             MAPPINGS['q3'], ROM, HERE.parent / 'assumed/execute.py',
             *(CORE / name for name in ('core.c', 'opcodes.c', 'disasm.c',
                                       'emu8051.h')),
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(experiment='nonzero first-byte frame-mode receive PROM and paced USART handoff',
                  fixture=dict(payloads=PAYLOADS, frame_edge_wrapper_visit=FRAME_EDGE,
                               mode_reads=MODE_READS, aligned_pulse_bit=64,
                               first_non_11_pulse_bit=66),
                  cases=rows,
                  limitations=['The ADC, frame-byte, latch, serializer, RxD/RxC and SYNDET connections remain hypotheses.',
                               'The SYNDET pulse is placed by the fixture; its physical source is not identified.',
                               'The paced 8251 model and controller serial completion are synthetic.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
