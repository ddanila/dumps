"""Inspect executed receive bytes around long-stream holdout gaps."""

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
from receiver_mask04_dual_feature_consensus import consensus, decisions
from receiver_mask04_dual_zero_handoff import frozen_tables
from receiver_mask04_feature_choice import alternative_states
from receiver_mask04_four_bit_transition import states_from_symbols
from receiver_mask04_frequency_offset import offset_transmit
from receiver_mask04_long_pair_union import classify
from receiver_mask04_long_pair_union_holdout import DATA_SYMBOLS, SEED
from receiver_mask04_offset_visit_phase import project

PRIOR = HERE / 'results/receiver-mask04-long-pair-union-holdout.json'
CASES = ((7, 75, 60), (7, 165, 32))
PAIRS = ((46, 93), (47, 94), (93, 140), (94, 141),
         (140, 187), (141, 188))
PHASES = tuple(sorted(set((0, 1, 44, 45, 46, 47, 48, 49,
                           91, 92, 93, 94, 95, 96, 140, 141,
                           187, 188, 234, 235, 281, 282,
                           328, 329, 374))))


def adc_sample(pcm, symbol, phase):
    boundary = 0
    for sample in range(8):
        boundary += 47 if sample < 7 else 46
        if phase < boundary:
            return dict(sample=sample,
                        complementary_byte=127 - pcm[8 * symbol + sample])
    raise ValueError(('invalid visit phase', phase))


def run(out=HERE / 'results/receiver-mask04-holdout-gap-audit.json'):
    prior = json.loads(PRIOR.read_text())
    generator = random.Random(SEED)
    middle = [generator.randrange(4) for _ in range(DATA_SYMBOLS)]
    if middle != prior['fixture']['data_dibits']:
        raise ValueError('holdout data changed')
    primary, alternative = frozen_tables()
    mapping = capture_module.candidate(
        capture_module.mapping_with_upper_source(0, '17.6'),
        capture_module.mapped(capture_module.MAPPINGS['q3']), 4)
    _, base = capture_module.fixture()
    adc_visits = (capture_module.PREAMBLE_SYMBOLS + DATA_SYMBOLS) * \
        capture_module.VISITS_PER_SYMBOL
    cycles = 32 * adc_visits + 47
    rows = []
    for offset_hz, degrees, target in CASES:
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
        old = next(row for row in prior['cases']
                   if row['offset_hz'] == offset_hz and
                   row['degrees'] == degrees)
        if (trace['trace_digest'] != old['trace_digest'] or
                trace['adc_stream_sha256'] != old['adc_stream_sha256']):
            raise ValueError('PROM stream differs from holdout')
        expected = [symbol['dibit'] for symbol in trace['symbols']]
        variants = {}
        for first, second in PAIRS:
            symbols = project(trace['symbols'], first, second)
            p = decisions(states_from_symbols(symbols), primary)
            a = decisions(alternative_states(symbols), alternative)
            both = consensus(p, a)
            variants[f'{first}/{second}'] = dict(
                primary_at_target=p[target],
                alternative_at_target=a[target],
                consensus_at_target=both[target],
                score=classify(both, expected))
        for key in ('46/93', '47/94'):
            result = variants[key]['score']
            baseline = old['variants'][key]['consensus']
            if (result['errors'], result['unknown_symbols']) != \
                    (baseline['errors'], baseline['unknown_symbols']):
                raise ValueError('baseline pair differs from holdout')
        snapshots = []
        for symbol in range(target - 2, target + 3):
            source = trace['symbols'][symbol]
            snapshots.append(dict(symbol=symbol, dibit=source['dibit'],
                                  visits={str(phase): dict(
                                      **source['visits'][str(phase)],
                                      adc=adc_sample(pcm, symbol, phase))
                                      for phase in PHASES}))
        rows.append(dict(offset_hz=offset_hz, degrees=degrees,
                         target=target, expected_dibit=expected[target],
                         trace_digest=trace['trace_digest'],
                         adc_stream_sha256=trace['adc_stream_sha256'],
                         variants=variants, nearby_symbols=snapshots))
        print(degrees, target, 'expected', expected[target],
              {key: (value['primary_at_target'],
                     value['alternative_at_target'],
                     value['consensus_at_target'],
                     value['score']['errors'],
                     value['score']['unknown'])
               for key, value in variants.items()}, flush=True)
    paths = [Path(__file__), PRIOR,
             HERE / 'receiver_mask04_long_pair_union_holdout.py',
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
    report = dict(experiment='executed PROM visit audit at held-out receive gaps',
                  fixture=dict(seed=SEED, data_symbols=DATA_SYMBOLS,
                               cases=CASES, capture_phases=PHASES,
                               evaluated_pairs=PAIRS, adc_visits=adc_visits,
                               cycles=cycles,
                               mapping='joint upper-source mask 04',
                               adc='complementary PCM, 47/46 visits per sample'),
                  cases=rows,
                  limitations=[
                      'The holdout labels are used only to score predeclared phase pairs and describe the ambiguous symbols; no table is refitted.',
                      'Capturing a PROM byte at a visit does not establish a physical latch, selector or USART path.',
                      'The fixed ADC schedule and reference PCM remain explicit input hypotheses.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
