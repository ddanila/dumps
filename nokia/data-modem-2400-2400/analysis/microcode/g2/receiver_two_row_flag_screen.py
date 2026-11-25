"""Test ALU flags from both interleaved receive rows as dibit decisions."""

import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from joint_upper_receive_bit_screen import HOLDOUT, TRAIN
from joint_upper_source_screen import SELECTED_MASK, candidate
from lower_i_d3f8_full_adc import LONG_CYCLES, LONG_SAMPLES, SAMPLE_START, scenario_for_full_byte
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from lower_i_d3f8_upper_symbol_screen import LAGS, SYMBOL_INDEXES, sequences
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from reference_modem import receive, transmit

PCS = (0x3EF, 0x3F0, 0x3F1, 0x3F2, 0x3F7, 0x3F8, 0x3F9, 0x3FA)
FLAGS = ('carry', 'overflow', 'sign', 'zero')
CHANNELS = tuple(f'{pc:03X}.{flag}' for pc in PCS for flag in FLAGS)
VISITS_PER_SYMBOL = 750
ADC_VISITS = 12000


def capture(mapping, base, middle):
    dibits = [0] * 8 + middle + [0] * 8
    pcm = transmit(dibits)
    if receive(pcm) != dibits[1:]:
        raise ValueError('reference stimulus did not recover')
    samples = [127 - sample for sample in
               pcm[SAMPLE_START:SAMPLE_START + LONG_SAMPLES]]
    values = [sample for index, sample in enumerate(samples)
              for _ in range(94 if index % 4 < 3 else 93)]
    scenario = scenario_for_full_byte(base, values, 'complementary')
    scenario['dispatch']['mode'] = 'sequence'
    scenario['dispatch']['sequence'] = [0, 2]
    latest = {}
    rows = []
    adc_selected = 0
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, LONG_CYCLES,
                         mode='integrated', out=temporary, trace_limit=LONG_CYCLES)
        for line in (Path(temporary) / 'trace.jsonl').open():
            record = json.loads(line)
            pc = record['pc']
            if pc in PCS:
                latest[pc] = tuple(record['alu'][flag] for flag in FLAGS)
            if pc == 0x3F8:
                event = record['external_read']
                if (not event.get('selected_by_alu') or
                        event['value'] != values[adc_selected]):
                    raise ValueError('two-row ADC input not selected')
                adc_selected += 1
            elif pc == 0x3FA:
                if len(latest) != len(PCS):
                    raise ValueError('missing two-row ALU flag site')
                rows.append(bytes(value for site in PCS
                                  for value in latest[site]))
    if (not result['clean'] or adc_selected != ADC_VISITS or
            len(rows) != ADC_VISITS or
            result['address_counts'].get(0x3EF, 0) != ADC_VISITS + 1):
        raise ValueError('two-row flag trace did not sustain')
    return rows, result['trace_digest']


def count_errors(streams, stimuli, indexes, channel, phase, lag,
                 target_bit, inverted):
    return sum(
        (streams[index][symbol * VISITS_PER_SYMBOL + phase][channel] ^
         inverted) !=
        ((stimuli[index]['middle'][symbol + lag] >> target_bit) & 1)
        for index in indexes for symbol in SYMBOL_INDEXES)


def screen(streams, stimuli, target_bit):
    checks = len(TRAIN) * len(SYMBOL_INDEXES)
    minimum = checks
    exact_train = exact_all = 0
    best = None
    variable = []
    for channel, name in enumerate(CHANNELS):
        values = {row[channel] for stream in streams.values() for row in stream}
        if len(values) < 2:
            continue
        variable.append(name)
        for lag in LAGS:
            for phase in range(VISITS_PER_SYMBOL):
                raw = count_errors(streams, stimuli, TRAIN, channel,
                                   phase, lag, target_bit, False)
                inverted = raw > checks // 2
                train = min(raw, checks - raw)
                minimum = min(minimum, train)
                exact_train += train == 0
                if train > 3:
                    continue
                holdout = count_errors(streams, stimuli, HOLDOUT, channel,
                                       phase, lag, target_bit, inverted)
                exact_all += train == holdout == 0
                row = dict(channel=name, phase_visit=phase, symbol_lag=lag,
                           inverted=inverted, training_errors=train,
                           holdout_errors=holdout)
                if best is None or (
                        train + holdout, holdout, train, phase) < (
                        best['training_errors'] + best['holdout_errors'],
                        best['holdout_errors'], best['training_errors'],
                        best['phase_visit']):
                    best = row
    return dict(target_bit=target_bit, variable_channels=variable,
                minimum_training_errors=minimum,
                exact_training_candidates=exact_train,
                exact_training_and_holdout_candidates=exact_all,
                best_at_most_three_training_errors=best)


def run(out=HERE / 'results/receiver-two-row-flag-screen.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), SELECTED_MASK)
    _, base = fixture()
    stimuli = sequences()
    selected = sorted(set(TRAIN + HOLDOUT))
    streams, digests = {}, {}
    for index in selected:
        streams[index], digests[index] = capture(mapping, base,
                                                 stimuli[index]['middle'])
    if len(set(digests.values())) != len(selected):
        raise ValueError('two-row flag stimulus traces collapsed')
    results = [screen(streams, stimuli, bit) for bit in (0, 1)]
    paths = [Path(__file__), HERE / 'receiver_two_row_decision_screen.py',
             HERE / 'joint_upper_receive_bit_screen.py',
             HERE / 'joint_upper_source_screen.py',
             HERE / 'lower_i_d3f8_full_adc.py',
             HERE / 'lower_i_d3f8_upper_d_route.py',
             HERE / 'lower_i_d3f8_upper_symbol_screen.py',
             HERE / 'photo_controller_path.py', HERE / 'reference_modem.py',
             HERE / 'split_slice_probe.py',
             HERE.parent / 'assumed/execute.py', HERE.parent / 'model.py',
             MAPPINGS['q3'],
             HERE / 'results/joint-upper-source-mask08-mapping.json',
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(
        status='fixed-phase ALU flag decision screen on the interleaved 3EF/3F7 ADC path',
        fixture=dict(mapping='joint upper-source mask 08',
                     dispatch='scenario sequence [0,2] at 3EC',
                     adc='complementary 127-PCM, 94/94/94/93 visit holds',
                     channels=list(CHANNELS),
                     row0_flags='latest 3EF-3F2 flags held until subsequent 3FA',
                     row2_flags='3F7-3FA flags from current ADC visit',
                     visits_per_symbol=VISITS_PER_SYMBOL,
                     symbol_indexes=list(SYMBOL_INDEXES), lags=list(LAGS),
                     train_indexes=list(TRAIN), holdout_indexes=list(HOLDOUT),
                     polarities='both'),
        stimuli=[dict(index=index, **stimuli[index], trace_digest=digests[index])
                 for index in selected],
        results=results,
        limitations=[
            'Only single flags at one fixed symbol phase are tested; no multi-sample or externally clocked decision is ruled out.',
            'ALU flags are modeled under an assumed instruction map and are not traced to USART RxD.',
            'The two-row dispatch, ADC bus, sample clock and condition source remain wiring/timing hypotheses.'],
        source_sha256={str(path.relative_to(HERE.parents[2])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    for row in report['results']:
        print(row['target_bit'], len(row['variable_channels']),
              row['minimum_training_errors'],
              row['exact_training_candidates'],
              row['exact_training_and_holdout_candidates'],
              row['best_at_most_three_training_errors'])
