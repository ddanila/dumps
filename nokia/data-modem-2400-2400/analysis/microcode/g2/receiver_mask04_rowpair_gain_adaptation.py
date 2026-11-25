"""Validate gain-specific phase-code labels on fresh full-PROM receive runs."""

import hashlib
import json
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
PHASE_REPORT = HERE / 'results/receiver-mask04-rowpair-phase-code.json'
GAINS = (0.75, 1.25)
TRAIN = (0, 6)
HOLDOUT = (7, 8)
LAG = 0
ORIENTATION = 1
CARRIER_OFFSET = 2


def score_pairs(streams, truth, indexes, labels):
    return evaluate(streams, truth, indexes, labels, 0, LAG, ORIENTATION,
                    CARRIER_OFFSET, 1)


def run(out=HERE / 'results/receiver-mask04-rowpair-gain-adaptation.json'):
    level = json.loads(LEVEL_REPORT.read_text())
    phase = json.loads(PHASE_REPORT.read_text())
    nominal = {(row['row0'], row['row3']): (0, row['phase_quadrant'])
               for row in phase['selected']['codebook']}
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    stimuli = sequences()
    truth = {index: stimuli[index]['middle'] for index in TRAIN + HOLDOUT}
    cases = []
    for gain in GAINS:
        training_cases = [next(case for case in level['cases']
                               if case['gain'] == gain and case['bias'] == 0
                               and case['stream_index'] == index)
                          for index in TRAIN]
        streams = {case['stream_index']: [tuple(pair) for pair in
                                         case['phase0_symbol_pairs']]
                   for case in training_cases}
        conflicts, labels = solve(streams, truth, TRAIN, 0, LAG,
                                  ORIENTATION, CARRIER_OFFSET, 1)
        if conflicts or len({root for root, _ in labels.values()}) != 1:
            raise ValueError(('gain-specific training codebook failed', gain))
        training = score_pairs(streams, truth, TRAIN, labels)
        if training != dict(known=24, errors=0, unknown=0, checks=24):
            raise ValueError(('gain-specific training coverage changed', gain))
        traces = []
        for index in HOLDOUT:
            captured, trace = capture_level(mapping, base, truth[index], gain, 0)
            pairs = row_pairs(captured)
            streams[index] = [pairs[375 * symbol] for symbol in range(16)]
            traces.append(dict(stream_index=index,
                               phase0_symbol_pairs=streams[index], **trace))
            print('captured', gain, index, flush=True)
        cases.append(dict(gain=gain,
                          training_source_hashes=[case['captured_sha256']
                                                  for case in training_cases],
                          codebook=[dict(row0=state[0], row3=state[1],
                                         phase_quadrant=label[1])
                                    for state, label in sorted(labels.items())],
                          training=training,
                          holdout=score_pairs(streams, truth, HOLDOUT, labels),
                          nominal_codebook_holdout=score_pairs(
                              streams, truth, HOLDOUT, nominal),
                          traces=traces))
    paths = (Path(__file__), LEVEL_REPORT, PHASE_REPORT,
             HERE / 'receiver_mask04_rowpair_level_check.py',
             HERE / 'receiver_mask04_rowpair_phase_code.py',
             HERE / 'receiver_mask04_3ed_prom_latch.py',
             HERE / 'receiver_four_row_condition_screen.py',
             HERE / 'reference_modem.py', HERE.parent / 'assumed/execute.py',
             MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='gain-specific row-pair phase-code holdout validation',
                  fixture=dict(gains=GAINS, bias=0,
                               train_stream_indexes=TRAIN,
                               holdout_stream_indexes=HOLDOUT,
                               capture='same mask-04 four-row full-PROM fixture and phase-0 row pair',
                               codebook='fixed graph labels from two training streams at each gain; no holdout labels used',
                               lag=LAG, orientation=ORIENTATION,
                               carrier_offset=CARRIER_OFFSET),
                  cases=cases,
                  limitations=['The gain-specific phase labels and differential decision are external diagnostics.',
                               'This does not identify gain-control circuitry or USART RxD output.',
                               'Only two gains, two training streams and two holdout streams per gain are tested.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    for case in run()['cases']:
        print(case['gain'], case['training'], case['holdout'],
              case['nominal_codebook_holdout'])
