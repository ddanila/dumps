"""Validate one mask-04 phase-47 receive codebook across input levels."""

import hashlib
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from joint_upper_source_screen import candidate
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from lower_i_d3f8_upper_symbol_screen import sequences
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_mask04_rowpair_level_check import capture_level
from receiver_mask04_rowpair_phase_code import evaluate, row_pairs, solve

LEVEL_REPORT = HERE / 'results/receiver-mask04-rowpair-level-check.json'
CAPTURE_PHASE = 47
TRAIN_LEVELS = ((0.75, 0), (1.25, 0), (1.0, 16))
HOLDOUT_LEVELS = ((1.0, 0),) + TRAIN_LEVELS
HOLDOUT_SEEDS = (0x4733, 0x2847)
LAG = 0
ORIENTATION = 1
CARRIER_OFFSET = 2


def score(streams, truth, indexes, labels):
    return evaluate(streams, truth, indexes, labels, 0, LAG,
                    ORIENTATION, CARRIER_OFFSET, 1)


def run(out=HERE / 'results/receiver-mask04-phase47-joint-codebook.json'):
    level = json.loads(LEVEL_REPORT.read_text())
    stimuli = sequences()
    training = level['cases']
    if (len(training) != 6 or
            {(case['gain'], case['bias']) for case in training} != set(TRAIN_LEVELS)):
        raise ValueError('three-level training fixture changed')
    streams = {index: [tuple(pair) for pair in case['phase47_symbol_pairs']]
               for index, case in enumerate(training)}
    truth = {index: stimuli[case['stream_index']]['middle']
             for index, case in enumerate(training)}
    train_indexes = tuple(streams)
    conflicts, labels = solve(streams, truth, train_indexes, 0, LAG,
                              ORIENTATION, CARRIER_OFFSET, 1)
    if conflicts or len({root for root, _ in labels.values()}) != 1:
        raise ValueError('phase-47 training codebook is inconsistent')
    train_score = score(streams, truth, train_indexes, labels)
    if train_score != dict(known=72, errors=0, unknown=0, checks=72):
        raise ValueError('phase-47 training coverage changed')

    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    holdout_cases = []
    holdout_indexes = []
    for gain, bias in HOLDOUT_LEVELS:
        for seed in HOLDOUT_SEEDS:
            generator = random.Random(seed)
            middle = [generator.randrange(4) for _ in range(16)]
            captured, trace = capture_level(mapping, base, middle, gain, bias)
            pairs = row_pairs(captured)
            index = len(streams)
            streams[index] = [pairs[375 * symbol + CAPTURE_PHASE]
                              for symbol in range(16)]
            truth[index] = middle
            holdout_indexes.append(index)
            result = score(streams, truth, (index,), labels)
            holdout_cases.append(dict(gain=gain, bias=bias, seed=seed,
                                      middle_dibits=middle,
                                      phase47_symbol_pairs=streams[index],
                                      score=result, **trace))
            print('captured', gain, bias, seed, result, flush=True)
    aggregate = score(streams, truth, holdout_indexes, labels)
    paths = (Path(__file__), LEVEL_REPORT,
             HERE / 'receiver_mask04_rowpair_level_check.py',
             HERE / 'receiver_mask04_rowpair_phase_code.py',
             HERE / 'receiver_mask04_3ed_prom_latch.py',
             HERE / 'receiver_four_row_condition_screen.py',
             HERE / 'reference_modem.py', HERE.parent / 'assumed/execute.py',
             MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='one fixed phase-47 row-pair codebook across nominal, reduced-gain and biased ADC inputs',
                  fixture=dict(mapping='joint upper-source mask 04',
                               adc='complementary reference PCM with 47/46 visit holds',
                               training_levels=TRAIN_LEVELS,
                               holdout_levels=HOLDOUT_LEVELS,
                               capture_phase_adc_visits=CAPTURE_PHASE,
                               capture='3ED row-0 and row-3 Y, hypothetical U19 NAND edge',
                               lag=LAG, orientation=ORIENTATION,
                               carrier_offset=CARRIER_OFFSET,
                               holdout_seeds=HOLDOUT_SEEDS),
                  training=dict(cases=[dict(gain=case['gain'], bias=case['bias'],
                                            stream_index=case['stream_index'],
                                            captured_sha256=case['captured_sha256'])
                                       for case in training],
                                state_count=len(labels),
                                codebook=[dict(row0=state[0], row3=state[1],
                                               phase_quadrant=label[1])
                                          for state, label in sorted(labels.items())],
                                score=train_score),
                  holdout_cases=holdout_cases, holdout_aggregate=aggregate,
                  limitations=['The phase labels and differential subtraction are external diagnostics, not executed DSC decisions.',
                               'The ADC route, four-row dispatch, proposed latch and USART RxD connection remain untraced.',
                               'The tested reference streams use one carrier phase and a small set of gain/bias levels.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    print(run()['holdout_aggregate'])
