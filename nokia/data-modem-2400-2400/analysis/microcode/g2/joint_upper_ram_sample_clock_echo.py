"""Sample-clocked candidate RAM feedback with own-echo and remote controls."""

import hashlib
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from joint_upper_echo_feed_probe import (
    ECHO_DELAY, ECHO_GAIN, JOINED, REMOTE_GAIN, REMOTE_SEED,
    SELECTORS, TXREADY, candidate_tx_codes,
)
from joint_upper_ram_feedback_screen import instrumented_execute
from joint_upper_source_screen import SELECTED_MASK, candidate
from lower_i_d3f8_full_adc import SAMPLE_START, hold, scenario_for_full_byte
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_127_liveness import ROM
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from reference_modem import transmit

TRAIN_SAMPLES = 128
TAIL_SAMPLES = 64
SAMPLES = TRAIN_SAMPLES + TAIL_SAMPLES
TRAIN_VISITS = TRAIN_SAMPLES * 375 // 2
VISITS = SAMPLES * 375 // 2
CYCLES = 8 * VISITS + 47
ROUTES = (('trained_no_feedback', False, 0),
          ('read_previous_3_samples', True, -3),
          ('read_previous_64_samples', True, -64))


def sample_starts():
    starts = []
    visit = 0
    for sample in range(SAMPLES):
        starts.append(visit)
        visit += 188 if sample % 2 == 0 else 187
    if visit != VISITS or starts[TRAIN_SAMPLES] != TRAIN_VISITS:
        raise ValueError('ADC hold clock changed')
    return starts


def sources():
    yield 'zero', [0] * TRAIN_SAMPLES, None
    generator = random.Random(REMOTE_SEED)
    dibits = [0] * 8 + [generator.randrange(4) for _ in range(16)] + [0] * 8
    pcm = transmit(dibits)[SAMPLE_START:SAMPLE_START + TRAIN_SAMPLES]
    yield 'independent_remote', [round(REMOTE_GAIN * x) for x in pcm], None
    txready = json.loads(TXREADY.read_text())
    joined = json.loads(JOINED.read_text())
    rom = ROM.read_bytes()
    for selector in SELECTORS:
        dac, digest = candidate_tx_codes(selector, txready, joined, rom)
        echo = [round(ECHO_GAIN * (dac[index - ECHO_DELAY] - 128))
                if index >= ECHO_DELAY else 0 for index in range(TRAIN_SAMPLES)]
        yield f'own_echo_{selector}', echo, digest


def run(out=HERE / 'results/joint-upper-ram-sample-clock-echo.json'):
    execute = instrumented_execute()
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), SELECTED_MASK)
    _, base = fixture()
    ticks = sample_starts()
    cases = []
    observations = {}
    for stimulus, prefix, tx_digest in sources():
        samples = prefix + [0] * TAIL_SAMPLES
        if any(not -127 <= x <= 127 for x in samples):
            raise ValueError(('ADC sample out of range', stimulus))
        offered = hold([127 - x for x in samples])
        if len(offered) != VISITS:
            raise ValueError('ADC held visits changed')
        for name, feedback, offset in ROUTES:
            scenario = scenario_for_full_byte(base, offered, 'complementary')
            scenario.update(external_ram_feedback=feedback,
                            external_ram_write=True,
                            external_ram_lane='low',
                            external_ram_latch_pc=0x3FA,
                            external_ram_read_pc=0x3FA,
                            external_ram_read_offset=offset,
                            external_ram_write_until=TRAIN_VISITS,
                            external_ram_address_tick_visits=ticks)
            result = execute(mapping, scenario, CYCLES,
                             mode='integrated', trace_limit=0)
            ram = result['external_ram_candidate']
            observations[(stimulus, name)] = ram['y_by_pc']
            cases.append(dict(stimulus=stimulus, route=name,
                              tx_sample_sha256=tx_digest,
                              adc_sha256=hashlib.sha256(bytes(offered)).hexdigest(),
                              clean=result['clean'],
                              d3f8_visits=result['address_counts'].get(0x3F8, 0),
                              loop_exits=result['edge_counts'].get('3ed->3ee', 0),
                              final_pc=f"{result['final_state']['pc']:03X}",
                              final_q=result['final_state']['q'],
                              final_internal_ram=result['final_state']['ram'],
                              trace_digest=result['trace_digest'],
                              external_reads=ram['reads'],
                              external_writes=ram['writes'],
                              external_noninitial=sum(x != 1 for x in ram['bytes']),
                              external_sha256=hashlib.sha256(bytes(ram['bytes'])).hexdigest(),
                              first_changed_read=ram['first_changed_read']))
            print(stimulus, name, cases[-1]['d3f8_visits'],
                  cases[-1]['loop_exits'], flush=True)
    by_key = {(row['stimulus'], row['route']): row for row in cases}
    for row in cases:
        baseline = by_key[(row['stimulus'], 'trained_no_feedback')]
        row['final_internal_state_equals_control'] = (
            row['final_pc'] == baseline['final_pc'] and
            row['final_q'] == baseline['final_q'] and
            row['final_internal_ram'] == baseline['final_internal_ram'])
        row['tail_y_differences_vs_control'] = {}
        row['unsigned_y_response_vs_zero'] = {}
        for pc in (0x3F8, 0x3F9, 0x3FA):
            key = f'{pc:03X}'
            control_y = observations[(row['stimulus'], 'trained_no_feedback')][pc]
            test_y = observations[(row['stimulus'], row['route'])][pc]
            zero_y = observations[('zero', row['route'])][pc]
            if len(control_y) == VISITS and len(test_y) == VISITS:
                row['tail_y_differences_vs_control'][key] = sum(
                    a != b for a, b in zip(control_y[TRAIN_VISITS:],
                                             test_y[TRAIN_VISITS:]))
                row['unsigned_y_response_vs_zero'][key] = dict(
                    train_mean_absolute_difference=round(
                        sum(abs(a - b) for a, b in
                            zip(test_y[:TRAIN_VISITS], zero_y[:TRAIN_VISITS])) / TRAIN_VISITS, 4),
                    tail_mean_absolute_difference=round(
                        sum(abs(a - b) for a, b in
                            zip(test_y[TRAIN_VISITS:], zero_y[TRAIN_VISITS:])) /
                        (VISITS - TRAIN_VISITS), 4))
            else:
                row['tail_y_differences_vs_control'][key] = None
                row['unsigned_y_response_vs_zero'][key] = None
    if any(row['d3f8_visits'] != VISITS or
           row['external_writes'] != TRAIN_VISITS
           for row in cases if row['route'] == 'trained_no_feedback'):
        raise ValueError('sample-paced baseline or freeze did not sustain')
    paths = (Path(__file__), HERE / 'joint_upper_ram_feedback_screen.py',
             HERE / 'joint_upper_echo_feed_probe.py',
             HERE / 'joint_upper_source_screen.py',
             HERE / 'lower_i_d3f8_full_adc.py',
             HERE / 'lower_i_d3f8_upper_d_route.py',
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             HERE / 'photo_controller_path.py',
             HERE / 'reference_modem.py',
             HERE.parent / 'assumed/execute.py',
             HERE.parents[2] / 'photos/PXL_20261123_114811760.jpg',
             MAPPINGS['q3'], TXREADY, JOINED, ROM,
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='sample-paced external RAM on own-echo and remote PROM receive runs',
                  fixture=dict(train_samples=TRAIN_SAMPLES, tail_samples=TAIL_SAMPLES,
                               visits=VISITS, cycles=CYCLES,
                               adc='complementary PCM, 188/187 receive visits per sample',
                               address='increment at each held ADC sample start',
                               ram='256x8, initial 01; write 3FA low-nibble Y at 3EC',
                               freeze=f'after {TRAIN_VISITS} writes',
                               read='3FA low-nibble D, 0/-3/-64 address offset',
                               echo_gain=ECHO_GAIN, echo_delay=ECHO_DELAY,
                               remote_gain=REMOTE_GAIN, remote_seed=REMOTE_SEED),
                  cases=cases,
                  limitations=['The sample clock, address offset, RAM pins, write gate and read route are hypotheses.',
                               'The candidate ADC, DAC, echo gain/delay and output site are unverified.',
                               'Y differences are not an analog residual or proof of echo cancellation.'],
                  source_sha256={str(p.relative_to(HERE.parents[4])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
