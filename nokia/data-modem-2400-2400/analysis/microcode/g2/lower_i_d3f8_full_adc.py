"""Feed held full ADC sample bytes into the sustained D3F8 PROM loop."""

import argparse
import hashlib
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from lower_i_d3f8_adc_cross_symbols import PATTERNS
from lower_i_d3f8_adc_decoder_screen import input_stream
from lower_i_d3f8_input import run_trace
from lower_i_d3f8_sign_adc import condition_scenario
from lower_i_prom_data_route import mapping_for
from photo_controller_path import fixture
from reference_modem import receive, transmit
from split_slice_probe import split_scenario

SAMPLE_START = 64
LONG_SAMPLES = 128
SHORT_SAMPLES = 32
LONG_VISITS = 24000
SHORT_VISITS = 6000
LONG_CYCLES = 8 * LONG_VISITS + 47
SHORT_CYCLES = 8 * SHORT_VISITS + 47
INPUT_PC = 0x3F8
DETAIL_PATTERNS = ((0, 1, 3, 2), (0, 0, 0, 0))
RANDOM_SEEDS = (0x2847, 0x3557, 0x3558, 0x8102)


def codes(pattern, samples, coding):
    repeats = 16 if samples == LONG_SAMPLES else 4
    dibits = [0] * 8 + list(pattern) * repeats + [0] * 8
    pcm = transmit(dibits)
    if receive(pcm) != dibits[1:]:
        raise ValueError(('reference failed', pattern))
    pcm = pcm[SAMPLE_START:SAMPLE_START + samples]
    if len(pcm) != samples:
        raise ValueError('ADC sample window changed')
    code = [127 - sample if coding.startswith('complementary') else 128 + sample
            for sample in pcm]
    if coding.endswith('_d0_high'):
        code = [value | 1 for value in code]
    return code


def hold(code):
    values = []
    for index, value in enumerate(code):
        values.extend([value] * (188 if index % 2 == 0 else 187))
    if len(values) != len(code) * 375 // 2:
        raise ValueError('ADC hold schedule changed')
    return values


def scenario_for_full_byte(base, values, coding):
    scenario = split_scenario(condition_scenario(base, 'previous'))
    scenario['initial']['q'] = 5
    for bit in ('7', '0'):
        scenario['inputs']['instruction_bit_overrides'].pop(bit)
    for bit in ('0', '1'):
        scenario['inputs']['register_address_bit_overrides']['a'].pop(bit)
    if INPUT_PC in scenario['io']['read']['address']['pcs']:
        scenario['io']['read']['address']['pcs'].remove(INPUT_PC)
    scenario['io']['read']['pc_sequences'][str(INPUT_PC)] = values
    scenario['io']['read']['evidence'] += (
        f'; diagnostic held {coding} 8-bit ADC sample bytes at D3F8; '
        'ADC-to-DSC bus, conversion schedule and condition mux untraced')
    return scenario


def compare(left, right):
    if any(a['pc'] != b['pc'] for a, b in zip(left['trace'], right['trace'])):
        raise ValueError('detailed full-ADC PC paths differ')
    return dict(same_pc_path=True,
                different_boundaries=sum(a != b for a, b in
                                         zip(left['boundaries'], right['boundaries'])),
                different_selected_rom_addresses=sum(a != b for a, b in
                                                     zip(left['reads'], right['reads'])),
                different_alu_y_by_pc={pc: sum(a != b for a, b in
                                               zip(left['outputs'][pc],
                                                   right['outputs'][pc]))
                                       for pc in left['outputs']})


def run(out=HERE / 'results/lower-i-d3f8-full-adc.json'):
    mapping = mapping_for('!10.6', '11.2')
    _, base = fixture()
    cases = []
    variants = [('complementary', pattern) for pattern in PATTERNS]
    variants += [('natural_binary', pattern) for pattern in PATTERNS]
    variants += [(coding, pattern) for coding in
                 ('complementary_d0_high', 'natural_binary_d0_high')
                 for pattern in DETAIL_PATTERNS]
    for coding, pattern in variants:
        samples = codes(pattern, LONG_SAMPLES, coding)
        values = hold(samples)
        scenario = scenario_for_full_byte(base, values, coding)
        result = execute(mapping, scenario, LONG_CYCLES,
                         mode='integrated', trace_limit=0)
        counts = result['address_counts']
        visits = counts.get(INPUT_PC, 0)
        cases.append(dict(coding=coding, pattern=list(pattern),
                          distinct_sample_codes=len(set(samples)),
                          samples_with_d0_low=sum(not (value & 1)
                                                  for value in samples),
                          d3f8_visits=visits,
                          offered_input_visits=result['read_sequence_visits'].get(INPUT_PC, 0),
                          selected_rom_reads=result['rom_reads']['selected_by_alu'],
                          loop_1e9_visits=counts.get(0x1E9, 0),
                          loop_1ea_visits=counts.get(0x1EA, 0),
                          final_pc=f"{result['final_state']['pc']:03X}",
                          trace_digest=result['trace_digest']))
    if any(row['d3f8_visits'] != LONG_VISITS or
           row['offered_input_visits'] != LONG_VISITS or
           row['loop_1e9_visits'] or row['loop_1ea_visits'] or
           row['final_pc'] != '3F8' for row in cases):
        raise ValueError('full-byte D3F8 loop no longer sustained')
    random_cases = []
    for seed in RANDOM_SEEDS:
        generator = random.Random(seed)
        middle = [generator.randrange(4) for _ in range(16)]
        dibits = [0] * 8 + middle + [0] * 8
        pcm = transmit(dibits)
        if receive(pcm) != dibits[1:]:
            raise ValueError(('random reference sequence failed', seed))
        samples = [127 - sample for sample in
                   pcm[SAMPLE_START:SAMPLE_START + LONG_SAMPLES]]
        values = hold(samples)
        result = execute(mapping,
                         scenario_for_full_byte(base, values, 'complementary'),
                         LONG_CYCLES, mode='integrated', trace_limit=0)
        counts = result['address_counts']
        if (not result['clean'] or counts.get(INPUT_PC, 0) != LONG_VISITS or
                result['read_sequence_visits'].get(INPUT_PC, 0) != LONG_VISITS or
                counts.get(0x1E9, 0) or counts.get(0x1EA, 0) or
                result['final_state']['pc'] != INPUT_PC):
            raise ValueError(('random full-byte stream did not sustain', seed))
        random_cases.append(dict(seed=seed, dibits=middle,
                                 distinct_sample_codes=len(set(samples)),
                                 samples_with_d0_low=sum(not (value & 1)
                                                         for value in samples),
                                 d3f8_visits=counts[INPUT_PC],
                                 selected_rom_reads=result['rom_reads']['selected_by_alu'],
                                 final_pc='3F8', trace_digest=result['trace_digest']))
    detail = {}
    runs = {}
    for pattern in DETAIL_PATTERNS:
        values = hold(codes(pattern, SHORT_SAMPLES, 'complementary'))
        run_result = run_trace(mapping, condition_scenario(base, 'previous'),
                               INPUT_PC, values, SHORT_CYCLES)
        selected = [row['external_read']['value'] for row in run_result['trace']
                    if row['pc'] == INPUT_PC]
        if (run_result['site_visits'] != SHORT_VISITS or
                run_result['site_selected'] != SHORT_VISITS or selected != values):
            raise ValueError(('detailed full ADC bytes not selected', pattern))
        runs[pattern] = run_result
    detail['distinct_patterns'] = compare(runs[DETAIL_PATTERNS[0]],
                                          runs[DETAIL_PATTERNS[1]])
    detail['full_byte_vs_low_nibble_by_pattern'] = {}
    for pattern in DETAIL_PATTERNS:
        low_nibble = hold([value & 0x0F for value in
                           codes(pattern, SHORT_SAMPLES, 'complementary')])
        low_result = run_trace(mapping, condition_scenario(base, 'previous'),
                               INPUT_PC, low_nibble, SHORT_CYCLES)
        if low_result['site_selected'] != SHORT_VISITS:
            raise ValueError(('masked ADC bytes not selected', pattern))
        comparison = compare(runs[pattern], low_result)
        if (comparison['different_boundaries'] or
                comparison['different_selected_rom_addresses'] or
                any(comparison['different_alu_y_by_pc'].values()) or
                runs[pattern]['result']['trace_digest'] !=
                low_result['result']['trace_digest']):
            raise ValueError(('ADC upper nibble unexpectedly affects trace', pattern))
        detail['full_byte_vs_low_nibble_by_pattern'][
            ''.join(map(str, pattern))] = comparison
    low_bit = input_stream(codes(DETAIL_PATTERNS[0], SHORT_SAMPLES,
                                 'complementary'), 3, 5, 0, 0)
    bit_result = run_trace(mapping, condition_scenario(base, 'previous'),
                           INPUT_PC, low_bit, SHORT_CYCLES)
    if bit_result['site_selected'] != SHORT_VISITS:
        raise ValueError('bit-0 comparison no longer selects input')
    detail['full_byte_vs_bit0'] = compare(runs[DETAIL_PATTERNS[0]], bit_result)
    detail['selected_input_visits_per_run'] = SHORT_VISITS
    paths = [Path(__file__), HERE / 'lower_i_d3f8_sign_adc.py',
             HERE / 'lower_i_d3f8_adc_decoder_screen.py',
             HERE / 'lower_i_d3f8_input.py', HERE / 'reference_modem.py',
             HERE / 'lower_i_prom_data_route.py', HERE / 'photo_controller_path.py',
             HERE / 'split_slice_probe.py', HERE.parent / 'assumed/execute.py',
             HERE.parent / 'model.py',
             HERE.parents[2] / 'am27s31dc-prom/nokia-modem-am27s31dc.bin']
    report = dict(status='conditional sustained ADC-code input with low-nibble-only effect in D3F8 loop',
                  fixture=dict(mapping='I7/A0=!10.6, I0/A1=11.2, lower I6=11.0',
                               condition_select_0='inverted previous sign',
                               initial_q=5, initial_ram=[0] * 16,
                               sample_window=[SAMPLE_START,
                                              SAMPLE_START + LONG_SAMPLES],
                               sample_hold_visits=[188, 187],
                               expected_input_visits=LONG_VISITS,
                               cycles_per_long_run=LONG_CYCLES,
                               coding='complementary=127-PCM; natural binary=128+PCM; D0-high controls OR 1'),
                  cases=cases, random_cases=random_cases,
                  detailed_comparisons=detail,
                  limitations=[
                      'ADC-to-D3F8 data-bit order, buffer enables, reference range, sample clock and condition mux are untraced hypotheses.',
                      'Six periodic and four seeded nonperiodic symbol streams use one Q/RAM seed and one field mapping.',
                      'Detailed exact-byte selection and high-nibble masking are checked for two 32-sample complementary streams; long runs count offered visits but do not save full traces.',
                      'Under the tested mapping the upper nibble has no observed effect; sustained low-nibble sensitivity does not prove demodulation or a USART-01 RxD route.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path,
                        default=HERE / 'results/lower-i-d3f8-full-adc.json')
    args = parser.parse_args()
    report = run(args.out)
    print(len(report['cases']), len(report['random_cases']),
          report['detailed_comparisons'])
