"""Check whether own-echo stimulation leaves persistent joint-map state."""

import hashlib
import json
import random
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from joint_upper_echo_feed_probe import (
    ECHO_DELAY, ECHO_GAIN, JOINED, REMOTE_GAIN, REMOTE_SEED,
    SELECTORS, TXREADY, candidate_tx_codes,
)
from joint_upper_source_screen import SELECTED_MASK, candidate
from lower_i_d3f8_full_adc import SAMPLE_START, hold, scenario_for_full_byte
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_127_liveness import ROM
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from reference_modem import transmit

TRAIN = 128
TAIL = 64
SAMPLES = TRAIN + TAIL
VISITS = SAMPLES * 375 // 2
CYCLES = 8 * VISITS + 47
CHANNELS = ('Y3F8', 'Y3F9', 'Y3FA', 'Q',
            *(f'R{index}' for index in range(16)))


def capture(mapping, base, samples):
    values = hold([127 - sample for sample in samples])
    if len(values) != VISITS:
        raise ValueError('ADC hold count changed')
    scenario = scenario_for_full_byte(base, values, 'complementary')
    ram = scenario['initial']['ram'][:]
    states = []
    y8 = y9 = None
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, CYCLES,
                         mode='integrated', out=temporary, trace_limit=CYCLES)
        for line in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(line)
            for address, value in row['registers'].items():
                ram[int(address)] = value
            if row['pc'] == 0x3F8:
                read = row['external_read']
                if (not read.get('selected_by_alu') or
                        read['value'] != values[len(states)]):
                    raise ValueError('ADC byte selection changed')
                y8 = row['alu']['y']
            elif row['pc'] == 0x3F9:
                y9 = row['alu']['y']
            elif row['pc'] == 0x3FA:
                if y8 is None or y9 is None:
                    raise ValueError('incomplete receive visit')
                states.append(bytes((y8, y9, row['alu']['y'], row['q'], *ram)))
                y8 = y9 = None
    if (not result['clean'] or len(states) != VISITS or
            result['read_sequence_visits'].get(0x3F8) != VISITS):
        raise ValueError('joint receive path stopped')
    return (states, result['trace_digest'],
            hashlib.sha256(bytes(values)).hexdigest(), result['final_state'])


def center(sample):
    start = 188 * ((sample + 1) // 2) + 187 * (sample // 2)
    return start + (188 if sample % 2 == 0 else 187) // 2


def compare(source, control):
    tail_start = TRAIN * 375 // 2
    by_channel = {}
    for index, name in enumerate(CHANNELS):
        changed = [visit for visit in range(tail_start, VISITS)
                   if source[visit][index] != control[visit][index]]
        by_channel[name] = dict(changed_tail_visits=len(changed),
                                last_changed_tail_visit=changed[-1] - tail_start
                                if changed else None,
                                last_16_center_samples_changed=sum(
                                    source[center(sample)][index] !=
                                    control[center(sample)][index]
                                    for sample in range(SAMPLES - 16, SAMPLES)))
    state_changed = [visit for visit in range(tail_start, VISITS)
                     if source[visit][4:] != control[visit][4:]]
    centers = [sum(a != b for a, b in
                   zip(source[center(sample)], control[center(sample)]))
               for sample in range(TRAIN, SAMPLES)]
    return dict(channels=by_channel,
                changed_channels_at_last_train_visit=sum(
                    a != b for a, b in
                    zip(source[tail_start - 1], control[tail_start - 1])),
                ram_changed_tail_visits=len(state_changed),
                ram_last_changed_tail_visit=(state_changed[-1] - tail_start
                                             if state_changed else None),
                changed_channels_at_tail_centers=centers)


def run(out=HERE / 'results/joint-upper-echo-washout.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), SELECTED_MASK)
    _, base = fixture()
    txready = json.loads(TXREADY.read_text())
    joined = json.loads(JOINED.read_text())
    rom = ROM.read_bytes()
    baseline, baseline_digest, baseline_adc, baseline_final = capture(
        mapping, base, [0] * SAMPLES)
    generator = random.Random(REMOTE_SEED)
    dibits = [0] * 8 + [generator.randrange(4) for _ in range(16)] + [0] * 8
    pcm = transmit(dibits)[SAMPLE_START:SAMPLE_START + TRAIN]
    remote = [round(REMOTE_GAIN * sample) for sample in pcm]
    sources = [('independent_remote', remote, None)]
    for selector in SELECTORS:
        dac, tx_digest = candidate_tx_codes(selector, txready, joined, rom)
        echo = [round(ECHO_GAIN * (dac[index - ECHO_DELAY] - 128))
                if index >= ECHO_DELAY else 0 for index in range(TRAIN)]
        sources.append((f'own_echo_{selector}', echo, tx_digest))
    cases = []
    for name, prefix, tx_digest in sources:
        samples = prefix + [0] * TAIL
        if len(samples) != SAMPLES or any(not -127 <= sample <= 127
                                         for sample in samples):
            raise ValueError('ADC stimulus out of range')
        states, digest, adc_digest, final_state = capture(mapping, base, samples)
        result = compare(states, baseline)
        if result['changed_channels_at_last_train_visit'] == 0:
            raise ValueError('input prefix failed to change late training state')
        cases.append(dict(name=name, tx_sample_sha256=tx_digest,
                          adc_stream_sha256=adc_digest,
                          trace_digest=digest,
                          final_state_matches_zero=final_state == baseline_final,
                          comparison=result))
        print(name, result['ram_changed_tail_visits'],
              result['ram_last_changed_tail_visit'],
              result['changed_channels_at_tail_centers'][-8:], flush=True)
    paths = [Path(__file__),
             HERE / 'joint_upper_echo_feed_probe.py',
             HERE / 'joint_upper_source_screen.py',
             HERE / 'lower_i_d3f8_full_adc.py',
             HERE / 'lower_i_d3f8_upper_d_route.py',
             HERE / 'photo_joint_tone_training_data.py',
             HERE / 'photo_main_dibit_pulse.py',
             HERE / 'photo_dac_bus_permutations.py',
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             HERE / 'photo_controller_path.py',
             HERE / 'reference_modem.py',
             HERE / 'split_slice_probe.py',
             HERE.parent / 'assumed/execute.py',
             HERE.parent / 'model.py',
             MAPPINGS['q3'], TXREADY, JOINED, ROM,
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(experiment='joint-map echo and remote input state washout',
                  fixture=dict(train_samples=TRAIN, identical_zero_tail=TAIL,
                               adc_visits=VISITS, microinstructions=CYCLES,
                               mapping='joint upper-source mask 08',
                               adc='complementary PCM, 188/187 visits per sample',
                               echo_gain=ECHO_GAIN, echo_delay=ECHO_DELAY,
                               remote_gain=REMOTE_GAIN, remote_seed=REMOTE_SEED),
                  baseline_trace_digest=baseline_digest,
                  baseline_adc_stream_sha256=baseline_adc,
                  cases=cases,
                  limitations=['The own-echo DAC and ADC routes, gain/delay, mode and output site remain hypothetical.',
                               'A persistent state difference is memory, not by itself echo cancellation; absence constrains only this fixed mapping and fixture.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
