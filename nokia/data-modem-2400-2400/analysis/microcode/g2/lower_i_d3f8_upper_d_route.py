"""Test an upper instruction-bit source that selects ADC D7-D4 at D3F8."""

import argparse
import copy
import hashlib
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from lower_i_d3f8_adc_cross_symbols import PATTERNS
from lower_i_d3f8_full_adc import (
    DETAIL_PATTERNS, LONG_CYCLES, LONG_SAMPLES, LONG_VISITS, RANDOM_SEEDS,
    SAMPLE_START, SHORT_CYCLES, SHORT_SAMPLES, SHORT_VISITS,
    codes, hold, scenario_for_full_byte,
)
from lower_i_d3f8_input import run_trace
from lower_i_d3f8_sign_adc import condition_scenario
from lower_i_prom_data_route import mapping_for
from photo_controller_path import fixture
from reference_modem import receive, transmit

INPUT_PC = 0x3F8
SOURCE_ALTERNATIVES = ((0, '17.6'), (0, '18.1'),
                       (1, '17.6'), (1, '18.1'))


def mapping_with_upper_source(position, token):
    mapping = copy.deepcopy(mapping_for('!10.6', '11.2'))
    previous = mapping['fields']['i_high']['bits'][position]
    mapping['fields']['i_high']['bits'][position] = token
    mapping['fields']['i_high']['evidence'] += (
        f'; diagnostic U8 I{position} source {previous}->{token} within '
        'photo-compatible U17/U18 upper PROM/latch bundle; pin route untraced')
    mapping['name'] += f'-upper-I{position}-{token}'
    return mapping


def comparison(left, right):
    if any(a['pc'] != b['pc'] for a, b in zip(left['trace'], right['trace'])):
        raise ValueError('upper-D full/masked PC paths diverged')
    return dict(same_pc_path=True,
                different_boundaries=sum(a != b for a, b in
                                         zip(left['boundaries'], right['boundaries'])),
                different_selected_rom_addresses=sum(a != b for a, b in
                                                     zip(left['reads'], right['reads'])),
                different_alu_y_by_pc={pc: sum(a != b for a, b in
                                               zip(left['outputs'][pc],
                                                   right['outputs'][pc]))
                                       for pc in left['outputs']})


def run(out=HERE / 'results/lower-i-d3f8-upper-d-route.json'):
    _, base = fixture()
    baseline = mapping_for('!10.6', '11.2')
    selected = mapping_with_upper_source(0, '17.6')
    source_cases = []
    for position, token in SOURCE_ALTERNATIVES:
        mapping = mapping_with_upper_source(position, token)
        runs = []
        for byte in (0x04, 0x14):
            scenario = scenario_for_full_byte(base, [byte] * 100,
                                              'complementary')
            result = execute(mapping, scenario, 512,
                             mode='integrated', trace_limit=0)
            runs.append(result)
        source_cases.append(dict(upper_i_bit=position, prom_source=token,
                                 d3f8_visits=[run['address_counts'].get(INPUT_PC, 0)
                                              for run in runs],
                                 high_nibble_changes_trace=(runs[0]['trace_digest'] !=
                                                            runs[1]['trace_digest']),
                                 final_pcs=[f"{run['final_state']['pc']:03X}"
                                            for run in runs],
                                 trace_digests=[run['trace_digest'] for run in runs]))
    if any(row['d3f8_visits'] != [59, 59] or
           not row['high_nibble_changes_trace'] for row in source_cases):
        raise ValueError('upper-source short screen changed')
    long_cases = []
    for pattern in PATTERNS:
        values = hold(codes(pattern, LONG_SAMPLES, 'complementary'))
        result = execute(selected,
                         scenario_for_full_byte(base, values, 'complementary'),
                         LONG_CYCLES, mode='integrated', trace_limit=0)
        counts = result['address_counts']
        if (not result['clean'] or counts.get(INPUT_PC, 0) != LONG_VISITS or
                result['read_sequence_visits'].get(INPUT_PC, 0) != LONG_VISITS or
                counts.get(0x1E9, 0) or counts.get(0x1EA, 0) or
                result['final_state']['pc'] != INPUT_PC):
            raise ValueError(('upper-D periodic run did not sustain', pattern))
        long_cases.append(dict(kind='periodic', pattern=list(pattern),
                               d3f8_visits=counts[INPUT_PC],
                               selected_rom_reads=result['rom_reads']['selected_by_alu'],
                               final_pc='3F8', trace_digest=result['trace_digest']))
    for seed in RANDOM_SEEDS:
        generator = random.Random(seed)
        middle = [generator.randrange(4) for _ in range(16)]
        dibits = [0] * 8 + middle + [0] * 8
        pcm = transmit(dibits)
        if receive(pcm) != dibits[1:]:
            raise ValueError(('random reference failed', seed))
        values = hold([127 - sample for sample in
                       pcm[SAMPLE_START:SAMPLE_START + LONG_SAMPLES]])
        result = execute(selected,
                         scenario_for_full_byte(base, values, 'complementary'),
                         LONG_CYCLES, mode='integrated', trace_limit=0)
        counts = result['address_counts']
        if (not result['clean'] or counts.get(INPUT_PC, 0) != LONG_VISITS or
                result['read_sequence_visits'].get(INPUT_PC, 0) != LONG_VISITS or
                counts.get(0x1E9, 0) or counts.get(0x1EA, 0) or
                result['final_state']['pc'] != INPUT_PC):
            raise ValueError(('upper-D nonperiodic run did not sustain', seed))
        long_cases.append(dict(kind='nonperiodic', seed=seed, dibits=middle,
                               d3f8_visits=counts[INPUT_PC],
                               selected_rom_reads=result['rom_reads']['selected_by_alu'],
                               final_pc='3F8', trace_digest=result['trace_digest']))
    details = []
    for pattern in DETAIL_PATTERNS:
        code = codes(pattern, SHORT_SAMPLES, 'complementary')
        full = hold(code)
        masked = hold([value & 0x0F for value in code])
        detail_runs = {}
        for label, mapping in (('baseline', baseline), ('upper_i0_17_6', selected)):
            scenario = condition_scenario(base, 'previous')
            raw = run_trace(mapping, scenario, INPUT_PC, full, SHORT_CYCLES)
            low = run_trace(mapping, scenario, INPUT_PC, masked, SHORT_CYCLES)
            for result, offered in ((raw, full), (low, masked)):
                selected_bytes = [row['external_read']['value'] for row in
                                  result['trace'] if row['pc'] == INPUT_PC]
                if (result['site_visits'] != SHORT_VISITS or
                        result['site_selected'] != SHORT_VISITS or
                        selected_bytes != offered):
                    raise ValueError(('upper-D input not selected', pattern, label))
            high_instructions = sorted({row['instruction_i_high'] for row in
                                        raw['trace'] if row['pc'] == INPUT_PC})
            compared = comparison(raw, low)
            detail_runs[label] = dict(high_instructions_at_d3f8=high_instructions,
                                      high_operand_selects_d=any(
                                          (value & 7) in (5, 6, 7)
                                          for value in high_instructions),
                                      **compared)
        if (detail_runs['baseline']['high_instructions_at_d3f8'] != [0xFC] or
                detail_runs['baseline']['different_boundaries'] != 0 or
                detail_runs['upper_i0_17_6']['high_instructions_at_d3f8'] != [0xFD] or
                detail_runs['upper_i0_17_6']['different_boundaries'] == 0 or
                detail_runs['upper_i0_17_6']['different_selected_rom_addresses'] == 0):
            raise ValueError(('upper-D detailed control changed', pattern))
        details.append(dict(pattern=list(pattern), cases=detail_runs))
    paths = [Path(__file__), HERE / 'lower_i_d3f8_full_adc.py',
             HERE / 'lower_i_d3f8_sign_adc.py', HERE / 'lower_i_d3f8_input.py',
             HERE / 'lower_i_prom_data_route.py', HERE / 'photo_controller_path.py',
             HERE / 'split_slice_probe.py', HERE / 'reference_modem.py',
             HERE.parent / 'assumed/execute.py', HERE.parent / 'model.py',
             HERE.parents[2] / 'am27s31dc-prom/nokia-modem-am27s31dc.bin']
    report = dict(status='conditional upper-slice ADC D selection under one photo-compatible instruction source swap',
                  fixture=dict(mapping='lower I7/A0=!10.6, I0/A1=11.2, I6=11.0',
                               upper_instruction_baseline_i0='17.5',
                               upper_instruction_candidate_i0='17.6',
                               other_upper_instruction_bits='unchanged',
                               upper_crosslinks='I4=lower I1, I6=lower I2',
                               condition_select_0='inverted previous sign',
                               initial_q=5, initial_ram=[0] * 16,
                               input='held complementary ADC code 127-PCM at D3F8',
                               sample_hold_visits=[188, 187],
                               long_sample_window=[SAMPLE_START,
                                                   SAMPLE_START + LONG_SAMPLES],
                               expected_long_visits=LONG_VISITS,
                               long_cycles=LONG_CYCLES),
                  source_cases=source_cases,
                  long_cases=long_cases,
                  detailed_full_vs_masked=details,
                  limitations=[
                      'U17 D6 to U8 I0 is a photo-compatible source hypothesis, not traced continuity; other upper-slice instruction and address bits remain uncertain.',
                      'ADC bus order, buffer enables, reference range, conversion clock and select-0 condition wiring are also untraced.',
                      'Two detailed 32-sample streams prove upper-bit influence under this mapping; long runs count offered visits but do not save full traces.',
                      'An input-sensitive upper slice is not a decoded symbol, verified output latch or USART-01 RxD route.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path,
                        default=HERE / 'results/lower-i-d3f8-upper-d-route.json')
    args = parser.parse_args()
    report = run(args.out)
    print(len(report['long_cases']),
          [(row['pattern'], row['cases']['upper_i0_17_6']['different_boundaries'])
           for row in report['detailed_full_vs_masked']])
