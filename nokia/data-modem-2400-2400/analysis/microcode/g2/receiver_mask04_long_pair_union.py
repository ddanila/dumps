"""Recheck long offset traces with frozen readouts on two ADC sample edges."""

import hashlib
import json
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
from receiver_mask04_long_offset import CASES, DATA_SYMBOLS, SEED

PRIOR = HERE / 'results/receiver-mask04-long-offset.json'
PHASES = (46, 47, 93, 94)
PAIRS = ((46, 93), (47, 94), (46, 94), (47, 93))


def classify(values, expected):
    result = metrics(values, expected)
    result['wrong_symbols'] = [i for i in range(1, len(values))
                               if values[i] is not None and
                               values[i] != expected[i]]
    result['unknown_symbols'] = [i for i in range(1, len(values))
                                 if values[i] is None]
    return result


def run(out=HERE / 'results/receiver-mask04-long-pair-union.json'):
    prior = json.loads(PRIOR.read_text())
    generator = random.Random(SEED)
    middle = [generator.randrange(4) for _ in range(DATA_SYMBOLS)]
    if middle != prior['fixture']['data_dibits']:
        raise ValueError('long-stream data changed')
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
        old = next(row for row in prior['cases']
                   if row['offset_hz'] == offset_hz and
                   row['degrees'] == degrees)
        if (trace['trace_digest'] != old['trace_digest'] or
                trace['adc_stream_sha256'] != old['adc_stream_sha256']):
            raise ValueError('PROM stream differs from prior long run')
        expected = [symbol['dibit'] for symbol in trace['symbols']]
        predictions = {}
        variants = {}
        for first, second in PAIRS:
            symbols = project(trace['symbols'], first, second)
            p = decisions(states_from_symbols(symbols), primary)
            a = decisions(alternative_states(symbols), alternative)
            both = consensus(p, a)
            key = f'{first}/{second}'
            predictions[key] = both
            variants[key] = dict(primary=classify(p, expected),
                                 alternative=classify(a, expected),
                                 consensus=classify(both, expected),
                                 conflicts=[i for i in range(1, len(p))
                                            if p[i] is not None and
                                            a[i] is not None and p[i] != a[i]])
        baseline = variants['46/93']['consensus']
        if (baseline['errors'] != old['consensus']['errors'] or
                baseline['unknown'] != old['consensus']['unknown'] or
                baseline['unknown_symbols'] != old['unknown_symbols']):
            raise ValueError('frozen 46/93 result differs from prior run')
        pair_union = consensus(predictions['46/93'], predictions['47/94'])
        pair_conflicts = [i for i in range(1, len(expected))
                          if predictions['46/93'][i] is not None and
                          predictions['47/94'][i] is not None and
                          predictions['46/93'][i] != predictions['47/94'][i]]
        row = dict(offset_hz=offset_hz, degrees=degrees,
                   trace_digest=trace['trace_digest'],
                   adc_stream_sha256=trace['adc_stream_sha256'],
                   variants=variants,
                   conservative_union=classify(pair_union, expected),
                   pair_conflicts=pair_conflicts)
        rows.append(row)
        print(offset_hz, degrees,
              {key: value['consensus']['unknown_symbols']
               for key, value in variants.items()},
              'union', row['conservative_union'],
              'conflicts', pair_conflicts, flush=True)
    paths = [Path(__file__), PRIOR,
             HERE / 'receiver_mask04_long_offset.py',
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
    report = dict(experiment='long receive adjacent-pair union on identical PROM traces',
                  fixture=dict(seed=SEED, data_symbols=DATA_SYMBOLS,
                               cases=CASES, capture_phases=PHASES,
                               pairs=PAIRS, adc_visits=adc_visits,
                               cycles=cycles,
                               mapping='joint upper-source mask 04',
                               adc='complementary PCM, 47/46 visits per sample'),
                  cases=rows,
                  limitations=[
                      'All tables and case choices are frozen, but these phase-pair variants are exploratory external readouts.',
                      'A union accepts a dibit only when the two pair readouts agree or one abstains; a disagreement remains unknown.',
                      'The two physical capture clocks, readout logic and USART path have not been identified.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
