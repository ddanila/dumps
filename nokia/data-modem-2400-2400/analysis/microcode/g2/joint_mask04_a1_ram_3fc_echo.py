"""Challenge held A1 mode plus delayed 3FC RAM return on echo controls."""

import hashlib
import json
from pathlib import Path

import joint_mask04_external_ram_echo_screen as echo
from joint_mask04_ram_carry_echo_screen import metric
from joint_upper_ram_feedback_screen import instrumented_execute
from joint_upper_source_screen import candidate
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_four_row_condition_screen import configured

HERE = Path(__file__).resolve().parent
PRIOR = HERE / 'results/joint-mask04-ram-carry-3fd-echo-screen.json'
STIMULI = ('zero', 'own_echo', 'independent_remote', 'remote_plus_echo')
ROUTES = (('write_only', False), ('high_return_3fc', True))


def run(out=HERE / 'results/joint-mask04-a1-ram-3fc-echo.json'):
    execute = instrumented_execute()
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    starts = echo.sample_starts()
    saved = json.loads(PRIOR.read_text())
    training = echo.training_inputs()
    if set(training) != set(STIMULI):
        raise ValueError('echo input fixture changed')
    captured = {}
    cases = []
    for stimulus in STIMULI:
        samples = training[stimulus] + [0] * echo.TAIL_SAMPLES
        adc = [value for index, value in enumerate([127 - x for x in samples])
               for _ in range(47 if index % 8 < 7 else 46)]
        if len(adc) != echo.VISITS:
            raise ValueError('ADC schedule changed')
        for route, feedback in ROUTES:
            scenario = configured(base, adc, 'previous', 'carry', 1)
            scenario['io']['read']['pc_sequences'][str(0x3EB)] = [0xA1] * (
                4 * echo.VISITS + 1)
            scenario['io']['read']['evidence'] += (
                '; held controller A1 frame byte to 3EB is a wiring hypothesis')
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
            if (not result['clean'] or
                    result['completed_cycles'] != echo.CYCLES or
                    result['address_counts'].get(0x3F8) != echo.VISITS or
                    result['address_counts'].get(0x3EB) != 4 * echo.VISITS + 1 or
                    result['edge_counts'].get('3ed->3ee', 0)):
                raise ValueError(('A1 receive loop did not sustain',
                                  stimulus, route,
                                  result['address_counts'].get(0x3F8)))
            memory = result['external_ram_candidate']
            y = memory['y_by_pc'][0x3FD]
            if len(y) != echo.VISITS:
                raise ValueError(('3FD output count changed', stimulus, route))
            captured[(stimulus, route)] = y
            cases.append(dict(stimulus=stimulus, route=route,
                              adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                              trace_digest=result['trace_digest'],
                              y3fd_sha256=hashlib.sha256(bytes(y)).hexdigest(),
                              ram_sha256=hashlib.sha256(bytes(memory['bytes'])).hexdigest(),
                              writes=memory['writes'], reads=memory['reads'],
                              tail_changes_vs_control=None))
            print(stimulus, route, flush=True)
    by_key = {(c['stimulus'], c['route']): c for c in cases}
    baseline_cases = {(c['stimulus'], c['route']): c for c in saved['cases']}
    for stimulus in STIMULI:
        for route, _ in ROUTES:
            if (by_key[(stimulus, route)]['adc_sha256'] !=
                    baseline_cases[(stimulus, route)]['adc_sha256']):
                raise ValueError('mode test changed input samples')
        changed = captured[(stimulus, 'high_return_3fc')]
        control = captured[(stimulus, 'write_only')]
        by_key[(stimulus, 'high_return_3fc')]['tail_changes_vs_control'] = sum(
            a != b for a, b in zip(changed[echo.TRAIN_VISITS:],
                                   control[echo.TRAIN_VISITS:]))
    comparisons = {}
    for name, window in (('early', slice(0, 32 * 375 // 8)),
                         ('late', slice(96 * 375 // 8, echo.TRAIN_VISITS)),
                         ('tail', slice(echo.TRAIN_VISITS, echo.VISITS))):
        comparisons[name] = {}
        for route, _ in ROUTES:
            take = lambda key: captured[(key, route)]
            comparisons[name][route] = dict(
                own_vs_zero=metric(take('own_echo'), take('zero'), window),
                remote_vs_zero=metric(take('independent_remote'),
                                      take('zero'), window),
                mixed_vs_remote=metric(take('remote_plus_echo'),
                                       take('independent_remote'), window))
    phase_rows = []
    for phase in range(46):
        selected = {key: [values[starts[sample] + phase]
                          for sample in range(echo.SAMPLES)]
                    for key, values in captured.items()}
        row = dict(phase=phase)
        for name, window in (('early', slice(0, 32)),
                             ('late', slice(96, 128))):
            take = lambda key: selected[(key, 'high_return_3fc')]
            row[name] = dict(
                own_vs_zero=metric(take('own_echo'), take('zero'),
                                   window)['mean_absolute_code_difference'],
                remote_vs_zero=metric(take('independent_remote'),
                                      take('zero'), window)[
                                          'mean_absolute_code_difference'],
                mixed_vs_remote=metric(take('remote_plus_echo'),
                                       take('independent_remote'), window)[
                                           'mean_absolute_code_difference'])
        phase_rows.append(row)
    attenuating = [r['phase'] for r in phase_rows
                   if r['late']['own_vs_zero'] < r['early']['own_vs_zero']
                   and r['late']['mixed_vs_remote'] <
                   r['early']['mixed_vs_remote']
                   and r['late']['remote_vs_zero'] > 0]
    report = dict(experiment='held A1 frame mode with delayed 3FC RAM return',
                  fixture=dict(mode_3eb='A1 on every wrapper visit',
                               return_route='3F9 Y high -> sample-paced RAM, offset -3 -> 3FC D high',
                               conditions='previous carry, polarity 1',
                               output='executed 3FD Y',
                               controls='same-input write-only, zero, own, remote, mixed',
                               train_samples=echo.TRAIN_SAMPLES,
                               tail_samples=echo.TAIL_SAMPLES,
                               visits=echo.VISITS, cycles=echo.CYCLES),
                  cases=cases, comparisons=comparisons,
                  phase_training_comparisons=phase_rows,
                  late_attenuating_phases=attenuating,
                  limitations=[
                      'The A1-to-3EB connection, RAM mux, TEST, 3FD output latch, ADC and sample clock are assumptions.',
                      'Unsigned 3FD Y-byte contrast is a code diagnostic, not a measured analog residual.',
                      'A falling code contrast alone would not prove trained echo cancellation.'
                  ],
                  source_sha256={str(p.relative_to(HERE.parents[4])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (Path(__file__), PRIOR,
                                           HERE / 'joint_mask04_ram_carry_3fd_echo_screen.py',
                                           HERE / 'joint_upper_ram_feedback_screen.py',
                                           HERE.parent / 'assumed/execute.py')})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    report = run()
    print('late attenuating phases', report['late_attenuating_phases'])
    for window in ('early', 'late'):
        print(window, {name: row['mean_absolute_code_difference']
                       for name, row in report['comparisons'][window][
                           'high_return_3fc'].items()})
