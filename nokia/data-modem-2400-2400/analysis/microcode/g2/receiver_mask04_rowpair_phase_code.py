"""Test whether two executed 3ED row bytes encode differential phase."""

import hashlib
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from joint_upper_receive_bit_screen import HOLDOUT, TRAIN
from joint_upper_source_screen import candidate
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from lower_i_d3f8_upper_symbol_screen import LAGS, SYMBOL_INDEXES, sequences
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_mask04_3ed_prom_latch import capture, VALIDATION_SEEDS
from reference_modem import PHASE_STEPS, transmit

PRIOR = HERE / 'results/receiver-mask04-3ed-prom-latch.json'
ADC_VISITS_PER_SYMBOL = 375
ROWS_PER_VISIT = 4
PHASE_STEPS_QUADRANTS = tuple(step // 4 for step in PHASE_STEPS)
OFFSETS = tuple(range(4))
ORIENTATIONS = (1, -1)


def row_pairs(captured):
    if len(captured) != 6000 * ROWS_PER_VISIT:
        raise ValueError('four-row capture length changed')
    return [tuple(captured[index:index + ROWS_PER_VISIT:3])
            for index in range(0, len(captured), ROWS_PER_VISIT)]


def solve(streams, truth, indexes, phase, lag, orientation, offset, spacing):
    """Solve state-to-Z4 labels from known symbol transitions; count contradictions."""
    parent = {}
    weight = {}
    conflicts = 0

    def find(state):
        if state not in parent:
            parent[state], weight[state] = state, 0
        if parent[state] != state:
            root, potential = find(parent[state])
            weight[state] = (weight[state] + potential) & 3
            parent[state] = root
        return parent[state], weight[state]

    for index in indexes:
        for symbol in SYMBOL_INDEXES:
            previous = streams[index][(symbol - 1) * spacing + phase]
            current = streams[index][symbol * spacing + phase]
            expected = (orientation * PHASE_STEPS_QUADRANTS[
                truth[index][symbol + lag]] + offset) & 3
            root_before, value_before = find(previous)
            root_after, value_after = find(current)
            if root_before == root_after:
                conflicts += ((value_after - value_before) & 3) != expected
            else:
                parent[root_after] = root_before
                weight[root_after] = (expected + value_before - value_after) & 3
    labels = {state: find(state) for state in parent}
    return conflicts, labels


def evaluate(streams, truth, indexes, labels, phase, lag, orientation, offset,
             spacing):
    errors = known = 0
    for index in indexes:
        for symbol in SYMBOL_INDEXES:
            previous = streams[index][(symbol - 1) * spacing + phase]
            current = streams[index][symbol * spacing + phase]
            before = labels.get(previous)
            after = labels.get(current)
            if before is None or after is None or before[0] != after[0]:
                continue
            expected = (orientation * PHASE_STEPS_QUADRANTS[
                truth[index][symbol + lag]] + offset) & 3
            known += 1
            errors += ((after[1] - before[1]) & 3) != expected
    total = len(indexes) * len(SYMBOL_INDEXES)
    return dict(known=known, errors=errors, unknown=total - known, checks=total)


def exact_solutions(streams, truth, indexes, phases, spacing):
    solutions = []
    for phase in phases:
        for lag in LAGS:
            for orientation in ORIENTATIONS:
                for offset in OFFSETS:
                    conflicts, labels = solve(streams, truth, indexes,
                                              phase, lag, orientation, offset,
                                              spacing)
                    if conflicts == 0:
                        solutions.append(dict(phase=phase, lag=lag,
                                              orientation=orientation,
                                              carrier_offset=offset,
                                              states=len(labels),
                                              components=len({root for root, _
                                                              in labels.values()})))
    return solutions


def raw_adc_controls(truth, training, holdout, fresh):
    raw = {index: [127 - value for value in
                   transmit([0] * 8 + middle + [0] * 8)[64:192]]
           for index, middle in truth.items()}
    results = []
    for width, positions in ((1, range(8)), (2, range(7))):
        stream = {index: [tuple(samples[n:n + width]) for n in range(128)]
                  for index, samples in raw.items()}
        for candidate in exact_solutions(stream, truth, training, positions, 8):
            conflicts, labels = solve(stream, truth, training,
                                      candidate['phase'], candidate['lag'],
                                      candidate['orientation'],
                                      candidate['carrier_offset'], 8)
            if conflicts:
                raise ValueError('raw ADC exact candidate changed')
            kwargs = dict(phase=candidate['phase'], lag=candidate['lag'],
                          orientation=candidate['orientation'],
                          offset=candidate['carrier_offset'], spacing=8)
            results.append(dict(width=width, **candidate,
                                holdout=evaluate(stream, truth, holdout,
                                                 labels, **kwargs),
                                fresh=evaluate(stream, truth, fresh,
                                               labels, **kwargs)))
    return dict(exact_training_by_width={str(width): sum(row['width'] == width
                                                       for row in results)
                                         for width in (1, 2)},
                max_holdout_covered=max(row['holdout']['known'] for row in results),
                max_fresh_covered=max(row['fresh']['known'] for row in results),
                max_combined_covered=max(row['holdout']['known'] +
                                         row['fresh']['known'] for row in results),
                best_coverage=sorted(results, key=lambda row: -(
                    row['holdout']['known'] + row['fresh']['known']))[:4])


def run(out=HERE / 'results/receiver-mask04-rowpair-phase-code.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    stimuli = sequences()
    training, holdout, fresh = TRAIN, HOLDOUT, VALIDATION_SEEDS
    truth = {index: stimuli[index]['middle'] for index in training + holdout}
    for seed in fresh:
        generator = random.Random(seed)
        truth[seed] = [generator.randrange(4) for _ in range(16)]

    prior = json.loads(PRIOR.read_text())
    prior_hashes = {int(index): case['captured_sha256']
                    for index, case in prior['cases'].items()}
    prior_hashes.update({row['seed']: row['captured_sha256']
                         for row in prior['validation']})
    streams, cases = {}, {}
    for index in training + holdout + fresh:
        captured, case, _ = capture(mapping, base, truth[index])
        if case['captured_sha256'] != prior_hashes[index]:
            raise ValueError(('prior full-PROM capture changed', index))
        streams[index] = row_pairs(captured)
        cases[str(index)] = dict(**case,
                                 middle_dibits=truth[index],
                                 row1_nonzero=sum(captured[4 * n + 1] != 0
                                                  for n in range(6000)),
                                 row2_nonzero=sum(captured[4 * n + 2] != 0
                                                  for n in range(6000)))
        print('captured', index, flush=True)

    solutions = exact_solutions(streams, truth, training,
                                range(ADC_VISITS_PER_SYMBOL),
                                ADC_VISITS_PER_SYMBOL)
    if not solutions:
        raise ValueError('no row-pair phase code fits training')
    ranked = sorted(solutions, key=lambda row: (row['states'], row['phase'],
                                                 abs(row['lag']), row['lag'],
                                                 -row['orientation'],
                                                 row['carrier_offset']))
    all_exact_validation = []
    for choice in ranked:
        _, choice_labels = solve(streams, truth, training,
                                 choice['phase'], choice['lag'],
                                 choice['orientation'], choice['carrier_offset'],
                                 ADC_VISITS_PER_SYMBOL)
        choice_kwargs = dict(phase=choice['phase'], lag=choice['lag'],
                             orientation=choice['orientation'],
                             offset=choice['carrier_offset'],
                             spacing=ADC_VISITS_PER_SYMBOL)
        all_exact_validation.append(dict(
            **choice,
            holdout=evaluate(streams, truth, holdout, choice_labels,
                             **choice_kwargs),
            fresh=evaluate(streams, truth, fresh, choice_labels,
                           **choice_kwargs)))
    selected = ranked[0]
    conflicts, labels = solve(streams, truth, training,
                              selected['phase'], selected['lag'],
                              selected['orientation'], selected['carrier_offset'],
                              ADC_VISITS_PER_SYMBOL)
    if conflicts or selected['components'] != 1:
        raise ValueError('selected codebook is inconsistent or disconnected')
    kwargs = dict(phase=selected['phase'], lag=selected['lag'],
                  orientation=selected['orientation'],
                  offset=selected['carrier_offset'],
                  spacing=ADC_VISITS_PER_SYMBOL)
    selected = dict(**selected,
                    codebook=[dict(row0=state[0], row3=state[1],
                                   phase_quadrant=label[1])
                              for state, label in sorted(labels.items())],
                    training=evaluate(streams, truth, training, labels, **kwargs),
                    holdout=evaluate(streams, truth, holdout, labels, **kwargs),
                    fresh=evaluate(streams, truth, fresh, labels, **kwargs))
    if (selected['training'] != dict(known=36, errors=0, unknown=0, checks=36)
            or selected['holdout'] != dict(known=48, errors=0, unknown=0,
                                          checks=48)
            or selected['fresh'] != dict(known=48, errors=0, unknown=0,
                                        checks=48)):
        raise ValueError('selected phase code did not generalize')

    controls = raw_adc_controls(truth, training, holdout, fresh)
    paths = (Path(__file__), PRIOR, HERE / 'receiver_mask04_3ed_prom_latch.py',
             HERE / 'receiver_four_row_condition_screen.py',
             HERE / 'reference_modem.py', HERE.parent / 'assumed/execute.py',
             HERE.parent / 'model.py', MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='differential phase code in paired executed mask-04 3ED row bytes',
                  fixture=dict(mapping='joint upper-source mask 04',
                               dispatch='scenario 0,1,2,3',
                               condition='inverted previous overflow at select 0',
                               adc='complementary reference PCM, 47/46 visits per sample',
                               latch='hypothetical U19 NAND edge at 3ED to 3EA',
                               row_pair='3ED Y at rows 0 and 3 of each ADC visit',
                               fixed_phase_choices=ADC_VISITS_PER_SYMBOL,
                               lags=LAGS, orientations=ORIENTATIONS,
                               carrier_offsets=OFFSETS,
                               phase_steps_quadrants=PHASE_STEPS_QUADRANTS,
                               train_indexes=training,
                               holdout_indexes=holdout,
                               fresh_seeds=fresh),
                  cases=cases, exact_training_choices=all_exact_validation,
                  selected=selected, raw_adc_controls=controls,
                  limitations=['The phase codebook and differential operation are external diagnostics, not executed DSC instructions or a traced USART RxD output.',
                               'The ADC route, TEST/dispatch schedule, U19/U12 capture and row-pair consumer are still hypotheses.',
                               'The raw ADC control tests fixed one- and two-sample codebooks, not a full independent receiver or all possible ADC preprocessing.',
                               'Reference PCM is ideal and fixed-amplitude; line noise and gain variation are not tested.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    print(result['selected']['training'], result['selected']['holdout'],
          result['selected']['fresh'])
