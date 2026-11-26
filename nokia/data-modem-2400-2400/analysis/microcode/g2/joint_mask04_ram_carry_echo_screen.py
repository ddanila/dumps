"""Challenge the surviving previous-carry high-RAM route with own/remote mixtures."""

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

import joint_mask04_external_ram_echo_screen as prior
from joint_upper_ram_feedback_screen import instrumented_execute
from joint_upper_source_screen import candidate
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_four_row_condition_screen import configured

ROUTES = (('write_only', False), ('high_return', True))


def metric(left, right, interval):
    a, b = left[interval], right[interval]
    return dict(mean_absolute_code_difference=
                sum(abs(x - y) for x, y in zip(a, b)) / len(a),
                unequal_visits=sum(x != y for x, y in zip(a, b)))


def run(out=HERE / 'results/joint-mask04-ram-carry-echo-screen.json'):
    execute = instrumented_execute()
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    starts = prior.sample_starts()
    inputs = prior.training_inputs()
    cases = []
    captured = {}
    for stimulus, prefix in inputs.items():
        offered = [127 - value for value in prefix + [0] * prior.TAIL_SAMPLES]
        adc = [value for index, value in enumerate(offered)
               for _ in range(47 if index % 8 < 7 else 46)]
        if len(adc) != prior.VISITS:
            raise ValueError('ADC schedule changed')
        for route, feedback in ROUTES:
            scenario = configured(base, adc, 'previous', 'carry', 1)
            scenario.update(external_ram_feedback=feedback,
                            external_ram_write=True,
                            external_ram_lane='high',
                            external_ram_latch_pc=0x3F9,
                            external_ram_read_pc=0x3FA,
                            external_ram_read_offset=-3,
                            external_ram_write_until=4 * prior.TRAIN_VISITS,
                            external_ram_address_tick_visits=[4 * tick for tick in starts])
            result = execute(mapping, scenario, prior.CYCLES,
                             mode='integrated', trace_limit=0)
            memory = result['external_ram_candidate']
            y = memory['y_by_pc']
            captured[(stimulus, route)] = y
            cases.append(dict(stimulus=stimulus, route=route,
                              input_sha256=hashlib.sha256(bytes(offered)).hexdigest(),
                              adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                              clean=result['clean'], cycles=result['completed_cycles'],
                              adc_visits=result['address_counts'].get(0x3F8, 0),
                              loop_exits=result['edge_counts'].get('3ed->3ee', 0),
                              final_pc=f"{result['final_state']['pc']:03X}",
                              trace_digest=result['trace_digest'],
                              first_changed_read=memory['first_changed_read'],
                              writes=memory['writes'], reads=memory['reads'],
                              ram_noninitial=sum(value != 1 for value in memory['bytes']),
                              ram_sha256=hashlib.sha256(bytes(memory['bytes'])).hexdigest(),
                              y3fa_sha256=hashlib.sha256(bytes(y[0x3FA])).hexdigest()))
            print(stimulus, route, cases[-1]['adc_visits'],
                  cases[-1]['loop_exits'], flush=True)
    by_key = {(case['stimulus'], case['route']): case for case in cases}
    windows = dict(early=slice(0, 32 * 375 // 8),
                   late=slice(96 * 375 // 8, prior.TRAIN_VISITS),
                   tail=slice(prior.TRAIN_VISITS, prior.VISITS))
    comparisons = {}
    for route, _ in ROUTES:
        if any(len(captured[(name, route)][0x3FA]) != prior.VISITS
               for name in inputs):
            comparisons[route] = None
            continue
        comparisons[route] = {}
        for window, interval in windows.items():
            take = lambda name: captured[(name, route)][0x3FA]
            comparisons[route][window] = dict(
                own_vs_zero=metric(take('own_echo'), take('zero'), interval),
                remote_vs_zero=metric(take('independent_remote'), take('zero'), interval),
                mixed_vs_remote=metric(take('remote_plus_echo'),
                                       take('independent_remote'), interval),
                mixed_vs_own=metric(take('remote_plus_echo'),
                                    take('own_echo'), interval))
    for case in cases:
        stimulus, route = case['stimulus'], case['route']
        if route == 'write_only':
            continue
        changed = captured[(stimulus, route)][0x3FA]
        control = captured[(stimulus, 'write_only')][0x3FA]
        case['tail_changes_vs_write_only'] = (
            sum(a != b for a, b in zip(changed[prior.TRAIN_VISITS:],
                                     control[prior.TRAIN_VISITS:]))
            if len(changed) == len(control) == prior.VISITS else None)
        case['same_trace_as_write_only'] = (
            case['trace_digest'] == by_key[(stimulus, 'write_only')]['trace_digest'])
    report = dict(experiment='previous-carry high-nibble RAM route on own echo and remote mixtures',
                  fixture=dict(train_samples=prior.TRAIN_SAMPLES,
                               tail_samples=prior.TAIL_SAMPLES,
                               adc_visits=prior.VISITS,
                               cycles=prior.CYCLES,
                               condition='previous ALU carry, polarity 1',
                               own_source='saved real-PROM call Y7 reconstructed PCM',
                               input_source='same four controls as corrected low-lane echo screen',
                               ram='3F9 Y high nibble to 256x8 sample-paced RAM, frozen after training',
                               return_path='RAM address minus three samples to 3FA D high nibble, D0=1'),
                  cases=cases, y3fa_code_space_comparisons=comparisons,
                  limitations=[
                      'RAM and TEST wiring, sample clock, ADC and line model are assumed.',
                      'Y3FA byte differences are code-space diagnostics, not measured analog residuals.',
                      'A candidate C4 pass requires selective late echo attenuation and a freeze response under sustained execution.'
                  ])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
