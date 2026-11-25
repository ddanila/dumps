"""Validate a fixed Boolean two-dibit readout of executed phase-47 row bytes."""

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
from lower_i_d3f8_upper_symbol_screen import SYMBOL_INDEXES, sequences
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_mask04_rowpair_level_check import capture_level
from receiver_mask04_rowpair_phase_code import row_pairs
from reference_modem import PHASE_STEPS, QUADRANT_TO_DIBIT

LEVEL_REPORT = HERE / 'results/receiver-mask04-rowpair-level-check.json'
CODEBOOK_REPORT = HERE / 'results/receiver-mask04-phase47-joint-codebook.json'
LEVELS = ((1.0, 0), (0.75, 0), (1.25, 0), (1.0, 16))
FRESH_SEEDS = (0x5A17, 0x76A5)
CAPTURE_PHASE = 47


def phase_quadrant(row0, row3):
    """Proposed gate network; derived on the earlier executed fixtures."""
    b0 = bool(row0 & 0x01)
    b1 = bool(row0 & 0x02)
    b2 = bool(row0 & 0x04)
    b3 = bool(row0 & 0x08)
    c0 = bool(row3 & 0x01)
    c1 = bool(row3 & 0x02)
    c2 = bool(row3 & 0x04)
    low = b0 or b2
    high = b3 or (b2 and (not b0 or c2)) or (
        b1 and not b0 and c0 and (c1 or c2))
    return int(low) + 2 * int(high)


def score(pairs, middle):
    errors = 0
    actual = []
    for symbol in SYMBOL_INDEXES:
        previous = phase_quadrant(*pairs[symbol - 1])
        current = phase_quadrant(*pairs[symbol])
        differential = (current - previous - 2) & 3
        dibit = QUADRANT_TO_DIBIT[differential]
        actual.append(dibit)
        errors += dibit != middle[symbol]
    return dict(errors=errors, checks=len(SYMBOL_INDEXES), dibits=actual)


def run(out=HERE / 'results/receiver-mask04-phase47-logic.json'):
    level = json.loads(LEVEL_REPORT.read_text())
    codebook = json.loads(CODEBOOK_REPORT.read_text())
    if any(phase_quadrant(row['row0'], row['row3']) !=
           row['phase_quadrant'] for row in
           codebook['training']['codebook']):
        raise ValueError('Boolean phase rule changed on its development codebook')
    stimuli = sequences()
    development = []
    for case in level['cases']:
        result = score(case['phase47_symbol_pairs'],
                       stimuli[case['stream_index']]['middle'])
        development.append(dict(source='level-check training stream',
                                gain=case['gain'], bias=case['bias'],
                                stream_index=case['stream_index'],
                                captured_sha256=case['captured_sha256'],
                                score=result))
    for case in codebook['holdout_cases']:
        result = score(case['phase47_symbol_pairs'], case['middle_dibits'])
        development.append(dict(source='inspected earlier holdout',
                                gain=case['gain'], bias=case['bias'],
                                seed=case['seed'],
                                captured_sha256=case['captured_sha256'],
                                score=result))
    if len(development) != 14 or any(row['score']['errors']
                                      for row in development):
        raise ValueError('development fixture did not reproduce')

    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    fresh = []
    for gain, bias in LEVELS:
        for seed in FRESH_SEEDS:
            generator = random.Random(seed)
            middle = [generator.randrange(4) for _ in range(16)]
            captured, trace = capture_level(mapping, base, middle, gain, bias)
            rows = row_pairs(captured)
            pairs = [rows[375 * symbol + CAPTURE_PHASE]
                     for symbol in range(16)]
            result = score(pairs, middle)
            fresh.append(dict(gain=gain, bias=bias, seed=seed,
                              middle_dibits=middle,
                              phase47_symbol_pairs=pairs,
                              score=result, **trace))
            print('captured', gain, bias, seed,
                  result['errors'], '/', result['checks'], flush=True)
    aggregate = dict(checks=sum(case['score']['checks'] for case in fresh),
                     errors=sum(case['score']['errors'] for case in fresh))
    paths = (Path(__file__), LEVEL_REPORT, CODEBOOK_REPORT,
             HERE / 'receiver_mask04_phase47_joint_codebook.py',
             HERE / 'receiver_mask04_rowpair_level_check.py',
             HERE / 'receiver_mask04_rowpair_phase_code.py',
             HERE / 'receiver_mask04_3ed_prom_latch.py',
             HERE / 'receiver_four_row_condition_screen.py',
             HERE / 'reference_modem.py', HERE.parent / 'assumed/execute.py',
             MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='fixed Boolean phase-47 row-pair decoder of both reference dibit bits',
                  fixture=dict(mapping='joint upper-source mask 04',
                               adc='complementary PCM, 47/46 visits per sample',
                               capture='3ED row-0 and row-3 Y at ADC-visit phase 47',
                               phase_logic='low=r0.b0|r0.b2; high=r0.b3|(r0.b2&(!r0.b0|r3.b2))|(r0.b1&!r0.b0&r3.b0&(r3.b1|r3.b2))',
                               decision='(phase[k]-phase[k-1]-2) mod 4, then reference quadrant-to-dibit map',
                               levels=LEVELS, fresh_seeds=FRESH_SEEDS),
                  development_cases=development,
                  fresh_cases=fresh, fresh_aggregate=aggregate,
                  limitations=['This logic was derived using the earlier level-check and codebook-holdout traces; only the new fresh seeds are independent validation.',
                               'The Boolean gates, phase subtraction and dibit map are external diagnostics, not executed DSC microinstructions or traced board logic.',
                               'The ADC path, four-row dispatch, latch timing and USART-01 RxD route remain hypotheses.',
                               'Carrier phase, noise and arbitrary gain/bias values are not covered by these fixed fixtures.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    print(run()['fresh_aggregate'])
