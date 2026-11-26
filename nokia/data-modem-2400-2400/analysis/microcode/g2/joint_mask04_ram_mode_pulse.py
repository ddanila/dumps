"""Check whether held controller-like D3EB bytes gate the candidate RAM pulse return."""

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
import joint_mask04_ram_pulse_freeze as pulse
import joint_mask04_receive_impulse_memory as impulse
from joint_upper_ram_feedback_screen import instrumented_execute
from joint_upper_source_screen import candidate
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_four_row_condition_screen import configured
from reference_modem import transmit

MODES = ('01', '81', 'A1', 'C1', '81_to_A1_at_freeze',
         '81_to_C1_at_freeze')
ROUTES = (('write_only', False), ('read_3', True))
PRIOR = HERE / 'results/joint-mask04-ram-pulse-freeze.json'


def mode_sequence(name):
    size = 4 * impulse.ADC_VISITS + 1
    if name in ('81_to_A1_at_freeze', '81_to_C1_at_freeze'):
        edge = 4 * pulse.TRAIN_VISITS
        target = 0xA1 if name == '81_to_A1_at_freeze' else 0xC1
        return [0x81] * edge + [target] * (size - edge)
    return [int(name, 16)] * size


def run(out=HERE / 'results/joint-mask04-ram-mode-pulse.json'):
    prior = {(case['input'], case['route']): case
             for case in json.loads(PRIOR.read_text())['cases']}
    execute = instrumented_execute()
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    samples = [127 - value for value in transmit(impulse.VARYING_DIBITS)]
    if len(samples) != impulse.SAMPLES or samples[25] != 0x51:
        raise ValueError('reference source changed')
    starts = pulse.sample_starts()
    offered = dict(baseline=impulse.held_samples(samples, 25, None),
                   pulse=impulse.held_samples(samples, 25,
                                              impulse.VARYING_HIGH_PULSE_ADC))
    cases = []
    y_by_case = {}
    ram_by_case = {}
    for mode in MODES:
        wrapper = mode_sequence(mode)
        for input_name, adc in offered.items():
            for route, feedback in ROUTES:
                scenario = configured(base, adc, 'previous', 'overflow', 1)
                scenario['io']['read']['pc_sequences'][str(0x3EB)] = wrapper
                scenario['io']['read']['evidence'] += (
                    '; assumed held controller frame byte at D3EB')
                scenario.update(external_ram_feedback=feedback,
                                external_ram_write=True,
                                external_ram_lane='low',
                                external_ram_latch_pc=0x3F9,
                                external_ram_read_pc=0x3FA,
                                external_ram_read_offset=-3,
                                external_ram_write_until=pulse.TRAIN_WRITES,
                                external_ram_address_tick_visits=[4 * visit
                                                                  for visit in starts])
                result = execute(mapping, scenario, impulse.CYCLES,
                                 mode='integrated', trace_limit=0)
                ram = result['external_ram_candidate']
                if (not result['clean'] or
                        result['completed_cycles'] != impulse.CYCLES or
                        result['address_counts'].get(0x3F8) != impulse.ADC_VISITS or
                        result['edge_counts'].get('3ed->3ee', 0) != 0 or
                        ram['writes'] != pulse.TRAIN_WRITES or
                        any(len(ram['y_by_pc'][pc]) != impulse.ADC_VISITS
                            for pc in (0x3F8, 0x3F9, 0x3FA))):
                    raise ValueError(('receive loop did not sustain', mode, input_name, route))
                key = (mode, input_name, route)
                y_by_case[key] = ram['y_by_pc']
                ram_by_case[key] = ram['bytes']
                case = dict(mode=mode, input=input_name,
                                  route=route, feedback=feedback,
                                  adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                                  completed_cycles=result['completed_cycles'],
                                  trace_digest=result['trace_digest'],
                                  ram_sha256=hashlib.sha256(bytes(ram['bytes'])).hexdigest(),
                                  noninitial_ram_bytes=sum(x != 1 for x in ram['bytes']),
                                  external_reads=ram['reads'],
                                  external_writes=ram['writes'])
                if mode == '01':
                    earlier = prior[(input_name, route)]
                    for key in ('adc_sha256', 'trace_digest', 'ram_sha256'):
                        if case[key] != earlier[key]:
                            raise ValueError(('01 replay differs', input_name, route, key))
                cases.append(case)
                print(mode, input_name, route,
                      result['trace_digest'], flush=True)
    comparisons = {}
    for mode in MODES:
        by_route = {}
        for route, _ in ROUTES:
            a = y_by_case[(mode, 'baseline', route)]
            b = y_by_case[(mode, 'pulse', route)]
            memories = list(zip(ram_by_case[(mode, 'baseline', route)],
                                ram_by_case[(mode, 'pulse', route)]))
            by_route[route] = dict(
                changed_ram_bytes=[dict(address=i, baseline=x, pulse=y)
                                   for i, (x, y) in enumerate(memories) if x != y],
                y_by_site={f'{pc:03X}': dict(
                    pulse=pulse.delta(a[pc], b[pc], starts[25], starts[26]),
                    delayed_3=pulse.delta(a[pc], b[pc], starts[28], starts[29]),
                    other_tail=pulse.delta(a[pc], b[pc], starts[26], starts[28]))
                    for pc in (0x3F8, 0x3F9, 0x3FA)})
        comparisons[mode] = by_route
    mode_equivalence = {}
    for mode in ('C1', '81_to_C1_at_freeze'):
        mode_equivalence[mode] = {}
        for input_name in offered:
            for route, _ in ROUTES:
                left = y_by_case[('81', input_name, route)]
                right = y_by_case[(mode, input_name, route)]
                mode_equivalence[mode][f'{input_name}/{route}'] = {
                    f'{pc:03X}': sum(a != b for a, b in zip(left[pc], right[pc]))
                    for pc in (0x3F8, 0x3F9, 0x3FA)}
    paths = (Path(__file__), PRIOR, Path(pulse.__file__), Path(impulse.__file__),
             HERE / 'joint_upper_ram_feedback_screen.py',
             HERE / 'receiver_four_row_condition_screen.py',
             HERE.parent / 'assumed/execute.py', HERE / 'reference_modem.py',
             MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(
        experiment='held controller-like D3EB mode bytes with one frozen RAM pulse',
        fixture=dict(modes=list(MODES),
                     edge_wrapper_read=4 * pulse.TRAIN_VISITS,
                     reference_dibits=impulse.VARYING_DIBITS,
                     pulse_sample=25, baseline_adc=0x51, pulse_adc=0xB1,
                     samples=impulse.SAMPLES, adc_visits=impulse.ADC_VISITS,
                     cycles=impulse.CYCLES, train_visits=pulse.TRAIN_VISITS,
                     train_writes=pulse.TRAIN_WRITES,
                     return_route='3F9 Y low nibble to candidate RAM; 3FA D low nibble from address minus 3'),
        cases=cases, comparisons=comparisons,
        c1_vs_81_y_differences=mode_equivalence,
        limitations=[
            'D3EB controller mode connection and held timing are untraced assumptions.',
            'RAM pins, address clock, write gate and D return are untraced assumptions.',
            'One pulse and one waveform do not prove receive decisions or echo cancellation.'
        ],
        source_sha256={str(path.relative_to(HERE.parents[4])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
