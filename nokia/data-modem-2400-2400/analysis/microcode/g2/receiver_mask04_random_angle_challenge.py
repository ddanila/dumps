"""Challenge frozen PROM receive decisions with random payloads at new angles."""

import hashlib
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from receiver_mask04_dual_feature_consensus import consensus, decisions, metrics
from receiver_mask04_dual_zero_handoff import (
    DATA_BYTES, PREAMBLE, VISITS_PER_SYMBOL, capture_zero_stream,
    frozen_tables,
)
from receiver_mask04_feature_choice import alternative_states
from receiver_mask04_four_bit_transition import states_from_symbols
from receiver_mask04_protocol_preamble import (
    MAPPINGS, candidate, fixture, mapped, mapping_with_upper_source,
)
from receiver_mask04_serial_candidate import bytes_lsb_first
from receiver_mask04_controller_zero_handoff import dibits_from_bytes
from zero_run_detector import line_octets

FIXTURES = ((5, 15, 0x2847), (5, 105, 0x3557),
            (18, 15, 0x2848), (18, 105, 0x3558))
FRAME_EDGE = PREAMBLE * VISITS_PER_SYMBOL * 4
MODE_READS = (PREAMBLE + DATA_BYTES * 4) * VISITS_PER_SYMBOL * 4 + 1


def run(out=HERE / 'results/receiver-mask04-random-angle-challenge.json'):
    primary, alternative = frozen_tables()
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    modes = [0x81] * FRAME_EDGE + [0xA1] * (MODE_READS - FRAME_EDGE)
    rows = []
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
        data_decisions = decoded[PREAMBLE:]
        recovered = None
        if all(value is not None for value in data_decisions):
            bits = [bit for dibit in data_decisions
                    for bit in (dibit & 1, (dibit >> 1) & 1)]
            recovered = bytes_lsb_first(bits)
        wrong_indices = [index for index, (got, want) in enumerate(
            zip(decoded, expected)) if index and got is not None and got != want]
        unknown_indices = [index for index, value in enumerate(decoded)
                           if index and value is None]
        rows.append(dict(delay=delay, degrees=degrees, seed=seed,
                         payload=[f'{x:02X}' for x in payload],
                         offered_line_bytes=[f'{x:02X}' for x in offered],
                         recovered_line_bytes=([f'{x:02X}' for x in recovered]
                                               if recovered is not None else None),
                         score=scores, wrong_indices=wrong_indices,
                         unknown_indices=unknown_indices,
                         prom_cycles=trace['cycles'],
                         trace_digest=trace['trace_digest'],
                         adc_stream_sha256=trace['adc_stream_sha256'],
                         mode_reads=trace['mode_reads']))
        print(delay, degrees, hex(seed), scores, flush=True)
    paths = (Path(__file__), HERE / 'receiver_mask04_dual_zero_handoff.py',
             HERE / 'receiver_mask04_dual_feature_consensus.py',
             HERE / 'receiver_mask04_feature_choice.py',
             HERE / 'receiver_mask04_four_bit_transition.py',
             HERE / 'receiver_mask04_protocol_preamble.py',
             HERE / 'receiver_mask04_controller_zero_handoff.py',
             HERE / 'receiver_mask04_serial_candidate.py',
             HERE / 'zero_run_detector.py',
             HERE.parents[1] / 'controller_scrambler.py',
             MAPPINGS['q3'], HERE.parent / 'assumed/execute.py',
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='new-angle random eight-byte PROM receive readout challenge',
                  fixture=dict(seeds_angles=FIXTURES, payload_bytes=DATA_BYTES,
                               frame_edge_wrapper_visit=FRAME_EDGE,
                               mode_reads=MODE_READS,
                               rule='unchanged frozen primary/alternative consensus'),
                  cases=rows,
                  aggregate=dict(checks=sum(row['score']['checks'] for row in rows),
                                 errors=sum(row['score']['errors'] for row in rows),
                                 unknown=sum(row['score']['unknown'] for row in rows)),
                  limitations=['The ADC and frame-byte routes, capture logic, serializer and USART wires remain assumed.',
                               'The tested angles and payload seeds are a bounded challenge, not a full carrier/noise sweep.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
