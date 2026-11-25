"""Test independent upper-slice PROM instruction candidates."""

import copy
import hashlib
import json
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
from common import save
from execute import execute
from controller_bit_dispatch import controller_stream
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from split_slice_probe import split_scenario


def translate(token, lanes, reverse=False):
    sign = '!' if token.startswith('!') else ''
    chip, bit = token.lstrip('!').split('.')
    chip = lanes.get(chip, chip)
    bit = 7 - int(bit) if reverse else int(bit)
    return f'{sign}{chip}.{bit}'


def candidate_mapping(kind):
    mapping = mapped(MAPPINGS['q3'])
    mapping['name'] += f'-{kind}-independent-upper-instruction'
    original = mapping['fields']['i']['bits'][:]
    if kind == 'shared':
        return mapping
    if kind.startswith('separated'):
        mapping['fields']['i']['bits'] = [translate(token, {'17': '10', '18': '11'})
                                         for token in original]
        mapping['fields']['i']['status'] = 'hypothesis'
        mapping['fields']['i']['evidence'] = (
            'Diagnostic U10/U11-to-U2 lower-slice bundle; individual data order untraced')
    upper = [translate(token, {'10': '17', '11': '18'},
                       reverse=kind == 'separated_reversed_upper')
             for token in original]
    mapping['fields']['i_high'] = dict(bits=upper, status='hypothesis',
                                      evidence='Diagnostic U17/U18-to-U8 upper-slice bundle; '
                                               'individual pins and bit order untraced; '
                                               'U8 I4/I6 crosslinks supplied by scenario')
    return mapping


def stream_run(mapping, scenario, q, bits, directory, stimulus):
    case = copy.deepcopy(scenario)
    case['initial']['q'] = q
    case['io']['read']['pc_sequences']['910'] = bits
    result = execute(mapping, case, 1580, mode='integrated',
                     out=directory, trace_limit=1580)
    trace = [json.loads(line) for line in (directory / 'trace.jsonl').read_text().splitlines()]
    inputs = [row for row in trace if row['pc'] == 0x38E]
    first = inputs[0]['cycle'] if inputs else len(trace)
    rom_all = [row for row in trace if
               row.get('external_read', {}).get('selected_by_alu') and
               'address' in row['external_read']]
    rom = [row for row in trace if row['cycle'] > first and
           row.get('external_read', {}).get('selected_by_alu') and
           'address' in row['external_read']]
    sites = defaultdict(set)
    for row in trace:
        if row['cycle'] > first and 0x392 <= row['pc'] <= 0x39F:
            sites[f"{row['pc']:03X}"].add(row['alu']['y'])
    dispatches = [row for row in trace if row['pc'] == 0x38F]
    return dict(q=q, stimulus=stimulus, clean=result['clean'], completed_cycles=len(trace),
                input_visits=len(inputs),
                offered_bits_advanced=sum(not row['external_read']['held_last']
                                          for row in inputs),
                controller_bits_selected_by_alu=sum(
                    row['external_read']['selected_by_alu'] for row in inputs),
                selected_rom_reads_after_input=len(rom),
                selected_rom_reads_total=len(rom_all),
                rom_addresses=sorted({row['external_read']['address'] for row in rom_all}),
                distinct_rom_addresses_after_input=len({row['external_read']['address']
                                                        for row in rom}),
                output_y_by_site={site: sorted(values) for site, values in sites.items()},
                variable_output_sites={site: sorted(values) for site, values in sites.items()
                                       if len(values) > 1},
                reached_output_sites=sorted(sites),
                q_at_38f=sorted({row['q'] for row in dispatches}),
                final_pc=f"{result['final_state']['pc']:03X}",
                register_changes=result['register_changes'],
                trace_digest=result['trace_digest'])


def run(out=HERE / 'results/independent-slice-fields.json'):
    _, base = fixture()
    scenario = split_scenario(base)
    _, bits = controller_stream()
    kinds = ('shared', 'upper_pair', 'separated', 'separated_reversed_upper')
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        for kind in kinds:
            mapping = candidate_mapping(kind)
            sweep = []
            for q in range(256):
                state = copy.deepcopy(scenario)
                state['initial']['q'] = q
                state['io']['read']['pc_sequences']['910'] = bits
                result = execute(mapping, state, 512, mode='integrated', trace_limit=0)
                sweep.append(dict(q=q, clean=result['clean'],
                                  input_visits=result['address_counts'].get(0x38E, 0),
                                  selected_rom_reads=result['rom_reads']['selected_by_alu'],
                                  output_visits=sum(result['address_counts'].get(pc, 0)
                                                    for pc in range(0x392, 0x3A0)),
                                  final_pc=f"{result['final_state']['pc']:03X}"))
            best = max(sweep, key=lambda row:
                       (row['selected_rom_reads'], row['input_visits'], row['output_visits']))
            stream_qs = sorted({0, 5, best['q']})
            streams = [stream_run(mapping, scenario, q, bits,
                                  directory / f'{kind}-q{q}-actual', 'actual')
                       for q in stream_qs]
            for stimulus, offered in (('zero', [0] * len(bits)),
                                      ('one', [1] * len(bits))):
                streams.append(stream_run(mapping, scenario, 5, offered,
                                          directory / f'{kind}-q5-{stimulus}', stimulus))
            if kind.startswith('separated'):
                active = [row for row in streams if row['q'] == 5]
                if (len(active) != 3 or
                        any(row['input_visits'] != 128 or
                            row['selected_rom_reads_after_input'] != 127 or
                            row['distinct_rom_addresses_after_input'] != 1 or
                            row['output_y_by_site'] != {'39E': [11], '39F': [11]}
                            for row in active) or
                        any(row['controller_bits_selected_by_alu'] !=
                            (0 if kind == 'separated_reversed_upper' else 128)
                            for row in active)):
                    raise ValueError('independent-slice controller result changed')
            cases.append(dict(kind=kind, low_i=mapping['fields']['i']['bits'],
                              high_i=mapping['fields'].get('i_high', {}).get('bits'),
                              clean_seed_runs=sum(row['clean'] for row in sweep),
                              seed_input_runs=sum(bool(row['input_visits']) for row in sweep),
                              max_selected_rom_reads=max(row['selected_rom_reads']
                                                         for row in sweep),
                              best_seed=best, streams=streams))
    report = dict(status='diagnostic independent upper-slice field screen',
                  fixture=dict(mappings=list(kinds), cycles_per_seed=512,
                               seed_values='all 256 Q bytes', stream_cycles=1580,
                               stream_seed_selection='Q=0, Q=5 and maximum selected ROM reads',
                               controller_bits=len(bits),
                               high_links={'4': 1, '6': 2},
                               control='saved photo-controller-path scenario',
                               note='A/B, clock and physical PROM-to-latch order remain hypotheses'),
                  cases=cases,
                  limitations=[
                      'Lane ownership and bit order are photo-inspired hypotheses, not traced connections.',
                      'Upper I4 and I6 are overwritten from lower I1 and I2 per the candidate facing-pad tracks.',
                      'Other fields, input route, branch/ROM timing and output latch remain untraced.',
                      'The controller stimulus is a local 128-bit scrambler stream, not a full modem call.'],
                  source_sha256={str(path.relative_to(HERE.parent)):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in [Path(__file__), MAPPINGS['q3'],
                                              HERE / 'photo_mapping_q_sweep.py',
                                              HERE / 'photo_mapping_stream_screen.py',
                                              HERE / 'photo_controller_path.py',
                                              HERE / 'split_slice_probe.py',
                                              HERE / 'controller_bit_dispatch.py',
                                              ASSUMED / 'execute.py',
                                              ASSUMED / 'common.py',
                                              HERE.parent / 'model.py']})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    for case in report['cases']:
        print(case['kind'], case['clean_seed_runs'], case['seed_input_runs'],
              case['max_selected_rom_reads'],
              [(run['q'], run['input_visits'], run['selected_rom_reads_after_input'],
                run['variable_output_sites']) for run in case['streams']])
