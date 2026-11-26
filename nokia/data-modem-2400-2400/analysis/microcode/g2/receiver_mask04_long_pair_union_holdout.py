"""Hold out a new long seed for the frozen 46/93 + 47/94 receive union."""

import hashlib
import random
import sys
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
import receiver_mask04_multivisit_capture as capture_module
from receiver_mask04_dual_feature_consensus import consensus, decisions
from receiver_mask04_dual_zero_handoff import frozen_tables
from receiver_mask04_feature_choice import alternative_states
from receiver_mask04_four_bit_transition import states_from_symbols
from receiver_mask04_frequency_offset import offset_transmit
from receiver_mask04_long_pair_union import PHASES, classify
from receiver_mask04_offset_visit_phase import project

SEED = 0x93B5
DATA_SYMBOLS = 64
CASES = ((-7, 75), (-7, 165), (7, 75), (7, 165))
PAIRS = ((46, 93), (47, 94))


def run(out=HERE / 'results/receiver-mask04-long-pair-union-holdout.json'):
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
        expected = [symbol['dibit'] for symbol in trace['symbols']]
        variants = {}
        predictions = {}
        for first, second in PAIRS:
            symbols = project(trace['symbols'], first, second)
            p = decisions(states_from_symbols(symbols), primary)
            a = decisions(alternative_states(symbols), alternative)
            both = consensus(p, a)
            key = f'{first}/{second}'
            predictions[key] = both
            variants[key] = dict(primary=classify(p, expected),
                                 alternative=classify(a, expected),
                                 consensus=classify(both, expected))
        pair_conflicts = [i for i in range(1, len(expected))
                          if predictions['46/93'][i] is not None and
                          predictions['47/94'][i] is not None and
                          predictions['46/93'][i] != predictions['47/94'][i]]
        pair_union = consensus(predictions['46/93'], predictions['47/94'])
        row = dict(offset_hz=offset_hz, degrees=degrees,
                   trace_digest=trace['trace_digest'],
                   adc_stream_sha256=trace['adc_stream_sha256'],
                   variants=variants,
                   conservative_union=classify(pair_union, expected),
                   pair_conflicts=pair_conflicts)
        rows.append(row)
        print(offset_hz, degrees,
              '46/93', variants['46/93']['consensus'],
              '47/94', variants['47/94']['consensus'],
              'union', row['conservative_union'],
              'conflicts', pair_conflicts, flush=True)
    aggregate = dict(
        checks=sum(row['conservative_union']['checks'] for row in rows),
        errors=sum(row['conservative_union']['errors'] for row in rows),
        unknown=sum(row['conservative_union']['unknown'] for row in rows),
        data_errors=sum(row['conservative_union']['data_errors'] for row in rows),
        data_unknown=sum(row['conservative_union']['data_unknown'] for row in rows),
        pair_conflicts=sum(len(row['pair_conflicts']) for row in rows))
    paths = [Path(__file__),
             HERE / 'receiver_mask04_long_pair_union.py',
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
    report = dict(experiment='fresh long-seed frozen receive pair-union validation',
                  fixture=dict(seed=SEED, data_dibits=middle,
                               data_symbols=DATA_SYMBOLS, cases=CASES,
                               capture_phases=PHASES, pairs=PAIRS,
                               adc_visits=adc_visits, cycles=cycles,
                               mapping='joint upper-source mask 04',
                               adc='complementary PCM, 47/46 visits per sample'),
                  cases=rows, aggregate=aggregate,
                  limitations=[
                      'The pair union and decision tables were frozen before this seed; both are external readout hypotheses.',
                      'The reference receiver checks each generated PCM stream; neither physical ADC sampling nor USART routing is established.',
                      'A correct result at these offsets, phases and length does not prove unlimited carrier acquisition or noise tolerance.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    print(run()['aggregate'])
