"""Retain complete executed receive-byte sequences for full-byte line cases."""

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
from reference_modem import receive

PRIOR = HERE / 'results/joint-mask04-full-bus-carrier-offset.json'
TARGET = HERE / 'results/joint-mask04-full-bus-agc-candidate.json'


def run(out=HERE / 'results/joint-mask04-full-bus-receive-states.json'):
    prior = json.loads(PRIOR.read_text())
    learned = json.loads(TARGET.read_text())
    target = (learned['fixture']['target_mean'], learned['fixture']['target_rms'])
    mapping = full.candidate(full.mapping_with_upper_source(0, '17.6'),
                             full.mapped(full.MAPPINGS['q3']), 4)
    _, base = full.fixture()
    paths = (Path(__file__), PRIOR, TARGET, Path(offset.__file__),
             Path(visits.__file__), Path(bus.__file__), Path(joined.__file__),
             Path(agc.__file__), Path(payloads.__file__),
             Path(buffered.__file__), Path(full.__file__),
             Path(loopback.__file__))
    report = dict(
        experiment='complete executed receive Y-byte states under full-byte line and ±7 Hz offsets',
        fixture=dict(payloads='earlier frozen non-zero line-byte pair',
                     development_offsets_hz=(0,),
                     reserved_validation_offsets_hz=(-7, 7),
                     capture_phases=visits.PHASES,
                     capture_fields=('row0', 'y3f8', 'row3'),
                     sample_site=f'{levels.SITE:03X}',
                     DAC_order=joined.ORDER,
                     analog='same Hilbert-shifted Q=1 full-byte line',
                     AGC='same frozen 128-sample preamble calibration',
                     tx_cycles=buffered.TX_CYCLES,
                     rx_cycles=buffered.RX_CYCLES),
        cases=[],
        limitations=[
            'The ADC/DAC, AGC, clock and latch routes remain explicit hypotheses.',
            'The reserved offset cases must not be used to fit a rule later described as validated on them.',
            'Stored expected dibits come from the known transmitted stream and are labels for analysis, not a receive input.',
            'A decoder fitted to the two zero-offset payloads still needs independent payload and phase-start validation.'],
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
                raise ValueError('source PCM changed')
            if offset_hz == 0 and changed != baseline_pcm:
                raise ValueError('zero-offset PCM changed')
            pcm, _ = agc.normalize_later(changed, target)
            if offset.digest_pcm(pcm) != old['corrected_pcm_sha256']:
                raise ValueError('ADC PCM changed')
            if receive(pcm) != expected[1:]:
                raise ValueError('reference decoder control changed')
            with patch.object(loopback, 'DATA', buffered.PIPELINE_SYMBOLS +
                              buffered.DATA_SYMBOLS), \
                    patch.object(loopback, 'SYMBOLS', buffered.RX_SYMBOLS), \
                    patch.object(loopback, 'ADC_VISITS', buffered.ADC_VISITS), \
                    patch.object(loopback, 'CYCLES', buffered.RX_CYCLES), \
                    patch.object(loopback, 'PHASES', visits.PHASES):
                rx, adc, symbols = loopback.capture(mapping, base, pcm, expected)
            if (rx['trace_digest'] != old['rx_trace_digest'] or
                    hashlib.sha256(bytes(adc)).hexdigest() != old['adc_sha256']):
                raise ValueError('PROM trace changed')
            report['cases'].append(dict(
                selector=selector, offset_hz=offset_hz,
                offered_line_bytes=offered.hex(' ').upper(),
                tx_cycles=tx['completed_cycles'],
                rx_cycles=rx['completed_cycles'],
                rx_trace_digest=rx['trace_digest'],
                adc_sha256=old['adc_sha256'],
                symbols=symbols))
            save(out, report)
            print(selector, offset_hz, 'symbols', len(symbols),
                  'visits/symbol', len(symbols[0]['visits']), flush=True)
    return report


if __name__ == '__main__':
    run()
