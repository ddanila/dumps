"""Challenge the frozen full-byte DSC Tx/Rx readout at shifted ADC levels."""

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
import joint_mask04_buffered_serial_handoff as buffered
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

PRIOR = HERE / 'results/joint-mask04-buffered-full-bus-loopback.json'
VARIANTS = (('gain_0p75_bias_plus16', 0.75, 16),
            ('gain_0p75_bias_minus16', 0.75, -16))
SITE = 0x127


def recovered_bytes(values):
    data = values[33:]
    if len(data) != 32 or any(value is None for value in data):
        return None
    return bytes_lsb_first([
        bit for symbol in data for bit in (symbol & 1, (symbol >> 1) & 1)])


def run(out=HERE / 'results/joint-mask04-full-bus-level-challenge.json'):
    prior = json.loads(PRIOR.read_text())
    primary, alternative = frozen_tables()
    mapping = full.candidate(full.mapping_with_upper_source(0, '17.6'),
                             full.mapped(full.MAPPINGS['q3']), 4)
    _, base = full.fixture()
    paths = (Path(__file__), PRIOR, Path(bus.__file__), Path(joined.__file__),
             Path(buffered.__file__), Path(full.__file__), Path(loopback.__file__),
             HERE / 'receiver_mask04_adc_margin_selector.py')
    report = dict(experiment='frozen full-byte real-PROM Tx/Rx gain and ADC-bias challenge',
                  fixture=dict(variants=VARIANTS, sample_site=f'{SITE:03X}',
                               permutation=joined.ORDER,
                               source='nominal raw Y and PCM hash-checked against joined real-PROM run',
                               adc='complementary ADC after PCM level change',
                               tx_cycles=buffered.TX_CYCLES,
                               rx_cycles=buffered.RX_CYCLES,
                               readout='committed fixed 46/93 then frozen margin on abstention'),
                  cases=[],
                  limitations=[
                      'The gain and bias variants are modeled ADC input levels, not measured board conditions.',
                      'DAC/ADC nets, clocks, line filter, receiver decision gates and USART path remain untraced.',
                      'A reference decoder can retain information when the current PROM-byte readout fails.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    for selector, delay in (('40', 5), ('60', 18)):
        offered = line_octets([0] * 8, delay)
        tx, raw_by_site, dibits = bus.samples(mapping, base, offered)
        raw = raw_by_site[SITE]
        nominal = next(c for c in prior['cases']
                       if c['selector'] == selector and c['latch_word'] == f'{SITE:03X}')
        if hashlib.sha256(bytes(raw)).hexdigest() != nominal['tx_y_sha256']:
            raise ValueError('real-PROM Y source changed')
        codes, baseline_pcm, baseline_gain = joined.analog(raw)
        if (hashlib.sha256(bytes(codes)).hexdigest() != nominal['dac_code_sha256'] or
                hashlib.sha256(bytes(value + 127 for value in baseline_pcm)).hexdigest() !=
                nominal['pcm_sha256']):
            raise ValueError('nominal full-byte DAC/line fixture changed')
        expected = [3] * 33 + dibits
        for name, scale, bias in VARIANTS:
            pcm = [max(-127, min(127, round(scale * value + bias)))
                   for value in baseline_pcm]
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
                       scale=scale, pcm_bias=bias,
                       offered_line_bytes=[f'{value:02X}' for value in offered],
                       tx_cycles=tx['completed_cycles'],
                       tx_trace_digest=tx['trace_digest'],
                       nominal_pcm_gain=baseline_gain,
                       clipped_samples=sum(abs(round(scale * value + bias)) > 127
                                           for value in baseline_pcm),
                       pcm_sha256=hashlib.sha256(bytes(value + 127 for value in pcm)).hexdigest(),
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
                  'margin wrong/unknown', margin['data_errors'], margin['data_unknown'],
                  'fallback wrong/unknown', fallback_score['data_errors'],
                  fallback_score['data_unknown'],
                  'bytes exact', recovered == offered if recovered is not None else False,
                  flush=True)
    return report


if __name__ == '__main__':
    run()
