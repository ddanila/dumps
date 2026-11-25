"""Screen one uniform condition-select-0 policy at D3ED and D1EA."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import decode, load, save
from execute import execute
from lower_i_d3f8_adc_decoder_screen import (
    CYCLES, EXPECTED_INPUT_VISITS, SAMPLE_START, SAMPLES,
    input_stream, scenario_for,
)
from lower_i_prom_data_route import mapping_for
from photo_controller_path import fixture
from reference_modem import receive, transmit

PATTERNS = ((0, 1, 3, 2), (0, 0, 0, 0))
SOURCES = ('zero', 'carry', 'sign', 'overflow')
TIMINGS = ('previous', 'current')
POLARITIES = (0, 1)


def run(out=HERE / 'results/lower-i-d3f8-condition0-screen.json'):
    mapping = mapping_for('!10.6', '11.2')
    words = decode(mapping, load())
    if words[0x3ED]['raw'] != words[0x1EA]['raw'] or (
            words[0x3ED]['select'], words[0x1EA]['select']) != (0, 0):
        raise ValueError('shared D3ED/D1EA condition word changed')
    _, base = fixture()
    streams = {}
    for pattern in PATTERNS:
        dibits = [0] * 8 + list(pattern) * 4 + [0] * 8
        pcm = transmit(dibits)
        if receive(pcm) != dibits[1:]:
            raise ValueError(('reference pattern failed', pattern))
        adc = [127 - sample for sample in pcm[SAMPLE_START:
                                              SAMPLE_START + SAMPLES]]
        streams[''.join(map(str, pattern))] = input_stream(adc, 3, 5, 0, 0)
    cases = []
    for source in SOURCES:
        for timing in TIMINGS:
            for polarity in POLARITIES:
                for pattern, values in streams.items():
                    scenario = scenario_for(base, values)
                    scenario['condition']['sources'][0] = source
                    scenario['condition']['polarity'][0] = polarity
                    scenario['condition']['flag_timing'] = timing
                    scenario['condition']['evidence'] = (
                        'diagnostic uniform select-0 flag source, timing and polarity; '
                        'physical condition multiplexer untraced')
                    result = execute(mapping, scenario, CYCLES,
                                     mode='integrated', trace_limit=0)
                    counts = result['address_counts']
                    cases.append(dict(source=source, timing=timing,
                                      polarity=polarity, pattern=pattern,
                                      d3f8_visits=counts.get(0x3F8, 0),
                                      full_d3f8_window=(counts.get(0x3F8, 0)
                                                        >= EXPECTED_INPUT_VISITS),
                                      d3ee_returns=counts.get(0x3EE, 0),
                                      loop_1e9_visits=counts.get(0x1E9, 0),
                                      loop_1ea_visits=counts.get(0x1EA, 0),
                                      after_1ea_1eb_visits=counts.get(0x1EB, 0),
                                      poll_1ec_visits=counts.get(0x1EC, 0),
                                      final_pc=f"{result['final_state']['pc']:03X}",
                                      clean=result['clean'],
                                      trace_digest=result['trace_digest']))
    if len(cases) != len(SOURCES) * len(TIMINGS) * len(POLARITIES) * len(PATTERNS):
        raise ValueError('condition screen coverage changed')
    policies = []
    for source in SOURCES:
        for timing in TIMINGS:
            for polarity in POLARITIES:
                group = [row for row in cases if
                         (row['source'], row['timing'], row['polarity']) ==
                         (source, timing, polarity)]
                policies.append(dict(source=source, timing=timing, polarity=polarity,
                                     full_patterns=[row['pattern'] for row in group
                                                    if row['full_d3f8_window']],
                                     any_1eb=any(row['after_1ea_1eb_visits']
                                                 for row in group),
                                     d3f8_visits={row['pattern']: row['d3f8_visits']
                                                  for row in group}))
    paths = [Path(__file__), HERE / 'lower_i_d3f8_adc_decoder_screen.py',
             HERE / 'lower_i_prom_data_route.py', HERE / 'photo_controller_path.py',
             HERE / 'split_slice_probe.py', HERE / 'reference_modem.py',
             HERE.parent / 'assumed/execute.py', HERE.parent / 'assumed/common.py',
             HERE.parent / 'model.py',
             HERE.parents[2] / 'am27s31dc-prom/nokia-modem-am27s31dc.bin']
    report = dict(status='uniform condition-select-0 hypothesis screen for D3F8 receiver loop and D1EA drain',
                  fixture=dict(mapping='I7/A0=!10.6, I0/A1=11.2, lower I6=11.0',
                               initial_q=5, initial_ram=[0] * 16,
                               input_decoder='ADC bit0 normal to D3F8 03/05',
                               patterns=[list(pattern) for pattern in PATTERNS],
                               sample_window=[SAMPLE_START, SAMPLE_START + SAMPLES],
                               sample_hold_visits=[188, 187],
                               cycles=CYCLES,
                               shared_condition_word=words[0x3ED]['raw'],
                               condition_select=0),
                  policies=policies, cases=cases,
                  limitations=[
                      'Only two 32-sample patterns, one ADC-bit decoder and one initial Q/RAM state are tested.',
                      'Condition source, timing and polarity are diagnostic mux hypotheses, not traced Nokia wiring.',
                      'A full D3F8 visit window or release from 1EA is not a recovered bit or USART receive route.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path,
                        default=HERE / 'results/lower-i-d3f8-condition0-screen.json')
    args = parser.parse_args()
    result = run(args.out)
    print([(row['source'], row['timing'], row['polarity'],
            row['full_patterns'], row['any_1eb']) for row in result['policies']])
