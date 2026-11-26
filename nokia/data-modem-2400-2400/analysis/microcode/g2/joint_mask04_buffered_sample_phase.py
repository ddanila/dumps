"""Shift the ADC alignment of the saved real-PROM buffered payload streams."""

import hashlib
import json
import sys
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
import joint_mask04_buffered_serial_handoff as buffered
import joint_mask04_full_zero_handoff as full
import joint_mask04_tx_rx_loopback as loopback
from photo_joint_line_filter_screen import SILENCE_END, TONE_END, bandpass
from photo_joint_tone_training_data import DATA_STEP, SILENCE_SYMBOLS, TONE_STEP, TONE_SYMBOLS
from photo_main_dibit_pulse import BASE, VISITS_PER_SYMBOL
from receiver_mask04_adc_margin_selector import PAIRS, select
from receiver_mask04_dual_feature_consensus import consensus, decisions
from receiver_mask04_dual_zero_handoff import frozen_tables
from receiver_mask04_feature_choice import alternative_states
from receiver_mask04_four_bit_transition import states_from_symbols
from receiver_mask04_long_pair_union import classify
from receiver_mask04_offset_visit_phase import project
from reference_modem import receive

PRIOR = HERE / 'results/joint-mask04-buffered-payload-challenge.json'
OFFSETS = (5, 7)


def matched_line(prior):
    offered = bytes.fromhex(prior['offered_line_bytes'])
    candidate, dibits, _ = buffered.buffered_inputs(offered)
    inputs = ([TONE_STEP] * (TONE_SYMBOLS * VISITS_PER_SYMBOL) +
              [DATA_STEP] * (SILENCE_SYMBOLS * VISITS_PER_SYMBOL) +
              candidate + [BASE] * (6 * 375))
    phase = 242
    bits = []
    for visit, value in enumerate(inputs):
        phase = (phase + value) & 255
        if visit % 375 == 0:
            bits.append(phase >> 7)
        if len(bits) == buffered.SAMPLES + 1:
            break
    if (len(bits) != buffered.SAMPLES + 1 or
            hashlib.sha256(bytes(bits[:buffered.SAMPLES])).hexdigest() !=
            prior['tx_y7_sha256']):
        raise ValueError('phase recurrence does not match real-PROM Y7 source')
    codes = [8 * bit for bit in bits]
    gated = codes[:TONE_END] + [4] * (SILENCE_END - TONE_END) + codes[SILENCE_END:]
    line = bandpass([code - 4 for code in gated], 1.0)
    nominal = [max(-127, min(127, round(value * prior['pcm_gain'])))
               for value in line[SILENCE_END + 6:
                                 SILENCE_END + 6 + buffered.RX_SYMBOLS * 8]]
    if hashlib.sha256(bytes(value + 127 for value in nominal)).hexdigest() != prior['pcm_sha256']:
        raise ValueError('nominal PCM differs from executed-source report')
    return line, dibits


def run(out=HERE / 'results/joint-mask04-buffered-sample-phase.json'):
    prior = json.loads(PRIOR.read_text())
    primary, alternative = frozen_tables()
    mapping = full.candidate(full.mapping_with_upper_source(0, '17.6'),
                             full.mapped(full.MAPPINGS['q3']), 4)
    _, base = full.fixture()
    source_paths = (Path(__file__), PRIOR, Path(buffered.__file__),
                    Path(full.__file__), Path(loopback.__file__))
    report = dict(experiment='one-sample buffered analog/ADC phase challenge',
                  fixture=dict(sample_offsets=OFFSETS, nominal_offset=6,
                               gain='held at saved nominal PCM gain',
                               rx_cycles=buffered.RX_CYCLES,
                               source='phase recurrence hash-matched to executed real-PROM Y7',
                               analog='candidate B5, A2 gate, Q=1 filter'),
                  cases=[],
                  limitations=[
                      'Analog sample offset is an assumed ADC/line timing choice, not a measured board phase.',
                      'D127 source, DAC/ADC nets, decision circuit and USART route remain untraced.'],
                  source_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in source_paths})
    for original in prior['cases']:
        line, dibits = matched_line(original)
        expected = [3] * (buffered.PREAMBLE + buffered.PIPELINE_SYMBOLS) + dibits
        for offset in OFFSETS:
            selected_line = line[SILENCE_END + offset:
                                 SILENCE_END + offset + buffered.RX_SYMBOLS * 8]
            if len(selected_line) != buffered.RX_SYMBOLS * 8:
                raise ValueError('shifted signal incomplete')
            pcm = [max(-127, min(127, round(value * original['pcm_gain'])))
                   for value in selected_line]
            reference = receive(pcm)
            reference_errors = [i for i, (actual, target) in
                                enumerate(zip(reference, expected[1:]))
                                if actual != target]
            with patch.object(loopback, 'DATA', buffered.PIPELINE_SYMBOLS +
                              buffered.DATA_SYMBOLS), \
                    patch.object(loopback, 'SYMBOLS', buffered.RX_SYMBOLS), \
                    patch.object(loopback, 'ADC_VISITS', buffered.ADC_VISITS), \
                    patch.object(loopback, 'CYCLES', buffered.RX_CYCLES):
                rx, adc, symbols = loopback.capture(mapping, base, pcm, expected)
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
            row = dict(selector=original['selector'], sample_offset=offset,
                       offered_line_bytes=original['offered_line_bytes'],
                       reference_errors=reference_errors,
                       pcm_sha256=hashlib.sha256(bytes(value + 127 for value in pcm)).hexdigest(),
                       adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                       rx_cycles=rx['completed_cycles'],
                       rx_trace_digest=rx['trace_digest'],
                       frozen_pair_scores=scores,
                       margin_score=margin,
                       margin_selected_pairs=[None if pair is None else
                                              f'{pair[0]}/{pair[1]}'
                                              for pair in selected])
            report['cases'].append(row)
            save(out, report)
            print(original['selector'], offset, 'reference', len(reference_errors),
                  'fixed data wrong/unknown', scores['46/93']['data_errors'],
                  scores['46/93']['data_unknown'],
                  'margin data wrong/unknown', margin['data_errors'],
                  margin['data_unknown'], flush=True)
    return report


if __name__ == '__main__':
    run()
