"""Validate a frozen two-visit 45-degree receive-state rule on new streams."""

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
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_mask04_carrier_phase_screen import capture_rotated
from receiver_mask04_rotated_codebook import expected_states
from receiver_mask04_rowpair_phase_code import row_pairs
from reference_modem import QUADRANT_TO_DIBIT

RULE = {(0xF5, 0xF5): 2, (0xF5, 0xF9): 3,
        (0xF5, 0xF3): 2, (0xF3, 0xF2): 1,
        (0xF3, 0xFC): 1, (0xF3, 0xF8): 0,
        (0xF5, 0x00): 3}
SEEDS = (0x4E11, 0x6B39)
DEGREES = (45, 135)
VISITS_PER_SYMBOL = 375
CAPTURE_VISIT = 47
SECOND_VISIT = 94
SYMBOLS = range(2, 14)


def decode(base_pairs, next_pairs, middle):
    phases = []
    for pair, next_pair in zip(base_pairs, next_pairs):
        phase = RULE.get(tuple(pair))
        if tuple(pair) == (0xF3, 0xF2) and next_pair[1] == 0xF8:
            phase = 0
        phases.append(phase)
    dibits = []
    errors = unknown = 0
    for symbol in SYMBOLS:
        before, after = phases[symbol - 1:symbol + 1]
        if before is None or after is None:
            dibits.append(None)
            unknown += 1
        else:
            dibit = QUADRANT_TO_DIBIT[(after - before - 2) & 3]
            dibits.append(dibit)
            errors += dibit != middle[symbol]
    return dict(phases=phases, dibits=dibits, checks=len(SYMBOLS),
                errors=errors, unknown=unknown)


def run(out=HERE / 'results/receiver-mask04-two-visit-rule.json'):
    exploratory = json.loads((HERE / 'results/receiver-mask04-two-visit-phase.json').read_text())
    for case in exploratory['cases']:
        base_pairs = [window['base'] for window in case['windows']]
        next_pairs = [window['47'] for window in case['windows']]
        result = decode(base_pairs, next_pairs, case['middle'])
        if result['errors'] or result['unknown']:
            raise ValueError('frozen rule changed on exploratory streams')
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    cases = []
    for degrees in DEGREES:
        for seed in SEEDS:
            generator = random.Random(seed)
            middle = [generator.randrange(4) for _ in range(16)]
            captured, trace = capture_rotated(mapping, base, middle, degrees)
            rows = row_pairs(captured)
            base_pairs = [rows[VISITS_PER_SYMBOL * symbol + CAPTURE_VISIT]
                          for symbol in range(16)]
            next_pairs = [rows[VISITS_PER_SYMBOL * symbol + SECOND_VISIT]
                          for symbol in range(16)]
            result = decode(base_pairs, next_pairs, middle)
            cases.append(dict(degrees=degrees, seed=seed, middle=middle,
                              base_pairs=base_pairs, next_pairs=next_pairs,
                              expected_states=expected_states(middle),
                              score=result, **trace))
            print('captured', degrees, hex(seed), result['errors'],
                  result['unknown'], flush=True)
    paths = (Path(__file__), HERE / 'receiver_mask04_two_visit_phase.py',
             HERE / 'receiver_mask04_carrier_phase_screen.py',
             HERE / 'receiver_mask04_rotated_codebook.py',
             HERE / 'reference_modem.py', HERE.parent / 'assumed/execute.py',
             MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='frozen two-visit row-pair readout at 45 degrees with 135-degree control',
                  fixture=dict(degrees=DEGREES, fresh_seeds=SEEDS,
                               base_capture_visit=CAPTURE_VISIT,
                               second_capture_visit=SECOND_VISIT,
                               exploratory_streams=4),
                  rule={f'{a:02X}/{b:02X}': value for (a, b), value in RULE.items()},
                  collision_override='F3/F2 phase becomes 0 only when the next visit row-3 byte is F8',
                  cases=cases,
                  limitations=['The phase labels and readout logic are external hypotheses, not executed DSC code.',
                               'The rule was derived on inspected 45-degree streams and is not a carrier-phase-independent receiver.',
                               'The second visit requires untraced storage and timing; no USART RxD route is identified.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
