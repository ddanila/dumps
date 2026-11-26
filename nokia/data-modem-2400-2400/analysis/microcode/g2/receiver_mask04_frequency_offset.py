"""Stress the frozen two-visit receiver with carrier-frequency offsets."""

import hashlib
import json
import math
import random
import sys
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
import receiver_mask04_multivisit_capture as capture_module
from receiver_mask04_dual_feature_consensus import consensus, decisions, metrics
from receiver_mask04_dual_zero_handoff import frozen_tables
from receiver_mask04_feature_choice import alternative_states
from receiver_mask04_four_bit_transition import states_from_symbols
from reference_modem import (CARRIER_HZ, SAMPLE_RATE, phase_positions,
                             raised_cosine)

SEED = 0xA9D4
DEGREES = (75, 165)
OFFSETS_HZ = (-7, 0, 7)


def offset_transmit(dibits, degrees, offset_hz):
    phases = phase_positions(dibits)
    symbols = [complex(math.cos(math.pi * phase / 8),
                       math.sin(math.pi * phase / 8)) for phase in phases]
    rotation = math.radians(degrees)
    pcm = []
    for sample in range(len(symbols) * 8):
        center = sample // 8
        envelope = sum(symbols[index] * raised_cosine((sample - 8 * index) / 8)
                       for index in range(max(0, center - 4),
                                          min(len(symbols), center + 5)))
        angle = (2 * math.pi * (CARRIER_HZ + offset_hz) * sample /
                 SAMPLE_RATE + rotation)
        carrier = complex(math.cos(angle), math.sin(angle))
        pcm.append(max(-127, min(127, round(127 * (envelope * carrier).real))))
    return pcm


def run(out=HERE / 'results/receiver-mask04-frequency-offset.json'):
    generator = random.Random(SEED)
    middle = [generator.randrange(4) for _ in range(capture_module.DATA_SYMBOLS)]
    primary, alternative = frozen_tables()
    mapping = capture_module.candidate(
        capture_module.mapping_with_upper_source(0, '17.6'),
        capture_module.mapped(capture_module.MAPPINGS['q3']), 4)
    _, base = capture_module.fixture()
    cases = []
    for offset_hz in OFFSETS_HZ:
        for degrees in DEGREES:
            dibits = [3] * capture_module.PREAMBLE_SYMBOLS + middle + [0] * 8
            if (offset_hz == 0 and
                    offset_transmit(dibits, degrees, 0) !=
                    capture_module.rotated_transmit(dibits, degrees)):
                raise ValueError('zero-offset transmitter differs from reference')
            with patch.object(capture_module, 'rotated_transmit',
                              lambda values, angle: offset_transmit(
                                  values, angle, offset_hz)):
                trace = capture_module.capture(mapping, base, degrees, middle)
            symbols = trace['symbols']
            expected = [symbol['dibit'] for symbol in symbols]
            p = decisions(states_from_symbols(symbols), primary)
            a = decisions(alternative_states(symbols), alternative)
            both = consensus(p, a)
            conflicts = sum(x is not None and y is not None and x != y
                            for x, y in zip(p[1:], a[1:]))
            row = dict(offset_hz=offset_hz, degrees=degrees,
                       trace_digest=trace['trace_digest'],
                       adc_stream_sha256=trace['adc_stream_sha256'],
                       primary=metrics(p, expected),
                       alternative=metrics(a, expected),
                       consensus=metrics(both, expected),
                       conflicts=conflicts)
            cases.append(row)
            print(offset_hz, degrees, row['primary'], row['alternative'],
                  row['consensus'], conflicts, flush=True)
    summary = {str(offset): dict(
        checks=sum(row['consensus']['checks'] for row in cases
                   if row['offset_hz'] == offset),
        errors=sum(row['consensus']['errors'] for row in cases
                   if row['offset_hz'] == offset),
        unknown=sum(row['consensus']['unknown'] for row in cases
                    if row['offset_hz'] == offset),
        conflicts=sum(row['conflicts'] for row in cases
                      if row['offset_hz'] == offset))
               for offset in OFFSETS_HZ}
    paths = [Path(__file__),
             HERE / 'receiver_mask04_multivisit_capture.py',
             HERE / 'receiver_mask04_dual_feature_consensus.py',
             HERE / 'receiver_mask04_dual_zero_handoff.py',
             HERE / 'receiver_mask04_feature_choice.py',
             HERE / 'receiver_mask04_four_bit_transition.py',
             HERE / 'receiver_mask04_cubic_transition.py',
             HERE / 'receiver_mask04_carrier_phase_screen.py',
             HERE / 'reference_modem.py',
             HERE.parent / 'assumed/execute.py',
             capture_module.MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(experiment='frozen two-visit receive readout under carrier frequency offsets',
                  fixture=dict(seed=SEED, data_dibits=middle,
                               degrees=DEGREES, offsets_hz=OFFSETS_HZ,
                               symbols=48, adc_visits=18000,
                               mapping='joint upper-source mask 04',
                               adc='complementary PCM, 47/46 visits per sample'),
                  cases=cases, summary=summary,
                  limitations=[
                      'The reference receiver uses a fixed 1800 Hz carrier and decodes every tested PCM input before the PROM replay.',
                      'The output logic was frozen from zero-offset development traces; no offset trace refits either table.',
                      'Two static initial phases, one data seed and 48 symbols do not establish acquisition, arbitrary offset tolerance, noise tolerance or physical routing.',
                      'ADC input, symbol-relative capture clocks, logic and USART paths remain explicit board hypotheses.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    print(run()['summary'])
