"""Find history-dependent state under matched ADC bytes and sample phase."""

import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from joint_mask04_12a_buffered_line import MAPPINGS, candidate, fixture, mapped, mapping_with_upper_source
from lower_i_d3f8_full_adc import LONG_SAMPLES, SAMPLE_START
from receiver_four_row_condition_screen import configured
from receiver_mask04_carrier_phase_screen import rotated_transmit
from reference_modem import receive

HERE = Path(__file__).resolve().parent
EXECUTE = HERE.parent / 'assumed/execute.py'
PRIOR = HERE / 'results/receiver-mask04-3f9-3fa-feature-screen.json'
SITES = (0x3F9, 0x3FA, 0x3FE)
CASES = ((0x5A17, 45), (0x76A5, 135))
VISITS_PER_SYMBOL = 375


def state_execute():
    source = EXECUTE.read_text()
    patches = (
        ("    trace_count=0;io_count=0;dispatch_counts=Counter();register_changes=0",
         "    trace_count=0;io_count=0;dispatch_counts=Counter();register_changes=0\n"
         "    selected_state={0x3F9:[],0x3FA:[],0x3FE:[]}"),
        ("            carry_input.observe(result)",
         "            if pc in selected_state:\n"
         "                selected_state[pc].append(dict(pre_ram=old_ram,post_ram=tuple(cpu.ram),pre_q=old_q,post_q=cpu.q,y=result['y'],f=result['f'],rom_address=read_event.get('address') if read_event else None,rom_value=read_event.get('value') if read_event else None,instruction=instruction,high_instruction=high_instruction,a=register_address['a'],b=register_address['b'],a_high=register_address.get('a_high'),b_high=register_address.get('b_high'),carry=carry))\n"
         "            carry_input.observe(result)"),
        ("    if source_read['mode']=='pc_sequence':summary['read_sequence_visits']=dict(sequence_visits)",
         "    summary['selected_state']=selected_state\n"
         "    if source_read['mode']=='pc_sequence':summary['read_sequence_visits']=dict(sequence_visits)"),
    )
    for old, new in patches:
        if source.count(old) != 1:
            raise ValueError(('emulator injection moved', old))
        source = source.replace(old, new)
    scope = {'__name__': 'receiver_mask04_state_instrumented',
             '__file__': str(EXECUTE)}
    exec(compile(source, str(EXECUTE), 'exec'), scope)
    return scope['execute']


def case_input(seed, degrees):
    rng = random.Random(seed)
    middle = [rng.randrange(4) for _ in range(16)]
    dibits = [0] * 8 + middle + [0] * 8
    pcm = rotated_transmit(dibits, degrees)
    if receive(pcm) != dibits[1:]:
        raise ValueError('legal reference carrier lost symbols')
    samples = [127 - value for value in
               pcm[SAMPLE_START:SAMPLE_START + LONG_SAMPLES]]
    adc = [value for index, value in enumerate(samples)
           for _ in range(47 if index % 8 < 7 else 46)]
    if len(adc) != 6000:
        raise ValueError('ADC hold schedule changed')
    return samples, adc


def first_visit(sample_index):
    return sample_index // 8 * VISITS_PER_SYMBOL + sample_index % 8 * 47


def run(out=HERE / 'results/receiver-mask04-postvisit-state-history.json'):
    prior = json.loads(PRIOR.read_text())
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    execute = state_execute()
    captures = []
    for seed, degrees in CASES:
        samples, adc = case_input(seed, degrees)
        result = execute(mapping, configured(base, adc, 'previous', 'overflow', 1),
                         32 * len(adc) + 47, mode='integrated', trace_limit=0)
        old = next(c for c in prior['cases']
                   if c['seed'] == seed and c['degrees'] == degrees)
        if (not result['clean'] or result['trace_digest'] != old['trace_digest'] or
                hashlib.sha256(bytes(adc)).hexdigest() != old['adc_sha256'] or
                any(len(result['selected_state'][pc]) != len(adc)
                    for pc in SITES)):
            raise ValueError('matched legal receive trace changed')
        captures.append(dict(seed=seed, degrees=degrees,
                             trace_digest=result['trace_digest'],
                             samples=samples, states=result['selected_state']))
    groups = defaultdict(list)
    for case_index, case in enumerate(captures):
        for sample_index, adc_byte in enumerate(case['samples']):
            visit = first_visit(sample_index)
            previous_adc = (case['samples'][sample_index - 1]
                            if sample_index else None)
            key = (sample_index % 8, adc_byte)
            groups[key].append(dict(case=case_index, sample=sample_index,
                                    previous_adc=previous_adc,
                                    state={f'{pc:03X}':case['states'][pc][visit]
                                           for pc in SITES}))
    eligible = {}
    for key, rows in groups.items():
        rows = [row for row in rows if row['previous_adc'] is not None]
        if len(rows) >= 2 and len({row['previous_adc'] for row in rows}) >= 2:
            eligible[key] = rows
    fields = ('rom_address', 'rom_value', 'y', 'post_q')
    summary = {}
    witnesses = {}
    for pc in SITES:
        site = f'{pc:03X}'
        metrics = Counter()
        examples = []
        for (phase, adc_byte), rows in eligible.items():
            states = [row['state'][site] for row in rows]
            for field in fields:
                if len({state[field] for state in states}) > 1:
                    metrics[field] += 1
            differing_pre = [address for address in range(16)
                             if len({state['pre_ram'][address]
                                     for state in states}) > 1]
            for address in differing_pre:
                metrics[f'pre_ram_{address:X}'] += 1
            differing_ram = [address for address in range(16)
                             if len({state['post_ram'][address]
                                     for state in states}) > 1]
            if differing_ram:
                metrics['post_ram_any'] += 1
                for address in differing_ram:
                    metrics[f'post_ram_{address:X}'] += 1
            if (len({state['post_q'] for state in states}) > 1 or
                    differing_pre or differing_ram):
                if len(examples) < 8:
                    examples.append(dict(sample_phase=phase, adc_byte=adc_byte,
                                         differing_pre_ram=differing_pre,
                                         differing_ram=differing_ram,
                                         rows=[dict(case=row['case'], sample=row['sample'],
                                                    previous_adc=row['previous_adc'],
                                                    rom_address=row['state'][site]['rom_address'],
                                                    y=row['state'][site]['y'],
                                                    q=row['state'][site]['post_q'],
                                                    pre_r13=row['state'][site]['pre_ram'][13],
                                                    post_r13=row['state'][site]['post_ram'][13])
                                               for row in rows[:4]]))
        summary[site] = dict(eligible_groups=len(eligible),
                             varying_group_counts=dict(metrics),
                             instruction_pairs=sorted({
                                 f"{state['instruction']:02X}/{state['high_instruction']:02X}"
                                 for case in captures for state in case['states'][pc]}))
        witnesses[site] = examples
    report = dict(experiment='matched-ADC post-3F9/3FA/3FE state history',
                  fixture=dict(cases=[dict(seed=s, degrees=d) for s, d in CASES],
                               matched_on='exact current ADC byte and 0..7 sample position',
                               eligible='at least two occurrences with distinct preceding ADC bytes',
                               captured_visit='first of each 47/46-visit ADC hold'),
                  cases=[dict(seed=c['seed'], degrees=c['degrees'],
                              trace_digest=c['trace_digest'], samples=len(c['samples']))
                         for c in captures],
                  total_groups=len(groups), eligible_groups=len(eligible),
                  summary=summary, witnesses=witnesses,
                  source_sha256={str(p.relative_to(HERE.parents[4])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (Path(__file__), EXECUTE, PRIOR)},
                  limitations=[
                      'A different prior ADC byte establishes history sensitivity, not a decoded dibit.',
                      'Only two legal carriers and the first visit of each held sample are compared.',
                      'The ADC timing, external RAM and output circuit remain assumed.'
                  ])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print('eligible', result['eligible_groups'])
    for site, values in result['summary'].items():
        print(site, values['varying_group_counts'])
