"""Train a bounded 3F9/3FA transition readout on independent carriers."""

import hashlib
import itertools
import json
import random
from collections import defaultdict
from pathlib import Path

from joint_upper_source_screen import candidate
from lower_i_d3f8_full_adc import LONG_SAMPLES, SAMPLE_START
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_four_row_condition_screen import configured
from receiver_mask04_3ed_prom_latch import ADC_VISITS, CYCLES
from receiver_mask04_carrier_phase_screen import rotated_transmit
from reference_modem import receive

HERE = Path(__file__).resolve().parent
EXECUTE = HERE.parent / 'assumed/execute.py'
PRIOR = HERE / 'results/receiver-mask04-carrier-phase-screen.json'
DEGREES = (45, 135)
TRAIN_SEED = 0x5A17
HOLDOUT_SEEDS = (0x76A5, 0x26A1)
PHASE_PAIRS = ((46, 93), (47, 94), (94, 141))
TWO_BIT_SHIFTS = (0, 2, 4, 6)
EXTRA = ('none', 'first_3fa_y0', 'second_3fa_y0')
SYMBOLS = range(2, 14)
VISITS_PER_SYMBOL = 375


def instrumented_execute():
    source = EXECUTE.read_text()
    patches = (
        ("    trace_count=0;io_count=0;dispatch_counts=Counter();register_changes=0",
         "    trace_count=0;io_count=0;dispatch_counts=Counter();register_changes=0\n"
         "    selected_y={0x3F9:[],0x3FA:[]}"),
        ("            carry_input.observe(result)",
         "            if pc in selected_y:selected_y[pc].append(result['y'])\n"
         "            carry_input.observe(result)"),
        ("    if source_read['mode']=='pc_sequence':summary['read_sequence_visits']=dict(sequence_visits)",
         "    summary['selected_y']=selected_y\n"
         "    if source_read['mode']=='pc_sequence':summary['read_sequence_visits']=dict(sequence_visits)"),
    )
    for old, new in patches:
        if source.count(old) != 1:
            raise ValueError(('emulator injection moved', old))
        source = source.replace(old, new)
    scope = {'__name__': 'receiver_mask04_3f9_3fa_instrumented',
             '__file__': str(EXECUTE)}
    exec(compile(source, str(EXECUTE), 'exec'), scope)
    return scope['execute']


def capture(execute, mapping, base, seed, degrees):
    generator = random.Random(seed)
    middle = [generator.randrange(4) for _ in range(16)]
    dibits = [0] * 8 + middle + [0] * 8
    pcm = rotated_transmit(dibits, degrees)
    if receive(pcm) != dibits[1:]:
        raise ValueError('reference lost carrier data')
    samples = [127 - value for value in
               pcm[SAMPLE_START:SAMPLE_START + LONG_SAMPLES]]
    adc = [sample for index, sample in enumerate(samples)
           for _ in range(47 if index % 8 < 7 else 46)]
    if len(adc) != ADC_VISITS:
        raise ValueError('ADC hold schedule changed')
    result = execute(mapping, configured(base, adc, 'previous', 'overflow', 1),
                     CYCLES, mode='integrated', trace_limit=0)
    y = result['selected_y']
    if (not result['clean'] or result['completed_cycles'] != CYCLES or
            any(len(y[pc]) != ADC_VISITS for pc in (0x3F9, 0x3FA)) or
            result['read_sequence_visits'].get(0x3F8) != ADC_VISITS):
        raise ValueError('receive loop did not sustain')
    return dict(seed=seed, degrees=degrees, middle=middle,
                trace_digest=result['trace_digest'],
                adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                y_sha256={f'{pc:03X}': hashlib.sha256(bytes(y[pc])).hexdigest()
                          for pc in (0x3F9, 0x3FA)},
                y_values={f'{pc:03X}': sorted(set(y[pc]))
                          for pc in (0x3F9, 0x3FA)},
                y=y)


def state(case, symbol, phases, shift, extra):
    a, b = phases
    start = symbol * VISITS_PER_SYMBOL
    y9, ya = case['y'][0x3F9], case['y'][0x3FA]
    result = (((y9[start + a] >> shift) & 3) << 2) | ((y9[start + b] >> shift) & 3)
    if extra == 'first_3fa_y0':
        result = (result << 1) | (ya[start + a] & 1)
    elif extra == 'second_3fa_y0':
        result = (result << 1) | (ya[start + b] & 1)
    return result


def key(case, symbol, phases, shift, extra):
    width = 5 if extra != 'none' else 4
    return ((state(case, symbol - 1, phases, shift, extra) << width) |
            state(case, symbol, phases, shift, extra))


def table(cases, phases, shift, extra):
    labels = defaultdict(set)
    for case in cases:
        for symbol in SYMBOLS:
            labels[key(case, symbol, phases, shift, extra)].add(
                case['middle'][symbol])
    return labels


def score(labels, cases, phases, shift, extra):
    wrong = unknown = 0
    for case in cases:
        for symbol in SYMBOLS:
            values = labels.get(key(case, symbol, phases, shift, extra), set())
            if len(values) != 1:
                unknown += 1
            else:
                wrong += next(iter(values)) != case['middle'][symbol]
    return dict(checks=len(cases) * len(SYMBOLS), wrong=wrong, unknown=unknown)


def run(out=HERE / 'results/receiver-mask04-3f9-3fa-feature-screen.json'):
    execute = instrumented_execute()
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    cases = [capture(execute, mapping, base, seed, degrees)
             for degrees in DEGREES
             for seed in (TRAIN_SEED, *HOLDOUT_SEEDS)]
    prior = json.loads(PRIOR.read_text())
    for case in cases:
        if case['seed'] not in (TRAIN_SEED, HOLDOUT_SEEDS[0]):
            continue
        old = next(row for row in prior['cases']
                   if row['carrier_phase_degrees'] == case['degrees'] and
                   row['seed'] == case['seed'])
        if (case['trace_digest'] != old['trace_digest'] or
                case['adc_sha256'] != old['adc_stream_sha256']):
            raise ValueError('PROM trace differs from earlier carrier replay')
    training = [case for case in cases if case['seed'] == TRAIN_SEED]
    holdout = [case for case in cases if case['seed'] in HOLDOUT_SEEDS]
    screens = []
    for phases, shift, extra in itertools.product(
            PHASE_PAIRS, TWO_BIT_SHIFTS, EXTRA):
        labels = table(training, phases, shift, extra)
        train_score = score(labels, training, phases, shift, extra)
        hold_score = score(labels, holdout, phases, shift, extra)
        screens.append(dict(phases=phases, y3f9_two_bit_shift=shift,
                            y3fa_extra=extra, table_keys=len(labels),
                            conflicting_training_keys=sum(len(v) > 1
                                                          for v in labels.values()),
                            training=train_score, holdout=hold_score))
    selected = min(screens, key=lambda row: (
        row['training']['unknown'], row['table_keys'],
        row['phases'], row['y3f9_two_bit_shift'],
        0 if row['y3fa_extra'] == 'none' else 1,
        row['y3fa_extra']))
    selected_labels = table(training, selected['phases'],
                            selected['y3f9_two_bit_shift'],
                            selected['y3fa_extra'])
    selected['frozen_table'] = {str(key): next(iter(labels))
                                for key, labels in sorted(selected_labels.items())
                                if len(labels) == 1}
    paths = (Path(__file__), EXECUTE, PRIOR,
             HERE / 'receiver_mask04_carrier_phase_screen.py',
             HERE / 'receiver_four_row_condition_screen.py', MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='bounded 3F9 and 3FA receive transition feature screen',
                  fixture=dict(degrees=DEGREES, training_seed=TRAIN_SEED,
                               holdout_seeds=HOLDOUT_SEEDS,
                               phase_pairs=PHASE_PAIRS,
                               two_bit_shifts=TWO_BIT_SHIFTS,
                               extra_features=EXTRA,
                               symbols=list(SYMBOLS),
                               candidate_count=len(screens),
                               label='independent offered dibit; external diagnostic'),
                  cases=[{k: v for k, v in case.items() if k != 'y'}
                         for case in cases],
                  selected=selected,
                  exact_training_models=sum(row['training']['unknown'] == 0
                                            for row in screens),
                  screens=screens,
                  limitations=[
                      'Only the stated 36 fixed-phase, small-bit feature families are screened.',
                      'The transition lookup and symbol clock are external diagnostics, not proven DSC circuitry.',
                      'The ADC, output latches and USART RxD route remain photo-compatible assumptions.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print(result['selected'])
