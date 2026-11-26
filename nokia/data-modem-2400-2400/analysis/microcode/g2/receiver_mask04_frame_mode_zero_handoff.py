"""Carry a controller frame-byte edge through the PROM receiver and paced USART."""

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
from receiver_mask04_dual_zero_handoff import (ANGLES, DATA_BYTES, PREAMBLE,
                                               VISITS_PER_SYMBOL, capture_zero_stream,
                                               controller, frozen_tables)
from receiver_mask04_feature_choice import alternative_states
from receiver_mask04_four_bit_transition import states_from_symbols
from receiver_mask04_protocol_preamble import (MAPPINGS, candidate, fixture,
                                               mapped, mapping_with_upper_source)
from receiver_mask04_serial_candidate import bytes_lsb_first
from receiver_mask04_controller_zero_handoff import dibits_from_bytes
from receiver_timed_controller_handoff import BIT_TICKS
from zero_run_detector import CORE, ROM, line_octets

BASELINE = HERE / 'results/receiver-mask04-dual-zero-handoff.json'
WRAPPER_PER_ADC_VISIT = 4
FRAME_EDGE_WRAPPER_VISIT = PREAMBLE * VISITS_PER_SYMBOL * WRAPPER_PER_ADC_VISIT
DATA_DIBITS = DATA_BYTES * 4
ADC_VISITS = (PREAMBLE + DATA_DIBITS) * VISITS_PER_SYMBOL
WRAPPER_VISITS = WRAPPER_PER_ADC_VISIT * ADC_VISITS + 1


def run(out=HERE / 'results/receiver-mask04-frame-mode-zero-handoff.json'):
    baseline = json.loads(BASELINE.read_text())
    primary, alternative = frozen_tables()
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    modes = ([0x81] * FRAME_EDGE_WRAPPER_VISIT +
             [0xA1] * (WRAPPER_VISITS - FRAME_EDGE_WRAPPER_VISIT))
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        exe = Path(temporary) / 'receiver-timed-controller-probe'
        subprocess.run(['cc', '-O2', '-Wall', '-Wno-unused-parameter',
                        '-DSAT_TRACE', '-I', str(CORE),
                        str(HERE / 'receiver_timed_controller_probe.c'),
                        *(str(CORE / name) for name in
                          ('core.c', 'opcodes.c', 'disasm.c')),
                        '-o', str(exe)], check=True)
        for delay, degrees in ANGLES:
            offered = line_octets([0] * DATA_BYTES, delay)
            data_dibits = dibits_from_bytes(offered)
            trace = capture_zero_stream(mapping, base, degrees, data_dibits,
                                        mode_values=modes)
            if (trace['mode_reads'] != WRAPPER_VISITS or
                    trace['candidate_clock_edges'] != ADC_VISITS + 1):
                raise ValueError('frame-mode PROM timing changed')
            symbols = trace['symbols']
            expected = [row['dibit'] for row in symbols]
            p = decisions(states_from_symbols(symbols), primary)
            a = decisions(alternative_states(symbols), alternative)
            decoded = consensus(p, a)
            scores = dict(primary=metrics(p, expected),
                          alternative=metrics(a, expected),
                          consensus=metrics(decoded, expected))
            if scores['consensus']['errors'] or scores['consensus']['unknown']:
                raise ValueError(('frame-mode receive decisions changed', degrees, scores))
            bits = [bit for dibit in decoded[PREAMBLE:]
                    for bit in (dibit & 1, (dibit >> 1) & 1)]
            recovered = bytes_lsb_first(bits)
            if (recovered != offered or decoded[1:PREAMBLE] !=
                    [3] * (PREAMBLE - 1)):
                raise ValueError('frame-mode line stream changed')
            selector = 0x40 if delay == 5 else 0x60
            aligned = controller(exe, delay, selector, 64, recovered)
            early = controller(exe, delay, selector, 63, recovered)
            late = controller(exe, delay, selector, 65, recovered)
            absent = controller(exe, delay, selector, 128, recovered)
            opposite = controller(exe, delay,
                                  0x60 if selector == 0x40 else 0x40,
                                  64, recovered)
            if (aligned['state'] != 0xB0 or aligned['zero_octets'] != DATA_BYTES or
                    aligned['consumed_bytes'] != recovered or
                    aligned['decoded_bytes'] != [0] * DATA_BYTES or
                    aligned['errors'] or aligned['overruns'] or
                    any(row['state'] != 0xAF for row in
                        (early, late, absent, opposite))):
                raise ValueError('frame-mode controller handoff changed')
            prior = next(row for row in baseline['cases'] if row['degrees'] == degrees)
            if (prior['recovered_line_bytes'] != [f'{x:02X}' for x in recovered] or
                    prior['trace_digest'] == trace['trace_digest']):
                raise ValueError('mode route failed to distinguish full PROM trace')
            row = dict(degrees=degrees, polynomial_delay=delay,
                       trace_digest=trace['trace_digest'],
                       baseline_trace_digest=prior['trace_digest'],
                       adc_stream_sha256=trace['adc_stream_sha256'],
                       candidate_clock_edges=trace['candidate_clock_edges'],
                       mode_reads=trace['mode_reads'],
                       recovered_line_bytes=[f'{x:02X}' for x in recovered],
                       scores=scores,
                       controller=dict(aligned=aligned, early=early,
                                       late=late, absent=absent,
                                       opposite_selector=opposite))
            cases.append(row)
            print(degrees, scores['consensus'], row['recovered_line_bytes'],
                  aligned['state'], flush=True)
    paths = [Path(__file__), BASELINE,
             HERE / 'receiver_mask04_dual_zero_handoff.py',
             HERE / 'receiver_mask04_dual_feature_consensus.py',
             HERE / 'receiver_mask04_feature_choice.py',
             HERE / 'receiver_mask04_four_bit_transition.py',
             HERE / 'receiver_mask04_cubic_transition.py',
             HERE / 'receiver_mask04_serial_candidate.py',
             HERE / 'receiver_mask04_controller_zero_handoff.py',
             HERE / 'receiver_timed_controller_handoff.py',
             HERE / 'receiver_timed_controller_probe.c',
             HERE / 'zero_run_detector.py',
             HERE / 'results/receiver-mask04-four-bit-transition.json',
             HERE / 'results/receiver-mask04-feature-choice.json',
             HERE / 'results/receiver-mask04-multivisit-capture.json',
             HERE / 'results/receiver-mask04-three-bit-two-visit.json',
             MAPPINGS['q3'], ROM, HERE.parent / 'assumed/execute.py',
             *(CORE / name for name in ('core.c', 'opcodes.c', 'disasm.c',
                                       'emu8051.h')),
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(experiment='controller 81-to-A1 frame edge through real-PROM receive and paced 8251/8031 handoff',
                  fixture=dict(angles=ANGLES, data_bytes=DATA_BYTES,
                               frame_edge_wrapper_visit=FRAME_EDGE_WRAPPER_VISIT,
                               wrapper_visits=WRAPPER_VISITS,
                               mode='81 before data, A1 after data boundary',
                               controller_bit_ticks=BIT_TICKS),
                  cases=cases,
                  limitations=['The controller frame-byte-to-3EB, ADC, latch, decision, RxD/RxC and SYNDET routes are not traced.',
                               'The mode edge is projected to the symbol boundary; the DSC and 8031 execute sequentially under an exact-rate timing hypothesis.',
                               'The paced USART model uses synthetic 8031 serial completion and remains a conditional C3 handoff.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
