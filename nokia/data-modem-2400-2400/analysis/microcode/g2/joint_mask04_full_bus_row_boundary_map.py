"""Determine whether 3ED boundary bytes reduce to adjacent ADC nibbles."""

import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save

SOURCE = HERE / 'results/joint-mask04-full-bus-receive-states.json'
EQUIVALENCE = HERE / 'results/joint-mask04-full-bus-3f8-adc-equivalence.json'
BOUNDARIES = ((46, 47), (93, 94), (140, 141))


def summarized_map(observations, input_index, output_index):
    groups = defaultdict(set)
    for row in observations:
        groups[row[input_index]].add(row[output_index])
    return dict(input_codes=len(groups),
                conflicting_inputs=sum(len(values) > 1 for values in groups.values()),
                max_outputs_per_input=max(map(len, groups.values())),
                codebook={f'{key:X}': [f'{value:02X}' for value in sorted(values)]
                          for key, values in sorted(groups.items())})


def run(out=HERE / 'results/joint-mask04-full-bus-row-boundary-map.json'):
    source = json.loads(SOURCE.read_text())
    equivalence = json.loads(EQUIVALENCE.read_text())
    if (len(source['cases']) != 6 or
            any(row['mismatches'] for row in equivalence['cases'])):
        raise ValueError('ADC-nibble source equivalence changed')
    observations = []
    for case in source['cases']:
        for symbol in case['symbols']:
            for before, after in BOUNDARIES:
                visits = symbol['visits']
                observations.append((
                    visits[str(before)]['y3f8'] >> 4,
                    visits[str(after)]['y3f8'] >> 4,
                    visits[str(after)]['row0'],
                    visits[str(after)]['row3']))
    row0_from_previous = summarized_map(observations, 0, 2)
    row0_from_current = summarized_map(observations, 1, 2)
    row3_from_previous = summarized_map(observations, 0, 3)
    row3_from_current = summarized_map(observations, 1, 3)
    if (row0_from_previous['conflicting_inputs'] or
            row3_from_current['conflicting_inputs']):
        raise ValueError('single-sample boundary map changed')
    opposite_for_previous = defaultdict(set)
    opposite_for_current = defaultdict(set)
    for previous, current, _, _ in observations:
        opposite_for_previous[previous].add(current)
        opposite_for_current[current].add(previous)
    paths = (Path(__file__), SOURCE, EQUIVALENCE)
    report = dict(
        experiment='executed 3ED row bytes versus adjacent ADC nibbles at sample boundaries',
        fixture=dict(boundaries=BOUNDARIES,
                     capture='row0 and row3 of 3ED at first visit after each boundary',
                     previous_sample='3F8 Y high nibble at final visit before boundary',
                     current_sample='3F8 Y high nibble at first visit after boundary',
                     ADC_equivalence='previous report proved captured 3F8 Y high nibble equals modeled ADC high nibble'),
        observations=len(observations),
        distinct_adjacent_sample_pairs=len(set(row[:2] for row in observations)),
        previous_ADC_bins=len(opposite_for_previous),
        current_ADC_bins=len(opposite_for_current),
        following_bins_per_previous=(min(map(len, opposite_for_previous.values())),
                                     max(map(len, opposite_for_previous.values()))),
        preceding_bins_per_current=(min(map(len, opposite_for_current.values())),
                                    max(map(len, opposite_for_current.values()))),
        maps=dict(row0_from_previous=row0_from_previous,
                  row0_from_current=row0_from_current,
                  row3_from_previous=row3_from_previous,
                  row3_from_current=row3_from_current),
        limitations=[
            'The codebooks cover only the ADC nibbles observed in six modeled line fixtures and three boundary positions.',
            'An observed functional map does not prove that the same row bytes are history-free for all inputs, modes or clock phases.',
            'The ROM lookup and row calculations are executed, but using these two bytes as a dibit decision remains an external hypothesis.',
            'The physical ADC, latch, clock and USART routes are untraced.'],
        source_sha256={str(path.relative_to(HERE.parents[4])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    save(out, report)
    print('observations',len(observations),
          'row0 previous conflicts',row0_from_previous['conflicting_inputs'],
          'row3 current conflicts',row3_from_current['conflicting_inputs'],
          'row0 current conflicts',row0_from_current['conflicting_inputs'],
          'row3 previous conflicts',row3_from_previous['conflicting_inputs'])
    return report


if __name__ == '__main__':
    run()
