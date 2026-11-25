"""Search direct state-bit receive decisions on the joint TX/ADC field map."""

import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from joint_upper_source_screen import SELECTED_MASK, candidate
from lower_i_d3f8_full_adc import (
    LONG_CYCLES, LONG_SAMPLES, LONG_VISITS, SAMPLE_START,
    hold, scenario_for_full_byte,
)
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from lower_i_d3f8_upper_symbol_screen import (
    CHANNELS, LAGS, SYMBOL_INDEXES, VISITS_PER_SYMBOL, sequences,
)
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from reference_modem import receive, transmit

TRAIN = (0, 1, 6)
HOLDOUT = (2, 7, 8, 9)
TARGET_BITS = (0, 1)


def capture(mapping, base, middle):
    dibits = [0] * 8 + middle + [0] * 8
    pcm = transmit(dibits)
    if receive(pcm) != dibits[1:]:
        raise ValueError('reference receiver did not recover stimulus')
    values = hold([127 - sample for sample in
                   pcm[SAMPLE_START:SAMPLE_START + LONG_SAMPLES]])
    scenario = scenario_for_full_byte(base, values, 'complementary')
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, LONG_CYCLES,
                         mode='integrated', out=temporary,
                         trace_limit=LONG_CYCLES)
        if (not result['clean'] or
                result['address_counts'].get(0x3F8, 0) != LONG_VISITS or
                result['read_sequence_visits'].get(0x3F8, 0) != LONG_VISITS):
            raise ValueError('joint receive trace did not sustain')
        ram = scenario['initial']['ram'][:]
        y8 = y9 = None
        rows = []
        for line in (Path(temporary) / 'trace.jsonl').open():
            record = json.loads(line)
            for address, value in record['registers'].items():
                ram[int(address)] = value
            pc = record['pc']
            if pc == 0x3F8:
                read = record['external_read']
                if (not read.get('selected_by_alu') or
                        read['value'] != values[len(rows)] or
                        record['instruction_i_high'] != 0xD5):
                    raise ValueError('joint D3F8 byte or instruction changed')
                y8 = record['alu']['y']
            elif pc == 0x3F9:
                y9 = record['alu']['y']
            elif pc == 0x3FA:
                if y8 is None or y9 is None:
                    raise ValueError('incomplete D3F8/3F9/3FA visit')
                rows.append(bytes((y8, y9, record['alu']['y'], record['q'], *ram)))
                y8 = y9 = None
        if len(rows) != LONG_VISITS:
            raise ValueError(('joint receive visit count changed', len(rows)))
    return rows, result['trace_digest']


def count_errors(streams, stimuli, indexes, target_bit, channel, bit, phase,
                 lag, inverted):
    errors = 0
    for index in indexes:
        for symbol in SYMBOL_INDEXES:
            visit = symbol * VISITS_PER_SYMBOL + phase
            observed = ((streams[index][visit][channel] >> bit) & 1) ^ inverted
            expected = (stimuli[index]['middle'][symbol + lag] >> target_bit) & 1
            errors += observed != expected
    return errors


def run(out=HERE / 'results/joint-upper-receive-bit-screen.json'):
    receiver = mapping_with_upper_source(0, '17.6')
    transmitter = mapped(MAPPINGS['q3'])
    mapping = candidate(receiver, transmitter, SELECTED_MASK)
    _, base = fixture()
    stimuli = sequences()
    selected = sorted(set(TRAIN + HOLDOUT))
    streams = {}
    digests = {}
    for index in selected:
        rows, digest = capture(mapping, base, stimuli[index]['middle'])
        streams[index], digests[index] = rows, digest
    if len(set(digests.values())) != len(selected):
        raise ValueError('independent ADC stimulus digests collapsed')

    results = []
    checks_train = len(TRAIN) * len(SYMBOL_INDEXES)
    for target_bit in TARGET_BITS:
        minimum = checks_train
        exact_training = 0
        exact_train_and_holdout = 0
        best = None
        for channel in range(len(CHANNELS)):
            for bit in range(8):
                for lag in LAGS:
                    for phase in range(VISITS_PER_SYMBOL):
                        raw_train = count_errors(streams, stimuli, TRAIN,
                                                 target_bit, channel, bit,
                                                 phase, lag, False)
                        inverted = raw_train > checks_train // 2
                        train_errors = min(raw_train, checks_train - raw_train)
                        minimum = min(minimum, train_errors)
                        if train_errors == 0:
                            exact_training += 1
                        if train_errors > 3:
                            continue
                        holdout_errors = count_errors(
                            streams, stimuli, HOLDOUT, target_bit, channel,
                            bit, phase, lag, inverted)
                        if train_errors == holdout_errors == 0:
                            exact_train_and_holdout += 1
                        row = dict(channel=CHANNELS[channel], bit=bit,
                                   phase_visit=phase, symbol_lag=lag,
                                   inverted=inverted,
                                   training_errors=train_errors,
                                   holdout_errors=holdout_errors)
                        if best is None or (
                                train_errors + holdout_errors,
                                holdout_errors, train_errors, phase) < (
                                best['training_errors'] + best['holdout_errors'],
                                best['holdout_errors'],
                                best['training_errors'], best['phase_visit']):
                            best = row
        results.append(dict(target_bit=target_bit,
                            minimum_training_errors=minimum,
                            exact_training_candidates=exact_training,
                            exact_train_and_holdout_candidates=exact_train_and_holdout,
                            best_low_training_error_candidate=best))

    paths = [Path(__file__), HERE / 'joint_upper_source_screen.py',
             HERE / 'lower_i_d3f8_upper_symbol_screen.py',
             HERE / 'lower_i_d3f8_full_adc.py',
             HERE / 'photo_controller_path.py',
             HERE / 'reference_modem.py',
             HERE / 'split_slice_probe.py',
             HERE.parent / 'assumed/execute.py', HERE.parent / 'model.py',
             MAPPINGS['q3'],
             HERE / 'results/joint-upper-source-mask08-mapping.json',
             HERE.parents[2] / 'am27s31dc-prom/nokia-modem-am27s31dc.bin',
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(status='direct fixed-phase state-bit receive-decision screen under joint TX/ADC map',
                  fixture=dict(mapping='joint upper-source mask 08',
                               adc='127 minus reference PCM, held 188/187 D3F8 visits per sample',
                               upper_instruction_at_d3f8='D5',
                               channels=list(CHANNELS),
                               visits_per_symbol=VISITS_PER_SYMBOL,
                               symbol_indexes=list(SYMBOL_INDEXES),
                               lags=list(LAGS),
                               train_indexes=list(TRAIN),
                               holdout_indexes=list(HOLDOUT),
                               polarity='both',
                               receiver='independent reference decoder validates stimuli'),
                  stimuli=[dict(index=index, **stimuli[index], trace_digest=digests[index])
                           for index in selected],
                  results=results,
                  limitations=[
                      'Only one direct bit of Y, Q or RAM at one fixed symbol phase is tested; no coded or multi-sample decision is ruled out.',
                      'The upper instruction, ADC ingress, sample clock and condition mux are untraced.',
                      'Any internal bit fit still needs a route to USART RxD and independent echo-path evidence.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    print([(row['target_bit'], row['minimum_training_errors'],
            row['exact_training_candidates'],
            row['exact_train_and_holdout_candidates'])
           for row in report['results']])
