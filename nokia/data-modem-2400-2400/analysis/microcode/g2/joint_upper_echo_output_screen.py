"""Screen reached joint-map state bytes for an echo-sensitive receive readout."""

import hashlib
import json
import random
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from joint_upper_echo_feed_probe import (
    ECHO_DELAY, ECHO_GAIN, JOINED, REMOTE_GAIN, REMOTE_SEED,
    SELECTORS, TXREADY, WINDOW, candidate_tx_codes, delta, rms,
)
from joint_upper_receive_bit_screen import CHANNELS
from joint_upper_sampled_state_dpsk import positions
from joint_upper_source_screen import SELECTED_MASK, candidate
from lower_i_d3f8_full_adc import (
    LONG_CYCLES, LONG_SAMPLES, LONG_VISITS, SAMPLE_START, hold,
    scenario_for_full_byte,
)
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_127_liveness import ROM
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from reference_modem import transmit


def capture(mapping, base, samples):
    values = hold([127 - sample for sample in samples])
    scenario = scenario_for_full_byte(base, values, 'complementary')
    ram = scenario['initial']['ram'][:]
    rows = []
    y8 = y9 = None
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, LONG_CYCLES,
                         mode='integrated', out=temporary, trace_limit=LONG_CYCLES)
        for line in (Path(temporary) / 'trace.jsonl').open():
            record = json.loads(line)
            for address, value in record['registers'].items():
                ram[int(address)] = value
            pc = record['pc']
            if pc == 0x3F8:
                read = record['external_read']
                if not read.get('selected_by_alu') or read['value'] != values[len(rows)]:
                    raise ValueError('ADC input selection changed')
                y8 = record['alu']['y']
            elif pc == 0x3F9:
                y9 = record['alu']['y']
            elif pc == 0x3FA:
                if y8 is None or y9 is None:
                    raise ValueError('incomplete ADC loop visit')
                rows.append(bytes((y8, y9, record['alu']['y'], record['q'], *ram)))
                y8 = y9 = None
    if (not result['clean'] or len(rows) != LONG_VISITS or
            result['read_sequence_visits'].get(0x3F8, 0) != LONG_VISITS):
        raise ValueError('ADC state capture did not sustain')
    return [rows[index] for index in positions('center', 0)], result['trace_digest']


def response(source, control, channel):
    differences = delta([row[channel] for row in source],
                        [row[channel] for row in control])
    return [rms(differences[start:start + WINDOW])
            for start in range(0, LONG_SAMPLES, WINDOW)]


def screen(selector, dac, mapping, base, zero, remote_rows, remote, tx_digest):
    echo = [round(ECHO_GAIN * (dac[index - ECHO_DELAY] - 128))
            if index >= ECHO_DELAY else 0 for index in range(LONG_SAMPLES)]
    mixed = [left + right for left, right in zip(remote, echo)]
    if any(not -127 <= value <= 127 for value in mixed):
        raise ValueError('mixed ADC input clipped')
    echo_rows, echo_digest = capture(mapping, base, echo)
    mixed_rows, mixed_digest = capture(mapping, base, mixed)
    echo_rms = [rms(echo[start:start + WINDOW])
                for start in range(0, LONG_SAMPLES, WINDOW)]
    remote_rms = [rms(remote[start:start + WINDOW])
                  for start in range(0, LONG_SAMPLES, WINDOW)]
    channels = []
    for index, name in enumerate(CHANNELS):
        echo_only = response(echo_rows, zero, index)
        mixed_response = response(mixed_rows, remote_rows, index)
        remote_response = response(remote_rows, zero, index)
        channels.append(dict(
            channel=name,
            echo_only_ratios=[round(a / b, 6) for a, b in zip(echo_only, echo_rms)],
            mixed_echo_ratios=[round(a / b, 6) for a, b in zip(mixed_response, echo_rms)],
            remote_only_ratios=[round(a / b, 6)
                                for a, b in zip(remote_response, remote_rms)],
            distinct_echo_only_codes=len({row[index] for row in echo_rows}),
            distinct_remote_only_codes=len({row[index] for row in remote_rows})))
    responsive = [row for row in channels
                  if min(row['remote_only_ratios']) > 0.1]
    half_attenuated = [row['channel'] for row in responsive
                       if row['mixed_echo_ratios'][-1] <
                       row['mixed_echo_ratios'][0] / 2]
    return dict(selector=selector, candidate_tx_sample_sha256=tx_digest,
                echo_trace_digest=echo_digest, mixed_trace_digest=mixed_digest,
                remote_responsive_channels=[row['channel'] for row in responsive],
                remote_responsive_with_half_echo_attenuation=half_attenuated,
                channels=channels)


def run(out=HERE / 'results/joint-upper-echo-output-screen.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), SELECTED_MASK)
    _, base = fixture()
    txready = json.loads(TXREADY.read_text())
    joined = json.loads(JOINED.read_text())
    rom = ROM.read_bytes()
    generator = random.Random(REMOTE_SEED)
    dibits = [0] * 8 + [generator.randrange(4) for _ in range(16)] + [0] * 8
    pcm = transmit(dibits)[SAMPLE_START:SAMPLE_START + LONG_SAMPLES]
    remote = [round(REMOTE_GAIN * sample) for sample in pcm]
    zero, zero_digest = capture(mapping, base, [0] * LONG_SAMPLES)
    remote_rows, remote_digest = capture(mapping, base, remote)
    cases = []
    for selector in SELECTORS:
        dac, digest = candidate_tx_codes(selector, txready, joined, rom)
        cases.append(screen(selector, dac, mapping, base, zero,
                            remote_rows, remote, digest))
    y8_index = CHANNELS.index('Y3F8')
    prior = json.loads((HERE / 'results/joint-upper-echo-feed-probe.json').read_text())
    for case in cases:
        old = next(row for row in prior['cases'] if row['selector'] == case['selector'])
        y8 = case['channels'][y8_index]
        for key, old_key in (('echo_only_ratios', 'echo_only'),
                             ('mixed_echo_ratios', 'remote_plus_echo')):
            expected = [row['output_change_to_echo_ratio'] for row in old[old_key]]
            if y8[key] != expected:
                raise ValueError(('Y3F8 control changed', case['selector'], key))
    paths = [Path(__file__), HERE / 'joint_upper_echo_feed_probe.py',
             HERE / 'joint_upper_receive_bit_screen.py',
             HERE / 'joint_upper_sampled_state_dpsk.py',
             HERE / 'joint_upper_source_screen.py',
             HERE / 'lower_i_d3f8_full_adc.py',
             HERE / 'photo_controller_path.py', HERE / 'reference_modem.py',
             HERE / 'split_slice_probe.py',
             HERE.parent / 'assumed/execute.py', HERE.parent / 'model.py',
             MAPPINGS['q3'], TXREADY, JOINED, ROM,
             HERE / 'results/joint-upper-echo-feed-probe.json',
             HERE / 'results/joint-upper-source-mask08-mapping.json',
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(
        status='all reached Y/Q/RAM bytes screened for paired echo response under the fixed joint-map ADC fixture',
        fixture=dict(mapping='joint upper-source mask 08',
                     adc='complementary 127-PCM held 188/187 D3F8 visits per sample',
                     output='Y3F8/Y3F9/Y3FA, Q, and RAM 0-15 at center of each held sample',
                     output_difference='signed modulo-256 paired difference',
                     windows='four consecutive 32-sample RMS windows',
                     echo_gain=ECHO_GAIN, echo_delay_samples=ECHO_DELAY,
                     remote_gain=REMOTE_GAIN, remote_seed=REMOTE_SEED,
                     training_enable='not modeled'),
        zero_trace_digest=zero_digest, remote_trace_digest=remote_digest,
        cases=cases,
        limitations=[
            'Low echo response at one byte is not cancellation unless the byte also represents the remote signal and has a justified output route.',
            'Modulo-256 differences on Q/RAM are diagnostic; accumulator wrap and coding could change the interpretation.',
            'This is a short fixed-mode fixture with assumed echo/ADC path and no identified train/freeze control.'],
        source_sha256={str(path.relative_to(HERE.parents[2])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    for case in result['cases']:
        print(case['selector'], case['remote_responsive_channels'],
              case['remote_responsive_with_half_echo_attenuation'])
