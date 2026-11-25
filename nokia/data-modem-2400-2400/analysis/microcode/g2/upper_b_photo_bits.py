"""Test upper-B bit positions inspired by the U18→U30 photo bundle."""

import hashlib
import itertools
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
from common import save
from independent_slice_addresses import mapping_for
from independent_slice_fields import stream_run
from photo_controller_path import fixture
from split_slice_probe import split_scenario


def run(out=HERE / 'results/upper-b-photo-bits.json'):
    photo = json.loads((HERE / 'results/photo-upper-bundle/report.json').read_text())
    if [track['name'] for track in photo['tracks']] != ['U17-to-U29', 'U18-to-U30']:
        raise ValueError('upper-bundle photo record changed')
    _, base = fixture()
    scenario = split_scenario(base)
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        for index, order in enumerate(itertools.permutations(['18.4', '18.5', '18.6', '18.7'])):
            mapping = mapping_for('b')
            mapping['fields']['b_high']['bits'] = list(order)
            mapping['fields']['b_high']['evidence'] = (
                'Diagnostic U18 high-data-bit bundle through U30 to U8 B; '
                'front photo shows two adjacent PROM-to-latch track candidates, '
                'but neither individual data pin nor U30-to-U8 continuation is traced.')
            zero = stream_run(mapping, scenario, 5, [0] * 128,
                              root / f'{index}-zero', 'D4 zero')
            one = stream_run(mapping, scenario, 5, [16] * 128,
                             root / f'{index}-one', 'D4 one')
            if (not zero['clean'] or not one['clean'] or
                    zero['input_visits'] != 128 or one['input_visits'] != 128 or
                    zero['controller_bits_selected_by_alu'] != 128 or
                    one['controller_bits_selected_by_alu'] != 128):
                raise ValueError(f'upper-B order {order} changed controller loop')
            cases.append(dict(index=index, upper_b_bits=list(order),
                              output_zero=zero['output_y_by_site'],
                              output_one=one['output_y_by_site'],
                              selected_rom_reads_zero=zero['selected_rom_reads_after_input'],
                              distinct_rom_addresses_zero=zero['distinct_rom_addresses_after_input'],
                              q_at_38f_zero=zero['q_at_38f'],
                              q_at_38f_one=one['q_at_38f'],
                              state_trace_differs=zero['trace_digest'] != one['trace_digest'],
                              zero_trace_digest=zero['trace_digest'],
                              one_trace_digest=one['trace_digest']))
    low_mapping = mapping_for('b')
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        low_zero = stream_run(low_mapping, scenario, 5, [0] * 128,
                              root / 'low-zero', 'D4 zero')
        low_one = stream_run(low_mapping, scenario, 5, [16] * 128,
                             root / 'low-one', 'D4 one')
    report = dict(status='photo-inspired upper B-bit source comparison',
                  fixture=dict(mapping='separated pair instructions and upper B address',
                               upper_high_bit_set=['18.4', '18.5', '18.6', '18.7'],
                               all_permutations=24, input='128 D4 zero or one bytes at 38E',
                               cycles=1580, startup_q=5,
                               photo_overlay='results/photo-upper-bundle/candidate-front-tracks.jpg'),
                  high_bit_cases=cases,
                  low_bit_comparator=dict(bits=low_mapping['fields']['b_high']['bits'],
                                          output_zero=low_zero['output_y_by_site'],
                                          output_one=low_one['output_y_by_site'],
                                          zero_trace_digest=low_zero['trace_digest'],
                                          one_trace_digest=low_one['trace_digest']),
                  summary=dict(high_orders_with_different_output_sets=sum(
                      row['output_zero'] != row['output_one'] for row in cases),
                      high_orders_with_different_state_traces=sum(
                          row['state_trace_differs'] for row in cases),
                      high_order_output_set_classes=sorted({
                          json.dumps([row['output_zero'], row['output_one']], sort_keys=True)
                          for row in cases})),
                  limitations=[
                      'The photo establishes track segments, not U18 bit identities or U30-to-U8 wiring.',
                      'The four U18 high bits and their B-field role are diagnostic assumptions.',
                      'D4 controller input, q3 branch/ROM timing, Q=5 and output sites remain hypotheses.',
                      'A fixed output in this loop does not reject other input routes or transmitter paths.'],
                  source_sha256={str(p.relative_to(HERE.parent)):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (Path(__file__), HERE / 'photo_upper_bundle.py',
                                           HERE / 'results/photo-upper-bundle/report.json',
                                           HERE / 'independent_slice_addresses.py',
                                           HERE / 'independent_slice_fields.py',
                                           HERE / 'split_slice_probe.py',
                                           ASSUMED / 'execute.py', HERE.parent / 'model.py')})
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    print(result['summary'])
