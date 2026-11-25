"""Screen initial Q seeds for persistent response to a candidate ADC impulse."""

import copy
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
from independent_slice_addresses import mapping_for
from independent_slice_d38c import state_after_loop
from independent_slice_fields import candidate_mapping
from photo_controller_path import fixture
from photo_mapping_stream_screen import MAPPINGS
from split_slice_probe import split_scenario

CYCLES = 1024
IMPULSE_VISIT = 20
VALUES = (1, 16, 64, 128, 255)
ROM = HERE.parents[2] / 'am27s31dc-prom/nokia-modem-am27s31dc.bin'
LAYOUTS = (('separated', candidate_mapping('separated'), 0x38E),
           ('reversed_upper', candidate_mapping('separated_reversed_upper'), 0x3A1),
           ('upper_b', mapping_for('b'), 0x38E))


def scenario_for(base, controller_bits, site, q, value):
    scenario = split_scenario(base)
    scenario['initial']['q'] = q
    scenario['io']['read']['pc_sequences'][str(0x38E)] = controller_bits
    if site in scenario['io']['read']['address']['pcs']:
        scenario['io']['read']['address']['pcs'].remove(site)
    scenario['io']['read']['pc_sequences'][str(site)] = (
        [0] * IMPULSE_VISIT + [value] + [0] * 107)
    scenario['io']['read']['evidence'] += (
        f'; diagnostic ADC-like D input at {site:03X}, with assumed source and timing')
    return scenario


def witness(mapping, base, bits, site, value):
    traces = []
    digests = []
    for offered in (0, value):
        scenario = scenario_for(base, bits, site, 5, offered)
        with tempfile.TemporaryDirectory() as temporary:
            result = execute(mapping, scenario, CYCLES, mode='integrated',
                             out=temporary, trace_limit=CYCLES)
            trace = [json.loads(line) for line in
                     (Path(temporary) / 'trace.jsonl').read_text().splitlines()]
        if not result['clean'] or len(trace) != CYCLES:
            raise ValueError('Q=5 witness stopped')
        traces.append(trace)
        digests.append(result['trace_digest'])
    site_rows = [[row for row in trace if row['pc'] == site]
                 for trace in traces]
    if (len(site_rows[0]) < IMPULSE_VISIT + 3 or
            [row['external_read']['value'] for row in site_rows[1]][:IMPULSE_VISIT+1]
            != [0] * IMPULSE_VISIT + [value] or
            not site_rows[1][IMPULSE_VISIT]['external_read']['selected_by_alu']):
        raise ValueError('candidate impulse was not selected')
    snapshots = [state_after_loop(trace, base['initial']['ram'])[0]
                 for trace in traces]
    differences = [index for index, (a, b) in
                   enumerate(zip(*snapshots)) if a != b]
    return dict(q=5, site=f'{site:03X}', impulse=value,
                site_visits=len(site_rows[1]),
                selected_impulse_cycle=site_rows[1][IMPULSE_VISIT]['cycle'],
                differing_loop_boundaries=differences,
                baseline_trace_digest=digests[0], impulse_trace_digest=digests[1])


def run(out=HERE / 'results/receiver-seed-retention.json'):
    _, base = fixture()
    _, controller_bits = controller_stream()
    cases = []
    for name, mapping, site in LAYOUTS:
        reached = []
        retained_by_value = {f'{value:02X}': [] for value in VALUES}
        visit_counts = {}
        for q in range(256):
            impulse = scenario_for(base, controller_bits, site, q, 255)
            test = execute(mapping, impulse, CYCLES, mode='integrated', trace_limit=0)
            if not test['clean']:
                raise ValueError(f'{name} Q={q}: model stopped')
            visits = test['address_counts'].get(site, 0)
            if visits < IMPULSE_VISIT + 3:
                continue
            reached.append(q)
            visit_counts[q] = visits
            control = scenario_for(base, controller_bits, site, q, 0)
            baseline = execute(mapping, control, CYCLES, mode='integrated',
                               trace_limit=0)
            if not baseline['clean'] or baseline['address_counts'].get(site, 0) != visits:
                raise ValueError(f'{name} Q={q}: baseline path differs')
            if test['final_state'] != baseline['final_state']:
                retained_by_value['FF'].append(q)
            for value in VALUES[:-1]:
                alternative = scenario_for(base, controller_bits, site, q, value)
                result = execute(mapping, alternative, CYCLES, mode='integrated',
                                 trace_limit=0)
                if not result['clean'] or result['address_counts'].get(site, 0) != visits:
                    raise ValueError(f'{name} Q={q} D={value}: path differs')
                if result['final_state'] != baseline['final_state']:
                    retained_by_value[f'{value:02X}'].append(q)
        if not reached:
            raise ValueError(f'{name}: no Q seed reached the candidate input')
        cases.append(dict(layout=name, mapping=mapping['name'],
                          selected_input_site=f'{site:03X}', q_seeds_tested=256,
                          q_seeds_with_at_least_23_visits=reached,
                          site_visits_by_reached_seed={str(q): visit_counts[q]
                                                       for q in reached},
                          retained_final_states_by_impulse=retained_by_value,
                          q5_witness=witness(mapping, base, controller_bits,
                                             site, 255)))
    sources = [Path(__file__), HERE / 'independent_slice_d38c.py',
               HERE / 'independent_slice_fields.py',
               HERE / 'independent_slice_addresses.py',
               HERE / 'photo_controller_path.py', HERE / 'split_slice_probe.py',
               HERE / 'controller_bit_dispatch.py',
               ASSUMED / 'execute.py', HERE.parent / 'model.py',
               MAPPINGS['q3'], ROM]
    report = dict(status='bounded ADC-impulse retention screen, not a receiver proof',
                  fixture=dict(cycles=CYCLES, impulse_visit=IMPULSE_VISIT,
                               impulses=list(VALUES), initial_ram=[0] * 16,
                               q_seed_domain=list(range(256)),
                               state_compared='full modeled final_state at cycle 1024'),
                  cases=cases,
                  limitations=[
                      'The candidate ADC site, byte polarity, PROM fields, branch timing and controller interface are assumptions.',
                      'Only one impulse visit and five byte values are tested, at one cycle horizon.',
                      'Final-state convergence does not rule out transient output or other paths.',
                      'No recovered bit or echo residual is produced.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in sources})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    for case in report['cases']:
        print(case['layout'], len(case['q_seeds_with_at_least_23_visits']),
              case['q5_witness']['differing_loop_boundaries'])
