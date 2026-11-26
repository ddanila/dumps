"""Screen a fixed two-visit dibit readout from the executed 3FA Y bit."""

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
SEEDS = (0x5A17, 0x76A5, 0x26A1)
DEGREES = (45, 135)
VISITS_PER_SYMBOL = 375
SYMBOLS = range(2, 14)


def capturing_execute():
    source = EXECUTE.read_text()
    patches = (
        ("    trace_count=0;io_count=0;dispatch_counts=Counter();register_changes=0",
         "    trace_count=0;io_count=0;dispatch_counts=Counter();register_changes=0\n"
         "    site_y=[]"),
        ("            carry_input.observe(result)",
         "            if pc==0x3FA:site_y.append(result['y'])\n"
         "            carry_input.observe(result)"),
        ("    if source_read['mode']=='pc_sequence':summary['read_sequence_visits']=dict(sequence_visits)",
         "    summary['site_y3fa']=site_y\n"
         "    if source_read['mode']=='pc_sequence':summary['read_sequence_visits']=dict(sequence_visits)"),
    )
    for old, new in patches:
        if source.count(old) != 1:
            raise ValueError(('emulator injection point moved', old))
        source = source.replace(old, new)
    scope = {'__name__': 'receiver_mask04_3fa_bit_instrumented',
             '__file__': str(EXECUTE)}
    exec(compile(source, str(EXECUTE), 'exec'), scope)
    return scope['execute']


def capture(execute, mapping, base, seed, degrees):
    generator = random.Random(seed)
    middle = [generator.randrange(4) for _ in range(16)]
    dibits = [0] * 8 + middle + [0] * 8
    pcm = rotated_transmit(dibits, degrees)
    if receive(pcm) != dibits[1:]:
        raise ValueError('reference receiver lost carrier data')
    samples = [127 - value for value in
               pcm[SAMPLE_START:SAMPLE_START + LONG_SAMPLES]]
    adc = [value for index, sample in enumerate(samples)
           for value in [sample] * (47 if index % 8 < 7 else 46)]
    if len(adc) != ADC_VISITS:
        raise ValueError('ADC hold schedule changed')
    result = execute(mapping, configured(base, adc, 'previous', 'overflow', 1),
                     CYCLES, mode='integrated', trace_limit=0)
    y = result['site_y3fa']
    if (not result['clean'] or result['completed_cycles'] != CYCLES or
            len(y) != ADC_VISITS or
            result['read_sequence_visits'].get(0x3F8) != ADC_VISITS):
        raise ValueError('receiver loop changed')
    return dict(seed=seed, degrees=degrees, middle=middle,
                trace_digest=result['trace_digest'],
                adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                y3fa_sha256=hashlib.sha256(bytes(y)).hexdigest(),
                output_values=sorted(set(y)),
                bit0_ones=sum(value & 1 for value in y),
                bits=bytes(value & 1 for value in y))


def key(case, symbol, p, q):
    bits = case['bits']
    prev = (symbol - 1) * VISITS_PER_SYMBOL
    curr = symbol * VISITS_PER_SYMBOL
    return ((bits[prev + p] << 3) | (bits[prev + q] << 2) |
            (bits[curr + p] << 1) | bits[curr + q])


def table(cases, p, q):
    labels = defaultdict(set)
    for case in cases:
        for symbol in SYMBOLS:
            labels[key(case, symbol, p, q)].add(case['middle'][symbol])
    return labels


def score(labels, cases, p, q):
    wrong = unknown = 0
    for case in cases:
        for symbol in SYMBOLS:
            values = labels.get(key(case, symbol, p, q), set())
            if len(values) != 1:
                unknown += 1
            else:
                wrong += next(iter(values)) != case['middle'][symbol]
    return dict(checks=len(cases) * len(SYMBOLS), wrong=wrong,
                unknown=unknown)


def run(out=HERE / 'results/receiver-mask04-3fa-two-visit-bits.json'):
    execute = capturing_execute()
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    cases = [capture(execute, mapping, base, seed, degrees)
             for degrees in DEGREES for seed in SEEDS]
    prior = json.loads(PRIOR.read_text())
    for case in cases:
        if case['seed'] not in SEEDS[:2]:
            continue
        old = next(row for row in prior['cases']
                   if row['seed'] == case['seed'] and
                   row['carrier_phase_degrees'] == case['degrees'])
        if (case['trace_digest'] != old['trace_digest'] or
                case['adc_sha256'] != old['adc_stream_sha256']):
            raise ValueError('executed receiver stream differs from earlier replay')
    train = [case for case in cases if case['seed'] == SEEDS[0]]
    holdout = [case for case in cases if case['seed'] == SEEDS[1]]
    fresh = [case for case in cases if case['seed'] == SEEDS[2]]
    selected = None
    exact_training_pairs = 0
    best_training_known = 0
    for p, q in itertools.combinations(range(VISITS_PER_SYMBOL), 2):
        labels = table(train, p, q)
        training = score(labels, train, p, q)
        exact_training_pairs += training['unknown'] == 0
        best_training_known = max(best_training_known,
                                  training['checks'] - training['unknown'])
        rank = (training['unknown'], len(labels), q - p, p, q)
        if selected is None or rank < selected['rank']:
            selected = dict(rank=rank, p=p, q=q,
                            labels={str(k): sorted(values)
                                    for k, values in labels.items()},
                            training=training)
    p, q = selected['p'], selected['q']
    labels = table(train, p, q)
    selected['holdout'] = score(labels, holdout, p, q)
    selected['fresh'] = score(labels, fresh, p, q)
    selected.pop('rank')
    paths = (Path(__file__), EXECUTE, PRIOR,
             HERE / 'receiver_mask04_carrier_phase_screen.py',
             HERE / 'receiver_four_row_condition_screen.py', MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='two fixed symbol visits of PROM-clockable 3FA Y0',
                  fixture=dict(seeds=SEEDS, degrees=DEGREES,
                               training_seed=SEEDS[0], holdout_seed=SEEDS[1],
                               fresh_seed=SEEDS[2],
                               symbols=list(SYMBOLS),
                               visit_pairs_tested=VISITS_PER_SYMBOL *
                               (VISITS_PER_SYMBOL - 1) // 2,
                               key='previous/current 3FA Y0 at visits p and q',
                               label='known offered dibit; external diagnostic'),
                  cases=[{k: v for k, v in case.items() if k != 'bits'}
                         for case in cases],
                  exact_training_pairs=exact_training_pairs,
                  best_training_known=best_training_known,
                  selected=selected,
                  limitations=[
                      'The table and symbol clock are external diagnostics, not executed DSC decision logic.',
                      'Only two fixed visits of one 3FA bit and two carrier rotations are tested; other temporal circuits remain possible.',
                      'The raw-PROM gate, latch pins and downstream USART RxD route remain photo-compatible assumptions.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = run()
    print(result['exact_training_pairs'], result['best_training_known'],
          result['selected'])
