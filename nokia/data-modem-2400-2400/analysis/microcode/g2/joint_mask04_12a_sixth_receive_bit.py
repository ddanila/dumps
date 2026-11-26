"""Find six-bit two-visit features after frozen five-bit gain/phase failures."""

import hashlib
import itertools
import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEVELOPMENT = HERE / 'results/joint-mask04-12a-fifth-receive-bit.json'
NEW = HERE / 'results/joint-mask04-12a-frozen-fifth-new-payloads.json'
CONTROLLER = HERE / 'results/joint-mask04-12a-fifth-bit-holdout.json'
BITS = tuple([('first', bit) for bit in range(5)] +
             [('second', bit) for bit in range(7)])


def state(first, second, extras):
    value = ((first >> 5) & 7) | (((second >> 7) & 1) << 3)
    for position, (source, bit) in enumerate(extras, 4):
        sample = first if source == 'first' else second
        value |= ((sample >> bit) & 1) << position
    return value


def transitions(case, extras):
    states = [state(a, b, extras)
              for a, b in zip(case['first_y'], case['second_y'])]
    width = 4 + len(extras)
    return [((a << width) | b, case['expected_dibits'][index], index)
            for index, (a, b) in enumerate(zip(states, states[1:]), 1)]


def scan(cases, extras):
    observed = defaultdict(lambda: defaultdict(list))
    for case in cases:
        for key, value, index in transitions(case, extras):
            observed[key][value].append(
                f"{case.get('fixture',case.get('level'))}:{case['selector']}:{index}")
    conflicts = {f'{key:03X}': {str(value): examples[:3]
                                 for value, examples in labels.items()}
                 for key, labels in observed.items() if len(labels) > 1}
    table = {key: next(iter(labels)) for key, labels in observed.items()
             if len(labels) == 1}
    return table, conflicts


def run(out=HERE / 'results/joint-mask04-12a-sixth-receive-bit.json'):
    development = json.loads(DEVELOPMENT.read_text())['cases']
    new = json.loads(NEW.read_text())['cases']
    controller = json.loads(CONTROLLER.read_text())['cases']
    training = development + new
    if len(training) != 14 or len(controller) != 2:
        raise ValueError('gain/phase fixture count changed')
    fifth = []
    for extra in BITS:
        table, conflicts = scan(training, (extra,))
        fifth.append(dict(extra=extra, transition_keys=len(table),
                          conflicting_keys=conflicts))
    sixth = []
    for extras in itertools.combinations(BITS, 2):
        table, conflicts = scan(training, extras)
        holdouts = []
        if not conflicts:
            for case in controller:
                wrong = [index for key, value, index in transitions(case, extras)
                         if key in table and table[key] != value]
                unknown = [index for key, _, index in transitions(case, extras)
                           if key not in table]
                holdouts.append(dict(selector=case['selector'],
                                     wrong_indices=wrong,
                                     unknown_indices=unknown))
        sixth.append(dict(extras=extras, transition_keys=len(table),
                          conflicting_keys=conflicts,
                          controller_holdouts=holdouts))
    winners = [row for row in sixth if not row['conflicting_keys']]
    report = dict(experiment='sixth Y bit for combined gain/phase transition collisions',
                  fixture=dict(development_cases=8,
                               new_payload_cases=6,
                               controller_holdouts=2,
                               base='first Y bits 5–7, second Y bit 7',
                               added_bit_candidates=BITS,
                               visits=[46,93]),
                  fifth_bit=fifth,
                  sixth_bit=sixth,
                  zero_conflict_pairs=[row['extras'] for row in winners],
                  limitations=['The new payload labels are now development data for this feature screen.',
                               'The controller A4/A5 capture was used for earlier five-bit validation, so this is a reused holdout, not an untouched final test.',
                               'No physical capture/latch or transition logic has been identified.'],
                  source_sha256={str(p.relative_to(HERE.parents[4])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (Path(__file__), DEVELOPMENT, NEW, CONTROLLER)})
    out.write_text(json.dumps(report, indent=2) + '\n')
    print('one extra zero-conflict',sum(not r['conflicting_keys'] for r in fifth),
          'two extra zero-conflict',len(winners),flush=True)
    for row in winners:
        print(row['extras'],row['transition_keys'],
              [(h['selector'],len(h['wrong_indices']),len(h['unknown_indices']))
               for h in row['controller_holdouts']],flush=True)
    return report


if __name__ == '__main__':
    run()
