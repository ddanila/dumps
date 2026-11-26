"""Feed a frozen full-byte DAC bus from real DSC Tx into real DSC Rx and 8031."""

import hashlib
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
import joint_mask04_buffered_dac_bus as bus
import joint_mask04_buffered_serial_handoff as buffered
import joint_mask04_full_zero_handoff as full
import joint_mask04_tx_rx_loopback as loopback
from photo_dac_bus_permutations import mapped_codes
from photo_joint_line_filter_screen import SILENCE_END, TONE_END, bandpass
from receiver_mask04_adc_margin_selector import PAIRS, select
from receiver_mask04_dual_feature_consensus import consensus, decisions
from receiver_mask04_dual_zero_handoff import controller, frozen_tables
from receiver_mask04_feature_choice import alternative_states
from receiver_mask04_four_bit_transition import states_from_symbols
from receiver_mask04_long_pair_union import classify
from receiver_mask04_offset_visit_phase import project
from receiver_mask04_serial_candidate import bytes_lsb_first
from reference_modem import receive
from zero_run_detector import line_octets

PRIOR = HERE / 'results/joint-mask04-buffered-dac-bus.json'
ORDER = (4, 0, 6, 1, 3, 2, 5, 7)


def analog(raw):
    codes = mapped_codes(raw, ORDER)
    gated = codes[:TONE_END] + [128] * (SILENCE_END - TONE_END) + codes[SILENCE_END:]
    line = bandpass([code - 128 for code in gated], 1.0)
    selected = line[SILENCE_END + 6:SILENCE_END + 6 + buffered.RX_SYMBOLS * 8]
    if len(selected) != buffered.RX_SYMBOLS * 8:
        raise ValueError('full-bus PCM window incomplete')
    gain = 110 / max(abs(value) for value in selected)
    pcm = [max(-127, min(127, round(value * gain))) for value in selected]
    return codes, pcm, gain


def run(out=HERE / 'results/joint-mask04-buffered-full-bus-loopback.json'):
    prior = json.loads(PRIOR.read_text())
    primary, alternative = frozen_tables()
    mapping = full.candidate(full.mapping_with_upper_source(0, '17.6'),
                             full.mapped(full.MAPPINGS['q3']), 4)
    _, base = full.fixture()
    paths = (Path(__file__), PRIOR, Path(bus.__file__), Path(buffered.__file__),
             Path(full.__file__), Path(loopback.__file__),
             HERE / 'receiver_mask04_dual_zero_handoff.py',
             HERE / 'receiver_mask04_adc_margin_selector.py')
    report = dict(experiment='frozen photo-B5 full-DAC-byte real-PROM Tx/Rx loopback',
                  fixture=dict(permutation=ORDER,
                               source='previously frozen highest-correlation photo-B5 order',
                               sample_sites=('127', '129'),
                               analog='DAC mid-code A2 gate, Q=1 bandpass, six-sample alignment',
                               fallback_rule='use frozen 46/93 when known; otherwise frozen margin selector',
                               tx_cycles=buffered.TX_CYCLES,
                               rx_cycles=buffered.RX_CYCLES,
                               data_start_bit=buffered.DATA_START_BIT),
                  cases=[],
                  limitations=[
                      'Only Q4 to DAC08 B5 is photo-suggested; Y-to-latch order, remaining DAC bits and clock are untraced.',
                      'Analog filter, complementary ADC, two-visit decision and USART/SYNDET routes are assumed.',
                      'The fixed-first fallback rule was proposed after inspecting this full-bus fixture and is not an independent holdout.',
                      'The paced controller model runs after separate DSC Tx/Rx executions.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    with tempfile.TemporaryDirectory() as temporary:
        exe, controller_source_hash = buffered.compiled_controller(temporary)
        report['fixture']['modified_controller_probe_sha256'] = controller_source_hash
        for selector, delay in (('40', 5), ('60', 18)):
            offered = line_octets([0] * 8, delay)
            tx, raw_by_site, dibits = bus.samples(mapping, base, offered)
            prior_case = next(c for c in prior['cases'] if c['selector'] == selector)
            expected = [3] * 33 + dibits
            for site in ('127', '129'):
                raw = raw_by_site[int(site, 16)]
                old_site = prior_case['sites'][site]
                old_bus = next(c for c in old_site['bus_orders']
                               if tuple(c['permutation']) == ORDER)
                if hashlib.sha256(bytes(raw)).hexdigest() != old_site['raw_y_sha256']:
                    raise ValueError('full-Y PROM source changed')
                codes, pcm, gain = analog(raw)
                pcm_hash = hashlib.sha256(bytes(value + 127 for value in pcm)).hexdigest()
                if (hashlib.sha256(bytes(codes)).hexdigest() != old_bus['dac_code_sha256'] or
                        pcm_hash != old_bus['pcm_sha256']):
                    raise ValueError('full DAC/line fixture changed')
                reference = receive(pcm)
                reference_errors = [i + 1 for i, (actual, want) in
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
                data = fixed[33:]
                data_wrong = [i for i, (actual, want) in enumerate(zip(data, dibits))
                              if actual is not None and actual != want]
                data_unknown = [i for i, actual in enumerate(data) if actual is None]
                recovered = handoffs = None
                if not data_wrong and not data_unknown:
                    recovered = bytes_lsb_first([
                        bit for symbol in data
                        for bit in (symbol & 1, (symbol >> 1) & 1)])
                    if recovered != offered:
                        raise ValueError('fixed readout bytes differ from controller TxD')
                    handoffs = {str(pulse): controller(
                        exe, delay, int(selector, 16), pulse, recovered)
                        for pulse in (65, 66, 67, 130)}
                    handoffs['opposite_selector'] = controller(
                        exe, delay, 0x60 if selector == '40' else 0x40,
                        66, recovered)
                fallback_data = fallback[33:]
                fallback_recovered = fallback_handoffs = None
                if all(value is not None for value in fallback_data):
                    fallback_recovered = bytes_lsb_first([
                        bit for symbol in fallback_data
                        for bit in (symbol & 1, (symbol >> 1) & 1)])
                    if fallback_recovered == offered:
                        fallback_handoffs = {str(pulse): controller(
                            exe, delay, int(selector, 16), pulse,
                            fallback_recovered) for pulse in (65, 66, 67, 130)}
                        fallback_handoffs['opposite_selector'] = controller(
                            exe, delay, 0x60 if selector == '40' else 0x40,
                            66, fallback_recovered)
                scores = {f'{a}/{b}': classify(predictions[(a, b)], expected)
                          for a, b in PAIRS}
                margin = classify(picked, expected)
                fallback_score = classify(fallback, expected)
                case = dict(selector=selector, latch_word=site,
                            offered_line_bytes=[f'{value:02X}' for value in offered],
                            tx_cycles=tx['completed_cycles'],
                            tx_trace_digest=tx['trace_digest'],
                            tx_y_sha256=old_site['raw_y_sha256'],
                            dac_code_sha256=old_bus['dac_code_sha256'],
                            pcm_sha256=pcm_hash, pcm_gain=gain,
                            reference_errors=reference_errors,
                            rx_cycles=rx['completed_cycles'],
                            rx_trace_digest=rx['trace_digest'],
                            adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                            frozen_pair_scores=scores,
                            fixed_data_wrong_indices=data_wrong,
                            fixed_data_unknown_indices=data_unknown,
                            fixed_decisions=fixed,
                            fixed_recovered_line_bytes=(
                                [f'{value:02X}' for value in recovered]
                                if recovered is not None else None),
                            margin_score=margin,
                            margin_decisions=picked,
                            margin_selected_pairs=[
                                None if pair is None else f'{pair[0]}/{pair[1]}'
                                for pair in selected],
                            controller_handoffs=handoffs,
                            fallback_score=fallback_score,
                            fallback_decisions=fallback,
                            fallback_recovered_line_bytes=(
                                [f'{value:02X}' for value in fallback_recovered]
                                if fallback_recovered is not None else None),
                            fallback_controller_handoffs=fallback_handoffs)
                report['cases'].append(case)
                save(out, report)
                print(selector, site, 'reference', len(reference_errors),
                      'fixed wrong/unknown', len(data_wrong), len(data_unknown),
                      'margin wrong/unknown', margin['data_errors'],
                      margin['data_unknown'],
                      'controller', handoffs['66']['state'] if handoffs else None,
                      'fallback wrong/unknown', fallback_score['data_errors'],
                      fallback_score['data_unknown'],
                      'fallback controller',
                      fallback_handoffs['66']['state'] if fallback_handoffs else None,
                      flush=True)
    return report


if __name__ == '__main__':
    run()
