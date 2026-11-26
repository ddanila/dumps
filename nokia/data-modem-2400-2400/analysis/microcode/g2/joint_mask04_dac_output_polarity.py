"""Test complementary DAC08 current-output polarity in the joined receiver."""

import hashlib
import json
import sys
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from joint_mask04_full_zero_analog_variants import reconstructed_pcm
from joint_mask04_full_zero_handoff import (
    ADC_VISITS, DATA_SYMBOLS, PREAMBLE, RX_CYCLES, SYMBOLS,
)
import joint_mask04_tx_rx_loopback as loopback
from receiver_mask04_adc_margin_selector import PAIRS, select
from receiver_mask04_dual_feature_consensus import consensus, decisions
from receiver_mask04_dual_zero_handoff import frozen_tables
from receiver_mask04_feature_choice import alternative_states
from receiver_mask04_four_bit_transition import states_from_symbols
from receiver_mask04_long_pair_union import classify
from receiver_mask04_offset_visit_phase import project
from receiver_mask04_serial_candidate import bytes_lsb_first
from reference_modem import receive

PRIOR = HERE / 'results/joint-mask04-full-zero-handoff.json'
PHOTO = HERE.parents[2] / 'photos/PXL_20261123_114854803.jpg'


def run(out=HERE / 'results/joint-mask04-dac-output-polarity.json'):
    prior = json.loads(PRIOR.read_text())
    primary, alternative = frozen_tables()
    mapping = loopback.candidate(
        loopback.mapping_with_upper_source(0, '17.6'),
        loopback.mapped(loopback.MAPPINGS['q3']), 4)
    _, base = loopback.fixture()
    cases = []
    for original in prior['cases']:
        baseline, offered, dibits, gain = reconstructed_pcm(original)
        pcm = [-value for value in baseline]
        expected = [3] * PREAMBLE + dibits
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
        cases.append(dict(selector=original['selector'],
                          tx_y7_sha256=original['tx_y7_sha256'],
                          nominal_pcm_sha256=original['pcm_sha256'],
                          inverted_pcm_sha256=hashlib.sha256(
                              bytes(value + 127 for value in pcm)).hexdigest(),
                          adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                          rx_cycles=result['completed_cycles'],
                          rx_trace_digest=result['trace_digest'],
                          reference_errors=reference_errors,
                          fixed_pair_scores=scores,
                          margin_score=margin,
                          margin_wrong_pairs=[dict(symbol=index,
                                                   pair=selected[index],
                                                   expected=expected[index],
                                                   actual=picked[index])
                                              for index in margin['wrong_symbols']],
                          recovered_46_93_bytes=(
                              [f'{value:02X}' for value in recovered]
                              if recovered is not None else None),
                          offered_bytes=[f'{value:02X}' for value in offered]))
        print(original['selector'], 'reference', len(reference_errors),
              'fixed', scores['46/93']['errors'], scores['46/93']['unknown'],
              'margin', margin['errors'], margin['unknown'], flush=True)
    paths = (Path(__file__), PRIOR, PHOTO,
             HERE / 'joint_mask04_full_zero_analog_variants.py',
             HERE / 'joint_mask04_tx_rx_loopback.py',
             HERE / 'receiver_mask04_adc_margin_selector.py',
             HERE / 'receiver_mask04_dual_zero_handoff.py',
             HERE / 'reference_modem.py',
             loopback.MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='joined executed-transmitter PCM with opposite candidate DAC current-output polarity',
                  fixture=dict(selector_count=2, rx_cycles=RX_CYCLES,
                               source='reconstructed Y7/B5 PCM hash-matched to full real-PROM transmitter',
                               inversion='multiply centered analog PCM by minus one before complementary ADC',
                               readout='frozen capture pairs and ADC-margin selector'),
                  cases=cases,
                  limitations=[
                      'A DAC08 pin-2 versus pin-4 output choice is a polarity hypothesis; downstream amplification can also invert it.',
                      'The actual current-output and line route are not continuity-traced.',
                      'The receiver and controller links remain modeled; this test does not identify onboard phase or decision logic.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
