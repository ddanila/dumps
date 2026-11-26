"""Challenge the 3FC RAM return at its changed downstream 3FD output."""

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

import joint_mask04_external_ram_echo_screen as echo
from joint_mask04_ram_carry_echo_screen import metric
from joint_upper_ram_feedback_screen import instrumented_execute
from joint_upper_source_screen import candidate
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_four_row_condition_screen import configured

ROUTES = (('write_only', False), ('high_return_3fc', True))


def comparisons(captured, window):
    result = {}
    for route, _ in ROUTES:
        take = lambda name: captured[(name, route)]
        result[route] = dict(
            own_vs_zero=metric(take('own_echo'), take('zero'), window),
            remote_vs_zero=metric(take('independent_remote'),
                                  take('zero'), window),
            mixed_vs_remote=metric(take('remote_plus_echo'),
                                   take('independent_remote'), window),
            mixed_vs_own=metric(take('remote_plus_echo'),
                                take('own_echo'), window))
    return result


def run(out=HERE / 'results/joint-mask04-ram-carry-3fd-echo-screen.json'):
    execute = instrumented_execute()
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    starts = echo.sample_starts()
    captured = {}
    cases = []
    for stimulus, prefix in echo.training_inputs().items():
        samples = prefix + [0] * echo.TAIL_SAMPLES
        adc = [value for index, value in enumerate([127 - x for x in samples])
               for _ in range(47 if index % 8 < 7 else 46)]
        if len(adc) != echo.VISITS:
            raise ValueError('ADC schedule changed')
        for route, feedback in ROUTES:
            scenario = configured(base, adc, 'previous', 'carry', 1)
            scenario.update(external_ram_feedback=feedback,
                            external_ram_write=True,
                            external_ram_lane='high',
                            external_ram_latch_pc=0x3F9,
                            external_ram_read_pc=0x3FC,
                            external_ram_read_offset=-3,
                            external_ram_write_until=4 * echo.TRAIN_VISITS,
                            external_ram_address_tick_visits=[4 * tick
                                                              for tick in starts])
            result = execute(mapping, scenario, echo.CYCLES,
                             mode='integrated', trace_limit=0)
            if (not result['clean'] or result['completed_cycles'] != echo.CYCLES or
                    result['address_counts'].get(0x3F8, 0) != echo.VISITS or
                    result['edge_counts'].get('3ed->3ee', 0)):
                raise ValueError(('receive loop did not sustain', stimulus, route))
            memory = result['external_ram_candidate']
            y = memory['y_by_pc'][0x3FD]
            if len(y) != echo.VISITS:
                raise ValueError(('wrong 3FD capture length', stimulus, route))
            captured[(stimulus, route)] = y
            varying_samples = sum(
                len(set(y[starts[sample]:
                          starts[sample + 1] if sample + 1 < echo.SAMPLES
                          else echo.VISITS])) > 1
                for sample in range(echo.SAMPLES))
            cases.append(dict(stimulus=stimulus, route=route,
                              adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                              trace_digest=result['trace_digest'],
                              y3fd_sha256=hashlib.sha256(bytes(y)).hexdigest(),
                              ram_sha256=hashlib.sha256(bytes(memory['bytes'])).hexdigest(),
                              writes=memory['writes'], reads=memory['reads'],
                              samples_with_within_sample_y_change=varying_samples))
            print(stimulus, route, flush=True)
    by_key = {(row['stimulus'], row['route']): row for row in cases}
    for stimulus in echo.training_inputs():
        changed = captured[(stimulus, 'high_return_3fc')]
        control = captured[(stimulus, 'write_only')]
        by_key[(stimulus, 'high_return_3fc')]['tail_changes_vs_control'] = (
            sum(a != b for a, b in zip(changed[echo.TRAIN_VISITS:],
                                      control[echo.TRAIN_VISITS:])))
    windows = dict(early=slice(0, 32 * 375 // 8),
                   late=slice(96 * 375 // 8, echo.TRAIN_VISITS),
                   tail=slice(echo.TRAIN_VISITS, echo.VISITS))
    full_visit = {name: comparisons(captured, window)
                  for name, window in windows.items()}
    phase_rows = []
    for phase in range(46):
        selected = {key: [values[starts[sample] + phase]
                          for sample in range(echo.SAMPLES)]
                    for key, values in captured.items()}
        row = dict(phase=phase)
        for window, interval in (('early', slice(0, 32)),
                                 ('late', slice(96, 128))):
            measured = comparisons(selected, interval)['high_return_3fc']
            row[window] = {name: item['mean_absolute_code_difference']
                           for name, item in measured.items()}
        phase_rows.append(row)
    attenuating_phases = [row['phase'] for row in phase_rows
                         if (row['late']['mixed_vs_remote'] <
                             row['early']['mixed_vs_remote'] and
                             row['late']['own_vs_zero'] <
                             row['early']['own_vs_zero'] and
                             row['late']['remote_vs_zero'] > 0)]
    report = dict(experiment='3FC RAM return: 3FD own-echo/remote output challenge',
                  fixture=dict(condition='previous carry, polarity 1',
                               ram='3F9 Y high nibble -> sample-paced RAM -> -3 sample 3FC D high nibble',
                               output='executed 3FD Y, with one 3FD visit per ADC visit',
                               controls='same-input write-only; own echo; remote; mixed; zero',
                               train_samples=echo.TRAIN_SAMPLES,
                               tail_samples=echo.TAIL_SAMPLES,
                               visits=echo.VISITS, cycles=echo.CYCLES),
                  cases=cases, full_visit_comparisons=full_visit,
                  phase_training_comparisons=phase_rows,
                  late_attenuating_phases=attenuating_phases,
                  limitations=[
                      'The external RAM mux, TEST, 3FD output latch, ADC and sample clock are assumed.',
                      'Unsigned 3FD Y-byte differences are code-space diagnostics, not measured line residuals.',
                      'The phase screen requires both own-echo contrasts to fall from early to late training while retaining remote response; no code-space reduction alone proves C4.'
                  ])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
