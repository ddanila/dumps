"""Check USART event-based symbol pairing against executed DSC input sequences."""

import argparse
import hashlib
import json
from pathlib import Path

from controller_segment2_pattern import standard_bits

HERE = Path(__file__).resolve().parent
PACED = HERE / 'results/main-loop-usart-txready.json'
RAW = HERE / 'results/usart-sync-fill-segment1.json'
DSC = HERE / 'results/photo-segment1-to-segment2-continuous.json'


def serial_bits(values):
    return [(value >> bit) & 1 for value in values for bit in range(8)]


def dibits(bits):
    if len(bits) % 2:
        raise ValueError('odd number of serial bits')
    return [(bits[index] << 1) | bits[index + 1]
            for index in range(0, len(bits), 2)]


def run(out=HERE / 'results/usart-txrdy-boundary-gate.json'):
    paced = json.loads(PACED.read_text())
    raw = json.loads(RAW.read_text())
    dsc = json.loads(DSC.read_text())
    bit_ticks = paced['fixture']['machine_ticks_per_bit']
    if bit_ticks != 416 or len(paced['cases']) != 16:
        raise ValueError('paced USART fixture changed')
    candidates = []
    for case in paced['cases']:
        selector = case['selector']
        polynomial = 'GPC' if selector == '40' else 'GPA'
        delay = case['txempty_fall_to_txrdy_rise_ticks']
        if (delay != case['first_data_bit_cycle'] - case['first_a4_write_cycle'] or
                case['first_txrdy_rise_cycle'] != case['first_data_bit_cycle']):
            raise ValueError(('TxRDY event timing changed', selector))
        needed_edges = (delay + bit_ticks - 1) // bit_ticks
        data = serial_bits([int(value, 16) for value in
                            case['first_nine_transmitted_bytes']])
        if data[1:65] != standard_bits(polynomial):
            raise ValueError(('standard bits no longer start after bridge', selector))
        continuous = next(row for row in dsc['cases']
                          if row['selector'] == selector and
                          row['a3_idle_rule'] == 'repeated_11_idle')
        raw_case = next(row for row in raw['cases'] if row['selector'] == selector)
        direct = next(row for row in raw_case['raw_pairing_projections']
                      if row['first_bit_offset'] == 1)
        offered = dibits([1] * 64 + data[1:65])
        if (offered != continuous['a3_symbols'] +
                continuous['actual_a4_segment2_symbols']):
            raise ValueError(('event-gated DSC input differs from PROM run',
                              selector, case['tx_clock_phase_ticks']))
        if (set(continuous['errors_by_12_candidate_buses']) != {0} or
                set(direct['errors_by_12_candidate_buses']) !=
                ({0} if selector == '40' else {1})):
            raise ValueError(('prior PROM decision counts changed', selector))
        candidates.append(dict(selector=selector,
                               tx_clock_phase_ticks=case['tx_clock_phase_ticks'],
                               txempty_fall_cycle=case['first_a4_write_cycle'],
                               txrdy_rise_and_first_data_bit_cycle=case['first_data_bit_cycle'],
                               txempty_to_data_bit_ticks=delay,
                               bit_edges_needed_after_txempty=needed_edges,
                               fill_bits_after_a3_entry=case['sync_fill_bits_since_a3_entry'],
                               has_64_fill_bits_after_a3_entry=(
                                   case['sync_fill_bits_since_a3_entry'] >= 64),
                               first_data_bit_bridge=data[0],
                               event_gate_omits_first_data_bit=True,
                               event_gate_matches_prior_real_prom_input=True,
                               prior_real_prom_trace_digest=continuous['trace_digest'],
                               prior_real_prom_microinstructions=continuous['microinstructions'],
                               event_gate_errors_by_12_candidate_buses=(
                                   continuous['errors_by_12_candidate_buses']),
                               fixed_raw_pairing_errors_by_12_candidate_buses=(
                                   direct['errors_by_12_candidate_buses'])))
    required_edges = sorted({case['bit_edges_needed_after_txempty']
                             for case in candidates})
    if required_edges != list(range(1, 9)):
        raise ValueError(('fixed-delay sweep coverage changed', required_edges))
    eligible = [case for case in candidates if case['has_64_fill_bits_after_a3_entry']]
    if not all(any(case['selector'] == selector for case in eligible)
               for selector in ('40', '60')):
        raise ValueError('no 32-symbol fill window in a controller selector')
    paths = [Path(__file__), PACED, RAW, DSC,
             HERE / 'controller_segment2_pattern.py']
    report = dict(
        status='TxEMPTY fall needs 1-8 bit edges to reach first data bit across sampled phases; TxRDY rise marks that boundary in the one-byte USART model, and a one-bit data skip reproduces prior real-PROM 0-error inputs for both selectors',
        hypothesis='a downstream clocked decoder can detect the first TxRDY rise after data is queued, omit the first shifted data bit, and pair the following bits; physical pins and decoder are untraced',
        fixed_txempty_delay_bit_edges_required=required_edges,
        fixed_txempty_delay_works_for_all_sampled_phases=False,
        clock_phases_with_64_fill_bits_after_a3_entry={
            selector: [case['tx_clock_phase_ticks'] for case in eligible
                       if case['selector'] == selector]
            for selector in ('40', '60')},
        cases=candidates,
        limitations=['The event gate is a labelled circuit hypothesis, not a photographed or traced TxRDY-to-DSC connection.',
                     'Only eight byte-clock phases per controller selector are sampled; A3 entry may not coincide with the physical segment-1 start.',
                     'The candidate omits one raw data bit at the transition; the actual board may pair or discard it differently.',
                     'The DSC error counts and trace digests are referenced from prior real-PROM runs after byte-for-byte input equivalence checks, not newly executed here.',
                     'No analog line waveform, DSC receiver or echo cancellation is established.'],
        source_sha256={str(path.relative_to(HERE.parents[2])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path,
                        default=HERE / 'results/usart-txrdy-boundary-gate.json')
    args = parser.parse_args()
    report = run(args.out)
    print('required TxEMPTY delays:', report['fixed_txempty_delay_bit_edges_required'])
    print('eligible phases:', report['clock_phases_with_64_fill_bits_after_a3_entry'])
