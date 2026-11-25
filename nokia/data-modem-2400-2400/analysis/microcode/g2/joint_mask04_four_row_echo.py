"""Feed exact mask-04 transmitter samples back through its four-row ADC loop."""

import copy
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
from joint_four_row_retention_tx import (
    DATA_STEP, SAMPLE_COUNT, SAMPLE_DIVISOR, SEGMENT_SYMBOLS,
    SILENCE_SYMBOLS, TONE_STEP, TONE_SYMBOLS, TXREADY,
    VISITS_PER_SYMBOL, segment2_from_txd, scenario_inputs,
)
from joint_upper_source_screen import candidate
from lower_i_d3f8_full_adc import LONG_SAMPLES, SAMPLE_START
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_dac_bus_permutations import mapped_codes
from photo_i0_hold_screen import hold_candidate
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_four_row_condition_screen import configured
from reference_modem import transmit
from split_slice_probe import split_scenario

SELECTORS = ('40', '60')
ECHO_GAIN = 0.5
REMOTE_GAIN = 0.25
ECHO_DELAY = 3
WINDOW = 32
CHANNELS = ('Y3F8', 'Y3F9', 'Y3FA', 'Y3ED', 'Q') + tuple(
    f'R{index}' for index in range(16))
JOINT = HERE / 'results/joint-four-row-retention-tx.json'


def rms(values):
    return math.sqrt(sum(value * value for value in values) / len(values))


def delta(left, right):
    return [((a - b + 128) & 255) - 128 for a, b in zip(left, right)]


def tx_codes(mapping, base, controller, expected):
    segment2 = segment2_from_txd(controller)
    symbols = [3] * SEGMENT_SYMBOLS + segment2
    inputs = ([TONE_STEP] * (TONE_SYMBOLS * VISITS_PER_SYMBOL) +
              [DATA_STEP] * (SILENCE_SYMBOLS * VISITS_PER_SYMBOL) +
              scenario_inputs(symbols))
    scenario = split_scenario(hold_candidate(base))
    scenario['name'] += '; exact mask-04 own-echo source'
    scenario['inputs']['register_address_bit_overrides']['a_high'] = copy.deepcopy(
        scenario['inputs']['register_address_bit_overrides']['a'])
    for policy in scenario['inputs']['register_address_bit_overrides']['a_high'].values():
        policy['evidence'] += '; untraced high-slice A pin diagnostic level'
    scenario['initial']['q'] = 0
    scenario['io']['read']['pc_sequences'][str(0x127)] = inputs
    scenario['io']['read']['pc_sequences'][str(0x12C)] = [0xEA]
    scenario['io']['read']['address']['bank_by_pc'] = {
        str(0x129): 256, str(0x12E): 256}
    cycles = (len(inputs) + 63) * 4
    samples = []
    visits = 0
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, cycles, mode='integrated',
                         out=temporary, trace_limit=cycles)
        for line in (Path(temporary) / 'trace.jsonl').open():
            if '"pc": 297' not in line:
                continue
            row = json.loads(line)
            if visits % SAMPLE_DIVISOR == 0 and len(samples) < SAMPLE_COUNT:
                samples.append(row['alu']['y'])
            visits += 1
    digest = hashlib.sha256(bytes(samples)).hexdigest()
    if (not result['clean'] or len(samples) != SAMPLE_COUNT or
            digest != expected['raw_y_sample_sha256'] or
            result['trace_digest'] != expected['trace_digest']):
        raise ValueError('exact mask-04 TX replay changed')
    bus = expected['bus_cases'][0]['input_bit_to_dac_code_bit']
    dac = mapped_codes(samples, bus)
    start = (TONE_SYMBOLS + SILENCE_SYMBOLS + SEGMENT_SYMBOLS) * 8
    return dac[start:start + LONG_SAMPLES], dict(
        raw_sha256=digest, full_trace_digest=result['trace_digest'],
        bus=bus, dac_window_sha256=hashlib.sha256(
            bytes(dac[start:start + LONG_SAMPLES])).hexdigest(),
        first_16_dac_codes=dac[start:start + 16])


def adc_values(samples):
    if len(samples) != LONG_SAMPLES or any(not -127 <= x <= 127 for x in samples):
        raise ValueError('ADC input outside reference range')
    values = []
    centers = []
    for index, sample in enumerate(samples):
        hold = 47 if index % 8 < 7 else 46
        centers.append(len(values) + hold // 2)
        values.extend([127 - sample] * hold)
    if len(values) != 6000:
        raise ValueError('four-row ADC schedule changed')
    return values, centers


def rx_capture(mapping, base, samples):
    values, centers = adc_values(samples)
    scenario = configured(base, values, 'previous', 'overflow', 1)
    cycles = 32 * len(values) + 47
    ram = scenario['initial']['ram'][:]
    y8 = y9 = ya = ye = None
    rows = []
    pc_digest = hashlib.sha256()
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, cycles, mode='integrated',
                         out=temporary, trace_limit=cycles)
        if (not result['clean'] or result['completed_cycles'] != cycles or
                result['address_counts'].get(0x3FE, 0) != len(values) or
                result['read_sequence_visits'].get(0x3F8, 0) != len(values)):
            raise ValueError('mask-04 echo receive trace did not sustain')
        for line in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(line)
            pc = row['pc']
            pc_digest.update(pc.to_bytes(2, 'little'))
            if pc == 0x3F8:
                y8 = row['alu']['y']
                if (not row['external_read'].get('selected_by_alu') or
                        row['external_read']['value'] != values[len(rows)]):
                    raise ValueError('ADC selection changed')
            elif pc == 0x3F9:
                y9 = row['alu']['y']
            elif pc == 0x3FA:
                ya = row['alu']['y']
            elif pc == 0x3ED:
                ye = row['alu']['y']
            for address, value in row['registers'].items():
                ram[int(address)] = value
            if pc == 0x3FE:
                if None in (y8, y9, ya, ye):
                    raise ValueError('incomplete four-row output capture')
                rows.append(bytes((y8, y9, ya, ye, row['q'], *ram)))
                y8 = y9 = ya = ye = None
    if len(rows) != len(values):
        raise ValueError('fourth-row output count changed')
    return [rows[index] for index in centers], dict(
        trace_digest=result['trace_digest'], pc_digest=pc_digest.hexdigest(),
        row_sha256=hashlib.sha256(b''.join(rows)).hexdigest())


def response(source, control, channel):
    values = delta([row[channel] for row in source],
                   [row[channel] for row in control])
    return [rms(values[start:start + WINDOW])
            for start in range(0, LONG_SAMPLES, WINDOW)]


def run(out=HERE / 'results/joint-mask04-four-row-echo.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    controllers = json.loads(TXREADY.read_text())['cases']
    expected_tx = json.loads(JOINT.read_text())['transmit_mask04']
    generator = random.Random(0x3558)
    dibits = [0] * 8 + [generator.randrange(4) for _ in range(16)] + [0] * 8
    remote_pcm = transmit(dibits)[SAMPLE_START:SAMPLE_START + LONG_SAMPLES]
    remote = [round(REMOTE_GAIN * sample) for sample in remote_pcm]
    zero_output, zero_trace = rx_capture(mapping, base, [0] * LONG_SAMPLES)
    remote_output, remote_trace = rx_capture(mapping, base, remote)
    print('captured zero and remote controls', flush=True)
    remote_rms = [rms(remote[start:start + WINDOW])
                  for start in range(0, LONG_SAMPLES, WINDOW)]
    cases = []
    for selector in SELECTORS:
        controller = next(row for row in controllers
                          if row['selector'] == selector)
        expected = next(row for row in expected_tx
                        if row['selector'] == selector)
        dac, transmit_case = tx_codes(mapping, base, controller, expected)
        print('captured exact mask-04 TX window', selector, flush=True)
        echo = [round(ECHO_GAIN * (dac[index - ECHO_DELAY] - 128))
                if index >= ECHO_DELAY else 0 for index in range(LONG_SAMPLES)]
        mixed = [a + b for a, b in zip(remote, echo)]
        echo_output, echo_trace = rx_capture(mapping, base, echo)
        mixed_output, mixed_trace = rx_capture(mapping, base, mixed)
        print('captured echo and mixed controls', selector, flush=True)
        traces = dict(zero=zero_trace, remote=remote_trace,
                      echo=echo_trace, mixed=mixed_trace)
        if len({row['pc_digest'] for row in traces.values()}) != 1:
            raise ValueError(('ADC controls changed the PC path', selector))
        echo_rms = [rms(echo[start:start + WINDOW])
                    for start in range(0, LONG_SAMPLES, WINDOW)]
        channels = []
        for index, name in enumerate(CHANNELS):
            echo_only = response(echo_output, zero_output, index)
            mixed_echo = response(mixed_output, remote_output, index)
            remote_only = response(remote_output, zero_output, index)
            channels.append(dict(
                name=name,
                echo_only_ratios=[round(a / b, 6)
                                  for a, b in zip(echo_only, echo_rms)],
                mixed_echo_ratios=[round(a / b, 6)
                                   for a, b in zip(mixed_echo, echo_rms)],
                remote_only_ratios=[round(a / b, 6)
                                    for a, b in zip(remote_only, remote_rms)]))
        responsive = [row for row in channels
                      if min(row['remote_only_ratios']) > 0.1]
        half_attenuated = [row['name'] for row in responsive
                           if row['mixed_echo_ratios'][-1] <
                           row['mixed_echo_ratios'][0] / 2]
        cases.append(dict(selector=selector, transmit=transmit_case,
                          inputs=dict(echo_rms=echo_rms, remote_rms=remote_rms,
                                      first_16_echo_samples=echo[:16],
                                      first_16_remote_samples=remote[:16]),
                          traces=traces, channels=channels,
                          remote_responsive_channels=[row['name']
                                                      for row in responsive],
                          remote_responsive_with_half_echo_attenuation=half_attenuated))
    paths = [Path(__file__), HERE / 'joint_four_row_retention_tx.py',
             HERE / 'joint_upper_source_screen.py',
             HERE / 'receiver_four_row_condition_screen.py',
             HERE / 'reference_modem.py', HERE.parent / 'assumed/execute.py',
             HERE.parent / 'model.py', MAPPINGS['q3'], TXREADY, JOINT,
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(
        experiment='exact mask-04 own-TX echo in complete four-row receive loop',
        fixture=dict(selectors=SELECTORS, mapping='joint upper-source mask 04',
                     tx='controller-driven A1/A2/A3/A4 exact real-PROM trace',
                     dac='first photo-compatible candidate bus, raw codes',
                     echo_gain=ECHO_GAIN, echo_delay_samples=ECHO_DELAY,
                     remote_gain=REMOTE_GAIN, remote_seed=0x3558,
                     adc='complementary 127-PCM held 47/46 visits per sample',
                     receive='four-row [0,1,2,3], previous inverted overflow',
                     output='Y3F8/Y3F9/Y3FA/Y3ED/Q/R0-R15 after 3FE, center-sampled',
                     windows='four consecutive 32-sample RMS windows',
                     training_enable='not modeled'),
        cases=cases,
        limitations=[
            'DAC bus, analog echo coupling, ADC route, clock and field map remain photo-compatible hypotheses.',
            'This 128-sample fixed-mode window has no identified train/freeze control or line residual.',
            'Signed modulo-256 byte differences are diagnostic, not proof of echo cancellation.'],
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
