"""Screen recurring, actually selected D inputs for retained sample effects."""

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
from adc_sample_path import DIBITS
from controller_bit_dispatch import controller_stream
from independent_slice_d38c import state_after_loop
from independent_slice_fields import candidate_mapping
from photo_controller_path import fixture
from reference_modem import receive, transmit
from split_slice_probe import split_scenario

KINDS = ('separated', 'separated_reversed_upper')
CYCLES = 1580
INPUT_PC = 0x38E
OUTPUT_PCS = range(0x392, 0x3A0)


def run_trace(mapping, base, controller_bits, directory, site=None, values=None):
    scenario = split_scenario(base)
    scenario['initial']['q'] = 5
    scenario['io']['read']['pc_sequences'][str(INPUT_PC)] = controller_bits
    if site is not None:
        if site in scenario['io']['read']['address']['pcs']:
            scenario['io']['read']['address']['pcs'].remove(site)
        scenario['io']['read']['pc_sequences'][str(site)] = values
        scenario['io']['read']['evidence'] = (
            f'Diagnostic sample-byte stream at PC {site:03X}; ADC route, '
            'source switching and timing untraced')
    result = execute(mapping, scenario, CYCLES, mode='integrated',
                     out=directory, trace_limit=CYCLES)
    trace = [json.loads(line) for line in (directory / 'trace.jsonl').read_text().splitlines()]
    snapshots = state_after_loop(trace, scenario['initial']['ram'])[0]
    outputs = [(row['pc'], row['alu']['y']) for row in trace
               if row['pc'] in OUTPUT_PCS]
    input_rows = [row for row in trace if row['pc'] == INPUT_PC]
    return dict(clean=result['clean'], trace=trace, snapshots=snapshots,
                outputs=outputs, input_visits=len(input_rows),
                d38e_selected=sum(row['external_read']['selected_by_alu']
                                  for row in input_rows),
                trace_digest=result['trace_digest'])


def run(out=HERE / 'results/independent-slice-input-sites.json'):
    pcm = transmit(DIBITS)
    if receive(pcm) != DIBITS[1:]:
        raise ValueError('reference modem check failed')
    signal = pcm[:128]
    adc = [127 - sample for sample in signal]
    inverted = [128 + sample for sample in signal]
    stimuli = dict(zero=[0] * 128,
                   adc=adc, adc_reversed=adc[::-1],
                   inverted=inverted, inverted_reversed=inverted[::-1],
                   impulse=[0] * 20 + [255] + [0] * 107)
    _, base = fixture()
    _, controller_bits = controller_stream()
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        for kind in KINDS:
            mapping = candidate_mapping(kind)
            baseline = run_trace(mapping, base, controller_bits, directory)
            first_input = next(row['cycle'] for row in baseline['trace']
                               if row['pc'] == INPUT_PC)
            sites = sorted({row['pc'] for row in baseline['trace']
                            if row['cycle'] > first_input and
                            0x389 <= row['pc'] <= 0x3A1 and
                            row.get('external_read', {}).get('selected_by_alu')})
            expected = ([0x38C, 0x38D, 0x38E] if kind == 'separated' else
                        [0x38B, 0x38C, 0x38D, 0x39F, 0x3A1])
            if sites != expected:
                raise ValueError('dynamic D-selected site set changed')
            for site in sites:
                witness = next(row for row in baseline['trace']
                               if row['cycle'] > first_input and row['pc'] == site)
                runs = {}
                control = None
                for name, values in stimuli.items():
                    case = run_trace(mapping, base, controller_bits, directory,
                                     site, values)
                    site_rows = [row for row in case['trace'] if row['pc'] == site]
                    if (not case['clean'] or len(case['trace']) != CYCLES or
                            len(case['snapshots']) != 128 or len(site_rows) != 128 or
                            not all(row['external_read']['selected_by_alu']
                                    for row in site_rows)):
                        raise ValueError('sample-site fixture changed')
                    if control is None:
                        control = case
                    if len(case['outputs']) != len(control['outputs']):
                        raise ValueError('candidate output visit count changed')
                    differing_boundaries = [index for index, (a, b) in
                                            enumerate(zip(control['snapshots'],
                                                          case['snapshots'])) if a != b]
                    differing_outputs = sum(a != b for a, b in
                                            zip(control['outputs'], case['outputs']))
                    runs[name] = dict(distinct_offered_bytes=len(set(values)),
                                      selected_site_visits=len(site_rows),
                                      d38e_alu_selections=case['d38e_selected'],
                                      differing_boundaries=len(differing_boundaries),
                                      first_differing_boundaries=differing_boundaries[:12],
                                      differing_candidate_output_events=differing_outputs,
                                      trace_digest=case['trace_digest'])
                cases.append(dict(mapping=kind, site=f'{site:03X}',
                                  low_source=witness['instruction_i'] & 7,
                                  high_source=witness['instruction_i_high'] & 7,
                                  runs=runs))
    if len(cases) != 8:
        raise ValueError('site screen incomplete')
    for case in cases:
        retained = (case['mapping'], case['site'])
        expected = 108 if retained == ('separated', '38E') else (
            110 if retained == ('separated_reversed_upper', '3A1') else 0)
        if (case['runs']['adc']['differing_boundaries'] != expected or
                case['runs']['impulse']['first_differing_boundaries'] !=
                ([20] if expected else []) or
                any(run['differing_candidate_output_events'] for run in
                    case['runs'].values())):
            raise ValueError('D-site retention/output conclusion changed')
    paths = [Path(__file__), HERE / 'independent_slice_d38c.py',
             HERE / 'independent_slice_fields.py', HERE / 'adc_sample_path.py',
             HERE / 'reference_modem.py', HERE / 'controller_bit_dispatch.py',
             HERE / 'photo_controller_path.py', HERE / 'split_slice_probe.py',
             ASSUMED / 'execute.py', ASSUMED / 'common.py', HERE.parent / 'model.py']
    report = dict(status='diagnostic independent-slice D-input site screen',
                  fixture=dict(mappings=list(KINDS), cycles=CYCLES,
                               initial_q=5, controller_bits=len(controller_bits),
                               reference_samples=128,
                               sample_site='each recurring word with an executed D source',
                               boundary='3A1 after each 12-word loop',
                               candidate_outputs='392–39F ALU Y events'),
                  cases=cases,
                  limitations=[
                      'Every D-site assignment, ADC byte range, clock, branch table and PROM-to-slice field is hypothetical.',
                      'When the tested site is 38E, reference samples replace the controller bits rather than coexisting with them.',
                      'A D38E visit is not an ALU consumption in the reversed-upper layout.',
                      'Boundary-state changes alone do not establish recovered bits, a line output or echo cancellation.'],
                  source_sha256={str(path.relative_to(HERE.parent)):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    for case in report['cases']:
        print(case['mapping'], case['site'],
              case['runs']['adc']['differing_boundaries'],
              case['runs']['impulse']['first_differing_boundaries'],
              case['runs']['adc']['differing_candidate_output_events'])
