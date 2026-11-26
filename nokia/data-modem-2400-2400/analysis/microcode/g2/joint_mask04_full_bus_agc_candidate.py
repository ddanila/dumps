"""Test a causal preamble-calibrated analog normalization before DSC receive."""

import hashlib
import json
import math
import sys
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
import joint_mask04_buffered_dac_bus as bus
import joint_mask04_buffered_full_bus_loopback as joined
import joint_mask04_buffered_serial_handoff as buffered
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
from receiver_mask04_serial_candidate import bytes_lsb_first
from reference_modem import receive
from zero_run_detector import line_octets

PRIOR = HERE / 'results/joint-mask04-full-bus-level-challenge.json'
CALIBRATION_SAMPLES = 128


def moments(values):
    mean = sum(values) / len(values)
    rms = math.sqrt(sum((value - mean) ** 2 for value in values) / len(values))
    if rms == 0:
        raise ValueError('training waveform has no AC component')
    return mean, rms


def normalize_later(pcm, target):
    source = moments(pcm[:CALIBRATION_SAMPLES])
    mean, rms = source
    target_mean, target_rms = target
    ratio = target_rms / rms
    corrected = pcm[:CALIBRATION_SAMPLES] + [
        max(-127, min(127, round((value - mean) * ratio + target_mean)))
        for value in pcm[CALIBRATION_SAMPLES:]]
    return corrected, dict(source_mean=mean, source_rms=rms,
                           target_mean=target_mean, target_rms=target_rms,
                           gain_ratio=ratio,
                           calibration_samples=CALIBRATION_SAMPLES)


def recovered_bytes(decisions_):
    data = decisions_[33:]
    if len(data) != 32 or any(value is None for value in data):
        return None
    return bytes_lsb_first([
        bit for symbol in data for bit in (symbol & 1, (symbol >> 1) & 1)])


def run(out=HERE / 'results/joint-mask04-full-bus-agc-candidate.json'):
    prior = json.loads(PRIOR.read_text())
    primary, alternative = frozen_tables()
    mapping = full.candidate(full.mapping_with_upper_source(0, '17.6'),
                             full.mapped(full.MAPPINGS['q3']), 4)
    _, base = full.fixture()
    paths = (Path(__file__), PRIOR, Path(bus.__file__), Path(joined.__file__),
             Path(levels.__file__), Path(buffered.__file__),
             Path(full.__file__), Path(loopback.__file__))
    report = dict(experiment='preamble-calibrated gain/midpoint candidate before full-byte DSC receive',
                  fixture=dict(calibration_samples=CALIBRATION_SAMPLES,
                               calibration='first 128 A3 PCM samples; correction starts at sample 128',
                               target='nominal call preamble midpoint and RMS',
                               variants=levels.VARIANTS,
                               sample_site=f'{levels.SITE:03X}',
                               permutation=joined.ORDER,
                               tx_cycles=buffered.TX_CYCLES,
                               rx_cycles=buffered.RX_CYCLES,
                               readout='unchanged fixed 46/93 then frozen margin on abstention'),
                  cases=[],
                  limitations=[
                      'This AGC and midpoint stage is an external circuit hypothesis, not recovered DSC instructions or measured board behavior.',
                      'The target RMS comes from the modeled nominal call stream; it is not a measured ADC setpoint.',
                      'The first 128 training samples are uncorrected; only later samples use the learned coefficients.',
                      'DAC/ADC nets, sample clock, decision gates and USART route remain untraced.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    target = None
    for selector, delay in (('40', 5), ('60', 18)):
        offered = line_octets([0] * 8, delay)
        tx, raw_by_site, dibits = bus.samples(mapping, base, offered)
        raw = raw_by_site[levels.SITE]
        codes, baseline_pcm, gain = joined.analog(raw)
        prior_case = next(c for c in prior['cases']
                          if c['selector'] == selector and c['variant'] == levels.VARIANTS[0][0])
        variant_check = [max(-127, min(127, round(levels.VARIANTS[0][1] * value +
                                                  levels.VARIANTS[0][2])))
                         for value in baseline_pcm]
        if hashlib.sha256(bytes(value + 127 for value in variant_check)).hexdigest() != prior_case['pcm_sha256']:
            raise ValueError('level-challenge source waveform changed')
        if target is None:
            target = moments(baseline_pcm[:CALIBRATION_SAMPLES])
            report['fixture']['target_mean'] = target[0]
            report['fixture']['target_rms'] = target[1]
        expected = [3] * 33 + dibits
        for name, scale, bias in levels.VARIANTS:
            changed = [max(-127, min(127, round(scale * value + bias)))
                       for value in baseline_pcm]
            original = next(c for c in prior['cases']
                            if c['selector'] == selector and c['variant'] == name)
            if hashlib.sha256(bytes(value + 127 for value in changed)).hexdigest() != original['pcm_sha256']:
                raise ValueError('changed PCM differs from previous challenge')
            pcm, calibration = normalize_later(changed, target)
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
            recovered = recovered_bytes(fallback)
            scores = {f'{a}/{b}': classify(predictions[(a, b)], expected)
                      for a, b in PAIRS}
            margin = classify(picked, expected)
            fallback_score = classify(fallback, expected)
            row = dict(selector=selector, variant=name,
                       offered_line_bytes=[f'{value:02X}' for value in offered],
                       tx_cycles=tx['completed_cycles'],
                       tx_trace_digest=tx['trace_digest'],
                       raw_y_sha256=hashlib.sha256(bytes(raw)).hexdigest(),
                       dac_code_sha256=hashlib.sha256(bytes(codes)).hexdigest(),
                       nominal_pcm_gain=gain,
                       calibration=calibration,
                       uncorrected_prefix_samples=CALIBRATION_SAMPLES,
                       corrected_pcm_mae_vs_nominal=sum(abs(a-b) for a,b in zip(pcm,baseline_pcm))/len(pcm),
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
                           [f'{value:02X}' for value in recovered]
                           if recovered is not None else None),
                       margin_selected_pairs=[
                           None if pair is None else f'{pair[0]}/{pair[1]}'
                           for pair in selected])
            report['cases'].append(row)
            save(out, report)
            print(selector, name, 'reference wrong', len(reference_wrong),
                  'fixed wrong/unknown', scores['46/93']['data_errors'],
                  scores['46/93']['data_unknown'],
                  'fallback wrong/unknown', fallback_score['data_errors'],
                  fallback_score['data_unknown'],
                  'bytes exact', recovered == offered if recovered is not None else False,
                  flush=True)
    return report


if __name__ == '__main__':
    run()
