"""Validate a fixed three-bit receive-row gate on fresh PROM executions."""

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
from reference_modem import transmit

PHASE = HERE / 'results/receiver-mask04-rowpair-phase-code.json'
LEVEL = HERE / 'results/receiver-mask04-rowpair-level-check.json'
ADAPT = HERE / 'results/receiver-mask04-rowpair-gain-adaptation.json'
NEW_SEEDS = (0x4733, 0x2847)
LEVELS = ((1.0, 0), (0.75, 0), (1.0, 16))


def gate(value):
    return int(bool(value & 0x07))


def dibit_parity(dibit):
    return (dibit & 1) ^ ((dibit >> 1) & 1)


def score(pairs, middle):
    errors = 0
    for symbol in SYMBOL_INDEXES:
        observed = gate(pairs[symbol][1]) ^ gate(pairs[symbol - 1][1])
        errors += observed != dibit_parity(middle[symbol])
    return dict(errors=errors, checks=len(SYMBOL_INDEXES))


def adc_control(middle, gain, bias):
    pcm = transmit([0] * 8 + middle + [0] * 8)
    adc = [127 - max(-127, min(127, round(gain * value + bias)))
           for value in pcm[64:192]]
    pairs = [(0, adc[8 * symbol]) for symbol in range(16)]
    return score(pairs, middle)


def run(out=HERE / 'results/receiver-mask04-row3-parity-gate.json'):
    phase = json.loads(PHASE.read_text())
    level = json.loads(LEVEL.read_text())
    adapt = json.loads(ADAPT.read_text())
    if any(gate(row['row3']) != (row['phase_quadrant'] & 1)
           for row in phase['selected']['codebook']):
        raise ValueError('gate does not agree with original eight-state phase code')
    stimuli = sequences()
    prior_cases = []
    for case in level['cases']:
        pairs = case['phase0_symbol_pairs']
        middle = stimuli[case['stream_index']]['middle']
        prior_cases.append(dict(source='changed-level report',
                                gain=case['gain'], bias=case['bias'],
                                stream_index=case['stream_index'],
                                captured_sha256=case['captured_sha256'],
                                gate=score(pairs, middle),
                                direct_adc_control=adc_control(
                                    middle, case['gain'], case['bias'])))
    for case in adapt['cases']:
        for trace in case['traces']:
            middle = stimuli[trace['stream_index']]['middle']
            prior_cases.append(dict(source='gain-adaptation holdout',
                                    gain=case['gain'], bias=0,
                                    stream_index=trace['stream_index'],
                                    captured_sha256=trace['captured_sha256'],
                                    gate=score(trace['phase0_symbol_pairs'],
                                               middle),
                                    direct_adc_control=adc_control(
                                        middle, case['gain'], 0)))
    if len(prior_cases) != 10 or any(case['gate']['errors']
                                     for case in prior_cases):
        raise ValueError('previously executed gate evidence changed')

    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    fresh_cases = []
    for gain, bias in LEVELS:
        for seed in NEW_SEEDS:
            generator = random.Random(seed)
            middle = [generator.randrange(4) for _ in range(16)]
            captured, trace = capture_level(mapping, base, middle, gain, bias)
            pairs = row_pairs(captured)
            result = score([pairs[375 * symbol] for symbol in range(16)],
                           middle)
            fresh_cases.append(dict(gain=gain, bias=bias, seed=seed,
                                    middle_dibits=middle,
                                    gate=result,
                                    direct_adc_control=adc_control(
                                        middle, gain, bias),
                                    **trace))
            print('captured', gain, bias, seed, result, flush=True)
    if any(case['gate']['errors'] for case in fresh_cases):
        raise ValueError('fixed row-3 gate failed fresh PROM holdout')

    paths = (Path(__file__), PHASE, LEVEL, ADAPT,
             HERE / 'receiver_mask04_rowpair_level_check.py',
             HERE / 'receiver_mask04_rowpair_gain_adaptation.py',
             HERE / 'receiver_mask04_rowpair_phase_code.py',
             HERE / 'receiver_mask04_3ed_prom_latch.py',
             HERE / 'receiver_four_row_condition_screen.py',
             HERE / 'reference_modem.py', HERE.parent / 'assumed/execute.py',
             MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='fixed row-3 low-three-bit gate for one received dibit parity bit',
                  fixture=dict(mapping='joint upper-source mask 04',
                               adc='complementary reference PCM, same four-row schedule',
                               capture='3ED Y on row 3, symbol-boundary ADC visit',
                               gate='OR of Y[2:0], XOR with previous symbol gate bit',
                               target='dibit bit 0 XOR dibit bit 1',
                               gain_bias_levels=LEVELS,
                               fresh_seeds=NEW_SEEDS),
                  prior_cases=prior_cases, fresh_cases=fresh_cases,
                  executed_total=dict(gate_errors=sum(c['gate']['errors'] for c in
                                                      prior_cases + fresh_cases),
                                      gate_checks=sum(c['gate']['checks'] for c in
                                                      prior_cases + fresh_cases),
                                      direct_adc_errors=sum(
                                          c['direct_adc_control']['errors'] for c in
                                          prior_cases + fresh_cases)),
                  limitations=['The OR and previous-symbol XOR are external diagnostic logic, not an executed DSC decision or a traced USART RxD route.',
                               'Only one linear combination of the two dibit bits is recovered; a complete received dibit is not shown.',
                               'ADC input, four-row schedule and latch path remain labelled hypotheses.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    print(run()['executed_total'])
