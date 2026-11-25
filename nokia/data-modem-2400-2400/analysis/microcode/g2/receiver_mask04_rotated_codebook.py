"""Ask whether a fixed 3ED row-pair lookup survives carrier rotations."""

import hashlib
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from joint_upper_source_screen import candidate
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_mask04_carrier_phase_screen import capture_rotated
from receiver_mask04_phase47_logic import phase_quadrant
from receiver_mask04_rowpair_phase_code import row_pairs
from reference_modem import QUADRANT_TO_DIBIT, phase_positions

ROTATIONS = (45, 135)
TRAIN_SEED = 0x5A17
HOLDOUT_SEEDS = (0x76A5, 0x26A1)
PHASE = 47
SYMBOLS = range(2, 14)


def expected_states(middle):
    # The nominal readout was already validated as the reference quadrant
    # plus the alternating 1800-Hz carrier phase at the capture instant.
    phase = phase_positions([0] * 8 + middle + [0] * 8)[8:24]
    return [((value // 4) + (1 if symbol % 2 == 0 else 3)) & 3
            for symbol, value in enumerate(phase)]


def fit(cases, low_nibble=False, offset_135=0):
    labels = defaultdict(set)
    for case in cases:
        for pair, state in zip(case['pairs'], case['expected_states']):
            key = tuple(value & 15 for value in pair) if low_nibble else tuple(pair)
            labels[key].add((state + (offset_135 if case['degrees'] == 135
                                      else 0)) & 3)
    return labels


def evaluate(labels, case, low_nibble=False):
    observed = []
    for pair in case['pairs']:
        key = tuple(value & 15 for value in pair) if low_nibble else tuple(pair)
        states = labels.get(key, set())
        observed.append(next(iter(states)) if len(states) == 1 else None)
    errors = unknown = 0
    for symbol in SYMBOLS:
        before, after = observed[symbol - 1:symbol + 1]
        if before is None or after is None:
            unknown += 1
        else:
            decoded = QUADRANT_TO_DIBIT[(after - before - 2) & 3]
            errors += decoded != case['middle'][symbol]
    return dict(checks=len(SYMBOLS), errors=errors, unknown=unknown,
                known=len(SYMBOLS) - unknown)


def run(out=HERE / 'results/receiver-mask04-rotated-codebook.json'):
    nominal = json.loads((HERE / 'results/receiver-mask04-phase47-logic.json').read_text())
    if any([phase_quadrant(*pair) for pair in case['phase47_symbol_pairs']] !=
           expected_states(case['middle_dibits']) for case in nominal['fresh_cases']):
        raise ValueError('reference phase labels disagree with nominal full-PROM traces')
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    cases = []
    for degrees in ROTATIONS:
        for seed in (TRAIN_SEED, *HOLDOUT_SEEDS):
            generator = random.Random(seed)
            middle = [generator.randrange(4) for _ in range(16)]
            captured, trace = capture_rotated(mapping, base, middle, degrees)
            rows = row_pairs(captured)
            pairs = [rows[375 * symbol + PHASE] for symbol in range(16)]
            cases.append(dict(degrees=degrees, seed=seed, middle=middle,
                              pairs=pairs, expected_states=expected_states(middle),
                              **trace))
            print('captured', degrees, hex(seed), flush=True)
    previous = json.loads((HERE / 'results/receiver-mask04-carrier-phase-screen.json').read_text())
    for case in cases:
        if case['seed'] not in (TRAIN_SEED, HOLDOUT_SEEDS[0]):
            continue
        old = next(item for item in previous['cases'] if
                   (item['seed'], item['carrier_phase_degrees']) ==
                   (case['seed'], case['degrees']))
        if (case['trace_digest'] != old['trace_digest'] or
                case['captured_sha256'] != old['captured_sha256']):
            raise ValueError('rotated replay disagrees with prior trace')
    analyses = []
    for low_nibble in (False, True):
        for separate_rotation in (False, True):
            for degrees in ROTATIONS if separate_rotation else (None,):
                for offset_135 in (0,) if separate_rotation else range(4):
                    training = [case for case in cases if case['seed'] == TRAIN_SEED
                                and (degrees is None or case['degrees'] == degrees)]
                    validation = [case for case in cases if case['seed'] != TRAIN_SEED
                                  and (degrees is None or case['degrees'] == degrees)]
                    labels = fit(training, low_nibble, offset_135)
                    all_labels = fit(training + validation, low_nibble, offset_135)
                    analyses.append(dict(low_nibble=low_nibble, degrees=degrees,
                        offset_135=offset_135,
                        training_states=len(labels),
                        conflicted_training_states=sum(len(v) > 1 for v in labels.values()),
                        all_case_states=len(all_labels),
                        conflicted_all_case_states=sum(len(v) > 1 for v in all_labels.values()),
                        training=[dict(degrees=c['degrees'], seed=c['seed'],
                                       **evaluate(labels, c, low_nibble)) for c in training],
                        validation=[dict(degrees=c['degrees'], seed=c['seed'],
                                         **evaluate(labels, c, low_nibble)) for c in validation]))
    paths = (Path(__file__), HERE / 'receiver_mask04_carrier_phase_screen.py',
             HERE / 'receiver_mask04_rowpair_phase_code.py',
             HERE / 'reference_modem.py', HERE.parent / 'assumed/execute.py',
             MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='frozen row-pair state lookup across rotated-carrier traces',
                  fixture=dict(rotations=ROTATIONS, training_seed=TRAIN_SEED,
                               holdout_seeds=HOLDOUT_SEEDS, capture_visit=PHASE,
                               phase_labels='reference waveform phase plus validated nominal alternating carrier offset; external diagnostic'),
                  cases=cases, analyses=analyses,
                  limitations=['Codebook labels use the known stimulus phase and are not produced by executed microcode.',
                               'Carrier rotation is known to the analyst; a per-rotation table would need an unproven estimator.',
                               'No row-pair lookup, symbol clock or RxD path is traced to the board.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
