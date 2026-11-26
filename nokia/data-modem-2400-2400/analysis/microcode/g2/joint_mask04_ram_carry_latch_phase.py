"""Screen sample-paced 3FA Y latch phases on the sustained RAM echo route."""

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

import joint_mask04_external_ram_echo_screen as echo
from joint_upper_ram_feedback_screen import instrumented_execute
from joint_upper_source_screen import candidate
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_four_row_condition_screen import configured


def difference(left, right, sample_indices):
    pairs = [(left[i], right[i]) for i in sample_indices]
    return dict(mean_absolute_code_difference=
                sum(abs(a - b) for a, b in pairs) / len(pairs),
                unequal_samples=sum(a != b for a, b in pairs))


def run(out=HERE / 'results/joint-mask04-ram-carry-latch-phase.json'):
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
        for route, feedback in (('write_only', False), ('high_return', True)):
            scenario = configured(base, adc, 'previous', 'carry', 1)
            scenario.update(external_ram_feedback=feedback,
                            external_ram_write=True, external_ram_lane='high',
                            external_ram_latch_pc=0x3F9,
                            external_ram_read_pc=0x3FA,
                            external_ram_read_offset=-3,
                            external_ram_write_until=4 * echo.TRAIN_VISITS,
                            external_ram_address_tick_visits=[4 * tick for tick in starts])
            result = execute(mapping, scenario, echo.CYCLES,
                             mode='integrated', trace_limit=0)
            if (not result['clean'] or result['completed_cycles'] != echo.CYCLES or
                    result['address_counts'].get(0x3F8, 0) != echo.VISITS or
                    result['edge_counts'].get('3ed->3ee', 0)):
                raise ValueError(('receive loop did not sustain', stimulus, route))
            values = result['external_ram_candidate']['y_by_pc'][0x3FA]
            if len(values) != echo.VISITS:
                raise ValueError(('wrong 3FA capture length', stimulus, route))
            changing_samples = sum(
                len(set(values[starts[sample]:
                               starts[sample + 1] if sample + 1 < echo.SAMPLES
                               else echo.VISITS])) > 1
                for sample in range(echo.SAMPLES))
            captured[(stimulus, route)] = values
            cases.append(dict(stimulus=stimulus, route=route,
                              adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                              trace_digest=result['trace_digest'],
                              y3fa_sha256=hashlib.sha256(bytes(values)).hexdigest(),
                              samples_with_within_sample_y_change=changing_samples))
            print(stimulus, route, flush=True)
    windows = dict(early=range(0, 32), late=range(96, 128),
                   tail=range(128, echo.SAMPLES))
    phases = []
    for phase in range(46):
        selected = {key: [values[starts[sample] + phase]
                          for sample in range(echo.SAMPLES)]
                    for key, values in captured.items()}
        routes = {}
        for route in ('write_only', 'high_return'):
            routes[route] = {}
            for window, indices in windows.items():
                take = lambda name: selected[(name, route)]
                routes[route][window] = dict(
                    own_vs_zero=difference(take('own_echo'), take('zero'), indices),
                    remote_vs_zero=difference(take('independent_remote'),
                                              take('zero'), indices),
                    mixed_vs_remote=difference(take('remote_plus_echo'),
                                               take('independent_remote'), indices))
        phases.append(dict(phase=phase, routes=routes))
    paired = []
    for row in phases:
        control = row['routes']['write_only']['late']
        feedback = row['routes']['high_return']['late']
        paired.append(dict(phase=row['phase'],
                           control_mixed_remote=control['mixed_vs_remote']['mean_absolute_code_difference'],
                           feedback_mixed_remote=feedback['mixed_vs_remote']['mean_absolute_code_difference'],
                           control_own_zero=control['own_vs_zero']['mean_absolute_code_difference'],
                           feedback_own_zero=feedback['own_vs_zero']['mean_absolute_code_difference'],
                           control_remote_zero=control['remote_vs_zero']['mean_absolute_code_difference'],
                           feedback_remote_zero=feedback['remote_vs_zero']['mean_absolute_code_difference']))
    attenuating = [row['phase'] for row in paired
                   if (row['feedback_mixed_remote'] < row['control_mixed_remote'] and
                       row['feedback_remote_zero'] >= row['control_remote_zero'] / 2)]
    report = dict(experiment='sample-paced 3FA Y latch phase screen',
                  fixture=dict(condition='previous carry, polarity 1',
                               ram='3F9 Y high nibble, sample-paced write, -3 sample high-nibble 3FA return',
                               candidate_latch='one 3FA Y byte per held ADC sample at fixed visit offset 0..45',
                               samples=echo.SAMPLES, visits=echo.VISITS,
                               cycles=echo.CYCLES),
                  cases=cases, phases=phases, late_paired=paired,
                  late_attenuating_phases=attenuating,
                  limitations=[
                      'The output latch and its destination, RAM, TEST source, sample clock and ADC are assumed.',
                      'Absolute unsigned Y-byte difference is a code-space diagnostic, not an analog line residual.',
                      'The attenuating-phase screen requires mixed-versus-remote code contrast to fall and at least half the control remote response; no candidate under this rule proves C4.'
                  ])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
