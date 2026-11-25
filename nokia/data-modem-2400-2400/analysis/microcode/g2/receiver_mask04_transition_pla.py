"""Fit a two-output Boolean decoder to executed receive state transitions."""

import hashlib
import json
from pathlib import Path

from receiver_mask04_phase_state_audit import (HERE, GRID, MULTIVISIT,
                                               TRANSITIONS, observations)
from common import save

FRESH = TRANSITIONS


def popcount(value):
    return bin(value).count('1')


def fit_bit(table, bit):
    """Greedy cover of known ones using cubes that exclude every known zero."""
    on = {key for key, dibit in table.items() if dibit & (1 << bit)}
    off = set(table) - on
    cubes = []
    for mask in range(256):
        value = mask
        while True:
            if not any((key & mask) == value for key in off):
                covered = {key for key in on if (key & mask) == value}
                if covered:
                    cubes.append((mask, value, covered))
            if value == 0:
                break
            value = (value - 1) & mask
    selected = []
    remaining = set(on)
    while remaining:
        cube = max(cubes, key=lambda row:
                   (len(row[2] & remaining), -popcount(row[0]),
                    -row[0], -row[1]))
        selected.append(cube)
        remaining -= cube[2]
    for cube in selected[:]:
        if on <= set().union(*(other[2] for other in selected
                              if other is not cube)):
            selected.remove(cube)
    return [(mask, value) for mask, value, _ in selected]


def fit(table):
    return [fit_bit(table, bit) for bit in range(2)]


def decode(terms, key):
    return sum((1 << bit) if any((key & mask) == value
                                  for mask, value in output) else 0
               for bit, output in enumerate(terms))


def run(out=HERE / 'results/receiver-mask04-transition-pla.json'):
    rows = observations()
    table = {}
    for row in rows:
        key = (row['before'] << 4) | row['after']
        if key in table and table[key] != row['dibit']:
            raise ValueError(('transition collision', key))
        table[key] = row['dibit']
    saved = json.loads(FRESH.read_text())
    if (len(rows) != 987 or len(table) != 86 or
            {f'{key:02X}': value for key, value in table.items()} !=
            saved['rule']['table']):
        raise ValueError('development transition table changed')

    terms = fit(table)
    training_errors = sum(decode(terms, key) != value
                          for key, value in table.items())
    angles = sorted({row['degrees'] for row in rows})
    leave_angle_out = []
    for angle in angles:
        training = {((row['before'] << 4) | row['after']): row['dibit']
                    for row in rows if row['degrees'] != angle}
        candidate = fit(training)
        test = [row for row in rows if row['degrees'] == angle]
        errors = sum(decode(candidate, (row['before'] << 4) | row['after']) !=
                     row['dibit'] for row in test)
        known_errors = sum(decode(candidate, (row['before'] << 4) | row['after']) !=
                           row['dibit'] for row in test
                           if ((row['before'] << 4) | row['after']) in training)
        unseen = sum(((row['before'] << 4) | row['after']) not in training
                     for row in test)
        if known_errors:
            raise ValueError(('known-key angle holdout changed', angle))
        leave_angle_out.append(dict(degrees=angle, checks=len(test),
                                    errors=errors, unseen_keys=unseen,
                                    known_key_errors=known_errors,
                                    product_terms=[len(x) for x in candidate]))

    fresh = []
    for case in saved['fresh_cases']:
        states = case['states']
        expected = case['expected_dibits']
        misses = []
        for index, (before, after) in enumerate(zip(states, states[1:])):
            key = (before << 4) | after
            actual = decode(terms, key)
            if actual != expected[index + 1]:
                misses.append(dict(symbol=index + 1, key=f'{key:02X}',
                                   expected=expected[index + 1], actual=actual,
                                   unseen_in_training=key not in table))
        fresh.append(dict(degrees=case['degrees'],
                          trace_digest=case['trace_digest'],
                          checks=len(states) - 1, errors=len(misses),
                          misses=misses))

    if (training_errors != 0 or [len(x) for x in terms] != [9, 8] or
            sum(popcount(mask) for output in terms
                for mask, _ in output) != 59 or
            sum(row['errors'] for row in leave_angle_out) != 20 or
            sum(row['errors'] for row in fresh) != 2):
        raise ValueError('Boolean transition screen changed')
    paths = (Path(__file__), MULTIVISIT, GRID, FRESH,
             HERE / 'receiver_mask04_phase_state_audit.py',
             HERE / 'receiver_mask04_four_bit_transition.py')
    report = dict(experiment='greedy partial-truth-table Boolean receive transition decoder',
                  fixture=dict(input='previous and current four-bit visit47/94 states',
                               development_traces=21,
                               development_observations=len(rows),
                               known_transition_keys=len(table),
                               unknown_transition_keys=256 - len(table),
                               optimization='for each output bit, enumerate all eight-input cubes excluding known zeros; greedily cover known ones by new coverage, then fewer literals and fixed numeric tie breaks; prune redundant cubes',
                               validation='leave one carrier angle out; freeze final terms before testing third-seed fresh stream'),
                  terms=[dict(output_bit=bit,
                              cubes=[dict(mask=f'{mask:02X}', value=f'{value:02X}')
                                     for mask, value in output])
                         for bit, output in enumerate(terms)],
                  term_count=sum(len(x) for x in terms),
                  literal_count=sum(popcount(mask) for output in terms
                                    for mask, _ in output),
                  training=dict(keys=len(table), errors=training_errors),
                  leave_angle_out=leave_angle_out,
                  leave_angle_out_total=dict(checks=sum(x['checks'] for x in leave_angle_out),
                                             errors=sum(x['errors'] for x in leave_angle_out)),
                  fresh_cases=fresh,
                  fresh_total=dict(checks=sum(x['checks'] for x in fresh),
                                   errors=sum(x['errors'] for x in fresh)),
                  limitations=['Unobserved transition keys are Boolean don\'t-cares during fitting; their predictions are not established by the PROM traces.',
                               'This is external combinational logic, not a traced or executed DSC/8251A consumer.',
                               'The fresh errors and leave-angle-out errors reject this particular fitted circuit as a complete receiver.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    print(result['term_count'], result['literal_count'],
          result['leave_angle_out_total'], result['fresh_total'])
