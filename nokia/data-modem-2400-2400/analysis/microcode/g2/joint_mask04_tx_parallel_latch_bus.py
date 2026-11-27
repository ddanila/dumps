"""Exercise a photo-compatible parallel LS273/LS373 transmit bus."""

import hashlib
import json
from pathlib import Path

from joint_mask04_tx_bank_phase import scenario_for
from joint_mask04_tx_12a_delayed_latch import capturing_execute
from joint_four_row_retention_tx import (
    MAPPINGS, SAMPLE_COUNT, SAMPLE_DIVISOR, TXREADY, candidate, fixture,
    mapped, mapping_with_upper_source,
)
from photo_main_dibit_pulse import VISITS_PER_SYMBOL
from photo_joint_tone_training_data import TOTAL_SYMBOLS

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
PRIOR = RESULTS / 'joint-mask04-tx-12a-delayed-latch.json'
PINS = RESULTS / 'photo-ded-latch-pin-pairing.json'
FRONT = HERE.parents[2] / 'photos/PXL_20261123_114854803.jpg'
OUT = RESULTS / 'joint-mask04-tx-parallel-latch-bus.json'


def run(out=OUT):
    prior = json.loads(PRIOR.read_text())
    pins = json.loads(PINS.read_text())
    if pins['inferred_function_counts'] != {
            'output_to_output': 4, 'data_to_data': 4, 'output_to_data': 0}:
        raise ValueError('photo-inferred latch pairing changed')
    if {(row['ls273_signal'], row['ls373_signal']) for row in pins['pairings']} != {
            (f'{n}Q', f'{9 - n}Q') for n in range(5, 9)} | {
            (f'{n}D', f'{9 - n}D') for n in range(5, 9)}:
        raise ValueError('photo-inferred latch bit order changed')
    controller = json.loads(TXREADY.read_text())
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    execute = capturing_execute()
    cycles = (TOTAL_SYMBOLS * VISITS_PER_SYMBOL + 64) * 4
    cases = []
    for selector in ('40', '60'):
        controller_case = next(row for row in controller['cases']
                               if row['selector'] == selector)
        result = execute(mapping, scenario_for(base, controller_case, 256),
                         cycles, mode='integrated', trace_limit=0)
        saved = next(row for row in prior['cases'] if row['selector'] == selector)
        if not result['clean'] or result['completed_cycles'] != cycles:
            raise ValueError(('PROM run did not complete', selector))
        if result['trace_digest'] != saved['trace_digests']['256']:
            raise ValueError(('controller/PROM trace changed', selector))
        at_12a = result['site_y'][0x12A]
        at_127 = result['site_y'][0x127]
        direct = [at_12a[SAMPLE_DIVISOR * n] for n in range(SAMPLE_COUNT)]
        late = [at_127[SAMPLE_DIVISOR * n + 1] for n in range(SAMPLE_COUNT)]
        if (hashlib.sha256(bytes(direct)).hexdigest() !=
                saved['phases'][0]['banks']['256']['raw_y_sha256'] or
                hashlib.sha256(bytes(late)).hexdigest() !=
                saved['phases'][1]['banks']['256']['raw_y_sha256']):
            raise ValueError(('latch samples differ from prior execution', selector))
        # The four visible D-D and Q-Q pairs correspond to LS273 bits 5-8.
        # Immediately before an early LS273 clock, its Q pins still hold the
        # previous sample while a transparent LS373 presents current Y.
        before = [n for n in range(1, SAMPLE_COUNT)
                  if (direct[n - 1] ^ direct[n]) & 0xF0]
        differing_bits = sum(((direct[n - 1] ^ direct[n]) >> bit) & 1
                             for n in range(1, SAMPLE_COUNT)
                             for bit in range(4, 8))
        cases.append(dict(selector=selector,
                          trace_digest=result['trace_digest'],
                          sample_count=SAMPLE_COUNT,
                          direct_early_y_sha256=hashlib.sha256(bytes(direct)).hexdigest(),
                          late_y_sha256=hashlib.sha256(bytes(late)).hexdigest(),
                          early_vs_late_changed=sum(a != b for a, b in zip(direct, late)),
                          active_parallel_q_conflict_before_clock_samples=len(before),
                          active_parallel_q_conflict_before_clock_bits=differing_bits,
                          first_conflict_sample_indices=before[:24],
                          saved_early_data_errors_by_bus=[score['filtered_data_errors']
                              for score in saved['phases'][0]['banks']['256']['bus_scores']],
                          saved_late_data_errors_by_bus=[score['filtered_data_errors']
                              for score in saved['phases'][1]['banks']['256']['bus_scores']]))
        print('parallel latch', selector, 'pre-clock Q conflicts', len(before),
              'of', SAMPLE_COUNT - 1, 'early/late differences',
              cases[-1]['early_vs_late_changed'], flush=True)
    paths = (Path(__file__), PRIOR, PINS, TXREADY, FRONT,
             HERE / 'joint_mask04_tx_bank_phase.py',
             HERE / 'joint_mask04_tx_12a_delayed_latch.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='photo-compatible parallel D-D/Q-Q transmit latch timing',
                  model=dict(
                      visible_front_pairs='four LS273 D5-D8 to LS373 D4-D1 and four matching Q-Q tracks',
                      input='assume all eight LS273 D pins see the executed Y byte; visible four D-D pairs share Y with LS373',
                      direct_early='LS273 clocks after 12A Y settles and before next 127 Y settles',
                      control_late='LS273 clocks after next 127 Y settles',
                      contention_control='LS373 output enable is inactive whenever transparent Q differs from held LS273 Q on the four tied lines',
                      analog='use only the saved candidate DAC bus/filter scores; physical DAC08/line nets remain untraced'),
                  cases=cases,
                  limitations=[
                      'Pin pairing is photo-suggested, not proven pad continuity; the LS273 Y input, clock, LS373 output-enable and DAC nets are assumed.',
                      'A logic-level bus disagreement predicts contention only if both Q outputs are electrically enabled; no current or voltage is measured.',
                      'This run checks the direct early-capture topology against the late control, but cannot establish physical propagation order.',
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    run()
