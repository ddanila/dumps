"""Reach the 3C5/3DA tables from reset under photo-constrained pin hypotheses."""

import copy
import hashlib
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
from caller_study import inspect_trace
from common import read, save
from execute import execute
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

BASE_SCENARIO = ASSUMED / 'results/rotation-study/scenario-3.json'
VALUES = (0, 1, 0x55, 0xFF)
SEEDS = tuple(range(16))
SITES = (0x3C2, 0x3D7)


def word(ram, index):
    return ram[index] | (ram[index + 1] << 8)


def transforms(source, entry):
    x, y = source
    sign = ((x, y), (x, -y & 65535), (-x & 65535, -y & 65535),
            (-x & 65535, y))
    quarter = ((x, y), (-y & 65535, x), (-x & 65535, -y & 65535),
               (y, -x & 65535))
    return sign[entry], quarter[entry]


def scenario_for(e4, value):
    scenario = copy.deepcopy(read(BASE_SCENARIO))
    scenario['name'] += f'; photo E4={e4}, E2=0, external D={value:02X}'
    scenario['io']['read']['value'] = value
    def level(bit, evidence):
        return dict(value=bit, status='hypothesis', evidence=evidence)
    e4_note = 'Candidate U11 E4 through U6 Q0 to U2 I7 and A0; held diagnostic level'
    e2_note = 'Candidate U10 E2 through U5 to U2 I0 and A1; held diagnostic level'
    scenario['inputs']['instruction_bit_overrides'] = {
        '7': level(e4, e4_note), '0': level(0, e2_note)}
    scenario['inputs']['register_address_bit_overrides'] = {'a': {
        '0': level(e4, e4_note), '1': level(0, e2_note)}}
    return scenario


def reached_calls(trace, scenario):
    calls = []
    for sample in inspect_trace(trace, scenario):
        if sample['site'] not in SITES:
            continue
        after = sample['ram_at_entry'][:]
        for row in trace[sample['cycle'] + 1:sample['cycle'] + 5]:
            for index, value in row['registers'].items():
                after[int(index)] = value
        table = scenario['dispatch']['tables'][str(sample['site'])]
        expected_pcs = list(range(sample['target'], sample['target'] + 4))
        actual_pcs = [row['pc'] for row in trace[sample['cycle'] + 1:sample['cycle'] + 5]]
        if (table['base'] not in (0x3C5, 0x3DA) or
                actual_pcs != expected_pcs):
            raise ValueError('reached call does not execute a four-word table entry')
        before = sample['ram_at_entry']
        calls.append(dict(cycle=sample['cycle'], site=f'{sample["site"]:03X}',
                          entry=sample['entry'], target=f'{sample["target"]:03X}',
                          q=sample['q_at_entry'],
                          source=[word(before, 4), word(before, 8)],
                          output_before=[word(before, 10), word(before, 12)],
                          output_after=[word(after, 10), word(after, 12)]))
    return calls


def run(out=HERE / 'results/photo-table-callers.json'):
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        temporary = Path(temporary)
        for name, path in MAPPINGS.items():
            mapping = mapped(path)
            for e4 in (0, 1):
                observations = []
                clean_runs = 0
                for value in VALUES:
                    scenario = scenario_for(e4, value)
                    for seed in SEEDS:
                        result = execute(mapping, scenario, 1000, seed=seed,
                                         mode='integrated', out=temporary,
                                         trace_limit=1000)
                        if not result['clean']:
                            raise ValueError(f'{name} E4={e4} D={value:02X} seed={seed} stopped')
                        clean_runs += 1
                        trace = [json.loads(line) for line in
                                 (temporary / 'trace.jsonl').read_text().splitlines()]
                        observations.extend(dict(d=value, seed=seed, **call)
                                            for call in reached_calls(trace, scenario))
                cases.append(dict(mapping=name, e4=e4, e2=0, runs=clean_runs,
                                  calls=len(observations),
                                  calls_by_site=dict(Counter(x['site'] for x in observations)),
                                  selected_entries=sorted({x['entry'] for x in observations}),
                                  nonzero_source_calls=sum(any(x['source']) for x in observations),
                                  nonzero_q_calls=sum(x['q'] != 0 for x in observations),
                                  changed_output_calls=sum(x['output_after'] != x['output_before']
                                                           for x in observations),
                                  sign_matches_nonzero=sum(
                                      tuple(x['output_after']) == transforms(x['source'], x['entry'])[0]
                                      for x in observations if any(x['source'])),
                                  quarter_turn_matches_nonzero=sum(
                                      tuple(x['output_after']) == transforms(x['source'], x['entry'])[1]
                                      for x in observations if any(x['source'])),
                                  observations=observations))
    source_paths = [Path(__file__), BASE_SCENARIO,
                    ASSUMED / 'caller_study.py', ASSUMED / 'execute.py',
                    HERE / 'photo_mapping_q_sweep.py',
                    HERE / 'photo_mapping_stream_screen.py', *MAPPINGS.values()]
    report = dict(status='reset-path caller experiment under photo-based hypotheses',
                  fixture=dict(external_d=list(VALUES), seeds=list(SEEDS), cycles=1000,
                               initial_ram=[0]*16,
                               dispatch='saved rotation-study scenario; indices are scenario-driven',
                               pin_levels='E4=I7=A0; E2=I0=A1=0, held for each run'),
                  cases=cases,
                  limitations=[
                      'Photo routes and held latch levels are unverified hypotheses.',
                      'External D is a constant stub per run, not the controller bitstream.',
                      'Dispatch indices and branch conditions are from the saved scenario, not recovered physical wiring.',
                      'The model shares instruction controls across both Am2901 slices.',
                      'R10/R12 are register outputs, not traced DAC samples.'],
                  source_sha256={str(p.relative_to(HERE.parent)):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in source_paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    for case in report['cases']:
        print(case['mapping'], case['e4'], case['calls'],
              case['nonzero_source_calls'], case['changed_output_calls'])
