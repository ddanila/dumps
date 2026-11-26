"""Capture executed Y and ADC bytes at offset-case readout gaps."""

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
import joint_mask04_full_bus_offset_visit_screen as visits
import joint_mask04_full_zero_handoff as full
import joint_mask04_tx_rx_loopback as loopback
from receiver_mask04_dual_zero_handoff import frozen_tables
from receiver_mask04_feature_choice import alternative_state
from receiver_mask04_four_bit_transition import state
from receiver_mask04_holdout_gap_audit import adc_sample

PRIOR = HERE / 'results/joint-mask04-full-bus-offset-visit-screen.json'
TARGET = HERE / 'results/joint-mask04-full-bus-agc-candidate.json'
CASES = (('40', -7, (46, 56)), ('40', 7, (56,)), ('60', 7, (39,)))


def pair_features(symbols, index, pair, primary, alternative):
    first, second = pair
    prev = symbols[index - 1]['visits']
    current = symbols[index]['visits']
    p_before = state(prev[str(first)]['y3f8'], prev[str(second)]['y3f8'])
    p_after = state(current[str(first)]['y3f8'], current[str(second)]['y3f8'])
    a_before = alternative_state(prev[str(first)]['y3f8'], prev[str(second)]['y3f8'])
    a_after = alternative_state(current[str(first)]['y3f8'], current[str(second)]['y3f8'])
    p_key = (p_before << 4) | p_after
    a_key = (a_before << 4) | a_after
    return dict(primary_key=f'{p_key:02X}', primary_prediction=primary.get(p_key),
                alternative_key=f'{a_key:02X}',
                alternative_prediction=alternative.get(a_key))


def run(out=HERE / 'results/joint-mask04-full-bus-offset-gap-audit.json'):
    prior = json.loads(PRIOR.read_text())
    learned = json.loads(TARGET.read_text())
    target = (learned['fixture']['target_mean'], learned['fixture']['target_rms'])
    primary, alternative = frozen_tables()
    mapping = full.candidate(full.mapping_with_upper_source(0, '17.6'),
                             full.mapped(full.MAPPINGS['q3']), 4)
    _, base = full.fixture()
    paths = (Path(__file__), PRIOR, TARGET, Path(offset.__file__),
             Path(visits.__file__), Path(bus.__file__), Path(joined.__file__),
             Path(agc.__file__), Path(buffered.__file__),
             Path(full.__file__), Path(loopback.__file__))
    report = dict(
        experiment='executed DSC receive bytes at four full-byte carrier-offset readout gaps',
        fixture=dict(cases=CASES, pairs=visits.PAIRS,
                     capture_phases=visits.PHASES,
                     ADC='same complementary PCM and 47/46 visits per sample',
                     PROM='same joint mask-04 real-PROM receiver',
                     decision_tables='unchanged frozen primary/alternative'),
        cases=[],
        limitations=[
            'Expected dibits are used only to select and describe the four previously identified gaps.',
            'The captured bytes do not identify a physical latch or decoder.',
            'These fixtures retain assumed DAC/ADC, AGC, clock and line routes.'],
        source_sha256={str(path.relative_to(HERE.parents[4])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    offered_by_selector = {selector: offered for selector, offered in payloads.PAYLOADS}
    for selector, offset_hz, targets in CASES:
        old = next(row for row in prior['cases']
                   if row['selector'] == selector and row['offset_hz'] == offset_hz)
        if old['gaps_without_correct_candidate'] != list(targets):
            raise ValueError('prior gap targets changed')
        offered = offered_by_selector[selector]
        tx, raw_by_site, dibits = bus.samples(mapping, base, offered)
        raw = raw_by_site[levels.SITE]
        _, _, gain = joined.analog(raw)
        _, changed = offset.shifted_pcm(raw, offset_hz, gain)
        pcm, _ = agc.normalize_later(changed, target)
        expected = [3] * 33 + dibits
        with patch.object(loopback, 'DATA', buffered.PIPELINE_SYMBOLS +
                          buffered.DATA_SYMBOLS), \
                patch.object(loopback, 'SYMBOLS', buffered.RX_SYMBOLS), \
                patch.object(loopback, 'ADC_VISITS', buffered.ADC_VISITS), \
                patch.object(loopback, 'CYCLES', buffered.RX_CYCLES), \
                patch.object(loopback, 'PHASES', visits.PHASES):
            rx, adc, symbols = loopback.capture(mapping, base, pcm, expected)
        if (rx['trace_digest'] != old['rx_trace_digest'] or
                hashlib.sha256(bytes(adc)).hexdigest() != old['adc_sha256']):
            raise ValueError('PROM or ADC trace changed')
        gaps = []
        for index in targets:
            snapshots = []
            for symbol in range(index - 1, index + 2):
                s = symbols[symbol]
                snapshots.append(dict(
                    symbol=symbol, expected=s['dibit'],
                    visits={str(phase): dict(
                        **s['visits'][str(phase)],
                        adc=adc_sample(pcm, symbol, phase))
                            for phase in visits.PHASES}))
            pair_keys = {f'{a}/{b}': pair_features(symbols, index, (a, b),
                                                   primary, alternative)
                         for a, b in visits.PAIRS}
            gaps.append(dict(symbol=index, expected=expected[index],
                             nearby_symbols=snapshots, pair_keys=pair_keys))
        report['cases'].append(dict(selector=selector, offset_hz=offset_hz,
                                    tx_cycles=tx['completed_cycles'],
                                    rx_cycles=rx['completed_cycles'],
                                    rx_trace_digest=rx['trace_digest'],
                                    adc_sha256=old['adc_sha256'], gaps=gaps))
        save(out, report)
        print(selector, offset_hz, [(g['symbol'], g['expected'],
                                      g['pair_keys']['46/93']) for g in gaps],
              flush=True)
    return report


if __name__ == '__main__':
    run()
