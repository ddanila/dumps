"""Screen one sample-paced external-RAM feedback route in the four-row loop."""

import hashlib
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from joint_mask04_full_zero_analog_variants import reconstructed_pcm
from joint_upper_ram_feedback_screen import instrumented_execute
from receiver_four_row_condition_screen import configured
from receiver_mask04_protocol_preamble import (
    MAPPINGS, candidate, fixture, mapped, mapping_with_upper_source,
)
from reference_modem import transmit

PRIOR_TX = HERE / 'results/joint-mask04-full-zero-handoff.json'
TRAIN_SAMPLES = 128
TAIL_SAMPLES = 64
SAMPLES = TRAIN_SAMPLES + TAIL_SAMPLES
TRAIN_VISITS = TRAIN_SAMPLES * 375 // 8
VISITS = SAMPLES * 375 // 8
CYCLES = 32 * VISITS + 47
ECHO_DELAY = 3
ECHO_GAIN = 0.5
REMOTE_GAIN = 0.25
REMOTE_SEED = 0x3558
ROUTES = (('3fa_low_no_feedback', False, 0x3FA),
          ('3fa_low_read_previous_3', True, 0x3FA),
          ('3f9_low_no_feedback', False, 0x3F9),
          ('3f9_low_read_previous_3', True, 0x3F9))
BASELINES = {0x3FA: '3fa_low_no_feedback', 0x3F9: '3f9_low_no_feedback'}


def sample_starts():
    starts = []
    visit = 0
    for sample in range(SAMPLES):
        starts.append(visit)
        visit += 47 if sample % 8 < 7 else 46
    if visit != VISITS or starts[TRAIN_SAMPLES] != TRAIN_VISITS:
        raise ValueError('ADC sample clock changed')
    return starts


def training_inputs():
    prior = json.loads(PRIOR_TX.read_text())
    call = next(case for case in prior['cases'] if case['selector'] == '40')
    own_pcm, _, _, _ = reconstructed_pcm(call)
    own = [round(ECHO_GAIN * own_pcm[index - ECHO_DELAY])
           if index >= ECHO_DELAY else 0
           for index in range(TRAIN_SAMPLES)]
    generator = random.Random(REMOTE_SEED)
    remote_dibits = [0] * 8 + [generator.randrange(4) for _ in range(16)] + [0] * 8
    remote_pcm = transmit(remote_dibits)[64:64 + TRAIN_SAMPLES]
    remote = [round(REMOTE_GAIN * value) for value in remote_pcm]
    mixed = [a + b for a, b in zip(own, remote)]
    if any(abs(value) > 127 for value in mixed):
        raise ValueError('mixed ADC input clips')
    return dict(zero=[0] * TRAIN_SAMPLES,
                own_echo=own, independent_remote=remote,
                remote_plus_echo=mixed)


def mean_absolute_difference(left, right):
    if len(left) != len(right) or not left:
        raise ValueError('Y response length changed')
    return sum(abs(a - b) for a, b in zip(left, right)) / len(left)


def run(out=HERE / 'results/joint-mask04-external-ram-echo-screen.json'):
    execute = instrumented_execute()
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    ticks = sample_starts()
    inputs = training_inputs()
    rows = []
    observations = {}
    for name, prefix in inputs.items():
        samples = prefix + [0] * TAIL_SAMPLES
        offered = [127 - value for value in samples]
        adc = [value for index, value in enumerate(offered)
               for _ in range(47 if index % 8 < 7 else 46)]
        if len(adc) != VISITS:
            raise ValueError('held ADC visit count changed')
        for route, feedback, latch_pc in ROUTES:
            scenario = configured(base, adc, 'previous', 'overflow', 1)
            scenario.update(external_ram_feedback=feedback,
                            external_ram_write=True,
                            external_ram_lane='low',
                            external_ram_latch_pc=latch_pc,
                            external_ram_read_pc=0x3FA,
                            external_ram_read_offset=-3,
                            external_ram_write_until=TRAIN_VISITS,
                            external_ram_address_tick_visits=ticks)
            result = execute(mapping, scenario, CYCLES,
                             mode='integrated', trace_limit=0)
            memory = result['external_ram_candidate']
            observations[(name, route)] = memory['y_by_pc']
            rows.append(dict(stimulus=name, route=route,
                             latch_pc=f'{latch_pc:03X}',
                             input_sha256=hashlib.sha256(bytes(offered)).hexdigest(),
                             adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                             clean=result['clean'],
                             completed_cycles=result['completed_cycles'],
                             adc_visits=result['address_counts'].get(0x3F8, 0),
                             four_row_visits=result['address_counts'].get(0x3ED, 0),
                             loop_exits=result['edge_counts'].get('3ed->3ee', 0),
                             trace_digest=result['trace_digest'],
                             final_pc=f"{result['final_state']['pc']:03X}",
                             external_reads=memory['reads'],
                             external_writes=memory['writes'],
                             external_noninitial=sum(value != 1 for value in memory['bytes']),
                             external_ram_sha256=hashlib.sha256(bytes(memory['bytes'])).hexdigest(),
                             first_changed_read=memory['first_changed_read']))
            print(name, route, rows[-1]['adc_visits'],
                  rows[-1]['loop_exits'], flush=True)
    by_key = {(row['stimulus'], row['route']): row for row in rows}
    comparisons = {}
    for route, _, _ in ROUTES:
        channels = {name: observations[(name, route)][0x3FA]
                    for name in inputs}
        if any(len(values) != VISITS for values in channels.values()):
            comparisons[route] = None
            continue
        windows = dict(early=slice(0, 32 * 375 // 8),
                       late=slice(96 * 375 // 8, TRAIN_VISITS),
                       tail=slice(TRAIN_VISITS, VISITS))
        comparisons[route] = {}
        for window, interval in windows.items():
            take = lambda name: channels[name][interval]
            comparisons[route][window] = dict(
                own_vs_zero=mean_absolute_difference(take('own_echo'), take('zero')),
                remote_vs_zero=mean_absolute_difference(take('independent_remote'), take('zero')),
                mixed_vs_remote=mean_absolute_difference(take('remote_plus_echo'), take('independent_remote')),
                mixed_vs_own=mean_absolute_difference(take('remote_plus_echo'), take('own_echo')))
    for row in rows:
        control_name = BASELINES[int(row['latch_pc'], 16)]
        control = by_key[(row['stimulus'], control_name)]
        row['same_trace_as_no_feedback'] = row['trace_digest'] == control['trace_digest']
        test = observations[(row['stimulus'], row['route'])][0x3FA]
        baseline = observations[(row['stimulus'], control_name)][0x3FA]
        row['tail_y3fa_changes_vs_control'] = (
            sum(a != b for a, b in zip(test[TRAIN_VISITS:], baseline[TRAIN_VISITS:]))
            if len(test) == len(baseline) == VISITS else None)
    paths = (Path(__file__), PRIOR_TX,
             HERE / 'joint_mask04_full_zero_analog_variants.py',
             HERE / 'joint_upper_ram_feedback_screen.py',
             HERE / 'receiver_four_row_condition_screen.py',
             HERE / 'reference_modem.py',
             MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='sample-paced external RAM in joint mask04 four-row own-echo and remote screen',
                  fixture=dict(train_samples=TRAIN_SAMPLES, tail_samples=TAIL_SAMPLES,
                               adc_visits=VISITS, cycles=CYCLES,
                               own_source='hash-checked 838-bit real-PROM Y7 call stream, candidate B5/filter PCM',
                               own_echo_gain=ECHO_GAIN, own_echo_delay=ECHO_DELAY,
                               remote_gain=REMOTE_GAIN, remote_seed=REMOTE_SEED,
                               ram='hypothetical 256x8, low-nibble 3FA or 3F9 Y latch written at 3EC, D0 forced high',
                               read='3FA D low nibble from address minus three samples',
                               freeze='after 128 held ADC samples'),
                  cases=rows, y3fa_code_space_comparisons=comparisons,
                  limitations=[
                      'RAM address, data, write gate and return route are assumptions; the model is not measured board wiring.',
                      'The Y3FA byte difference is a code-space diagnostic, not a physical analog residual.',
                      'A negative result constrains only the tested mask04 route, source waveform, sample schedule and short training duration.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
