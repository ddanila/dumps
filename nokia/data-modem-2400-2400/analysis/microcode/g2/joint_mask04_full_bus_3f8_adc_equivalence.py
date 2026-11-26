"""Check whether captured 3F8 Y adds information beyond the ADC high nibble."""

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
import joint_mask04_buffered_dac_bus as bus
import joint_mask04_buffered_full_bus_loopback as joined
import joint_mask04_buffered_payload_challenge as payloads
import joint_mask04_full_bus_agc_candidate as agc
import joint_mask04_full_bus_carrier_offset as offset
import joint_mask04_full_bus_level_challenge as levels
import joint_mask04_full_bus_receive_states as states
import joint_mask04_full_zero_handoff as full
from receiver_mask04_holdout_gap_audit import adc_sample

SOURCE = HERE / 'results/joint-mask04-full-bus-receive-states.json'
PRIOR = HERE / 'results/joint-mask04-full-bus-carrier-offset.json'
TARGET = HERE / 'results/joint-mask04-full-bus-agc-candidate.json'
PAIR = (47, 94)


def run(out=HERE / 'results/joint-mask04-full-bus-3f8-adc-equivalence.json'):
    source = json.loads(SOURCE.read_text())
    prior = json.loads(PRIOR.read_text())
    learned = json.loads(TARGET.read_text())
    target = (learned['fixture']['target_mean'], learned['fixture']['target_rms'])
    mapping = full.candidate(full.mapping_with_upper_source(0, '17.6'),
                             full.mapped(full.MAPPINGS['q3']), 4)
    _, base = full.fixture()
    paths = (Path(__file__), SOURCE, PRIOR, TARGET,
             Path(states.__file__), Path(offset.__file__),
             Path(bus.__file__), Path(joined.__file__),
             Path(agc.__file__), Path(payloads.__file__), Path(full.__file__),
             HERE / 'receiver_mask04_holdout_gap_audit.py',
             HERE / 'JOINT-MASK04-ADC-ROM-WRAPPER-RULE.md')
    report = dict(
        experiment='captured 3F8 Y versus modeled ADC high nibble on full-byte DSC streams',
        fixture=dict(source=SOURCE.name, capture_phases=source['fixture']['capture_phases'],
                     ADC='127 - corrected signed PCM; 47/46 visits per sample',
                     checked_identity='Y3F8 == (ADC & 0xF0) | 0x0F',
                     sign_pair=PAIR,
                     DAC_order=joined.ORDER, sample_site=f'{levels.SITE:03X}'),
        cases=[],
        limitations=[
            'The equality is checked at the ten captured visits per symbol, not every 3F8 visit in the receive run.',
            'ADC/DAC, AGC, filter and clock routes remain model assumptions.',
            '3F8 still performs an executed ROM-index calculation; direct quantizer equivalence at Y does not characterize later state or 3ED output.',
            'A decoder using only these Y3F8 bytes cannot distinguish the modeled PROM from the same ADC high-nibble stream.'],
        source_sha256={str(path.relative_to(HERE.parents[4])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    for selector, offered in payloads.PAYLOADS:
        tx, raw_by_site, _ = bus.samples(mapping, base, offered)
        raw = raw_by_site[levels.SITE]
        _, _, gain = joined.analog(raw)
        for offset_hz in offset.OFFSETS_HZ:
            case = next(c for c in source['cases']
                        if c['selector'] == selector and c['offset_hz'] == offset_hz)
            old = next(c for c in prior['cases']
                       if c['selector'] == selector and c['offset_hz'] == offset_hz)
            _, changed = offset.shifted_pcm(raw, offset_hz, gain)
            pcm, _ = agc.normalize_later(changed, target)
            if (offset.digest_pcm(changed) != old['shifted_pcm_sha256'] or
                    offset.digest_pcm(pcm) != old['corrected_pcm_sha256'] or
                    case['rx_trace_digest'] != old['rx_trace_digest'] or
                    case['adc_sha256'] != old['adc_sha256']):
                raise ValueError('saved full-byte fixture changed')
            mismatches = []
            sign_pair_mismatches = []
            checks = 0
            for symbol in case['symbols']:
                index = symbol['symbol']
                for phase, captured in symbol['visits'].items():
                    adc = adc_sample(pcm, index, int(phase))['complementary_byte']
                    expected_y = (adc & 0xF0) | 0x0F
                    checks += 1
                    if captured['y3f8'] != expected_y:
                        mismatches.append(dict(symbol=index, phase=int(phase),
                                               adc=adc, observed_y=captured['y3f8'],
                                               expected_y=expected_y))
                a, b = PAIR
                adc_a = adc_sample(pcm, index, a)['complementary_byte']
                adc_b = adc_sample(pcm, index, b)['complementary_byte']
                y_a = symbol['visits'][str(a)]['y3f8']
                y_b = symbol['visits'][str(b)]['y3f8']
                raw_signs = ((adc_a >> 7) & 1, (adc_b >> 7) & 1)
                prom_signs = ((y_a >> 7) & 1, (y_b >> 7) & 1)
                if raw_signs != prom_signs:
                    sign_pair_mismatches.append(index)
            report['cases'].append(dict(
                selector=selector, offset_hz=offset_hz,
                tx_cycles=tx['completed_cycles'],
                rx_cycles=case['rx_cycles'],
                rx_trace_digest=case['rx_trace_digest'],
                adc_sha256=case['adc_sha256'],
                captures_checked=checks,
                mismatches=mismatches,
                sign_pair_mismatches=sign_pair_mismatches))
            save(out, report)
            print(selector, offset_hz, 'matches', checks - len(mismatches),
                  '/', checks, 'sign-pair mismatches', len(sign_pair_mismatches),
                  flush=True)
    return report


if __name__ == '__main__':
    run()
