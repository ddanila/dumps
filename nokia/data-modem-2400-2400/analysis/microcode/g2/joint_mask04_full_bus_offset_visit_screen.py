"""Screen adjacent PROM capture visits on the full-byte offset fixture."""

import hashlib
import json
import sys
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
import joint_mask04_buffered_dac_bus as bus
import joint_mask04_buffered_full_bus_loopback as joined
import joint_mask04_buffered_payload_challenge as payloads
import joint_mask04_buffered_serial_handoff as buffered
import joint_mask04_full_bus_agc_candidate as agc
import joint_mask04_full_bus_carrier_offset as offset
import joint_mask04_full_bus_level_challenge as levels
import joint_mask04_full_zero_handoff as full
import joint_mask04_tx_rx_loopback as loopback
from receiver_mask04_dual_feature_consensus import consensus, decisions
from receiver_mask04_dual_zero_handoff import frozen_tables
from receiver_mask04_feature_choice import alternative_states
from receiver_mask04_four_bit_transition import states_from_symbols
from receiver_mask04_long_pair_union import classify
from receiver_mask04_offset_visit_phase import project
from reference_modem import receive

PRIOR = HERE / 'results/joint-mask04-full-bus-carrier-offset.json'
TARGET = HERE / 'results/joint-mask04-full-bus-agc-candidate.json'
PAIRS = ((45, 92), (46, 93), (47, 94), (48, 95),
         (46, 94), (47, 93), (93, 140), (94, 141))
PHASES = tuple(sorted(set(phase for pair in PAIRS for phase in pair)))


def readout(symbols, primary, alternative, pair):
    projected = project(symbols, *pair)
    first = decisions(states_from_symbols(projected), primary)
    second = decisions(alternative_states(projected), alternative)
    return consensus(first, second)


def run(out=HERE / 'results/joint-mask04-full-bus-offset-visit-screen.json'):
    prior = json.loads(PRIOR.read_text())
    learned = json.loads(TARGET.read_text())
    target = (learned['fixture']['target_mean'], learned['fixture']['target_rms'])
    if tuple(prior['fixture']['offsets_hz']) != offset.OFFSETS_HZ:
        raise ValueError('offset challenge fixture changed')
    primary, alternative = frozen_tables()
    mapping = full.candidate(full.mapping_with_upper_source(0, '17.6'),
                             full.mapped(full.MAPPINGS['q3']), 4)
    _, base = full.fixture()
    paths = (Path(__file__), PRIOR, TARGET, Path(offset.__file__),
             Path(agc.__file__), Path(bus.__file__), Path(joined.__file__),
             Path(payloads.__file__), Path(buffered.__file__),
             Path(full.__file__), Path(loopback.__file__))
    report = dict(
        experiment='adjacent receive-PROM visit screen on full-byte carrier-offset traces',
        fixture=dict(pairs=PAIRS, capture_phases=PHASES,
                     offsets_hz=offset.OFFSETS_HZ,
                     payloads='same earlier frozen non-zero pair',
                     DAC_order=joined.ORDER, sample_site=f'{levels.SITE:03X}',
                     analog='same Hilbert-rotated Q=1 full-byte line fixture',
                     AGC='same frozen 128-sample preamble calibration',
                     decision_tables='unchanged frozen two-feature tables',
                     tx_cycles=buffered.TX_CYCLES,
                     rx_cycles=buffered.RX_CYCLES),
        cases=[],
        limitations=[
            'These capture visits are exploratory external latch-clock hypotheses, not traced hardware.',
            'The rescue availability diagnostic uses expected dibits and is not a runnable decoder.',
            'No selector is fitted or validated by this screen; a chosen rule requires a fresh holdout.',
            'DAC, ADC, AGC, clock, decision and USART routes remain untraced.'],
        source_sha256={str(path.relative_to(HERE.parents[4])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    for selector, offered in payloads.PAYLOADS:
        tx, raw_by_site, dibits = bus.samples(mapping, base, offered)
        raw = raw_by_site[levels.SITE]
        _, baseline_pcm, gain = joined.analog(raw)
        expected = [3] * 33 + dibits
        for offset_hz in offset.OFFSETS_HZ:
            old = next(c for c in prior['cases']
                       if c['selector'] == selector and c['offset_hz'] == offset_hz)
            _, changed = offset.shifted_pcm(raw, offset_hz, gain)
            if offset.digest_pcm(changed) != old['shifted_pcm_sha256']:
                raise ValueError('shifted PCM changed')
            if offset_hz == 0 and changed != baseline_pcm:
                raise ValueError('zero-offset PCM changed')
            pcm, _ = agc.normalize_later(changed, target)
            if offset.digest_pcm(pcm) != old['corrected_pcm_sha256']:
                raise ValueError('corrected PCM changed')
            if receive(pcm) != expected[1:]:
                raise ValueError('reference control changed')
            with patch.object(loopback, 'DATA', buffered.PIPELINE_SYMBOLS +
                              buffered.DATA_SYMBOLS), \
                    patch.object(loopback, 'SYMBOLS', buffered.RX_SYMBOLS), \
                    patch.object(loopback, 'ADC_VISITS', buffered.ADC_VISITS), \
                    patch.object(loopback, 'CYCLES', buffered.RX_CYCLES), \
                    patch.object(loopback, 'PHASES', PHASES):
                rx, adc, symbols = loopback.capture(mapping, base, pcm, expected)
            if (rx['trace_digest'] != old['rx_trace_digest'] or
                    hashlib.sha256(bytes(adc)).hexdigest() != old['adc_sha256']):
                raise ValueError('PROM/ADC trace changed with wider capture')
            predictions = {pair: readout(symbols, primary, alternative, pair)
                           for pair in PAIRS}
            fixed = predictions[(46, 93)]
            fixed_score = classify(fixed, expected)
            if fixed_score != old['frozen_pair_scores']['46/93']:
                raise ValueError('frozen 46/93 decision changed')
            variants = {}
            for pair in PAIRS:
                candidate = predictions[pair]
                fallback = [value if value is not None else candidate[index]
                            for index, value in enumerate(fixed)]
                variants[f'{pair[0]}/{pair[1]}'] = dict(
                    score=classify(candidate, expected),
                    fixed_first=classify(fallback, expected),
                    rescued=[index for index in range(33, len(expected))
                             if fixed[index] is None and candidate[index] is not None],
                    conflicts=[index for index in range(33, len(expected))
                               if fixed[index] is not None and
                               candidate[index] is not None and
                               fixed[index] != candidate[index]])
            gaps = []
            for index in range(33, len(expected)):
                if fixed[index] is None:
                    known = {f'{a}/{b}': predictions[(a, b)][index]
                             for a, b in PAIRS
                             if predictions[(a, b)][index] is not None}
                    gaps.append(dict(symbol=index, expected=expected[index],
                                     known=known,
                                     has_correct=expected[index] in known.values()))
            row = dict(selector=selector, offset_hz=offset_hz,
                       offered_line_bytes=offered.hex(' ').upper(),
                       tx_cycles=tx['completed_cycles'],
                       rx_cycles=rx['completed_cycles'],
                       rx_trace_digest=rx['trace_digest'],
                       adc_sha256=old['adc_sha256'],
                       fixed_score=fixed_score, variants=variants,
                       fixed_unknown_gap_diagnostics=gaps,
                       gaps_without_correct_candidate=[g['symbol'] for g in gaps
                                                       if not g['has_correct']])
            report['cases'].append(row)
            save(out, report)
            print(selector, offset_hz,
                  'fixed gaps', len(gaps),
                  'without correct adjacent candidate',
                  row['gaps_without_correct_candidate'],
                  'fixed-first errors/unknown',
                  {key: (value['fixed_first']['data_errors'],
                         value['fixed_first']['data_unknown'])
                   for key, value in variants.items()}, flush=True)
    return report


if __name__ == '__main__':
    run()
