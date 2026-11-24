"""Compare shared and photo-candidate split Am2901 controls at reached tables."""

import hashlib
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSUMED = HERE.parent / 'assumed'
sys.path[:0] = [str(ASSUMED), str(HERE)]
from common import save
from execute import execute
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from photo_table_callers import reached_calls, scenario_for, transforms
from split_slice_probe import split_scenario

VALUES = (0, 1, 0x55, 0xFF)
SEEDS = (11, 14)  # The only reached-call seeds in the full prior 0–15 sweep.


def ripple_flags(scenario):
    scenario['inputs']['logic_flags'] = dict(
        mode='am2901b-ripple', status='hypothesis',
        evidence='Same explicit Am2901B flag model required by split-slice runner')
    return scenario


def run(out=HERE / 'results/photo-split-callers.json'):
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        for name, path in MAPPINGS.items():
            mapping = mapped(path)
            for value in VALUES:
                for seed in SEEDS:
                    variants = {}
                    for control in ('shared', 'split0', 'split1'):
                        scenario = ripple_flags(scenario_for(1, value))
                        if control != 'shared':
                            scenario = split_scenario(scenario, int(control[-1]))
                        result = execute(mapping, scenario, 1000, seed=seed,
                                         mode='integrated', out=Path(temporary),
                                         trace_limit=1000)
                        if not result['clean']:
                            raise ValueError(f'{name} D={value:02X} seed={seed} {control} stopped')
                        trace = [json.loads(line) for line in
                                 (Path(temporary) / 'trace.jsonl').read_text().splitlines()]
                        calls = [
                            {key: call[key] for key in
                             ('cycle', 'site', 'entry', 'q', 'source',
                              'output_before', 'output_after')}
                            for call in reached_calls(trace, scenario)]
                        variants[control] = dict(
                            final_pc=f'{result["final_state"]["pc"]:03X}',
                            undriven_shift_reads=result.get('undriven_shift_reads', 0),
                            trace_digest=result['trace_digest'], calls=calls)
                    sites = [[(x['site'], x['entry'], x['cycle']) for x in variants[k]['calls']]
                             for k in variants]
                    cases.append(dict(mapping=name, d=value, seed=seed,
                                      same_call_sites_and_cycles=sites[0] == sites[1] == sites[2],
                                      split_fallback_equivalent=(
                                          variants['split0']['trace_digest'] ==
                                          variants['split1']['trace_digest']),
                                      variants=variants))
    summary = {}
    for name in MAPPINGS:
        selected = [c for c in cases if c['mapping'] == name]
        by_control = {}
        for control in ('shared', 'split0', 'split1'):
            calls = [x for c in selected for x in c['variants'][control]['calls']]
            nonzero = [x for x in calls if any(x['source'])]
            by_control[control] = dict(
                calls=len(calls), nonzero_source_calls=len(nonzero),
                changed_output_calls=sum(x['output_before'] != x['output_after'] for x in calls),
                sign_matches_nonzero=sum(
                    tuple(x['output_after']) == transforms(x['source'], x['entry'])[0]
                    for x in nonzero),
                quarter_turn_matches_nonzero=sum(
                    tuple(x['output_after']) == transforms(x['source'], x['entry'])[1]
                    for x in nonzero),
                final_pcs=dict(Counter(c['variants'][control]['final_pc'] for c in selected)),
                undriven_shift_reads=sum(c['variants'][control]['undriven_shift_reads']
                                         for c in selected))
        summary[name] = by_control
    paths = [Path(__file__), HERE / 'photo_table_callers.py',
             HERE / 'split_slice_probe.py', HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             HERE / 'results/photo-slice-link.json',
             ASSUMED / 'results/rotation-study/scenario-3.json',
             ASSUMED / 'execute.py', HERE.parent / 'model.py', *MAPPINGS.values()]
    report = dict(status='photo-candidate split-slice comparison at reached reset calls',
                  fixture=dict(seeds=list(SEEDS), external_d=list(VALUES), e4=1, e2=0,
                               cycles=1000, start_pc=0, initial_ram=[0]*16,
                               branch_dispatch='saved rotation-study scenario'),
                  summary=summary, cases=cases,
                  limitations=[
                      'The U8/U2 facing-pad links have pad gaps; they are wiring candidates.',
                      'Branch conditions and dispatch indices are scenario-driven; external D is constant per run.',
                      'The calls are confined to a reset prefix that ends at 084, not a continuous controller stream.',
                      'Output registers are not a traced DAC input.'],
                  source_sha256={str(p.relative_to(HERE.parent)):
                                 hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    for name, controls in report['summary'].items():
        print(name, {k: (v['calls'], v['nonzero_source_calls'],
                         v['changed_output_calls']) for k, v in controls.items()})
