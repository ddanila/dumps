"""Replay fixed mask-04 dibit logic with rotated reference carrier phases."""

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
from joint_upper_source_screen import candidate
from lower_i_d3f8_full_adc import LONG_SAMPLES, SAMPLE_START
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_four_row_condition_screen import configured
from receiver_mask04_3ed_prom_latch import ADC_VISITS, CYCLES, gate_high
from receiver_mask04_phase47_logic import score
from receiver_mask04_rowpair_phase_code import row_pairs
from reference_modem import (CARRIER_HZ, SAMPLE_RATE, phase_positions,
                             raised_cosine, receive, transmit)

PHASE_DEGREES = (45, 90, 135, 180)
SEEDS = (0x5A17, 0x76A5)
FIXED_PHASE = 47
VISITS_PER_SYMBOL = 375


def rotated_transmit(dibits, degrees):
    rotation = math.radians(degrees)
    phases = phase_positions(dibits)
    symbols = [complex(math.cos(math.pi * phase / 8),
                       math.sin(math.pi * phase / 8)) for phase in phases]
    pcm = []
    for n in range(len(symbols) * 8):
        center = n // 8
        envelope = sum(symbols[k] * raised_cosine((n - 8 * k) / 8)
                       for k in range(max(0, center - 4),
                                      min(len(symbols), center + 5)))
        angle = 2 * math.pi * CARRIER_HZ * n / SAMPLE_RATE + rotation
        carrier = complex(math.cos(angle), math.sin(angle))
        pcm.append(max(-127, min(127, round(127 * (envelope * carrier).real))))
    return pcm


def capture_rotated(mapping, base, middle, degrees):
    dibits = [0] * 8 + middle + [0] * 8
    pcm = rotated_transmit(dibits, degrees)
    if receive(pcm) != dibits[1:]:
        raise ValueError('independent receiver lost phase-rotated reference bits')
    samples = [127 - value for value in
               pcm[SAMPLE_START:SAMPLE_START + LONG_SAMPLES]]
    values = [sample for index, sample in enumerate(samples)
              for _ in range(47 if index % 8 < 7 else 46)]
    if len(values) != ADC_VISITS:
        raise ValueError('ADC schedule changed')
    scenario = configured(base, values, 'previous', 'overflow', 1)
    captured = []
    previous_high = False
    previous_y = None
    high_count = 0
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, CYCLES, mode='integrated',
                         out=temporary, trace_limit=CYCLES)
        if (not result['clean'] or result['completed_cycles'] != CYCLES or
                result['address_counts'].get(0x3ED, 0) != 4 * ADC_VISITS or
                result['read_sequence_visits'].get(0x3F8, 0) != ADC_VISITS):
            raise ValueError('rotated-input PROM path stopped')
        for line in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(line)
            high = gate_high(row)
            if high:
                if row['pc'] != 0x3ED:
                    raise ValueError('PROM latch gate left 3ED')
                high_count += 1
            if previous_high and not high:
                captured.append(previous_y)
            previous_high, previous_y = high, row['alu']['y']
    if high_count != 4 * ADC_VISITS or len(captured) != high_count:
        raise ValueError('rotated-input latch edge count changed')
    return captured, dict(trace_digest=result['trace_digest'],
                          captured_sha256=hashlib.sha256(bytes(captured)).hexdigest(),
                          adc_stream_sha256=hashlib.sha256(bytes(values)).hexdigest())


def run(out=HERE / 'results/receiver-mask04-carrier-phase-screen.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    cases = []
    for seed in SEEDS:
        generator = random.Random(seed)
        middle = [generator.randrange(4) for _ in range(16)]
        dibits = [0] * 8 + middle + [0] * 8
        if rotated_transmit(dibits, 0) != transmit(dibits):
            raise ValueError('zero-phase reference implementation differs')
    for degrees in PHASE_DEGREES:
        for seed in SEEDS:
            generator = random.Random(seed)
            middle = [generator.randrange(4) for _ in range(16)]
            captured, trace = capture_rotated(mapping, base, middle, degrees)
            pairs = row_pairs(captured)
            errors = []
            for phase in range(VISITS_PER_SYMBOL):
                symbol_pairs = [pairs[VISITS_PER_SYMBOL * symbol + phase]
                                for symbol in range(16)]
                errors.append(score(symbol_pairs, middle)['errors'])
            cases.append(dict(carrier_phase_degrees=degrees, seed=seed,
                              middle_dibits=middle,
                              fixed_phase_errors=errors[FIXED_PHASE],
                              minimum_errors=min(errors),
                              zero_error_capture_phases=[phase for phase, count
                                                         in enumerate(errors)
                                                         if count == 0],
                              errors_by_capture_phase=errors,
                              **trace))
            print('captured', degrees, seed, 'phase47',
                  errors[FIXED_PHASE], 'min', min(errors), flush=True)
    paths = (Path(__file__), HERE / 'receiver_mask04_phase47_logic.py',
             HERE / 'receiver_mask04_rowpair_phase_code.py',
             HERE / 'receiver_mask04_3ed_prom_latch.py',
             HERE / 'receiver_four_row_condition_screen.py',
             HERE / 'reference_modem.py', HERE.parent / 'assumed/execute.py',
             MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='rotated-carrier stress of fixed phase-47 Boolean receiver readout',
                  fixture=dict(mapping='joint upper-source mask 04',
                               carrier_phase_degrees=PHASE_DEGREES,
                               seeds=SEEDS,
                               fixed_capture_phase=FIXED_PHASE,
                               compared_capture_phases=VISITS_PER_SYMBOL,
                               adc='complementary reference PCM, 47/46 visit holds',
                               reference_receiver='independent known-carrier matched filter decodes every rotated stream'),
                  cases=cases,
                  limitations=['The carrier rotation changes analog PCM, not the controller dibit sequence.',
                               'The Boolean decoder, capture strobe, symbol timing and USART path remain external hypotheses.',
                               'The reference receiver is a diagnostic, not a measured Nokia receive chain.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
