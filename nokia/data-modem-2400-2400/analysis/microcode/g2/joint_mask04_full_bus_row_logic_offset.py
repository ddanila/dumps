"""Test the already-frozen row-3 Boolean readout on full-byte offset runs."""

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
import joint_mask04_full_zero_handoff as full
import joint_mask04_tx_rx_loopback as loopback
from receiver_mask04_long_pair_union import classify
from receiver_mask04_phase47_logic import phase_quadrant
from reference_modem import QUADRANT_TO_DIBIT, receive

PRIOR = HERE / 'results/joint-mask04-full-bus-carrier-offset.json'
TARGET = HERE / 'results/joint-mask04-full-bus-agc-candidate.json'
PHASES = (46, 47, 48, 93, 94)


def readout(symbols, phase):
    quadrants = [phase_quadrant(s['visits'][str(phase)]['row0'],
                                s['visits'][str(phase)]['row3'])
                 for s in symbols]
    return [None] + [QUADRANT_TO_DIBIT[(current - previous - 2) & 3]
                     for previous, current in zip(quadrants, quadrants[1:])]


def run(out=HERE / 'results/joint-mask04-full-bus-row-logic-offset.json'):
    prior = json.loads(PRIOR.read_text())
    learned = json.loads(TARGET.read_text())
    target = (learned['fixture']['target_mean'], learned['fixture']['target_rms'])
    if tuple(prior['fixture']['offsets_hz']) != offset.OFFSETS_HZ:
        raise ValueError('offset fixture changed')
    mapping = full.candidate(full.mapping_with_upper_source(0, '17.6'),
                             full.mapped(full.MAPPINGS['q3']), 4)
    _, base = full.fixture()
    paths = (Path(__file__), PRIOR, TARGET, Path(offset.__file__),
             HERE / 'receiver_mask04_phase47_logic.py',
             HERE / 'results/receiver-mask04-phase47-logic.json',
             Path(bus.__file__), Path(joined.__file__), Path(agc.__file__),
             Path(payloads.__file__), Path(buffered.__file__),
             Path(full.__file__), Path(loopback.__file__))
    report = dict(
        experiment='frozen row-3 Boolean phase readout on full-byte carrier-offset DSC receive',
        fixture=dict(payloads='previously frozen non-zero line-byte pair',
                     offsets_hz=offset.OFFSETS_HZ,
                     phases=PHASES, frozen_original_phase=47,
                     sample_site=f'{levels.SITE:03X}',
                     DAC_order=joined.ORDER,
                     analog='same Hilbert-shifted Q=1 full-byte line',
                     AGC='same fixed target and 128-sample preamble calibration',
                     readout='unchanged phase_quadrant(row0,row3), then subtract 2 and differential map',
                     tx_cycles=buffered.TX_CYCLES,
                     rx_cycles=buffered.RX_CYCLES),
        cases=[],
        limitations=[
            'The Boolean phase gate was derived on earlier reference-waveform traces, not this full-byte line fixture.',
            'Phase 47 is its frozen capture site; 46, 48, 93 and 94 are exploratory clock alternatives, not a fitted selector.',
            'The gate, symbol memory, clock, ADC, AGC, DAC and USART paths are external hypotheses.',
            'Only one carrier phase start and two non-zero payloads are represented.'],
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
            _, shifted = offset.shifted_pcm(raw, offset_hz, gain)
            if offset.digest_pcm(shifted) != old['shifted_pcm_sha256']:
                raise ValueError('shifted PCM changed')
            if offset_hz == 0 and shifted != baseline_pcm:
                raise ValueError('zero-offset PCM changed')
            pcm, _ = agc.normalize_later(shifted, target)
            if offset.digest_pcm(pcm) != old['corrected_pcm_sha256']:
                raise ValueError('corrected PCM changed')
            if receive(pcm) != expected[1:]:
                raise ValueError('independent reference control changed')
            with patch.object(loopback, 'DATA', buffered.PIPELINE_SYMBOLS +
                              buffered.DATA_SYMBOLS), \
                    patch.object(loopback, 'SYMBOLS', buffered.RX_SYMBOLS), \
                    patch.object(loopback, 'ADC_VISITS', buffered.ADC_VISITS), \
                    patch.object(loopback, 'CYCLES', buffered.RX_CYCLES), \
                    patch.object(loopback, 'PHASES', PHASES):
                rx, adc, symbols = loopback.capture(mapping, base, pcm, expected)
            if (rx['trace_digest'] != old['rx_trace_digest'] or
                    hashlib.sha256(bytes(adc)).hexdigest() != old['adc_sha256']):
                raise ValueError('PROM or ADC stream changed')
            phases = {}
            for phase in PHASES:
                dibit_out = readout(symbols, phase)
                recovered = agc.recovered_bytes(dibit_out)
                phases[str(phase)] = dict(
                    score=classify(dibit_out, expected),
                    recovered_line_bytes=(
                        bytes(recovered).hex(' ').upper()
                        if recovered is not None else None),
                    exact_bytes=recovered == list(offered)
                    if recovered is not None else False)
            report['cases'].append(dict(
                selector=selector, offset_hz=offset_hz,
                offered_line_bytes=offered.hex(' ').upper(),
                tx_cycles=tx['completed_cycles'],
                rx_cycles=rx['completed_cycles'],
                rx_trace_digest=rx['trace_digest'],
                adc_sha256=old['adc_sha256'], phases=phases))
            save(out, report)
            print(selector, offset_hz,
                  {phase: (value['score']['data_errors'],
                           value['exact_bytes'])
                   for phase, value in phases.items()}, flush=True)
    return report


if __name__ == '__main__':
    run()
