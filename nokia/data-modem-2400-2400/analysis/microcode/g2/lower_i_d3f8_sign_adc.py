"""Test sustained, input-sensitive D3F8 ADC runs with inverted-sign select 0."""

import argparse
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from lower_i_d3f8_adc_cross_symbols import PATTERNS
from lower_i_d3f8_adc_decoder_screen import input_stream, scenario_for
from lower_i_d3f8_input import run_trace
from lower_i_prom_data_route import mapping_for
from photo_controller_path import fixture
from reference_modem import receive, transmit

SAMPLE_START = 64
LONG_SAMPLES = 128
LONG_VISITS = 24000
SHORT_SAMPLES = 32
SHORT_VISITS = 6000
LONG_CYCLES = 8 * LONG_VISITS + 47
SHORT_CYCLES = 8 * SHORT_VISITS + 47
DETAIL_PATTERNS = ((0, 1, 3, 2), (0, 0, 0, 0))


def condition_scenario(base, timing):
    scenario = dict(base)
    scenario['condition'] = dict(base['condition'])
    scenario['condition']['sources'] = list(base['condition']['sources'])
    scenario['condition']['polarity'] = list(base['condition']['polarity'])
    scenario['condition']['sources'][0] = 'sign'
    scenario['condition']['polarity'][0] = 1
    scenario['condition']['flag_timing'] = timing
    scenario['condition']['evidence'] = (
        'diagnostic inverted-sign condition select 0; physical mux source '
        'and flag phase untraced')
    return scenario


def adc_stream(pattern, repeats, samples):
    dibits = [0] * 8 + list(pattern) * repeats + [0] * 8
    pcm = transmit(dibits)
    if receive(pcm) != dibits[1:]:
        raise ValueError(('reference waveform did not recover dibits', pattern))
    adc = [127 - sample for sample in pcm[SAMPLE_START:SAMPLE_START + samples]]
    if len(adc) != samples:
        raise ValueError('ADC window changed')
    if samples == SHORT_SAMPLES:
        return input_stream(adc, 3, 5, 0, 0)
    values = []
    for index, code in enumerate(adc):
        values.extend([5 if code & 1 else 3] * (188 if index % 2 == 0 else 187))
    if len(values) != LONG_VISITS:
        raise ValueError('ADC hold schedule changed')
    return values


def detail(mapping, base, timing):
    scenario = condition_scenario(base, timing)
    runs = []
    for pattern in DETAIL_PATTERNS:
        values = adc_stream(pattern, 4, SHORT_SAMPLES)
        result = run_trace(mapping, scenario, 0x3F8, values, SHORT_CYCLES)
        selected = [row['external_read']['value'] for row in result['trace']
                    if row['pc'] == 0x3F8]
        if (result['site_visits'] != SHORT_VISITS or
                result['site_selected'] != SHORT_VISITS or selected != values):
            raise ValueError(('detailed ADC bytes were not selected', timing, pattern))
        runs.append(result)
    left, right = runs
    if any(a['pc'] != b['pc'] for a, b in zip(left['trace'], right['trace'])):
        raise ValueError(('detailed PC paths diverged', timing))
    return dict(timing=timing,
                patterns=[list(pattern) for pattern in DETAIL_PATTERNS],
                selected_input_visits=SHORT_VISITS,
                same_pc_path=True,
                different_boundaries=sum(a != b for a, b in
                                         zip(left['boundaries'], right['boundaries'])),
                different_selected_rom_addresses=sum(a != b for a, b in
                                                     zip(left['reads'], right['reads'])),
                different_alu_y_by_pc={pc: sum(a != b for a, b in
                                               zip(left['outputs'][pc],
                                                   right['outputs'][pc]))
                                       for pc in left['outputs']},
                trace_digests=[run['result']['trace_digest'] for run in runs])


def run(out=HERE / 'results/lower-i-d3f8-sign-adc.json'):
    mapping = mapping_for('!10.6', '11.2')
    _, base = fixture()
    cases = []
    for timing in ('previous', 'current'):
        for pattern in PATTERNS:
            values = adc_stream(pattern, 16, LONG_SAMPLES)
            result = execute(mapping, scenario_for(condition_scenario(base, timing),
                                                   values),
                             LONG_CYCLES, mode='integrated', trace_limit=0)
            counts = result['address_counts']
            visits = counts.get(0x3F8, 0)
            if (not result['clean'] or visits != LONG_VISITS or
                    result['read_sequence_visits'].get(0x3F8, 0) != LONG_VISITS or
                    result['final_state']['pc'] != 0x3F8 or
                    counts.get(0x1E9, 0) or counts.get(0x1EA, 0)):
                raise ValueError(('sign ADC sustained run changed', timing, pattern))
            cases.append(dict(timing=timing, pattern=list(pattern),
                              d3f8_visits=visits,
                              offered_input_visits=result['read_sequence_visits'][0x3F8],
                              selected_rom_reads=result['rom_reads']['selected_by_alu'],
                              loop_1e9_visits=0, loop_1ea_visits=0,
                              final_pc='3F8', trace_digest=result['trace_digest']))
    details = [detail(mapping, base, timing) for timing in ('previous', 'current')]
    if any(row['different_boundaries'] == 0 or
           row['different_selected_rom_addresses'] == 0 or
           not any(row['different_alu_y_by_pc'].values()) for row in details):
        raise ValueError('sustained sign loop lost input sensitivity')
    paths = [Path(__file__), HERE / 'lower_i_d3f8_adc_cross_symbols.py',
             HERE / 'lower_i_d3f8_adc_decoder_screen.py',
             HERE / 'lower_i_d3f8_input.py', HERE / 'reference_modem.py',
             HERE / 'lower_i_prom_data_route.py', HERE / 'photo_controller_path.py',
             HERE / 'split_slice_probe.py', HERE.parent / 'assumed/execute.py',
             HERE.parent / 'model.py',
             HERE.parents[2] / 'am27s31dc-prom/nokia-modem-am27s31dc.bin']
    report = dict(status='conditional sustained input-sensitive ADC-bit loop under inverted-sign select 0',
                  fixture=dict(mapping='I7/A0=!10.6, I0/A1=11.2, lower I6=11.0',
                               initial_q=5, initial_ram=[0] * 16,
                               condition_select_0='inverted sign, previous or current flag',
                               adc_decoder='bit 0 normal, complementary code 127-PCM to D3F8 03/05',
                               dibit_frame='8 zero symbols + repeated four-dibit pattern 16 times + 8 zero symbols',
                               sample_window=[SAMPLE_START,
                                              SAMPLE_START + LONG_SAMPLES],
                               input_hold_visits=[188, 187],
                               expected_input_visits=LONG_VISITS,
                               cycles_per_long_run=LONG_CYCLES),
                  cases=cases, detailed_input_comparison=details,
                  limitations=[
                      'The ADC-bit decoder, D0 bias, input connection, oscillator division and sign-condition wiring are hypotheses.',
                      'Only one Q/RAM seed and one field mapping are used.',
                      'The detailed selected-byte and input-sensitivity check covers two 32-sample patterns; the long runs count offered input visits but do not save full traces.',
                      'Sustained input-sensitive state does not identify a bit decision, physical output path or USART-01 RxD; C3 remains open.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path,
                        default=HERE / 'results/lower-i-d3f8-sign-adc.json')
    args = parser.parse_args()
    report = run(args.out)
    print(len(report['cases']), [(row['timing'], row['different_boundaries'])
                                 for row in report['detailed_input_comparison']])
