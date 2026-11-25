"""Screen symbol-timed D3F8 state bits against known reference dibits."""

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from lower_i_d3f8_adc_cross_symbols import PATTERNS
from lower_i_d3f8_adc_decoder_screen import scenario_for
from lower_i_d3f8_sign_adc import LONG_CYCLES, LONG_VISITS, adc_stream, condition_scenario
from lower_i_prom_data_route import mapping_for
from photo_controller_path import fixture

VISITS_PER_SYMBOL = 1500
SYMBOL_INDEXES = tuple(range(2, 14))
LAGS = (-2, -1, 0, 1, 2)
TRAIN = (0, 1, 4)
HOLDOUT = (2, 3, 5)
CHANNELS = ('Y3F8', 'Y3F9', 'Y3FA', 'Q') + tuple(f'R{i}' for i in range(16))


def capture(mapping, base, pattern):
    values = adc_stream(pattern, 16, 128)
    scenario = scenario_for(condition_scenario(base, 'previous'), values)
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, LONG_CYCLES, mode='integrated',
                         out=temporary, trace_limit=LONG_CYCLES)
        if (not result['clean'] or result['address_counts'].get(0x3F8, 0) != LONG_VISITS or
                result['read_sequence_visits'].get(0x3F8, 0) != LONG_VISITS):
            raise ValueError(('symbol trace did not sustain', pattern))
        ram = scenario['initial']['ram'][:]
        y8 = y9 = None
        rows = []
        for line in (Path(temporary) / 'trace.jsonl').open():
            record = json.loads(line)
            for address, value in record['registers'].items():
                ram[int(address)] = value
            pc = record['pc']
            if pc == 0x3F8:
                if not record['external_read'].get('selected_by_alu'):
                    raise ValueError('D3F8 input not selected')
                if record['external_read']['value'] != values[len(rows)]:
                    raise ValueError('D3F8 input differs from offered byte')
                y8 = record['alu']['y']
            elif pc == 0x3F9:
                y9 = record['alu']['y']
            elif pc == 0x3FA:
                if y8 is None or y9 is None:
                    raise ValueError('incomplete D3F8/3F9/3FA visit')
                rows.append(bytes((y8, y9, record['alu']['y'], record['q'], *ram)))
                y8 = y9 = None
        if len(rows) != LONG_VISITS:
            raise ValueError(('symbol trace visit count changed', len(rows)))
    return rows, result['trace_digest']


def run(out=HERE / 'results/lower-i-d3f8-symbol-bit-screen.json'):
    mapping = mapping_for('!10.6', '11.2')
    _, base = fixture()
    rows = []
    digests = []
    for pattern in PATTERNS:
        visits, digest = capture(mapping, base, pattern)
        rows.append(visits)
        digests.append(digest)
    if len(set(digests)) != len(digests):
        raise ValueError('symbol traces are not distinct across patterns')
    results = []
    checks_per_set = len(TRAIN) * len(SYMBOL_INDEXES)
    for target_bit in (0, 1):
        best = None
        perfect_train = 0
        perfect_both = 0
        min_train = checks_per_set
        for channel in range(len(CHANNELS)):
            for bit in range(8):
                for lag in LAGS:
                    for phase in range(VISITS_PER_SYMBOL):
                        errors = 0
                        for pattern_index in TRAIN:
                            pattern = PATTERNS[pattern_index]
                            visits = rows[pattern_index]
                            for symbol in SYMBOL_INDEXES:
                                observed = (visits[symbol * VISITS_PER_SYMBOL + phase][channel] >> bit) & 1
                                expected = (pattern[(symbol + lag) % 4] >> target_bit) & 1
                                errors += observed != expected
                        inverted = errors > checks_per_set // 2
                        train_errors = min(errors, checks_per_set - errors)
                        min_train = min(min_train, train_errors)
                        if train_errors == 0:
                            perfect_train += 1
                        if train_errors > 4:
                            continue
                        holdout_errors = 0
                        for pattern_index in HOLDOUT:
                            pattern = PATTERNS[pattern_index]
                            visits = rows[pattern_index]
                            for symbol in SYMBOL_INDEXES:
                                observed = ((visits[symbol * VISITS_PER_SYMBOL + phase][channel] >> bit) & 1) ^ inverted
                                expected = (pattern[(symbol + lag) % 4] >> target_bit) & 1
                                holdout_errors += observed != expected
                        if train_errors == 0 and holdout_errors == 0:
                            perfect_both += 1
                        candidate = dict(channel=CHANNELS[channel], bit=bit,
                                         phase_visit=phase, symbol_lag=lag,
                                         inverted=inverted,
                                         training_errors=train_errors,
                                         holdout_errors=holdout_errors)
                        if best is None or (train_errors + holdout_errors,
                                            holdout_errors, train_errors) < (
                                                best['training_errors'] + best['holdout_errors'],
                                                best['holdout_errors'], best['training_errors']):
                            best = candidate
        results.append(dict(dibit_bit=target_bit,
                            checks_per_set=checks_per_set,
                            minimum_training_errors=min_train,
                            perfect_training_candidates=perfect_train,
                            perfect_train_and_holdout_candidates=perfect_both,
                            best_low_training_error_candidate=best))
    paths = [Path(__file__), HERE / 'lower_i_d3f8_sign_adc.py',
             HERE / 'lower_i_d3f8_adc_cross_symbols.py',
             HERE / 'lower_i_d3f8_adc_decoder_screen.py',
             HERE / 'lower_i_prom_data_route.py', HERE / 'photo_controller_path.py',
             HERE / 'split_slice_probe.py', HERE / 'reference_modem.py',
             HERE.parent / 'assumed/execute.py', HERE.parent / 'model.py',
             HERE.parents[2] / 'am27s31dc-prom/nokia-modem-am27s31dc.bin']
    report = dict(status='symbol-timed direct-bit screen of sustained D3F8 state',
                  fixture=dict(mapping='I7/A0=!10.6, I0/A1=11.2, lower I6=11.0',
                               condition_select_0='inverted previous sign',
                               input='complementary ADC bit0 to held D3F8 03/05',
                               patterns=[list(pattern) for pattern in PATTERNS],
                               sample_window=[64, 192],
                               visits_per_symbol=VISITS_PER_SYMBOL,
                               symbol_indexes=list(SYMBOL_INDEXES),
                               training_pattern_indexes=list(TRAIN),
                               holdout_pattern_indexes=list(HOLDOUT),
                               tested_symbol_lags=list(LAGS),
                               channels=list(CHANNELS)),
                  trace_digests=digests,
                  direct_bit_results=results,
                  limitations=[
                      'The candidate ADC decoder, condition source, clock and physical output route are untraced.',
                      'Only direct or inverted bits of Y at three PCs, Q and RAM are screened; a coded, differential or multiword decision could be missed.',
                      'Six periodic symbol streams and one Q/RAM seed are used; any correlation needs independent validation.',
                      'An internal bit fit is not a physical USART-01 RxD observation or proof of demodulation.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path,
                        default=HERE / 'results/lower-i-d3f8-symbol-bit-screen.json')
    args = parser.parse_args()
    report = run(args.out)
    print([(row['dibit_bit'], row['minimum_training_errors'],
            row['perfect_train_and_holdout_candidates'])
           for row in report['direct_bit_results']])
