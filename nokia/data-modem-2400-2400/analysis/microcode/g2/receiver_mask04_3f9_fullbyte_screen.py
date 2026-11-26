"""Screen richer executed 3F9 bytes on independent carriers, then loopback."""

import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path

from joint_mask04_12a_buffered_line import MAPPINGS, candidate, fixture, mapped, mapping_with_upper_source
from lower_i_d3f8_full_adc import LONG_SAMPLES, SAMPLE_START
from receiver_four_row_condition_screen import configured
from receiver_mask04_3f9_3fa_feature_screen import (DEGREES, TRAIN_SEED,
                                                     VISITS_PER_SYMBOL,
                                                     instrumented_execute)
from receiver_mask04_carrier_phase_screen import rotated_transmit
from reference_modem import receive

HERE = Path(__file__).resolve().parent
AUDIT = HERE / 'results/joint-mask04-12a-3f9-key-audit.json'
FEATURE = HERE / 'results/receiver-mask04-3f9-3fa-feature-screen.json'
PHASES = (46, 93)
TRAIN_VARIANT = (0.85, 1)
HOLDOUT_SEEDS = (0x76A5, 0x26A1)
FEATURES = ('high2', 'low2', 'high4', 'low4', 'full8',
            'high4_with_3fa', 'full8_with_3fa',
            'high4_transition', 'low4_transition', 'full8_transition',
            'full8_transition_with_3fa')
METRICS = ('hamming', 'absolute')


def independent_rows(execute, mapping, base, seed, degrees, gain, offset):
    generator = random.Random(seed)
    middle = [generator.randrange(4) for _ in range(16)]
    dibits = [0] * 8 + middle + [0] * 8
    pcm = rotated_transmit(dibits, degrees)
    scaled = [max(-127, min(127, round(value * gain))) for value in pcm]
    if receive(scaled) != dibits[1:]:
        raise ValueError('reference receiver lost independent carrier')
    adc_samples = [127 - value for value in
                   scaled[SAMPLE_START + offset:SAMPLE_START + offset + LONG_SAMPLES]]
    adc = [sample for index, sample in enumerate(adc_samples)
           for _ in range(47 if index % 8 < 7 else 46)]
    result = execute(mapping, configured(base, adc, 'previous', 'overflow', 1),
                     32 * len(adc) + 47, mode='integrated', trace_limit=0)
    if (not result['clean'] or
            any(len(result['selected_y'][pc]) != len(adc)
                for pc in (0x3F9, 0x3FA))):
        raise ValueError('independent receive loop stopped')
    rows = []
    for symbol in range(2, 14):
        start = symbol * VISITS_PER_SYMBOL
        rows.append(dict(wanted=middle[symbol],
                         y3f9_at_phases=[result['selected_y'][0x3F9][start + p]
                                         for p in PHASES],
                         y3fa_at_phases=[result['selected_y'][0x3FA][start + p]
                                         for p in PHASES]))
    return dict(seed=seed, degrees=degrees, gain=gain, offset=offset,
                trace_digest=result['trace_digest'],
                adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                rows=rows)


def vector(row, feature):
    values = row['y3f9_at_phases']
    if '_transition' in feature:
        values = row['previous_y3f9_at_phases'] + values
    if feature == 'high2':
        return tuple((v >> 6) & 3 for v in values)
    if feature == 'low2':
        return tuple(v & 3 for v in values)
    if feature.startswith('high4'):
        result = tuple(v >> 4 for v in values)
    elif feature.startswith('low4'):
        result = tuple(v & 15 for v in values)
    else:
        result = tuple(values)
    if feature.endswith('_with_3fa'):
        fa = row['y3fa_at_phases']
        if '_transition' in feature:
            fa = row['previous_y3fa_at_phases'] + fa
        result += tuple(v & 1 for v in fa)
    return result


def linked_rows(rows):
    linked = []
    for previous, current in zip(rows, rows[1:]):
        row = dict(current)
        row['previous_y3f9_at_phases'] = previous['y3f9_at_phases']
        row['previous_y3fa_at_phases'] = previous['y3fa_at_phases']
        linked.append(row)
    return linked


def distance(a, b, metric):
    if metric == 'hamming':
        return sum(bin(x ^ y).count('1') for x, y in zip(a, b))
    return sum(abs(x - y) for x, y in zip(a, b))


def model(training, feature, metric):
    labels = defaultdict(set)
    for row in training:
        labels[vector(row, feature)].add(row['wanted'])
    points = [(v, next(iter(labels[v]))) for v in labels if len(labels[v]) == 1]
    return labels, points


def predict(row, feature, metric, labels, points):
    v = vector(row, feature)
    if v in labels:
        return next(iter(labels[v])) if len(labels[v]) == 1 else None
    if not points:
        return None
    minimum = min(distance(v, p, metric) for p, _ in points)
    nearest = {label for p, label in points if distance(v, p, metric) == minimum}
    return next(iter(nearest)) if len(nearest) == 1 else None


def score(rows, predicted):
    return dict(checks=len(rows),
                wrong=sum(p is not None and p != r['wanted']
                          for r, p in zip(rows, predicted)),
                unknown=sum(p is None for p in predicted))


def run(out=HERE / 'results/receiver-mask04-3f9-fullbyte-screen.json'):
    audit = json.loads(AUDIT.read_text())
    prior = json.loads(FEATURE.read_text())
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    execute = instrumented_execute()
    training = [dict(seed=TRAIN_SEED, degrees=c['degrees'], gain=1.0,
                     offset=0, trace_digest=c['trace_digest'], rows=c['rows'])
                for c in audit['independent']]
    training += [independent_rows(execute, mapping, base, TRAIN_SEED,
                                  degrees, *TRAIN_VARIANT)
                 for degrees in DEGREES]
    holdout = [independent_rows(execute, mapping, base, seed, degrees, 1.0, 0)
               for seed in HOLDOUT_SEEDS for degrees in DEGREES]
    for case in holdout:
        old = next(c for c in prior['cases']
                   if c['seed'] == case['seed'] and c['degrees'] == case['degrees'])
        if (case['trace_digest'] != old['trace_digest'] or
                case['adc_sha256'] != old['adc_sha256']):
            raise ValueError('holdout carrier trace changed')
    train_rows = [r for c in training for r in linked_rows(c['rows'])]
    hold_rows = [r for c in holdout for r in linked_rows(c['rows'])]
    screens = []
    for feature in FEATURES:
        for metric in METRICS:
            labels, points = model(train_rows, feature, metric)
            train_predictions = [predict(r, feature, metric, labels, points)
                                 for r in train_rows]
            hold_predictions = [predict(r, feature, metric, labels, points)
                                for r in hold_rows]
            screens.append(dict(feature=feature, metric=metric,
                                training=score(train_rows, train_predictions),
                                holdout=score(hold_rows, hold_predictions),
                                conflicting_exact_vectors=sum(len(v) > 1
                                                              for v in labels.values()),
                                unique_vectors=len(labels)))
    selected = min(screens, key=lambda r: (
        r['holdout']['unknown'], r['holdout']['wrong'],
        r['training']['unknown'], FEATURES.index(r['feature']),
        METRICS.index(r['metric'])))
    feature, metric = selected['feature'], selected['metric']
    labels, points = model(train_rows, feature, metric)
    buffered = []
    for case in audit['loopbacks']:
        rows = linked_rows(case['rows'])
        predictions = [predict(r, feature, metric, labels, points)
                       for r in rows]
        buffered.append(dict(selector=case['selector'],
                             score=score(rows, predictions),
                             predictions=predictions,
                             original_gaps=[dict(index=r['data_index'],
                                                 wanted=r['wanted'],
                                                 predicted=p)
                                            for r, p in zip(rows, predictions)
                                            if r['original_no_correct_gap']]))
    report = dict(experiment='independent 3F9 byte projection and nearest-vector screen',
                  fixture=dict(phases=PHASES, training_variant=TRAIN_VARIANT,
                               holdout_seeds=HOLDOUT_SEEDS,
                               evaluated_symbols='second through last saved row per stream, so previous full Y is available',
                               model_selection='maximum independent holdout coverage, then minimum wrong; diagnostic only',
                               buffered_line='saved, untouched ROM-sensitive 12A audit'),
                  training=training, holdout=holdout,
                  screens=screens, selected=selected, buffered=buffered,
                  source_sha256={str(p.relative_to(HERE.parents[4])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (Path(__file__), AUDIT, FEATURE)},
                  limitations=[
                      'The independent holdout selects the model; its score is not an unbiased final validation.',
                      'Nearest-vector decoding is an external diagnostic, not a traced board circuit.',
                      'The buffered fixture retains assumed DAC, ADC, analog and RxD connections.'
                  ])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print('selected', result['selected'])
    for case in result['buffered']:
        print(case['selector'], case['score'], 'gaps', case['original_gaps'])
