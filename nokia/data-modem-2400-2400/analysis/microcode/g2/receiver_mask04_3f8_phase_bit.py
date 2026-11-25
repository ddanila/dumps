"""Validate a frozen 3F8 Y7 latch for the 45-degree row-pair collision."""

import hashlib
import itertools
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from joint_upper_source_screen import candidate
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_mask04_collision_state import run_case
from receiver_mask04_phase47_logic import score as nominal_boolean_score
from receiver_mask04_two_visit_rule import RULE, decode as two_visit_decode
from reference_modem import QUADRANT_TO_DIBIT

SEEDS = (0xA431, 0xC991)
DEGREES = (0, 45, 90, 135, 180)
SYMBOLS = range(2, 14)
ROM = HERE.parents[2] / 'microcode-810237c-810240c'
LOOP_PCS = (*range(0x3EA, 0x3EE), *range(0x3EF, 0x3FF))


def score(case):
    phases = []
    pairs = []
    next_pairs = []
    transient = []
    for symbol in case['symbols']:
        visits = symbol['visits']
        pair = (visits['47']['0']['y'], visits['47']['3']['y'])
        next_pair = (visits['94']['0']['y'], visits['94']['3']['y'])
        y3f8 = symbol['adc']['47']['state']['y']
        phase = RULE.get(pair)
        if pair == (0xF3, 0xF2):
            phase = (y3f8 >> 7) & 1
        pairs.append(pair)
        next_pairs.append(next_pair)
        transient.append(y3f8)
        phases.append(phase)
    dibits = []
    errors = unknown = 0
    for symbol in SYMBOLS:
        before, after = phases[symbol - 1:symbol + 1]
        if before is None or after is None:
            dibits.append(None)
            unknown += 1
        else:
            dibit = QUADRANT_TO_DIBIT[(after - before - 2) & 3]
            dibits.append(dibit)
            errors += dibit != case['middle'][symbol]
    return dict(score=dict(checks=len(SYMBOLS), errors=errors,
                           unknown=unknown, dibits=dibits),
                nominal_boolean=nominal_boolean_score(pairs, case['middle']),
                ambiguous_pairs=sum(pair == (0xF3, 0xF2) for pair in pairs),
                phase_errors=sum(a != s['expected_state'] for a, s in
                                 zip(phases, case['symbols']) if a is not None),
                phases=phases, pairs=pairs, next_pairs=next_pairs,
                y3f8=transient,
                previous_two_visit=two_visit_decode(pairs, next_pairs,
                                                     case['middle']))


def prom_gate_search():
    chips = {name: (ROM / f'chip{name}-{suffix}.bin').read_bytes()
             for name, suffix in (('10', '810237c'), ('11', '810238c'),
                                  ('17', '810239c'), ('18', '810240c'))}
    target = 1 << LOOP_PCS.index(0x3F8)
    all_sites = (1 << len(LOOP_PCS)) - 1
    literals = []
    for name in ('10', '11', '17', '18'):
        for bit in range(8):
            for value in (0, 1):
                mask = sum(1 << index for index, pc in enumerate(LOOP_PCS)
                           if ((chips[name][pc] >> bit) & 1) == value)
                literals.append((f'{"" if value else "!"}U{name}.D{bit}', mask))
    counts = {}
    examples = {}
    for width in (1, 2, 3, 4):
        matches = []
        for group in itertools.combinations(literals, width):
            mask = all_sites
            for _, level in group:
                mask &= level
            if mask == target:
                matches.append([name for name, _ in group])
        counts[str(width)] = len(matches)
        examples[str(width)] = matches[:4]
    if counts != {'1': 0, '2': 0, '3': 0, '4': 28}:
        raise ValueError('raw-PROM 3F8 gate search changed')
    outside = [pc for pc in range(1024)
               if (chips['10'][pc] & 0x02 and chips['10'][pc] & 0x08 and
                   chips['10'][pc] & 0x80 and not chips['17'][pc] & 0x02)]
    if len(outside) != 13 or 0x3F8 not in outside:
        raise ValueError('candidate PROM gate global sites changed')
    return dict(reached_loop_pcs=[f'{pc:03X}' for pc in LOOP_PCS],
                matches_by_width=counts, example_matches=examples,
                candidate_global_sites=[f'{pc:03X}' for pc in outside],
                caveat='Only static receiver-loop words; mode qualification and actual pin route untraced')


def run(out=HERE / 'results/receiver-mask04-3f8-phase-bit.json'):
    prior = json.loads((HERE / 'results/receiver-mask04-collision-state.json').read_text())
    development = [dict(seed=case['seed'], **score(case)) for case in prior['cases']]
    if any(case['score']['errors'] or case['score']['unknown'] or
           case['phase_errors'] for case in development):
        raise ValueError('3F8 bit rule changed on inspected streams')
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    fresh = []
    for degrees in DEGREES:
        for seed in SEEDS:
            case = run_case(mapping, base, seed, degrees)
            fresh.append(dict(degrees=degrees, seed=seed, middle=case['middle'],
                              trace_digest=case['trace_digest'], **score(case)))
            print('captured', degrees, hex(seed), fresh[-1]['score']['errors'],
                  fresh[-1]['score']['unknown'], flush=True)
    aggregates = {str(degrees): dict(
        checks=sum(case['score']['checks'] for case in fresh
                   if case['degrees'] == degrees),
        errors=sum(case['score']['errors'] for case in fresh
                   if case['degrees'] == degrees),
        unknown=sum(case['score']['unknown'] for case in fresh
                    if case['degrees'] == degrees),
        ambiguous_pairs=sum(case['ambiguous_pairs'] for case in fresh
                            if case['degrees'] == degrees),
        nominal_boolean_errors=sum(case['nominal_boolean']['errors']
                                   for case in fresh
                                   if case['degrees'] == degrees))
        for degrees in DEGREES}
    if any(aggregates[str(degrees)]['nominal_boolean_errors'] != 0
           for degrees in (0, 90, 180)):
        raise ValueError('cardinal-rotation Boolean control changed')
    paths = (Path(__file__), HERE / 'receiver_mask04_collision_state.py',
             HERE / 'receiver_mask04_two_visit_rule.py',
             HERE / 'receiver_mask04_carrier_phase_screen.py',
             HERE / 'reference_modem.py', HERE.parent / 'assumed/execute.py',
             MAPPINGS['q3'], *ROM.glob('chip*.bin'))
    report = dict(experiment='3F8 Y7 transient latch for ambiguous rotated receiver pair',
                  fixture=dict(carrier_degrees=DEGREES, development_seeds=[c['seed'] for c in prior['cases']],
                               fresh_seeds=SEEDS, capture_visit=47,
                               gate='one of 28 four-literal raw-PROM decodes of 3F8 within receiver loop; actual route untraced'),
                  rule='prior seven-state row-pair table, except F3/F2 state = Y[7] at same-visit 3F8',
                  prom_gate=prom_gate_search(), development=development,
                  fresh=fresh, fresh_aggregates=aggregates,
                  limitations=['Y7 capture clock, storage, subsequent phase logic and USART RxD wire are assumed external connections.',
                               'The rule was developed at 45 degrees and is not established across arbitrary carrier phases or input levels.',
                               'A static PROM-word match does not prove a photographed net or a hazard-free clock.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
