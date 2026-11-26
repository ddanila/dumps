"""Challenge the full joined zero-run with gain and ADC-bias alternatives."""

import hashlib
import json
import sys
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from joint_mask04_full_zero_handoff import (
    ADC_VISITS, DATA_SYMBOLS, PREAMBLE, RX_CYCLES, SYMBOLS,
    pcm_from_bits,
)
import joint_mask04_tx_rx_loopback as loopback
from photo_joint_tone_training_data import (
    DATA_STEP, SEGMENT_SYMBOLS, SILENCE_SYMBOLS, TONE_STEP, TONE_SYMBOLS,
)
from photo_main_dibit_pulse import BASE, VISITS_PER_SYMBOL, scenario_inputs
from receiver_mask04_adc_margin_selector import PAIRS, select
from receiver_mask04_controller_zero_handoff import dibits_from_bytes
from receiver_mask04_dual_feature_consensus import consensus, decisions
from receiver_mask04_dual_zero_handoff import frozen_tables
from receiver_mask04_feature_choice import alternative_states
from receiver_mask04_four_bit_transition import states_from_symbols
from receiver_mask04_long_pair_union import classify
from receiver_mask04_offset_visit_phase import project
from receiver_mask04_serial_candidate import bytes_lsb_first
from reference_modem import receive
from zero_run_detector import line_octets

PRIOR = HERE / 'results/joint-mask04-full-zero-handoff.json'
VARIANTS = (('gain_0p75_bias_plus16', 0.75, 16),
            ('gain_0p75_bias_minus16', 0.75, -16))


def reconstructed_pcm(prior):
    offered = line_octets([0] * 8, prior['polynomial_delay'])
    dibits = dibits_from_bytes(offered)
    inputs = ([TONE_STEP] * (TONE_SYMBOLS * VISITS_PER_SYMBOL) +
              [DATA_STEP] * (SILENCE_SYMBOLS * VISITS_PER_SYMBOL) +
              scenario_inputs([3] * SEGMENT_SYMBOLS + dibits) +
              [BASE] * (6 * 375))
    phase = 242
    bits = []
    for index, value in enumerate(inputs):
        phase = (phase + value) & 255
        if index % 375 == 0:
            bits.append(phase >> 7)
        if len(bits) == 838:
            break
    if (len(bits) != 838 or
            hashlib.sha256(bytes(bits)).hexdigest() != prior['tx_y7_sha256'] or
            bits[-6:] != prior['post_a4_bits']):
        raise ValueError('phase recurrence differs from executed transmitter')
    pcm, gain = pcm_from_bits(bits)
    if hashlib.sha256(bytes(value + 127 for value in pcm)).hexdigest() != prior['pcm_sha256']:
        raise ValueError('analog fixture differs from saved joined run')
    return pcm, offered, dibits, gain


def run(out=HERE / 'results/joint-mask04-full-zero-analog-variants.json'):
    prior = json.loads(PRIOR.read_text())
    primary, alternative = frozen_tables()
    mapping = loopback.candidate(
        loopback.mapping_with_upper_source(0, '17.6'),
        loopback.mapped(loopback.MAPPINGS['q3']), 4)
    _, base = loopback.fixture()
    rows = []
    for original in prior['cases']:
        baseline_pcm, offered, dibits, baseline_gain = reconstructed_pcm(original)
        expected = [3] * PREAMBLE + dibits
        for name, scale, bias in VARIANTS:
            pcm = [max(-127, min(127, round(value * scale + bias)))
                   for value in baseline_pcm]
            reference = receive(pcm)
            reference_errors = [index for index, (actual, target) in
                                enumerate(zip(reference, expected[1:]))
                                if actual != target]
            with patch.object(loopback, 'DATA', DATA_SYMBOLS), \
                    patch.object(loopback, 'SYMBOLS', SYMBOLS), \
                    patch.object(loopback, 'ADC_VISITS', ADC_VISITS), \
                    patch.object(loopback, 'CYCLES', RX_CYCLES):
                result, adc, symbols = loopback.capture(mapping, base, pcm, expected)
            predictions = {}
            for pair in PAIRS:
                projected = project(symbols, *pair)
                first = decisions(states_from_symbols(projected), primary)
                second = decisions(alternative_states(projected), alternative)
                predictions[pair] = consensus(first, second)
            picked, selected = select(pcm, predictions)
            scores = {f'{a}/{b}': classify(predictions[(a, b)], expected)
                      for a, b in PAIRS}
            margin = classify(picked, expected)
            fixed = predictions[(46, 93)]
            recovered = None
            if scores['46/93']['data_errors'] == scores['46/93']['data_unknown'] == 0:
                recovered = bytes_lsb_first([
                    bit for symbol in fixed[PREAMBLE:]
                    for bit in (symbol & 1, (symbol >> 1) & 1)])
            rows.append(dict(selector=original['selector'], variant=name,
                             gain_scale=scale, pcm_bias=bias,
                             baseline_pcm_gain=baseline_gain,
                             reference_errors=reference_errors,
                             tx_y7_sha256=original['tx_y7_sha256'],
                             pcm_sha256=hashlib.sha256(bytes(value + 127 for value in pcm)).hexdigest(),
                             adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                             rx_cycles=result['completed_cycles'],
                             rx_trace_digest=result['trace_digest'],
                             scores=scores, margin_score=margin,
                             margin_wrong_pairs=[dict(symbol=index, pair=selected[index],
                                                      expected=expected[index], decoded=picked[index])
                                                 for index in margin['wrong_symbols']],
                             recovered_46_93_bytes=(
                                 [f'{value:02X}' for value in recovered]
                                 if recovered is not None else None),
                             offered_bytes=[f'{value:02X}' for value in offered]))
            print(original['selector'], name, 'reference', len(reference_errors),
                  'fixed', scores['46/93']['errors'], scores['46/93']['unknown'],
                  'margin', margin['errors'], margin['unknown'], flush=True)
    paths = (Path(__file__), PRIOR,
             HERE / 'joint_mask04_full_zero_handoff.py',
             HERE / 'joint_mask04_tx_rx_loopback.py',
             HERE / 'receiver_mask04_adc_margin_selector.py',
             HERE / 'receiver_mask04_dual_zero_handoff.py',
             HERE / 'photo_joint_line_filter_screen.py',
             HERE / 'photo_main_dibit_pulse.py',
             loopback.MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='executed-transmitter zero-run receive gain and ADC-bias challenge',
                  fixture=dict(variants=VARIANTS, rx_cycles=RX_CYCLES,
                               adc_visits=ADC_VISITS,
                               source='phase recurrence hash-checked against all 838 Y7 samples of each real-PROM transmitter run',
                               analog='baseline B5, A2 gate and Q=1 filter; PCM gain and bias varied before complementary ADC',
                               readout='previously frozen pairs and ADC-margin selector'),
                  cases=rows,
                  limitations=[
                      'The PCM variations are separate hypothetical analog/ADC fixtures, not measured board conditions.',
                      'The D127, DAC, ADC, receive latch and USART routes remain untraced.',
                      'The source waveform is reconstructed from the verified R1 recurrence and byte-for-byte hash-matched to the executed Y7 transmitter; the variant receiver runs execute the real PROM.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
