"""Test a frozen 3F9 transition table on the 12A buffered-loopback gaps."""

import hashlib
import json
from pathlib import Path

from joint_mask04_12a_buffered_line import (BUSES, MAPPINGS, candidate, fixture, mapped,
                                           mapping_with_upper_source,
                                           pcm_at_shift, transmitter)
from joint_mask04_tx_12a_delayed_latch import capturing_execute as tx_execute
from receiver_mask04_3f9_3fa_feature_screen import (
    instrumented_execute as rx_execute, key)
from receiver_four_row_condition_screen import configured
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
FEATURE = HERE / 'results/receiver-mask04-3f9-3fa-feature-screen.json'
LOOPBACK = HERE / 'results/joint-mask04-12a-buffered-line.json'
GAPS = HERE / 'results/joint-mask04-12a-readout-gap-audit.json'
DATA_START_SYMBOL = 33
ADC_VISITS = 65 * 375
RX_CYCLES = 32 * ADC_VISITS + 47


def run(out=HERE / 'results/joint-mask04-12a-3f9-gap-test.json'):
    feature = json.loads(FEATURE.read_text())
    saved = json.loads(LOOPBACK.read_text())
    gaps = json.loads(GAPS.read_text())
    selected = feature['selected']
    if (selected['phases'] != [46, 93] or
            selected['y3f9_two_bit_shift'] != 4 or
            selected['y3fa_extra'] != 'none' or
            selected['training'] != {'checks': 24, 'wrong': 0, 'unknown': 0}):
        raise ValueError('frozen independent feature changed')
    table = {int(key): value for key, value in selected['frozen_table'].items()}
    if len(table) != selected['table_keys']:
        raise ValueError('frozen table is incomplete')
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    buses = json.loads(BUSES.read_text())['zero_error_survivors']
    tx = tx_execute()
    rx = rx_execute()
    cases = []
    for selector, delay in (('40', 5), ('60', 18)):
        offered = line_octets([0] * 8, delay)
        tx_result, raw, expected = transmitter(tx, mapping, base, offered)
        prior = next(case for case in saved['cases']
                     if case['selector'] == selector)
        if tx_result['trace_digest'] != prior['tx_trace_digest']:
            raise ValueError('buffered transmitter trace changed')
        pcm = pcm_at_shift(raw, buses[0], 6)
        pcm_sha = hashlib.sha256(bytes(value + 127 for value in pcm)).hexdigest()
        saved_pcm = next(row for row in prior['bus_cases'][0]['scores']
                         if row['shift'] == 6)['pcm_sha256']
        if pcm_sha != saved_pcm:
            raise ValueError('ROM-sensitive PCM changed')
        adc = [127 - value for value in pcm]
        values = [sample for index, sample in enumerate(adc)
                  for _ in range(47 if index % 8 < 7 else 46)]
        if len(values) != ADC_VISITS:
            raise ValueError('ADC visit schedule changed')
        result = rx(mapping, configured(base, values, 'previous', 'overflow', 1),
                    RX_CYCLES, mode='integrated', trace_limit=0)
        prior_rx = prior['receiver_handoff']
        if (not result['clean'] or result['completed_cycles'] != RX_CYCLES or
                result['trace_digest'] != prior_rx['rx_trace_digest'] or
                hashlib.sha256(bytes(values)).hexdigest() != prior_rx['adc_sha256'] or
                any(len(result['selected_y'][pc]) != ADC_VISITS
                    for pc in (0x3F9, 0x3FA))):
            raise ValueError('buffered receiver trace changed')
        case_for_key = {'y': result['selected_y']}
        predicted = [table.get(key(case_for_key, DATA_START_SYMBOL + index,
                                   selected['phases'],
                                   selected['y3f9_two_bit_shift'],
                                   selected['y3fa_extra']))
                     for index in range(32)]
        wanted = expected[DATA_START_SYMBOL:]
        wrong = [index for index, (a, b) in enumerate(zip(predicted, wanted))
                 if a is not None and a != b]
        unknown = [index for index, value in enumerate(predicted) if value is None]
        gap_case = next(case for case in gaps['cases']
                        if case['selector'] == selector)
        original = [row['data_dibit'] for row in gap_case['no_correct_dibit']]
        newly_correct = [index for index in original
                         if index not in wrong and index not in unknown]
        remaining = [index for index in original if index not in newly_correct]
        cases.append(dict(selector=selector,
                          tx_trace_digest=tx_result['trace_digest'],
                          rx_trace_digest=result['trace_digest'],
                          pcm_sha256=pcm_sha,
                          adc_sha256=hashlib.sha256(bytes(values)).hexdigest(),
                          y3f9_sha256=hashlib.sha256(bytes(
                              result['selected_y'][0x3F9])).hexdigest(),
                          predictions=predicted,
                          wrong_indices=wrong, unknown_indices=unknown,
                          original_no_correct_indices=original,
                          newly_correct_original_gaps=newly_correct,
                          remaining_original_gaps=remaining))
    paths = (Path(__file__), FEATURE, LOOPBACK, GAPS,
             HERE / 'joint_mask04_12a_buffered_line.py',
             HERE / 'receiver_mask04_3f9_3fa_feature_screen.py',
             HERE.parent / 'assumed/execute.py')
    report = dict(experiment='frozen independent 3F9 transition feature on ROM-sensitive buffered line',
                  fixture=dict(feature=selected,
                               output_bus=0, sample_shift=6,
                               data_start_symbol=DATA_START_SYMBOL,
                               adc_visits=ADC_VISITS,
                               rx_cycles=RX_CYCLES),
                  cases=cases,
                  limitations=[
                      'The frozen lookup is an external diagnostic, not an identified board circuit.',
                      'The held-out loopback labels are used only for evaluation; no table entry is added from them.',
                      'The PROM gate, DAC/ADC buses, analog line and USART RxD path are assumed.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    for case in run()['cases']:
        print(case['selector'], 'wrong', case['wrong_indices'],
              'unknown', case['unknown_indices'],
              'rescued', case['newly_correct_original_gaps'])
