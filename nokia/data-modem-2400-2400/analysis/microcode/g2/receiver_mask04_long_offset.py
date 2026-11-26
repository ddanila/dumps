"""Stress the frozen 46/93 receive readout over a 96-symbol PROM stream."""

import hashlib
import random
import sys
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
import receiver_mask04_multivisit_capture as capture_module
from receiver_mask04_dual_feature_consensus import consensus, decisions, metrics
from receiver_mask04_dual_zero_handoff import frozen_tables
from receiver_mask04_feature_choice import alternative_states
from receiver_mask04_four_bit_transition import states_from_symbols
from receiver_mask04_frequency_offset import offset_transmit
from receiver_mask04_offset_visit_phase import project

SEED = 0x7E2A
DATA_SYMBOLS = 64
PHASES = (46, 93)
CASES = ((-7, 165), (0, 165), (7, 75), (7, 165))


def run(out=HERE / 'results/receiver-mask04-long-offset.json'):
    generator = random.Random(SEED)
    middle = [generator.randrange(4) for _ in range(DATA_SYMBOLS)]
    primary, alternative = frozen_tables()
    mapping = capture_module.candidate(
        capture_module.mapping_with_upper_source(0, '17.6'),
        capture_module.mapped(capture_module.MAPPINGS['q3']), 4)
    _, base = capture_module.fixture()
    adc_visits = (capture_module.PREAMBLE_SYMBOLS + DATA_SYMBOLS) * \
        capture_module.VISITS_PER_SYMBOL
    cycles = 32 * adc_visits + 47
    rows = []
    for offset_hz, degrees in CASES:
        with patch.object(capture_module, 'DATA_SYMBOLS', DATA_SYMBOLS), \
                patch.object(capture_module, 'ADC_VISITS', adc_visits), \
                patch.object(capture_module, 'CYCLES', cycles), \
                patch.object(capture_module, 'PHASES', PHASES), \
                patch.object(capture_module, 'rotated_transmit',
                             lambda values, angle: offset_transmit(
                                 values, angle, offset_hz)):
            trace = capture_module.capture(mapping, base, degrees, middle)
        symbols = project(trace['symbols'], *PHASES)
        expected = [symbol['dibit'] for symbol in symbols]
        p = decisions(states_from_symbols(symbols), primary)
        a = decisions(alternative_states(symbols), alternative)
        both = consensus(p, a)
        row = dict(offset_hz=offset_hz, degrees=degrees,
                   trace_digest=trace['trace_digest'],
                   adc_stream_sha256=trace['adc_stream_sha256'],
                   primary=metrics(p, expected),
                   alternative=metrics(a, expected),
                   consensus=metrics(both, expected),
                   wrong_symbols=[i for i in range(1, len(expected))
                                  if both[i] is not None and
                                  both[i] != expected[i]],
                   unknown_symbols=[i for i in range(1, len(expected))
                                    if both[i] is None],
                   conflicts=[i for i in range(1, len(expected))
                              if p[i] is not None and a[i] is not None and
                              p[i] != a[i]])
        rows.append(row)
        print(offset_hz, degrees, row['consensus'],
              'wrong', row['wrong_symbols'],
              'unknown', row['unknown_symbols'], flush=True)
    paths = [Path(__file__),
             HERE / 'receiver_mask04_frequency_offset.py',
             HERE / 'receiver_mask04_offset_visit_phase.py',
             HERE / 'receiver_mask04_multivisit_capture.py',
             HERE / 'receiver_mask04_dual_feature_consensus.py',
             HERE / 'receiver_mask04_dual_zero_handoff.py',
             HERE / 'receiver_mask04_feature_choice.py',
             HERE / 'receiver_mask04_four_bit_transition.py',
             HERE / 'results/receiver-mask04-four-bit-transition.json',
             HERE / 'results/receiver-mask04-feature-choice.json',
             capture_module.MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(experiment='long frozen 46/93 receive under carrier offset',
                  fixture=dict(seed=SEED, data_dibits=middle,
                               preamble_symbols=capture_module.PREAMBLE_SYMBOLS,
                               data_symbols=DATA_SYMBOLS,
                               phases=PHASES, cases=CASES,
                               adc_visits=adc_visits, cycles=cycles,
                               mapping='joint upper-source mask 04',
                               adc='complementary PCM, 47/46 visits per sample'),
                  cases=rows,
                  limitations=[
                      'The reference receiver checks each generated PCM input; the ADC and capture-clock routes remain assumptions.',
                      'The two decision tables and selected 46/93 visits are frozen from earlier experiments; no labels from these streams enter either table.',
                      'A correct diagnostic readout does not by itself identify the actual modem decision or USART output circuit.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
