"""Hold out non-zero payloads for the committed 128-sample AGC candidate."""

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
import joint_mask04_full_bus_level_challenge as levels
import joint_mask04_full_zero_handoff as full
import joint_mask04_tx_rx_loopback as loopback
from receiver_mask04_adc_margin_selector import PAIRS, select
from receiver_mask04_dual_feature_consensus import consensus, decisions
from receiver_mask04_dual_zero_handoff import frozen_tables
from receiver_mask04_feature_choice import alternative_states
from receiver_mask04_four_bit_transition import states_from_symbols
from receiver_mask04_long_pair_union import classify
from receiver_mask04_offset_visit_phase import project
from reference_modem import receive

TARGET = HERE / 'results/joint-mask04-full-bus-agc-candidate.json'
PRIOR = HERE / 'results/joint-mask04-full-bus-payload-holdout.json'
Y7_PRIOR = HERE / 'results/joint-mask04-buffered-payload-challenge.json'


def run(out=HERE / 'results/joint-mask04-full-bus-agc-holdout.json'):
    learned = json.loads(TARGET.read_text())
    prior = json.loads(PRIOR.read_text())
    y7_prior = json.loads(Y7_PRIOR.read_text())
    target = (learned['fixture']['target_mean'], learned['fixture']['target_rms'])
    if learned['fixture']['calibration_samples'] != agc.CALIBRATION_SAMPLES:
        raise ValueError('committed AGC window changed')
    primary, alternative = frozen_tables()
    mapping = full.candidate(full.mapping_with_upper_source(0, '17.6'),
                             full.mapped(full.MAPPINGS['q3']), 4)
    _, base = full.fixture()
    paths = (Path(__file__), TARGET, PRIOR, Y7_PRIOR,
             Path(agc.__file__), Path(bus.__file__), Path(joined.__file__),
             Path(payloads.__file__), Path(levels.__file__),
             Path(buffered.__file__), Path(full.__file__), Path(loopback.__file__))
    report = dict(experiment='non-zero payload holdout for committed preamble AGC and full-byte DSC Rx',
                  fixture=dict(payloads='earlier frozen non-zero line-byte pair',
                               target_mean=target[0], target_rms=target[1],
                               calibration_samples=agc.CALIBRATION_SAMPLES,
                               correction_start_sample=agc.CALIBRATION_SAMPLES,
                               variants=levels.VARIANTS,
                               sample_site=f'{levels.SITE:03X}',
                               permutation=joined.ORDER,
                               readout='unchanged fixed 46/93 then frozen margin on abstention',
                               tx_cycles=buffered.TX_CYCLES,
                               rx_cycles=buffered.RX_CYCLES),
                  cases=[],
                  limitations=[
                      'The AGC/midpoint stage and target ADC amplitude are external modeling hypotheses, not identified Nokia hardware.',
                      'Gain/bias alternatives are synthetic and do not test arbitrary noise, drift or sample-clock phase.',
                      'Physical DAC/ADC, decision and USART routes remain untraced.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    for selector, offered in payloads.PAYLOADS:
        old_y7 = next(c for c in y7_prior['cases'] if c['selector'] == selector)
        if offered.hex(' ').upper() != old_y7['offered_line_bytes']:
            raise ValueError('held-out payload changed')
        tx, raw_by_site, dibits = bus.samples(mapping, base, offered)
        raw = raw_by_site[levels.SITE]
        if hashlib.sha256(bytes(value >> 7 for value in raw)).hexdigest() != old_y7['tx_y7_sha256']:
            raise ValueError('full-byte source differs from saved executed Y7')
        codes, nominal_pcm, gain = joined.analog(raw)
        old_full = next(c for c in prior['cases']
                        if c['selector'] == selector and c['sample_site'] == f'{levels.SITE:03X}')
        if hashlib.sha256(bytes(value + 127 for value in nominal_pcm)).hexdigest() != old_full['pcm_sha256']:
            raise ValueError('nominal held-out full-byte PCM changed')
        expected = [3] * 33 + dibits
        for name, scale, bias in levels.VARIANTS:
            changed = [max(-127, min(127, round(scale * value + bias)))
                       for value in nominal_pcm]
            pcm, calibration = agc.normalize_later(changed, target)
            reference = receive(pcm)
            if len(reference) != len(expected) - 1:
                raise ValueError('reference decoder window incomplete')
            reference_wrong = [index + 1 for index, (actual, want) in
                               enumerate(zip(reference, expected[1:]))
                               if actual != want]
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
            fixed = predictions[(46, 93)]
            fallback = [value if value is not None else picked[index]
                        for index, value in enumerate(fixed)]
            recovered = agc.recovered_bytes(fallback)
            scores = {f'{a}/{b}': classify(predictions[(a, b)], expected)
                      for a, b in PAIRS}
            margin = classify(picked, expected)
            fallback_score = classify(fallback, expected)
            row = dict(selector=selector, variant=name,
                       offered_line_bytes=offered.hex(' ').upper(),
                       tx_cycles=tx['completed_cycles'],
                       tx_trace_digest=tx['trace_digest'],
                       raw_y_sha256=hashlib.sha256(bytes(raw)).hexdigest(),
                       dac_code_sha256=hashlib.sha256(bytes(codes)).hexdigest(),
                       nominal_pcm_gain=gain,
                       calibration=calibration,
                       changed_pcm_sha256=hashlib.sha256(bytes(value + 127 for value in changed)).hexdigest(),
                       corrected_pcm_sha256=hashlib.sha256(bytes(value + 127 for value in pcm)).hexdigest(),
                       reference_wrong_symbols=reference_wrong,
                       rx_cycles=rx['completed_cycles'],
                       rx_trace_digest=rx['trace_digest'],
                       adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                       frozen_pair_scores=scores,
                       margin_score=margin,
                       fallback_score=fallback_score,
                       fallback_decisions=fallback,
                       fallback_recovered_line_bytes=(
                           bytes(recovered).hex(' ').upper()
                           if recovered is not None else None),
                       margin_selected_pairs=[
                           None if pair is None else f'{pair[0]}/{pair[1]}'
                           for pair in selected])
            report['cases'].append(row)
            save(out, report)
            print(selector, name, 'reference', len(reference_wrong),
                  'fixed wrong/unknown', scores['46/93']['data_errors'],
                  scores['46/93']['data_unknown'],
                  'fallback wrong/unknown', fallback_score['data_errors'],
                  fallback_score['data_unknown'],
                  'bytes exact', recovered == list(offered) if recovered is not None else False,
                  flush=True)
    return report


if __name__ == '__main__':
    run()
