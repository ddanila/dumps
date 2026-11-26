"""Ablate one real controller TxD bit through the buffered D127 route."""

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import joint_mask04_buffered_serial_handoff as buffered
import joint_mask04_full_zero_handoff as full
from photo_joint_tone_training_data import (DATA_STEP, SILENCE_SYMBOLS,
                                             TONE_STEP, TONE_SYMBOLS)
from photo_main_dibit_pulse import BASE, VISITS_PER_SAMPLE, VISITS_PER_SYMBOL

HERE = Path(__file__).resolve().parent
PRIOR = HERE / 'results/joint-mask04-buffered-serial-handoff.json'
NONZERO = HERE / 'results/joint-mask04-buffered-payload-challenge.json'
OUT = HERE / 'results/joint-mask04-buffered-txd-bit-ablation.json'
BIT_INDEX = 40
SAMPLE_COUNT = buffered.SAMPLES
INITIAL_R1_BEFORE_FIRST_INPUT = 242


def full_inputs(buffered_values):
    return ([TONE_STEP] * (TONE_SYMBOLS * VISITS_PER_SYMBOL) +
            [DATA_STEP] * (SILENCE_SYMBOLS * VISITS_PER_SYMBOL) +
            buffered_values + [BASE] * (6 * VISITS_PER_SAMPLE))


def predicted_y7(inputs):
    phase = INITIAL_R1_BEFORE_FIRST_INPUT
    bits = []
    for index, value in enumerate(inputs):
        phase = (phase + value) & 255
        if index % VISITS_PER_SAMPLE == 0:
            bits.append(phase >> 7)
        if len(bits) == SAMPLE_COUNT:
            break
    if len(bits) != SAMPLE_COUNT:
        raise ValueError('modeled output sample count changed')
    return bits


def run(out=OUT):
    prior = json.loads(PRIOR.read_text())
    nonzero = json.loads(NONZERO.read_text())
    independent_stream_controls = []
    for saved in nonzero['cases']:
        offered = [int(value, 16) for value in saved['offered_line_bytes'].split()]
        buffered_values, _, _ = buffered.buffered_inputs(offered)
        digest = hashlib.sha256(bytes(predicted_y7(full_inputs(buffered_values)))).hexdigest()
        if digest != saved['tx_y7_sha256']:
            raise ValueError(('nonzero buffered PROM output violates recurrence',
                              saved['selector']))
        independent_stream_controls.append(dict(selector=saved['selector'],
                                                saved_prom_y7_sha256=digest,
                                                recurrence_matches=True))
    mapping = full.candidate(full.mapping_with_upper_source(0, '17.6'),
                             full.mapped(full.MAPPINGS['q3']), 4)
    _, base = full.fixture()
    cases = []
    for saved in prior['cases']:
        selector = saved['selector']
        offered = [int(value, 16) for value in saved['offered_line_bytes']]
        flipped = offered.copy()
        flipped[BIT_INDEX // 8] ^= 1 << (BIT_INDEX % 8)
        original_inputs, original_dibits, original_events = buffered.buffered_inputs(offered)
        changed_inputs, changed_dibits, changed_events = buffered.buffered_inputs(flipped)
        original_full = full_inputs(original_inputs)
        changed_full = full_inputs(changed_inputs)
        differing = [index for index, (a, b) in enumerate(
            zip(original_full, changed_full)) if a != b]
        pulse = changed_events[BIT_INDEX // 2]
        pulse_global_visit = ((TONE_SYMBOLS + SILENCE_SYMBOLS +
                               buffered.PREAMBLE + BIT_INDEX // 2 + 1) *
                              VISITS_PER_SYMBOL)
        if (len(differing) != 4 or differing != list(range(
                pulse_global_visit, pulse_global_visit + 4)) or
                original_dibits[:20] != changed_dibits[:20] or
                original_dibits[21:] != changed_dibits[21:] or
                pulse['pulse_visit'] != 63000 or
                pulse['second_bit_visit'] != 61500):
            raise ValueError(('one-bit buffered decoder intervention changed', selector))
        delta = sum(changed_full[index] - original_full[index] for index in differing) & 255
        if delta != 192:
            raise ValueError(('single-bit phase step changed', selector, delta))
        baseline_bits = predicted_y7(original_full)
        baseline_sha = hashlib.sha256(bytes(baseline_bits)).hexdigest()
        if baseline_sha != saved['tx_y7_sha256']:
            raise ValueError(('saved baseline PROM Y7 differs from recurrence', selector))
        with patch.object(full, 'scenario_inputs', lambda symbols: changed_inputs), \
                patch.object(full, 'SAMPLES', SAMPLE_COUNT), \
                patch.object(full, 'TX_CYCLES', buffered.TX_CYCLES):
            result, executed_bits = full.transmitter(mapping, base, changed_dibits)
        modeled_bits = predicted_y7(changed_full)
        if (not result['clean'] or result['completed_cycles'] != saved['tx_cycles'] or
                executed_bits != modeled_bits or
                result['trace_digest'] == saved['tx_trace_digest']):
            raise ValueError(('mutant PROM output differs from R1 recurrence', selector))
        changed_indices = [index for index, (a, b) in enumerate(
            zip(baseline_bits, executed_bits)) if a != b]
        if (not changed_indices or min(changed_indices) <
                differing[0] // VISITS_PER_SAMPLE):
            raise ValueError(('output changed before altered D127 pulse', selector))
        cases.append(dict(selector=selector,
                          original_offered_line_bytes=[f'{value:02X}' for value in offered],
                          flipped_offered_line_bytes=[f'{value:02X}' for value in flipped],
                          original_bit=(offered[BIT_INDEX // 8] >> (BIT_INDEX % 8)) & 1,
                          changed_bit=(flipped[BIT_INDEX // 8] >> (BIT_INDEX % 8)) & 1,
                          original_pair=original_events[BIT_INDEX // 2],
                          changed_pair=pulse,
                          changed_d127_full_visits=differing,
                          persistent_r1_phase_delta=delta,
                          first_changed_y7_sample=changed_indices[0],
                          changed_y7_samples=len(changed_indices),
                          baseline_y7_sha256=baseline_sha,
                          mutant_y7_sha256=hashlib.sha256(bytes(executed_bits)).hexdigest(),
                          mutant_trace_digest=result['trace_digest'],
                          executed_matches_recurrence=True))
        print('TxD bit ablation', selector, 'phase', delta,
              'first Y7 sample', changed_indices[0],
              'changed samples', len(changed_indices), flush=True)
    paths = (Path(__file__), PRIOR, NONZERO,
             HERE / 'joint_mask04_buffered_serial_handoff.py',
             HERE / 'joint_mask04_full_zero_handoff.py',
             HERE / 'photo_joint_tone_training_data.py',
             HERE / 'photo_main_dibit_pulse.py',
             HERE.parent / 'assumed/execute.py', full.MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='one real controller TxD bit through buffered D127 and executed R1/Y7',
                  fixture=dict(controller_bit_zero_based=BIT_INDEX,
                               line_bit_rate_hz=2400,
                               buffered_symbol_rate_hz=1200,
                               one_symbol_pipeline=True,
                               pulse_width_visits=4,
                               predicted_phase_before_input=INITIAL_R1_BEFORE_FIRST_INPUT,
                               samples=SAMPLE_COUNT,
                               sample_divisor_visits=VISITS_PER_SAMPLE),
                  independent_nonzero_stream_controls=independent_stream_controls,
                  cases=cases,
                  limitations=[
                      'The original serial bits are real 8031/8251 outputs, but the one-bit mutant is a controlled counterfactual.',
                      'The paired-bit latch, symbol boundary, D127 mask, clock divider and DAC path are untraced board hypotheses.',
                      'The recurrence verifies digital Y7 output under those hypotheses, not measured DAC08 current or a line signal.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
