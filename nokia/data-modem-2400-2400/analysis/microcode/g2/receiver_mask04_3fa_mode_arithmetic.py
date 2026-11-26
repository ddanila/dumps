"""Check 3FA operands and history visibility under candidate mode bytes."""

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from joint_mask04_12a_buffered_line import MAPPINGS, candidate, fixture, mapped, mapping_with_upper_source
from receiver_four_row_condition_screen import configured
from receiver_mask04_postvisit_state_history import (CASES, PRIOR, case_input,
                                                      first_visit, state_execute)

HERE = Path(__file__).resolve().parent
MODES = (0x01, 0x81, 0xA1)


def equation(state, d):
    ram = state['pre_ram']
    low_total = (d & 15) + ((~ram[10]) & 15) + state['carry']
    high_total = (d >> 4) + (ram[10] >> 4) + (low_total >> 4)
    y = (low_total & 15) | ((high_total & 15) << 4)
    expected_r13 = (ram[13] & 15) | (y & 0xF0)
    if (state['instruction'] != 0x55 or state['high_instruction'] != 0xC5 or
            (state['a'], state['b'], state['a_high'], state['b_high']) !=
            (10, 13, 10, 13) or state['y'] != y or state['f'] != y or
            state['post_ram'][13] != expected_r13 or
            any(state['post_ram'][n] != ram[n] for n in range(16) if n != 13) or
            state['post_q'] != state['pre_q']):
        raise ValueError(('3FA mode arithmetic changed', state))
    return y


def run(out=HERE / 'results/receiver-mask04-3fa-mode-arithmetic.json'):
    prior = json.loads(PRIOR.read_text())
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    execute = state_execute()
    captures = {}
    cases = []
    for seed, degrees in CASES:
        samples, adc = case_input(seed, degrees)
        for mode_byte in MODES:
            scenario = configured(base, adc, 'previous', 'overflow', 1)
            if mode_byte != 1:
                scenario['io']['read']['pc_sequences'][str(0x3EB)] = [mode_byte]
                scenario['io']['read']['evidence'] += (
                    '; assumed held controller frame byte at 3EB')
            result = execute(mapping, scenario, 32 * len(adc) + 47,
                             mode='integrated', trace_limit=0)
            states = result['selected_state'][0x3FA]
            if (not result['clean'] or len(states) != len(adc) or
                    result['read_sequence_visits'].get(0x3F8) != len(adc)):
                raise ValueError(('mode loop did not sustain', seed, mode_byte))
            if mode_byte == 1:
                old = next(c for c in prior['cases']
                           if c['seed'] == seed and c['degrees'] == degrees)
                if (result['trace_digest'] != old['trace_digest'] or
                        hashlib.sha256(bytes(adc)).hexdigest() != old['adc_sha256']):
                    raise ValueError('baseline trace changed')
            if str(0x3FA) in scenario['io']['read']['pc_sequences'] or \
                    0x3FA in scenario['io']['read']['address']['pcs'] or \
                    scenario['io']['read']['value'] != 1:
                raise ValueError('3FA D source changed')
            for state in states:
                equation(state, 1)
            captures[(seed, mode_byte)] = dict(samples=samples, states=states)
            cases.append(dict(seed=seed, degrees=degrees,
                              mode_byte=f'{mode_byte:02X}',
                              trace_digest=result['trace_digest'],
                              equations_checked=len(states),
                              distinct_y=len({s['y'] for s in states}),
                              distinct_pre_r13=len({s['pre_ram'][13] for s in states}),
                              distinct_post_r13=len({s['post_ram'][13] for s in states})))
    mode_summary = {}
    for mode_byte in MODES:
        groups = defaultdict(list)
        for seed, _ in CASES:
            capture = captures[(seed, mode_byte)]
            for sample_index, adc_byte in enumerate(capture['samples']):
                if not sample_index:
                    continue
                visit = first_visit(sample_index)
                groups[(sample_index % 8, adc_byte)].append(dict(
                    previous_adc=capture['samples'][sample_index - 1],
                    state=capture['states'][visit]))
        eligible = [rows for rows in groups.values()
                    if len(rows) >= 2 and
                    len({row['previous_adc'] for row in rows}) >= 2]
        metrics = Counter()
        witnesses = []
        for rows in eligible:
            states = [row['state'] for row in rows]
            for name, values in (
                    ('pre_r13', [s['pre_ram'][13] for s in states]),
                    ('post_r13', [s['post_ram'][13] for s in states]),
                    ('pre_r10', [s['pre_ram'][10] for s in states]),
                    ('y', [s['y'] for s in states]),
                    ('post_q', [s['post_q'] for s in states])):
                if len(set(values)) > 1:
                    metrics[name] += 1
            if len({s['pre_ram'][13] for s in states}) > 1 and len(witnesses) < 4:
                witnesses.append([dict(previous_adc=row['previous_adc'],
                                       pre_r10=row['state']['pre_ram'][10],
                                       pre_r13=row['state']['pre_ram'][13],
                                       post_r13=row['state']['post_ram'][13],
                                       y=row['state']['y'], q=row['state']['post_q'])
                                  for row in rows[:4]])
        mode_summary[f'{mode_byte:02X}'] = dict(eligible_groups=len(eligible),
                                               varying_groups=dict(metrics),
                                               witnesses=witnesses)
    versus_01 = {}
    for mode_byte in MODES[1:]:
        counts = Counter()
        for seed, _ in CASES:
            base_states = captures[(seed, 1)]['states']
            changed_states = captures[(seed, mode_byte)]['states']
            for a, b in zip(base_states, changed_states):
                for name, left, right in (
                        ('y', a['y'], b['y']),
                        ('post_q', a['post_q'], b['post_q']),
                        ('pre_r13', a['pre_ram'][13], b['pre_ram'][13]),
                        ('post_r13', a['post_ram'][13], b['post_ram'][13])):
                    counts[name] += left != right
        versus_01[f'{mode_byte:02X}'] = dict(counts)
    report = dict(experiment='3FA operand and history test under held 3EB mode bytes',
                  fixture=dict(modes=[f'{m:02X}' for m in MODES],
                               legal_carriers=[dict(seed=s, degrees=d)
                                               for s, d in CASES],
                               adc_visits_per_run=6000,
                               d3fa=1,
                               mode_route='candidate held controller byte to 3EB D'),
                  cases=cases, mode_summary=mode_summary,
                  changed_visits_vs_01=versus_01,
                  source_sha256={str(p.relative_to(HERE.parents[4])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (Path(__file__), PRIOR,
                                           HERE / 'receiver_mask04_postvisit_state_history.py',
                                           HERE.parent / 'assumed/execute.py')},
                  limitations=[
                      'The 3EB frame-byte route is a hypothesis, not a traced connection.',
                      'The equations prove this mapped 3FA does not read its B=R13 operand; they do not exclude another mode-dependent circuit.',
                      'Internal state differences are not a demonstrated USART RxD or analog residual.'
                  ])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print('modes', result['mode_summary'])
    print('versus 01', result['changed_visits_vs_01'])
