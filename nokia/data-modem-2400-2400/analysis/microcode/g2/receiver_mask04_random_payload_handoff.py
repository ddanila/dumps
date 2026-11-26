"""Challenge the frozen receive readout with eight-byte nonzero payloads."""

import hashlib
import random
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from receiver_mask04_dual_feature_consensus import consensus, decisions, metrics
from receiver_mask04_dual_zero_handoff import (
    DATA_BYTES, PREAMBLE, VISITS_PER_SYMBOL, capture_zero_stream,
    controller, frozen_tables,
)
from receiver_mask04_feature_choice import alternative_states
from receiver_mask04_four_bit_transition import states_from_symbols
from receiver_mask04_protocol_preamble import (
    MAPPINGS, candidate, fixture, mapped, mapping_with_upper_source,
)
from receiver_mask04_serial_candidate import bytes_lsb_first
from receiver_mask04_controller_zero_handoff import dibits_from_bytes
from zero_run_detector import CORE, ROM, line_octets

FIXTURES = ((5, 75, 0x2847), (5, 75, 0x3557),
            (18, 165, 0x2848), (18, 165, 0x3558))
FRAME_EDGE = PREAMBLE * VISITS_PER_SYMBOL * 4
MODE_READS = (PREAMBLE + DATA_BYTES * 4) * VISITS_PER_SYMBOL * 4 + 1


def run(out=HERE / 'results/receiver-mask04-random-payload-handoff.json'):
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
                        '-o', str(exe)], check=True,
                       capture_output=True, text=True)
        for delay, degrees, seed in FIXTURES:
            generator = random.Random(seed)
            payload = [generator.randrange(1, 256) for _ in range(DATA_BYTES)]
            offered = line_octets(payload, delay)
            trace = capture_zero_stream(mapping, base, degrees,
                                        dibits_from_bytes(offered), mode_values=modes)
            symbols = trace['symbols']
            expected = [row['dibit'] for row in symbols]
            p = decisions(states_from_symbols(symbols), primary)
            a = decisions(alternative_states(symbols), alternative)
            decoded = consensus(p, a)
            scores = metrics(decoded, expected)
            if scores['errors'] or scores['unknown']:
                raise ValueError(('frozen PROM readout missed random payload',
                                  delay, seed, scores))
            bits = [bit for dibit in decoded[PREAMBLE:]
                    for bit in (dibit & 1, (dibit >> 1) & 1)]
            recovered = bytes_lsb_first(bits)
            if (recovered != offered or decoded[1:PREAMBLE] !=
                    [3] * (PREAMBLE - 1) or trace['mode_reads'] != MODE_READS):
                raise ValueError(('PROM byte recovery changed', delay, seed))
            selector = 0x40 if delay == 5 else 0x60
            aligned = controller(exe, delay, selector, 64, recovered)
            early = controller(exe, delay, selector, 63, recovered)
            late = controller(exe, delay, selector, 65, recovered)
            wrong_selector = controller(exe, delay, 0x60 if delay == 5 else 0x40,
                                        64, recovered)
            if (aligned['consumed_bytes'] != offered or
                    aligned['decoded_bytes'] != payload or
                    aligned['errors'] or aligned['overruns'] or
                    any(control['decoded_bytes'] == payload for control in
                        (early, late, wrong_selector))):
                raise ValueError(('paced USART/8031 control failed', delay, seed))
            rows.append(dict(delay=delay, degrees=degrees, seed=seed,
                             payload=[f'{x:02X}' for x in payload],
                             line_bytes=[f'{x:02X}' for x in offered],
                             recovered_line_bytes=[f'{x:02X}' for x in recovered],
                             score=scores,
                             prom_cycles=trace['cycles'],
                             trace_digest=trace['trace_digest'],
                             adc_stream_sha256=trace['adc_stream_sha256'],
                             mode_reads=trace['mode_reads'],
                             aligned=aligned, early=early, late=late,
                             wrong_selector=wrong_selector))
            print(delay, hex(seed), scores, 'aligned bytes',
                  len(aligned['consumed_bytes']), flush=True)
    paths = (Path(__file__), HERE / 'receiver_mask04_dual_zero_handoff.py',
             HERE / 'receiver_mask04_dual_feature_consensus.py',
             HERE / 'receiver_mask04_feature_choice.py',
             HERE / 'receiver_mask04_four_bit_transition.py',
             HERE / 'receiver_mask04_protocol_preamble.py',
             HERE / 'receiver_mask04_controller_zero_handoff.py',
             HERE / 'receiver_mask04_serial_candidate.py',
             HERE / 'receiver_timed_controller_probe.c',
             HERE / 'zero_run_detector.py',
             HERE.parents[1] / 'controller_scrambler.py',
             MAPPINGS['q3'], ROM, HERE.parent / 'assumed/execute.py',
             *(CORE / name for name in ('core.c', 'opcodes.c', 'disasm.c',
                                       'emu8051.h')),
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='random eight-byte frame-mode receive PROM and paced USART handoff',
                  fixture=dict(seeds=FIXTURES, payload_bytes=DATA_BYTES,
                               frame_edge_wrapper_visit=FRAME_EDGE,
                               mode_reads=MODE_READS,
                               aligned_pulse_bit=64,
                               controls='SYNDET one bit early/late and opposite controller selector'),
                  cases=rows,
                  limitations=['The ADC, frame-byte, capture logic, serializer, RxD/RxC and SYNDET connections remain hypotheses.',
                               'The SYNDET pulse is placed by the fixture; its physical source is not identified.',
                               'The reference line encoder and paced 8251 model are separate from the physical modem.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
