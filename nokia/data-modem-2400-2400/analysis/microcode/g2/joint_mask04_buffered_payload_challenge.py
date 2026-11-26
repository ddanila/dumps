"""Challenge the frozen buffered Tx/Rx path with non-zero line payloads."""

import hashlib
import sys
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
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

PAYLOADS = (
    ('40', bytes.fromhex('E4 1B C7 39 55 AA 00 FF')),
    ('60', bytes.fromhex('93 6C 2D D2 F0 0F 81 7E')),
)


def run(out=HERE / 'results/joint-mask04-buffered-payload-challenge.json'):
    primary, alternative = frozen_tables()
    mapping = full.candidate(full.mapping_with_upper_source(0, '17.6'),
                             full.mapped(full.MAPPINGS['q3']), 4)
    _, base = full.fixture()
    cases = []
    for selector, offered in PAYLOADS:
        inputs, dibits, events = buffered.buffered_inputs(offered)
        with patch.object(full, 'scenario_inputs', lambda symbols: inputs), \
                patch.object(full, 'SAMPLES', buffered.SAMPLES), \
                patch.object(full, 'TX_CYCLES', buffered.TX_CYCLES):
            tx, y7 = full.transmitter(mapping, base, dibits)
        with patch.object(full, 'SYMBOLS', buffered.RX_SYMBOLS):
            pcm, gain = full.pcm_from_bits(y7)
        expected = [3] * (buffered.PREAMBLE + buffered.PIPELINE_SYMBOLS) + dibits
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
        fixed = predictions[(46, 93)]
        fixed_data = fixed[buffered.PREAMBLE + buffered.PIPELINE_SYMBOLS:]
        recovered = None
        if all(value is not None for value in fixed_data):
            recovered = bytes_lsb_first([
                bit for dibit in fixed_data
                for bit in (dibit & 1, (dibit >> 1) & 1)])
        case = dict(selector=selector,
                    offered_line_bytes=offered.hex(' ').upper(),
                    dibits=dibits, bit_pair_events=events,
                    tx_cycles=tx['completed_cycles'],
                    tx_trace_digest=tx['trace_digest'],
                    tx_y7_sha256=hashlib.sha256(bytes(y7)).hexdigest(),
                    pcm_gain=gain,
                    pcm_sha256=hashlib.sha256(bytes(x + 127 for x in pcm)).hexdigest(),
                    reference_errors=reference_errors,
                    rx_cycles=rx['completed_cycles'],
                    rx_trace_digest=rx['trace_digest'],
                    adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                    frozen_pair_scores={f'{a}/{b}': classify(predictions[(a, b)], expected)
                                        for a, b in PAIRS},
                    fixed_recovered_line_bytes=(
                        bytes(recovered).hex(' ').upper()
                        if recovered is not None else None),
                    margin_score=classify(picked, expected),
                    margin_selected_pairs=[
                        None if pair is None else f'{pair[0]}/{pair[1]}'
                        for pair in selected])
        cases.append(case)
        print(selector, 'reference errors', len(reference_errors),
              'fixed data errors', case['frozen_pair_scores']['46/93']['data_errors'],
              'fixed data unknown', case['frozen_pair_scores']['46/93']['data_unknown'],
              'margin data errors', case['margin_score']['data_errors'], flush=True)
    report = dict(experiment='buffered serial non-zero payload challenge',
                  fixture=dict(data_start_bit=buffered.DATA_START_BIT,
                               pulse_width_visits=4,
                               tx_cycles=buffered.TX_CYCLES,
                               rx_cycles=buffered.RX_CYCLES,
                               analog='candidate B5, A2 gate, Q=1 filter, six-sample alignment'),
                  cases=cases,
                  limitations=[
                      'Serial buffer, D127 pulse decoder, DAC/ADC, clock, line and receiver readout are untraced hypotheses.',
                      'These arbitrary line bytes challenge modulation and demodulation only; they are not a completed 8031 receive protocol handoff.'],
                  source_sha256={path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in (Path(__file__), Path(buffered.__file__),
                                              Path(full.__file__), Path(loopback.__file__))})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
