"""Test surviving ADC-bit D3F8 decoders across distinct dibit sequences."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from lower_i_d3f8_adc_decoder_screen import (
    CYCLES, EXPECTED_INPUT_VISITS, SAMPLE_START, SAMPLES,
    input_stream, scenario_for,
)
from lower_i_prom_data_route import mapping_for
from photo_controller_path import fixture
from reference_modem import receive, transmit

SCREEN = HERE / 'results/lower-i-d3f8-adc-decoder-screen.json'
PATTERNS = ((0, 1, 3, 2), (0, 2, 3, 1), (0, 0, 0, 0),
            (3, 3, 3, 3), (1, 2, 1, 2), (2, 3, 0, 1))
LONG_SAMPLES = 128
BIT0_DECODER = '03/05:bit0:normal'


def run(out=HERE / 'results/lower-i-d3f8-adc-cross-symbols.json'):
    prior = json.loads(SCREEN.read_text())
    decoders = [row for row in prior['cases'] if row['consumed_full_window']]
    if len(decoders) != 8:
        raise ValueError('prior decoder survivor set changed')
    mapping = mapping_for('!10.6', '11.2')
    _, base = fixture()
    cases = []
    for pattern in PATTERNS:
        dibits = [0] * 8 + list(pattern) * 4 + [0] * 8
        pcm = transmit(dibits)
        if receive(pcm) != dibits[1:]:
            raise ValueError(('reference pattern failed', pattern))
        adc = [127 - sample for sample in pcm[SAMPLE_START:
                                              SAMPLE_START + SAMPLES]]
        if len(adc) != SAMPLES:
            raise ValueError('ADC sample window changed')
        for decoder in decoders:
            bit = decoder['adc_bit']
            low = int(decoder['low_code'], 16)
            high = int(decoder['high_code'], 16)
            invert = int(decoder['invert'])
            values = input_stream(adc, low, high, bit, invert)
            result = execute(mapping, scenario_for(base, values), CYCLES,
                             mode='integrated', trace_limit=0)
            visits = result['address_counts'].get(0x3F8, 0)
            cases.append(dict(pattern=list(pattern),
                              decoder=f'{low:02X}/{high:02X}:bit{bit}:' +
                                      ('inverted' if invert else 'normal'),
                              adc_bit_transitions=sum(
                                  ((a >> bit) & 1) != ((b >> bit) & 1)
                                  for a, b in zip(adc, adc[1:])),
                              reached_input_visits=visits,
                              consumed_full_window=visits >= EXPECTED_INPUT_VISITS,
                              loop_1e9_visits=result['address_counts'].get(0x1E9, 0),
                              loop_1ea_visits=result['address_counts'].get(0x1EA, 0),
                              final_pc=f"{result['final_state']['pc']:03X}",
                              trace_digest=result['trace_digest']))
    by_decoder = {row['decoder']: [case['pattern'] for case in cases
                                  if case['decoder'] == row['decoder'] and
                                  case['consumed_full_window']]
                  for row in cases}
    by_pattern = {''.join(map(str, pattern)): sum(
        row['consumed_full_window'] for row in cases
        if row['pattern'] == list(pattern)) for pattern in PATTERNS}
    if len(cases) != len(PATTERNS) * len(decoders):
        raise ValueError('cross-symbol screen coverage changed')
    long_cases = []
    for pattern in by_decoder[BIT0_DECODER]:
        dibits = [0] * 8 + pattern * 16 + [0] * 8
        pcm = transmit(dibits)
        if receive(pcm) != dibits[1:]:
            raise ValueError(('extended reference pattern failed', pattern))
        adc = [127 - sample for sample in pcm[SAMPLE_START:
                                              SAMPLE_START + LONG_SAMPLES]]
        if len(adc) != LONG_SAMPLES:
            raise ValueError('extended ADC window changed')
        values = []
        for sample_index, sample in enumerate(adc):
            values.extend([5 if sample & 1 else 3] *
                          (188 if sample_index % 2 == 0 else 187))
        expected_visits = LONG_SAMPLES * 375 // 2
        if len(values) != expected_visits:
            raise ValueError('extended hold schedule changed')
        result = execute(mapping, scenario_for(base, values),
                         8 * expected_visits + 47,
                         mode='integrated', trace_limit=0)
        long_cases.append(dict(pattern=pattern,
                               expected_input_visits=expected_visits,
                               reached_input_visits=result['address_counts'].get(0x3F8, 0),
                               consumed_full_window=(result['address_counts'].get(0x3F8, 0)
                                                     >= expected_visits),
                               loop_1e9_visits=result['address_counts'].get(0x1E9, 0),
                               loop_1ea_visits=result['address_counts'].get(0x1EA, 0),
                               final_pc=f"{result['final_state']['pc']:03X}",
                               trace_digest=result['trace_digest']))
    paths = [Path(__file__), SCREEN, HERE / 'lower_i_d3f8_adc_decoder_screen.py',
             HERE / 'reference_modem.py', HERE / 'lower_i_prom_data_route.py',
             HERE / 'photo_controller_path.py', HERE / 'split_slice_probe.py',
             HERE.parent / 'assumed/execute.py', HERE.parent / 'model.py',
             HERE.parents[2] / 'am27s31dc-prom/nokia-modem-am27s31dc.bin']
    report = dict(status='cross-symbol robustness screen for eight candidate ADC-bit D3F8 decoders',
                  fixture=dict(mapping='I7/A0=!10.6, I0/A1=11.2, lower I6=11.0',
                               initial_q=5, initial_ram=[0] * 16,
                               dibit_frame='8 zero symbols + repeated four-dibit pattern four times + 8 zero symbols',
                               sample_window=[SAMPLE_START, SAMPLE_START + SAMPLES],
                               adc_code='127 - signed PCM sample',
                               input_hold_visits=[188, 187],
                               expected_input_visits=EXPECTED_INPUT_VISITS,
                               cycles_per_run=CYCLES),
                  summary=dict(cases=len(cases),
                               full_window_by_pattern=by_pattern,
                               full_window_patterns_by_decoder=by_decoder,
                               extended_bit0_cases=len(long_cases),
                               extended_bit0_full_window_cases=sum(
                                   row['consumed_full_window'] for row in long_cases)),
                  cases=cases, extended_bit0_cases=long_cases,
                  limitations=[
                      'Only eight decoders that survived one earlier waveform are tested, not all possible input mappings.',
                      'Each pattern first uses one 32-sample window; four bit-0 survivors also use a 128-sample extension. All use one Q/RAM seed and one candidate clock/mapping.',
                      'ADC coding, D0 bias, the one-bit decoder and physical path are untraced assumptions.',
                      'A full visit window is not a decoded bit or USART receive route; C3 remains open.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path,
                        default=HERE / 'results/lower-i-d3f8-adc-cross-symbols.json')
    args = parser.parse_args()
    print(run(args.out)['summary']['full_window_by_pattern'])
