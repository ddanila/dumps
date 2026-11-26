"""Audit the frozen 3F9 transition keys at ROM-sensitive loopback gaps."""

import hashlib
import json
from pathlib import Path

from joint_mask04_12a_3f9_gap_test import (ADC_VISITS, DATA_START_SYMBOL,
                                           RX_CYCLES)
from joint_mask04_12a_buffered_line import (BUSES, MAPPINGS, candidate,
                                           fixture, mapped,
                                           mapping_with_upper_source,
                                           pcm_at_shift, transmitter)
from joint_mask04_tx_12a_delayed_latch import capturing_execute as tx_execute
from lower_i_d3f8_full_adc import LONG_SAMPLES, SAMPLE_START
from receiver_four_row_condition_screen import configured
from receiver_mask04_3f9_3fa_feature_screen import (
    DEGREES, TRAIN_SEED, VISITS_PER_SYMBOL, capture, instrumented_execute,
    key, state)
from receiver_mask04_carrier_phase_screen import rotated_transmit
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
FEATURE = HERE / 'results/receiver-mask04-3f9-3fa-feature-screen.json'
LOOPBACK = HERE / 'results/joint-mask04-12a-buffered-line.json'
GAPS = HERE / 'results/joint-mask04-12a-readout-gap-audit.json'
GAP_TEST = HERE / 'results/joint-mask04-12a-3f9-gap-test.json'


def symbol_row(y, adc, symbol, phases, shift, extra, table, wanted):
    start = symbol * VISITS_PER_SYMBOL
    transition = key({'y': y}, symbol, phases, shift, extra)
    sample_start = symbol * 8
    return dict(symbol=symbol, wanted=wanted,
                adc_octet=adc[sample_start:sample_start + 8],
                y3f9_at_phases=[y[0x3F9][start + phase] for phase in phases],
                y3fa_at_phases=[y[0x3FA][start + phase] for phase in phases],
                previous_state=state({'y': y}, symbol - 1, phases, shift, extra),
                current_state=state({'y': y}, symbol, phases, shift, extra),
                key=transition, frozen_label=table.get(transition),
                key_in_training=transition in table)


def run(out=HERE / 'results/joint-mask04-12a-3f9-key-audit.json'):
    feature = json.loads(FEATURE.read_text())
    saved = json.loads(LOOPBACK.read_text())
    gaps = json.loads(GAPS.read_text())
    gap_test = json.loads(GAP_TEST.read_text())
    selected = feature['selected']
    phases = selected['phases']
    shift = selected['y3f9_two_bit_shift']
    extra = selected['y3fa_extra']
    table = {int(k): v for k, v in selected['frozen_table'].items()}
    if (phases != [46, 93] or shift != 4 or extra != 'none' or
            len(table) != 16):
        raise ValueError('frozen readout changed')
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    buses = json.loads(BUSES.read_text())['zero_error_survivors']
    rx = instrumented_execute()
    independent = []
    for degrees in DEGREES:
        case = capture(rx, mapping, base, TRAIN_SEED, degrees)
        pcm = rotated_transmit([0] * 8 + case['middle'] + [0] * 8, degrees)
        adc_samples = [127 - value for value in
                       pcm[SAMPLE_START:SAMPLE_START + LONG_SAMPLES]]
        rows = [symbol_row(case['y'], adc_samples, symbol, phases, shift,
                           extra, table, case['middle'][symbol])
                for symbol in range(2, 14)]
        prior = next(c for c in feature['cases'] if c['seed'] == TRAIN_SEED
                     and c['degrees'] == degrees)
        if (case['trace_digest'] != prior['trace_digest'] or
                case['adc_sha256'] != prior['adc_sha256'] or
                any(row['frozen_label'] != row['wanted'] for row in rows)):
            raise ValueError('independent training replay changed')
        independent.append(dict(degrees=degrees,
                                trace_digest=case['trace_digest'], rows=rows))
    tx = tx_execute()
    loopbacks = []
    for selector, delay in (('40', 5), ('60', 18)):
        offered = line_octets([0] * 8, delay)
        tx_result, raw, expected = transmitter(tx, mapping, base, offered)
        prior = next(c for c in saved['cases'] if c['selector'] == selector)
        pcm = pcm_at_shift(raw, buses[0], 6)
        adc_samples = [127 - value for value in pcm]
        adc = [sample for index, sample in enumerate(adc_samples)
               for _ in range(47 if index % 8 < 7 else 46)]
        if len(adc) != ADC_VISITS:
            raise ValueError('ADC visit schedule changed')
        result = rx(mapping, configured(base, adc, 'previous', 'overflow', 1),
                    RX_CYCLES, mode='integrated', trace_limit=0)
        if (not result['clean'] or
                tx_result['trace_digest'] != prior['tx_trace_digest'] or
                result['trace_digest'] != prior['receiver_handoff']['rx_trace_digest'] or
                hashlib.sha256(bytes(adc)).hexdigest() !=
                prior['receiver_handoff']['adc_sha256']):
            raise ValueError('loopback replay changed')
        rows = [symbol_row(result['selected_y'], adc_samples,
                           DATA_START_SYMBOL + index, phases, shift, extra,
                           table, expected[DATA_START_SYMBOL + index])
                for index in range(32)]
        gap_case = next(c for c in gaps['cases'] if c['selector'] == selector)
        no_correct = [r['data_dibit'] for r in gap_case['no_correct_dibit']]
        old = next(c for c in gap_test['cases'] if c['selector'] == selector)
        if ([r['frozen_label'] for r in rows] != old['predictions'] or
                no_correct != old['original_no_correct_indices']):
            raise ValueError('saved gap predictions changed')
        for index, row in enumerate(rows):
            row['data_index'] = index
            row['original_no_correct_gap'] = index in no_correct
        loopbacks.append(dict(selector=selector,
                              tx_trace_digest=tx_result['trace_digest'],
                              rx_trace_digest=result['trace_digest'],
                              rows=rows))
    report = dict(experiment='paired ADC and 3F9/3FA key audit for frozen readout',
                  fixture=dict(phases=phases, shift=shift, extra=extra,
                               training_seed=TRAIN_SEED,
                               buffered_output_bus=0, sample_shift=6),
                  independent=independent, loopbacks=loopbacks,
                  source_sha256={str(p.relative_to(HERE.parents[4])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (Path(__file__), FEATURE, LOOPBACK,
                                           GAPS, GAP_TEST)},
                  limitations=[
                      'The frozen lookup and symbol clock are external diagnostics.',
                      'DAC/ADC wiring, analog gain and filter are modeled assumptions.'
                  ])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    for case in result['loopbacks']:
        print(case['selector'], 'unseen keys',
              [r['data_index'] for r in case['rows'] if not r['key_in_training']],
              'original gaps',
              [(r['data_index'], r['key'], r['frozen_label'])
               for r in case['rows'] if r['original_no_correct_gap']])
