"""Test a frozen ADC-magnitude capture selector on new long PROM streams."""

import hashlib
import random
import sys
from collections import Counter
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
from receiver_mask04_holdout_gap_audit import adc_sample
from receiver_mask04_long_pair_union import classify
from receiver_mask04_offset_visit_phase import project

SEED = 0xE35A
DATA_SYMBOLS = 64
CASES = ((-7, 75), (-7, 165), (7, 75), (7, 165))
PAIRS = ((46, 93), (47, 94), (94, 141))
PHASES = (46, 47, 93, 94, 141)


def confidence(pcm, symbol, pair):
    samples = [adc_sample(pcm, index, phase)['complementary_byte']
               for index in (symbol - 1, symbol)
               for phase in pair]
    return min(abs(value - 127) for value in samples)


def select(pcm, predictions):
    count = len(next(iter(predictions.values())))
    chosen = [None]
    selected = [None]
    for symbol in range(1, count):
        ranked = sorted(PAIRS, key=lambda pair: -confidence(pcm, symbol, pair))
        pick = next((pair for pair in ranked
                     if predictions[pair][symbol] is not None), None)
        selected.append(f'{pick[0]}/{pick[1]}' if pick is not None else None)
        chosen.append(predictions[pick][symbol] if pick is not None else None)
    return chosen, selected


def run(out=HERE / 'results/receiver-mask04-adc-margin-selector.json'):
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
        dibits = [3] * capture_module.PREAMBLE_SYMBOLS + middle + [0] * 8
        pcm = offset_transmit(dibits, degrees, offset_hz)
        with patch.object(capture_module, 'DATA_SYMBOLS', DATA_SYMBOLS), \
                patch.object(capture_module, 'ADC_VISITS', adc_visits), \
                patch.object(capture_module, 'CYCLES', cycles), \
                patch.object(capture_module, 'PHASES', PHASES), \
                patch.object(capture_module, 'rotated_transmit',
                             lambda values, angle: offset_transmit(
                                 values, angle, offset_hz)):
            trace = capture_module.capture(mapping, base, degrees, middle)
        expected = [symbol['dibit'] for symbol in trace['symbols']]
        predictions = {}
        variants = {}
        for pair in PAIRS:
            symbols = project(trace['symbols'], *pair)
            p = decisions(states_from_symbols(symbols), primary)
            a = decisions(alternative_states(symbols), alternative)
            both = consensus(p, a)
            predictions[pair] = both
            variants[f'{pair[0]}/{pair[1]}'] = classify(both, expected)
        baseline = consensus(predictions[PAIRS[0]], predictions[PAIRS[1]])
        picked, selected = select(pcm, predictions)
        row = dict(offset_hz=offset_hz, degrees=degrees,
                   trace_digest=trace['trace_digest'],
                   adc_stream_sha256=trace['adc_stream_sha256'],
                   variants=variants,
                   conservative_two_pair=classify(baseline, expected),
                   adc_margin_selector=classify(picked, expected),
                   selected_pair_counts=dict(Counter(selected[1:])),
                   wrong_choices=[dict(symbol=i, pair=selected[i],
                                       confidence=confidence(
                                           pcm, i,
                                           next(pair for pair in PAIRS
                                                if f'{pair[0]}/{pair[1]}' ==
                                                selected[i])))
                                  for i in range(1, len(picked))
                                  if picked[i] is not None and
                                  picked[i] != expected[i]])
        rows.append(row)
        print(offset_hz, degrees,
              'baseline', row['conservative_two_pair'],
              'margin', row['adc_margin_selector'],
              row['selected_pair_counts'], flush=True)
    aggregate = {name: dict(
        checks=sum(row[name]['checks'] for row in rows),
        errors=sum(row[name]['errors'] for row in rows),
        unknown=sum(row[name]['unknown'] for row in rows),
        data_errors=sum(row[name]['data_errors'] for row in rows),
        data_unknown=sum(row[name]['data_unknown'] for row in rows))
        for name in ('conservative_two_pair', 'adc_margin_selector')}
    paths = [Path(__file__),
             HERE / 'receiver_mask04_holdout_gap_audit.py',
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
    report = dict(experiment='new-seed ADC-magnitude receive capture selection',
                  fixture=dict(seed=SEED, data_dibits=middle,
                               data_symbols=DATA_SYMBOLS, cases=CASES,
                               capture_phases=PHASES, pairs=PAIRS,
                               adc_midpoint=127, adc_visits=adc_visits,
                               cycles=cycles,
                               mapping='joint upper-source mask 04',
                               adc='complementary PCM, 47/46 visits per sample'),
                  selector='For each decision, rank three sample pairs by the minimum absolute ADC distance from 127 across both symbols and both samples; choose the first pair with a known frozen-table decision; ties retain pair order.',
                  cases=rows, aggregate=aggregate,
                  limitations=[
                      'The selector was motivated by inspected gaps but frozen before this new seed; no reference labels enter its choices or either table.',
                      'This is an external signal-confidence hypothesis, not identified Nokia phase-tracking circuitry.',
                      'ADC range, sample clocks, latch logic and USART routing remain assumptions.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    print(run()['aggregate'])
