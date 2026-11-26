"""Test a delayed external-RAM return on legal receive carriers."""

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from joint_mask04_12a_buffered_line import MAPPINGS, candidate, fixture, mapped, mapping_with_upper_source
from joint_upper_ram_feedback_screen import instrumented_execute
from receiver_four_row_condition_screen import configured
from receiver_mask04_postvisit_state_history import CASES, case_input, first_visit

HERE = Path(__file__).resolve().parent
ROUTES = (('read_only', True, False), ('write_only', False, True),
          ('high_return_3fa', True, True))
SAMPLES = 128
VISITS = SAMPLES * 375 // 8
CYCLES = 32 * VISITS + 47


def scenario_for(base, adc, feedback, write):
    scenario = configured(base, adc, 'previous', 'carry', 1)
    scenario.update(external_ram_feedback=feedback,
                    external_ram_write=write,
                    external_ram_lane='high',
                    external_ram_latch_pc=0x3F9,
                    external_ram_read_pc=0x3FA,
                    external_ram_read_offset=-3,
                    external_ram_address_tick_visits=[4 * first_visit(sample)
                                                      for sample in range(SAMPLES)])
    return scenario


def matched_groups(captures, route):
    grouped = defaultdict(list)
    for seed, _ in CASES:
        case = captures[(seed, route)]
        for sample_index, adc_byte in enumerate(case['samples']):
            if not sample_index:
                continue
            grouped[(sample_index % 8, adc_byte)].append(dict(
                previous_adc=case['samples'][sample_index - 1],
                y3fa=case['y3fa'][first_visit(sample_index)]))
    eligible = [rows for rows in grouped.values()
                if len(rows) >= 2 and
                len({row['previous_adc'] for row in rows}) >= 2]
    varying = [rows for rows in eligible
               if len({row['y3fa'] for row in rows}) > 1]
    return dict(eligible_groups=len(eligible),
                groups_with_different_y3fa=len(varying),
                witnesses=[[dict(previous_adc=row['previous_adc'],
                                 y3fa=row['y3fa']) for row in rows[:4]]
                           for rows in varying[:6]])


def run(out=HERE / 'results/receiver-mask04-legal-ram-return.json'):
    execute = instrumented_execute()
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    captures = {}
    cases = []
    for seed, degrees in CASES:
        samples, full_adc = case_input(seed, degrees)
        samples = samples[:SAMPLES]
        adc = full_adc[:VISITS]
        if len(adc) != VISITS:
            raise ValueError('sample/visit window changed')
        for route, feedback, write in ROUTES:
            result = execute(mapping, scenario_for(base, adc, feedback, write),
                             CYCLES, mode='integrated', trace_limit=0)
            memory = result['external_ram_candidate']
            y3fa = memory['y_by_pc'][0x3FA]
            if (not result['clean'] or result['completed_cycles'] != CYCLES or
                    result['address_counts'].get(0x3F8) != VISITS or
                    len(y3fa) != VISITS):
                raise ValueError(('legal RAM return stopped', seed, route))
            captures[(seed, route)] = dict(samples=samples, y3fa=y3fa,
                                           trace_digest=result['trace_digest'])
            cases.append(dict(seed=seed, degrees=degrees, route=route,
                              adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                              trace_digest=result['trace_digest'],
                              y3fa_sha256=hashlib.sha256(bytes(y3fa)).hexdigest(),
                              writes=memory['writes'], reads=memory['reads'],
                              first_changed_read=memory['first_changed_read'],
                              distinct_y3fa=len(set(y3fa))))
    contrasts = []
    for seed, degrees in CASES:
        baseline = captures[(seed, 'write_only')]['y3fa']
        read_only = captures[(seed, 'read_only')]['y3fa']
        feedback = captures[(seed, 'high_return_3fa')]['y3fa']
        contrasts.append(dict(seed=seed, degrees=degrees,
                              read_only_vs_write_only=sum(a != b for a, b in
                                                           zip(read_only, baseline)),
                              feedback_vs_write_only=sum(a != b for a, b in
                                                          zip(feedback, baseline)),
                              feedback_vs_read_only=sum(a != b for a, b in
                                                         zip(feedback, read_only)),
                              first_feedback_change=next((i for i, (a, b) in
                                                          enumerate(zip(feedback, baseline))
                                                          if a != b), None)))
    matched = {route: matched_groups(captures, route)
               for route, _, _ in ROUTES}
    report = dict(experiment='legal-carrier delayed high-nibble MCM93422 return at 3FA',
                  fixture=dict(cases=[dict(seed=s, degrees=d) for s, d in CASES],
                               samples=SAMPLES, visits=VISITS, cycles=CYCLES,
                               ram='3F9 Y high -> sample-paced external RAM -> 3FA D high, -3 address offset',
                               test_source='previous carry, polarity 1',
                               matched_on='exact ADC byte and sample position with different previous ADC byte'),
                  cases=cases, contrasts=contrasts, matched_groups=matched,
                  source_sha256={str(p.relative_to(HERE.parents[4])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (Path(__file__),
                                           HERE / 'joint_upper_ram_feedback_screen.py',
                                           HERE / 'receiver_mask04_postvisit_state_history.py',
                                           HERE.parent / 'assumed/execute.py')},
                  limitations=[
                      'External RAM address, write gate, Y latch, return mux and TEST selection are assumed.',
                      'A varying 3FA Y is not a recovered bit or echo-cancelled line residual.',
                      'Only the first 128 samples of two legal carriers are challenged.'
                  ])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print('contrasts', result['contrasts'])
    print('matched', {k: (v['eligible_groups'],
                         v['groups_with_different_y3fa'])
                      for k, v in result['matched_groups'].items()})
