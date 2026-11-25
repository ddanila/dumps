"""Screen independently decoded upper-slice register addresses with real PROMs."""

import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
from common import save
from execute import execute
from controller_bit_dispatch import controller_stream
from independent_slice_fields import candidate_mapping, stream_run
from photo_controller_path import fixture
from split_slice_probe import split_scenario


def mapping_for(variant):
    mapping = candidate_mapping('separated')
    mapping['name'] += f'-upper-address-{variant}'
    if 'a' in variant:
        mapping['fields']['a_high'] = dict(
            bits=['18.1', '18.0', '17.7', '17.6'], status='hypothesis',
            evidence='U17 data through U29 to U8 A2/A3 is a mirrored photo-compatible '
                     'candidate, not a traced connection; A0/A1 retain the earlier field.')
    if 'b' in variant:
        mapping['fields']['b_high'] = dict(
            bits=['18.4', '18.3', '18.2', '18.1'], status='hypothesis',
            evidence='U18 data through U30 to U8 B0-B3 is a photo-compatible '
                     'bundle assumption; pin order is untraced.')
    return mapping


def run(out=HERE / 'results/independent-slice-addresses.json'):
    _, base = fixture()
    scenario = split_scenario(base)
    _, bits = controller_stream()
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        for variant in ('none', 'a', 'b', 'ab'):
            mapping = mapping_for(variant)
            streams = {}
            for label, offered in (('actual', bits), ('zero', [0] * len(bits)),
                                   ('one', [1] * len(bits))):
                directory = root / f'{variant}-{label}'
                streams[label] = stream_run(mapping, scenario, 5, offered,
                                            directory, label)
                output_events = {'39E': [], '39F': []}
                for line in (directory / 'trace.jsonl').read_text().splitlines():
                    row = json.loads(line)
                    site = f"{row['pc']:03X}"
                    if site in output_events:
                        output_events[site].append(row['alu']['y'])
                streams[label]['output_first_three_by_site'] = {
                    site: values[:3] for site, values in output_events.items()}
                streams[label]['output_after_first_by_site'] = {
                    site: sorted(set(values[1:])) for site, values in output_events.items()}
            if any(not row['clean'] or row['input_visits'] != 128
                   for row in streams.values()):
                raise ValueError(f'{variant}: controller loop changed')
            if any(row['controller_bits_selected_by_alu'] != 128
                   for row in streams.values()):
                raise ValueError(f'{variant}: offered D bytes were not selected')
            cases.append(dict(variant=variant,
                              high_a=mapping['fields'].get('a_high', {}).get('bits'),
                              high_b=mapping['fields'].get('b_high', {}).get('bits'),
                              q5=streams,
                              q5_zero_one_equal=(streams['zero']['trace_digest'] ==
                                                 streams['one']['trace_digest']),
                              q5_actual_zero_one_equal=(len({row['trace_digest']
                                                             for row in streams.values()}) == 1)))
        # The B-address variants change the output word, so check every Q seed
        # that reaches both the input and candidate output in a bounded run.
        for case in cases:
            if case['variant'] not in ('b', 'ab'):
                continue
            mapping = mapping_for(case['variant'])
            seed_scenario = json.loads(json.dumps(scenario))
            seed_scenario['io']['read']['pc_sequences']['910'] = bits
            reached = []
            for q in range(256):
                seed_scenario['initial']['q'] = q
                result = execute(mapping, seed_scenario, 512,
                                 mode='integrated', trace_limit=0)
                if (result['address_counts'].get(0x38E, 0) and
                        result['address_counts'].get(0x39E, 0)):
                    reached.append(q)
            comparisons = []
            for q in reached:
                zero = stream_run(mapping, scenario, q, [0] * len(bits),
                                  root / f"{case['variant']}-q{q}-zero", 'zero')
                one = stream_run(mapping, scenario, q, [1] * len(bits),
                                 root / f"{case['variant']}-q{q}-one", 'one')
                if zero['controller_bits_selected_by_alu'] != 128 or one['controller_bits_selected_by_alu'] != 128:
                    raise ValueError(f"{case['variant']} Q={q}: input not selected")
                comparisons.append(dict(q=q, zero_one_equal=(zero['trace_digest'] ==
                                                             one['trace_digest']),
                                        selected_input_visits=zero['controller_bits_selected_by_alu'],
                                        output_zero=zero['output_y_by_site'],
                                        output_one=one['output_y_by_site']))
            case['seed_screen'] = dict(cycles=512, reached_q=reached,
                                       compared_cycles=1580, comparisons=comparisons,
                                       differing_q=[row['q'] for row in comparisons
                                                    if not row['zero_one_equal']])
    report = dict(status='photo-compatible upper register-address hypothesis screen',
                  fixture=dict(mapping='separated lower/upper instruction pairs',
                               q5_streams=['actual', 'zero', 'one'],
                               controller_bits=len(bits),
                               output_sites='39E and 39F are candidates, not a traced DAC clock'),
                  cases=cases,
                  limitations=[
                      'Upper A/B PROM-to-latch and latch-to-U8 bit assignments are assumptions.',
                      'The candidate output words are ALU Y values, not measured DAC input bytes.',
                      'The controller stream is a local scrambler fixture, not a full modem call.'],
                  source_sha256={str(p.relative_to(HERE.parent)):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (Path(__file__), HERE / 'independent_slice_fields.py',
                                           HERE / 'controller_bit_dispatch.py',
                                           HERE / 'split_slice_probe.py',
                                           ASSUMED / 'common.py', ASSUMED / 'execute.py',
                                           HERE.parent / 'model.py')})
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    for case in result['cases']:
        print(case['variant'], case['q5']['actual']['output_y_by_site'],
              'q5 zero/one equal:', case['q5_zero_one_equal'],
              'differing seeds:', case.get('seed_screen', {}).get('differing_q'))
