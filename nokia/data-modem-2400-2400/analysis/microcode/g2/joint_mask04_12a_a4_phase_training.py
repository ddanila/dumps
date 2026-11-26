"""Learn offset-32 receive labels from controller A4 rate pattern only."""

import hashlib
import itertools
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import joint_mask04_12a_analog_holdout as holdout
import joint_mask04_12a_buffered_line as line
import joint_mask04_buffered_serial_handoff as handoff
import joint_mask04_q05_phase_level_map as phase_model
import joint_mask04_tx_rx_loopback as loopback
from controller_segment2_pattern import standard_bits
from joint_mask04_12a_phase_timing_map import decode
from joint_mask04_q05_fresh_payload_levels import PAYLOADS
from joint_mask04_tx_12a_delayed_latch import capturing_execute
from photo_dac_bus_permutations import mapped_codes
from photo_joint_line_filter_screen import SILENCE_END, TONE_END, bandpass
from receiver_mask04_feature_choice import alternative_states
from receiver_mask04_offset_visit_phase import project
from reference_modem import receive
from zero_run_detector import line_octets

HERE = Path(__file__).resolve().parent
FIXED = HERE / 'results/joint-mask04-12a-fixed-gain-phase.json'
FRESH_TX = HERE / 'results/joint-mask04-12a-phase-timing.json'
FRESH_RX = HERE / 'results/joint-mask04-12a-phase-timing-rx.json'
CONTROLLER_A4 = HERE / 'results/controller-segment2-pattern.json'
VISIT = TONE_END * 375 + 1


def pack_lsb(bits):
    if len(bits) != 64:
        raise ValueError('A4 segment-2 bit length changed')
    return [sum(bits[8 * byte + bit] << bit for bit in range(8))
            for byte in range(8)]


def run(out=HERE / 'results/joint-mask04-12a-a4-phase-training.json'):
    fixed = json.loads(FIXED.read_text())
    fresh_tx = json.loads(FRESH_TX.read_text())
    fresh_rx = json.loads(FRESH_RX.read_text())
    controller_a4 = json.loads(CONTROLLER_A4.read_text())
    if not any(row['selector'] == '40' and row['polynomial'] == 'GPC'
               and row['bit_order'] == 'lsb_first' and row['start_bit'] == 1
               for row in controller_a4['exact_64_bit_windows']):
        raise ValueError('controller A4 segment-2 window changed')
    offered = pack_lsb(standard_bits('GPC'))
    mapping = line.candidate(line.mapping_with_upper_source(0, '17.6'),
                             line.mapped(line.MAPPINGS['q3']), 4)
    _, base = line.fixture()
    tx, raw, expected = line.transmitter(
        capturing_execute((VISIT, 32)), mapping, base, offered)
    gain = next(b for b in next(c for c in fixed['cases']
                               if c['selector'] == '40')['bus_cases']
                if b['bus_index'] == 0)['gain']
    codes = mapped_codes(raw, holdout.BUSES[0])
    gated = codes[:TONE_END] + [128] * (SILENCE_END - TONE_END) + codes[SILENCE_END:]
    wave = bandpass([value - 128 for value in gated], 0.5)
    selected = wave[SILENCE_END + 6:SILENCE_END + 6 + line.RX_SYMBOLS * 8]
    pcm = [max(-127, min(127, round(value * gain))) for value in selected]
    reference_wrong = [i for i, (got, want) in enumerate(
        zip(receive(pcm), expected[1:])) if got != want]
    with patch.object(loopback, 'DATA', handoff.PIPELINE_SYMBOLS + handoff.DATA_SYMBOLS), \
            patch.object(loopback, 'SYMBOLS', line.RX_SYMBOLS), \
            patch.object(loopback, 'ADC_VISITS', handoff.ADC_VISITS), \
            patch.object(loopback, 'CYCLES', handoff.RX_CYCLES):
        rx, adc, symbols = loopback.capture(mapping, base, pcm, expected)
    states = [f'{value:X}' for value in alternative_states(project(symbols, 46, 93))]
    keys = sorted({int(value, 16) for value in states})
    exact = []
    for labels in itertools.product(range(4), repeat=len(keys) - 1):
        phase = dict(zip(keys, (0, *labels)))
        if decode(states, phase)[33:] == expected[33:]:
            exact.append(phase)
    holdouts = []
    with tempfile.TemporaryDirectory() as temp:
        controller, controller_sha = handoff.compiled_controller(temp)
        for phase in exact:
            family = []
            for selector, delay in (('40', 5), ('60', 18)):
                row = next(c for c in fresh_rx['cases'] if c['selector'] == selector)
                input_row = next(c for c in fresh_tx['cases']
                                 if c['selector'] == selector and c['timing'] == 'silence_start')
                if any(int(value, 16) not in phase for value in row['states']):
                    family.append(dict(selector=selector, missing_states=True))
                    continue
                decoded = decode(row['states'], phase)
                wrong = [i for i, (got, want) in enumerate(
                    zip(decoded[1:], input_row['expected_dibits'][1:])) if got != want]
                readout = line.readout_result(decoded, input_row['expected_dibits'],
                                              line_octets(PAYLOADS[selector], delay),
                                              controller, selector, delay)
                family.append(dict(selector=selector, wrong_indices=wrong,
                                   readout=readout))
            holdouts.append(dict(phase={f'{key:X}': value for key, value in phase.items()},
                                 cases=family))
    report = dict(experiment='controller A4-only phase training then fresh-payload holdout',
                  fixture=dict(standard='V.26 ter segment 2 GPC',
                               offered_a4_bytes=[f'{value:02X}' for value in offered],
                               offset=32, visit=VISIT,
                               training_decisions='indices 33–64 only',
                               line='fixed Q=0.5, bus 0, +6 samples, zero-run gain',
                               controller_probe_sha256=controller_sha),
                  a4=dict(tx_trace_digest=tx['trace_digest'],
                          rx_trace_digest=rx['trace_digest'],
                          raw_sha256=hashlib.sha256(bytes(raw)).hexdigest(),
                          pcm_sha256=hashlib.sha256(bytes(v + 127 for v in pcm)).hexdigest(),
                          adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                          reference_wrong_indices=reference_wrong,
                          states=states, expected_dibits=expected,
                          distinct_states=[f'{value:X}' for value in keys],
                          tested_maps=4 ** (len(keys) - 1),
                          exact_training_maps=len(exact)),
                  holdouts=holdouts,
                  limitations=['The 32-dibit A4 pattern is known from the controller and standard, but a fitting circuit is not identified.',
                               'The training fixture reuses a synthetic A3 interval and photo-compatible line/ADC/serial assumptions.',
                               'No fresh-payload labels were used to fit the A4 phase maps.'],
                  source_sha256={str(p.relative_to(HERE.parents[4])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (Path(__file__), FIXED, FRESH_TX, FRESH_RX,
                                           CONTROLLER_A4,
                                           HERE / 'controller_segment2_pattern.py',
                                           HERE.parent / 'assumed/execute.py')})
    out.write_text(json.dumps(report, indent=2) + '\n')
    print('A4 states', report['a4']['distinct_states'], 'exact maps', len(exact),
          'reference wrong', reference_wrong, flush=True)
    for row in holdouts:
        print('phase', row['phase'], 'holdouts',
              [(c['selector'], len(c.get('wrong_indices', [])),
                c.get('readout', {}).get('recovered_matches_offered'))
               for c in row['cases']], flush=True)
    return report


if __name__ == '__main__':
    run()
