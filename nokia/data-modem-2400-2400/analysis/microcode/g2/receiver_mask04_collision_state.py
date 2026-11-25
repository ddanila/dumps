"""Inspect executed Am2901 state at ambiguous rotated receive symbols."""

import hashlib
import json
import random
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from joint_upper_source_screen import candidate
from lower_i_d3f8_full_adc import LONG_SAMPLES, SAMPLE_START
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_four_row_condition_screen import configured
from receiver_mask04_3ed_prom_latch import ADC_VISITS, CYCLES
from receiver_mask04_carrier_phase_screen import rotated_transmit
from receiver_mask04_rotated_codebook import expected_states
from reference_modem import receive

SEEDS = (0x5A17, 0x76A5, 0x33C3, 0x7B23, 0x4E11, 0x6B39)
DEGREES = 45
VISITS_PER_SYMBOL = 375
PHASES = (47, 94)


def snapshot(row, ram):
    return dict(cycle=row['cycle'], y=row['alu']['y'], q=row['q'],
                ram=ram[:], flags={name: row['alu'][name] for name in
                                  ('sign', 'zero', 'carry', 'overflow')})


def run_case(mapping, base, seed, degrees=DEGREES):
    generator = random.Random(seed)
    middle = [generator.randrange(4) for _ in range(16)]
    pcm = rotated_transmit([0] * 8 + middle + [0] * 8, degrees)
    if receive(pcm) != ([0] * 8 + middle + [0] * 8)[1:]:
        raise ValueError('reference receiver lost input')
    samples = [127 - value for value in
               pcm[SAMPLE_START:SAMPLE_START + LONG_SAMPLES]]
    values = [sample for index, sample in enumerate(samples)
              for _ in range(47 if index % 8 < 7 else 46)]
    if len(values) != ADC_VISITS:
        raise ValueError('ADC hold schedule changed')
    scenario = configured(base, values, 'previous', 'overflow', 1)
    ram = scenario['initial']['ram'][:]
    states = {}
    adc_states = {}
    event = 0
    adc_event = 0
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, CYCLES, mode='integrated',
                         out=temporary, trace_limit=CYCLES)
        if (not result['clean'] or result['completed_cycles'] != CYCLES or
                result['address_counts'].get(0x3ED) != 4 * ADC_VISITS or
                result['read_sequence_visits'].get(0x3F8) != ADC_VISITS):
            raise ValueError('full-PROM receiver path stopped')
        for line in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(line)
            for address, value in row['registers'].items():
                ram[int(address)] = value
            if row['pc'] == 0x3F8:
                symbol, phase = divmod(adc_event, VISITS_PER_SYMBOL)
                read = row.get('external_read', {})
                if (not read.get('selected_by_alu') or
                        read.get('value') != values[adc_event]):
                    raise ValueError('3F8 did not select expected ADC byte')
                if phase in PHASES:
                    adc_states[(symbol, phase)] = dict(value=values[adc_event],
                                                      state=snapshot(row, ram))
                adc_event += 1
            if row['pc'] != 0x3ED:
                continue
            visit, row_index = divmod(event, 4)
            symbol, phase = divmod(visit, VISITS_PER_SYMBOL)
            if phase in PHASES and row_index in (0, 3):
                states[(symbol, phase, row_index)] = snapshot(row, ram)
            event += 1
    if (event != 4 * ADC_VISITS or adc_event != ADC_VISITS or
            len(states) != 16 * len(PHASES) * 2 or
            len(adc_states) != 16 * len(PHASES)):
        raise ValueError('symbol state capture count changed')
    symbols = []
    for symbol in range(16):
        symbols.append(dict(expected_state=expected_states(middle)[symbol],
                            adc={str(phase): adc_states[(symbol, phase)]
                                 for phase in PHASES},
                            visits={str(phase): {str(row): states[(symbol, phase, row)]
                                                 for row in (0, 3)}
                                    for phase in PHASES}))
    return dict(seed=seed, degrees=degrees, middle=middle, symbols=symbols,
                trace_digest=result['trace_digest'],
                adc_stream_sha256=hashlib.sha256(bytes(values)).hexdigest())


def feature(symbol, site):
    phase, row, field = site
    item = symbol['visits'][str(phase)][str(row)]
    if field == 'q':
        return item['q']
    if field.startswith('r'):
        return item['ram'][int(field[1:])]
    return item['flags'][field]


def conflicts(cases, site):
    labels = defaultdict(set)
    for case in cases:
        for symbol in case['symbols']:
            visits = symbol['visits']['47']
            pair = (visits['0']['y'], visits['3']['y'])
            labels[pair, feature(symbol, site)].add(symbol['expected_state'])
    return dict(states=len(labels), conflicts=sum(len(v) > 1 for v in labels.values()))


def whole_state_groups(events, phase, row):
    groups = defaultdict(set)
    examples = {}
    for event in events:
        item = event['visits'][str(phase)][str(row)]
        key = (item['y'], item['q'], tuple(item['ram']),
               tuple(sorted(item['flags'].items())))
        groups[key].add(event['expected_state'])
        examples[key] = dict(y=item['y'], q=item['q'],
                             r0=item['ram'][0], r1=item['ram'][1])
    return dict(states=len(groups),
                conflicted_states=sum(len(values) > 1 for values in groups.values()),
                groups=[dict(**examples[key], reference_labels=sorted(labels))
                        for key, labels in sorted(groups.items())])


def run(out=HERE / 'results/receiver-mask04-collision-state.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    cases = []
    for seed in SEEDS:
        cases.append(run_case(mapping, base, seed))
        print('captured', hex(seed), flush=True)
    prior_a = json.loads((HERE / 'results/receiver-mask04-two-visit-phase.json').read_text())
    prior_b = json.loads((HERE / 'results/receiver-mask04-two-visit-rule.json').read_text())
    for case in cases:
        old = next((c for c in prior_a['cases'] if c['seed'] == case['seed']), None)
        if old is None:
            old = next(c for c in prior_b['cases'] if c['seed'] == case['seed']
                       and c['degrees'] == DEGREES)
            pairs = (old['base_pairs'], old['next_pairs'])
        else:
            pairs = ([w['base'] for w in old['windows']],
                     [w['47'] for w in old['windows']])
        actual = [[(s['visits'][str(phase)]['0']['y'],
                    s['visits'][str(phase)]['3']['y']) for s in case['symbols']]
                  for phase in PHASES]
        if case['trace_digest'] != old['trace_digest'] or actual != [list(map(tuple, p)) for p in pairs]:
            raise ValueError('state trace differs from earlier pair capture')
    sites = [(phase, row, field) for phase in PHASES for row in (0, 3)
             for field in ('q', *(f'r{i}' for i in range(16)),
                           'sign', 'zero', 'carry', 'overflow')]
    screens = []
    for site in sites:
        screens.append(dict(site=site, development=conflicts(cases[:4], site),
                            all_cases=conflicts(cases, site)))
    ambiguous = []
    for case in cases:
        for index, symbol in enumerate(case['symbols']):
            visits = symbol['visits']['47']
            if (visits['0']['y'], visits['3']['y']) == (0xF3, 0xF2):
                ambiguous.append(dict(seed=case['seed'], symbol=index,
                                      expected_state=symbol['expected_state'],
                                      adc=symbol['adc'],
                                      visits=symbol['visits']))
    whole_states = {f'{phase}_row{row}': whole_state_groups(ambiguous, phase, row)
                    for phase in PHASES for row in (0, 3)}
    if (len(ambiguous) != 24 or
            any(whole_states[key]['states'] != 1 or
                whole_states[key]['conflicted_states'] != 1
                for key in ('47_row0', '47_row3', '94_row0')) or
            whole_states['94_row3']['states'] != 4 or
            whole_states['94_row3']['conflicted_states'] != 0):
        raise ValueError('ambiguous whole-state structure changed')
    paths = (Path(__file__), HERE / 'receiver_mask04_two_visit_rule.py',
             HERE / 'receiver_mask04_carrier_phase_screen.py',
             HERE / 'receiver_four_row_condition_screen.py',
             HERE / 'reference_modem.py', HERE.parent / 'assumed/execute.py',
             MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='executed state at F3/F2 rotated receive collision',
                  fixture=dict(degrees=DEGREES, seeds=SEEDS, capture_phases=PHASES,
                               development_seeds=SEEDS[:4], holdout_seeds=SEEDS[4:]),
                  cases=cases, ambiguous_events=ambiguous, screens=screens,
                  ambiguous_whole_states=whole_states,
                  limitations=['Phase labels come from the known reference stimulus, not DSC instructions.',
                               'A register that separates labels is not thereby an executed dibit decision or traced output wire.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
