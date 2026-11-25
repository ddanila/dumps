"""Feed candidate own-TX echo into the same-map D3F8 ADC path."""

import hashlib
import json
import math
import random
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from joint_upper_sampled_state_dpsk import positions
from joint_upper_source_screen import SELECTED_MASK, candidate
from lower_i_d3f8_full_adc import LONG_CYCLES, LONG_SAMPLES, LONG_VISITS, SAMPLE_START, hold, scenario_for_full_byte
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_127_liveness import ROM
from photo_controller_path import fixture
from photo_dac_bus_permutations import SELECTED, mapped_codes
from photo_joint_tone_training_data import (
    DATA_STEP, SEGMENT_SYMBOLS, SILENCE_SYMBOLS, TONE_STEP, TONE_SYMBOLS,
    TXREADY, raw_codes, segment2_from_txd,
)
from photo_main_dibit_pulse import VISITS_PER_SYMBOL, scenario_inputs
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from reference_modem import transmit

JOINED = HERE / 'results/photo-joint-tone-training-data.json'
SELECTORS = ('40', '60')
REMOTE_SEED = 0x3558
ECHO_GAIN = 0.5
REMOTE_GAIN = 0.25
ECHO_DELAY = 3
WINDOW = 32


def rms(values):
    return math.sqrt(sum(value * value for value in values) / len(values))


def candidate_tx_codes(selector, txready, joined, rom):
    case = next(row for row in txready['cases'] if row['selector'] == selector)
    target = [3] * SEGMENT_SYMBOLS + segment2_from_txd(case)
    inputs = ([TONE_STEP] * (TONE_SYMBOLS * VISITS_PER_SYMBOL) +
              [DATA_STEP] * (SILENCE_SYMBOLS * VISITS_PER_SYMBOL) +
              scenario_inputs(target))
    raw, _ = raw_codes(rom, inputs)
    dac = mapped_codes(raw, SELECTED)
    prior = next(row for row in joined['cases'] if row['selector'] == selector)
    digest = hashlib.sha256(bytes(dac)).hexdigest()
    if digest != prior['selected_bus_sample_sha256']:
        raise ValueError(('candidate TX codes differ from executed PROM trace', selector))
    start = (TONE_SYMBOLS + SILENCE_SYMBOLS + SEGMENT_SYMBOLS) * 8
    return dac[start:start + LONG_SAMPLES], digest


def capture(mapping, base, samples):
    if len(samples) != LONG_SAMPLES or any(not -127 <= value <= 127
                                           for value in samples):
        raise ValueError('ADC sample window out of range')
    scenario = scenario_for_full_byte(
        base, hold([127 - sample for sample in samples]), 'complementary')
    y = []
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, LONG_CYCLES,
                         mode='integrated', out=temporary, trace_limit=LONG_CYCLES)
        for line in (Path(temporary) / 'trace.jsonl').open():
            if '"pc": 1016' in line:
                row = json.loads(line)
                if not row['external_read'].get('selected_by_alu'):
                    raise ValueError('D3F8 ADC byte not selected')
                y.append(row['alu']['y'])
    if (not result['clean'] or result['address_counts'].get(0x3F8, 0) != LONG_VISITS or
            result['read_sequence_visits'].get(0x3F8, 0) != LONG_VISITS or
            len(y) != LONG_VISITS):
        raise ValueError('echo-feed receive trace did not sustain')
    return [y[visit] for visit in positions('center', 0)], result['trace_digest']


def delta(a, b):
    return [((left - right + 128) & 255) - 128
            for left, right in zip(a, b)]


def windows(echo, output_delta):
    rows = []
    for start in range(0, LONG_SAMPLES, WINDOW):
        expected = rms(echo[start:start + WINDOW])
        observed = rms(output_delta[start:start + WINDOW])
        rows.append(dict(sample_start=start, echo_rms=round(expected, 6),
                         output_change_rms=round(observed, 6),
                         output_change_to_echo_ratio=round(observed / expected, 6)))
    return rows


def run(out=HERE / 'results/joint-upper-echo-feed-probe.json'):
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
    zero_y, zero_digest = capture(mapping, base, [0] * LONG_SAMPLES)
    remote_y, remote_digest = capture(mapping, base, remote)
    cases = []
    for selector in SELECTORS:
        dac, tx_digest = candidate_tx_codes(selector, txready, joined, rom)
        echo = [round(ECHO_GAIN * (dac[index - ECHO_DELAY] - 128))
                if index >= ECHO_DELAY else 0
                for index in range(LONG_SAMPLES)]
        mixed = [left + right for left, right in zip(remote, echo)]
        if any(not -127 <= value <= 127 for value in mixed):
            raise ValueError('remote+echo ADC input clipped')
        echo_y, echo_digest = capture(mapping, base, echo)
        mixed_y, mixed_digest = capture(mapping, base, mixed)
        cases.append(dict(selector=selector, candidate_tx_sample_sha256=tx_digest,
                          first_16_echo_samples=echo[:16],
                          echo_only=windows(echo, delta(echo_y, zero_y)),
                          remote_plus_echo=windows(echo, delta(mixed_y, remote_y)),
                          echo_trace_digest=echo_digest,
                          mixed_trace_digest=mixed_digest))

    paths = [Path(__file__), HERE / 'joint_upper_source_screen.py',
             HERE / 'joint_upper_sampled_state_dpsk.py',
             HERE / 'photo_joint_tone_training_data.py',
             HERE / 'photo_main_dibit_pulse.py',
             HERE / 'photo_dac_bus_permutations.py',
             HERE / 'lower_i_d3f8_full_adc.py',
             HERE / 'photo_controller_path.py',
             HERE / 'reference_modem.py',
             HERE / 'split_slice_probe.py',
             HERE.parent / 'assumed/execute.py', HERE.parent / 'model.py',
             MAPPINGS['q3'], TXREADY, JOINED, ROM,
             HERE / 'results/joint-upper-source-mask08-mapping.json',
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(status='conditional own-transmit echo feed shows no strong short-window attenuation at Y3F8 under fixed receive fixture',
                  fixture=dict(mapping='joint upper-source mask 08',
                               tx='A4 first 16 symbols from controller-derived full real-PROM TX replay; selected candidate DAC bus',
                               echo_gain=ECHO_GAIN, echo_delay_samples=ECHO_DELAY,
                               remote='independent reference DPSK PCM',
                               remote_seed=REMOTE_SEED, remote_gain=REMOTE_GAIN,
                               adc='complementary 127-PCM held 188/187 visits per sample at D3F8',
                               output='Y3F8 at center of each held ADC sample',
                               compared_output='modulo-256 signed difference from zero-input or remote-only paired control',
                               training_enable='not modeled; no identified controller-to-DSC echo-train input'),
                  zero_trace_digest=zero_digest,
                  remote_trace_digest=remote_digest,
                  cases=cases,
                  limitations=[
                      'This 128-sample fixed-fixture test cannot establish or exclude an echo canceller that requires another mode, output site or longer training interval.',
                      'The DAC byte order, analog echo path, gain/delay, ADC bus, clock and high-slice wiring remain hypotheses.',
                      'An output difference at Y3F8 is not a verified line residual or USART receive bit.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    print([(case['selector'],
            [row['output_change_to_echo_ratio'] for row in case['echo_only']],
            [row['output_change_to_echo_ratio'] for row in case['remote_plus_echo']])
           for case in result['cases']])
