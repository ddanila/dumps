"""Compare training/freeze RAM feedback routes on two executed PROM inputs."""

import hashlib
import json
import random
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from joint_upper_ram_feedback_screen import instrumented_execute
from joint_upper_source_screen import SELECTED_MASK, candidate
from lower_i_d3f8_full_adc import scenario_for_full_byte
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

TRAIN = 256
TAIL = 128
VISITS = TRAIN + TAIL
CYCLES = 8 * VISITS + 47
SEEDS = (0x3557, 0x3558)
ROUTES = (
    ('write_frozen_no_feedback', 0x3EB, 'high', False, TRAIN),
    ('3EB_high_frozen', 0x3EB, 'high', True, TRAIN),
    ('3EB_low_frozen', 0x3EB, 'low', True, TRAIN),
    ('3FA_high_frozen', 0x3FA, 'high', True, TRAIN),
    ('3FA_low_frozen', 0x3FA, 'low', True, TRAIN),
    ('3EB_low_free_running', 0x3EB, 'low', True, None),
)


def run(out=HERE / 'results/joint-upper-ram-freeze-screen.json'):
    execute = instrumented_execute()
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), SELECTED_MASK)
    _, base = fixture()
    cases = []
    ram_by_seed_route = {}
    tail_by_seed_route = {}
    for seed in SEEDS:
        generator = random.Random(seed)
        train = [generator.randrange(80, 177) for _ in range(TRAIN)]
        offered = train + [127] * TAIL
        for name, read_pc, lane, feedback, write_until in ROUTES:
            scenario = scenario_for_full_byte(base, offered, 'complementary')
            scenario.update(external_ram_feedback=feedback,
                            external_ram_write=True,
                            external_ram_lane=lane,
                            external_ram_latch_pc=0x3FA,
                            external_ram_read_pc=read_pc,
                            external_ram_write_until=write_until)
            with tempfile.TemporaryDirectory() as temporary:
                result = execute(mapping, scenario, CYCLES,
                                 mode='integrated', out=temporary,
                                 trace_limit=CYCLES)
                tail = []
                for line in (Path(temporary) / 'trace.jsonl').open():
                    row = json.loads(line)
                    if row['cycle'] >= 47 + TRAIN * 8:
                        tail.append((row['pc'], row['q'], row['alu']['y'],
                                     row['registers']))
            ram = result['external_ram_candidate']
            ram_by_seed_route[(seed, name)] = ram['bytes']
            tail_by_seed_route[(seed, name)] = tail
            cases.append(dict(seed=seed, route=name,
                              offered_sha256=hashlib.sha256(bytes(offered)).hexdigest(),
                              clean=result['clean'],
                              d3f8_visits=result['address_counts'].get(0x3F8, 0),
                              loop_exits=result['edge_counts'].get('3ed->3ee', 0),
                              final_pc=f"{result['final_state']['pc']:03X}",
                              final_q=result['final_state']['q'],
                              final_internal_ram=result['final_state']['ram'],
                              trace_digest=result['trace_digest'],
                              tail_trace_sha256=hashlib.sha256(
                                  json.dumps(tail, sort_keys=True).encode()).hexdigest(),
                              tail_trace_rows=len(tail),
                              external_reads=ram['reads'],
                              external_writes=ram['writes'],
                              external_noninitial=sum(value != 1 for value in ram['bytes']),
                              external_sha256=hashlib.sha256(bytes(ram['bytes'])).hexdigest(),
                              first_changed_read=ram['first_changed_read']))
            print(hex(seed), name, cases[-1]['d3f8_visits'],
                  cases[-1]['loop_exits'], flush=True)
    by_key = {(row['seed'], row['route']): row for row in cases}
    for seed in SEEDS:
        baseline = by_key[(seed, 'write_frozen_no_feedback')]
        if baseline['d3f8_visits'] != VISITS or baseline['external_writes'] != TRAIN:
            raise ValueError('training/freeze baseline did not complete')
        for name in ('3EB_low_frozen', '3EB_low_free_running'):
            row = by_key[(seed, name)]
            if row['d3f8_visits'] != VISITS or row['trace_digest'] != baseline['trace_digest']:
                raise ValueError(('low-nibble trace unexpectedly changed', seed, name))
        if by_key[(seed, '3FA_high_frozen')]['loop_exits'] != 1:
            raise ValueError(('3FA high-nibble route did not exit', seed))
    for row in cases:
        control = by_key[(row['seed'], 'write_frozen_no_feedback')]
        reference = tail_by_seed_route[(row['seed'], 'write_frozen_no_feedback')]
        observed = tail_by_seed_route[(row['seed'], row['route'])]
        row['final_internal_state_equals_control'] = (
            row['final_q'] == control['final_q'] and
            row['final_internal_ram'] == control['final_internal_ram'] and
            row['final_pc'] == control['final_pc'])
        row['tail_different_rows_vs_control'] = (
            sum(a != b for a, b in zip(reference, observed))
            if row['d3f8_visits'] == VISITS and
            len(reference) == len(observed) else None)
    differences = {name: sum(a != b for a, b in zip(
        ram_by_seed_route[(SEEDS[0], name)], ram_by_seed_route[(SEEDS[1], name)]))
                   for name, *_ in ROUTES}
    if differences['write_frozen_no_feedback'] == 0 or differences['3EB_low_frozen'] == 0:
        raise ValueError('frozen RAM did not retain training-input differences')
    paths = (Path(__file__), HERE / 'joint_upper_ram_feedback_screen.py',
             HERE.parent / 'assumed/execute.py',
             HERE.parents[2] / 'photos/PXL_20261123_114811760.jpg',
             HERE / 'joint_upper_source_screen.py',
             HERE / 'lower_i_d3f8_full_adc.py',
             HERE / 'lower_i_d3f8_upper_d_route.py',
             HERE / 'photo_controller_path.py',
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='counter/RAM training-write and freeze under two PROM-driven ADC prefixes',
                  fixture=dict(train_visits=TRAIN, common_tail_visits=TAIL,
                               cycles=CYCLES, seeds=SEEDS,
                               adc='independent codes 80..176, then common 127',
                               address='modulo-256 counter increments at 3EA',
                               data='3FA Y nibble latched; D0 forced high',
                               write='at 3EC; frozen after 256 writes or free running',
                               read='3EB or 3FA D from RAM nibble'),
                  routes=[dict(name=name, read_pc=f'{read_pc:03X}', lane=lane,
                               feedback=feedback, write_until=write_until)
                          for name, read_pc, lane, feedback, write_until in ROUTES],
                  cases=cases,
                  external_ram_byte_differences_between_seeds=differences,
                  limitations=['Two independent pseudorandom ADC prefixes are not a measured own-echo/remote-only pair.',
                               'Counter, RAM, latch, write gate, readback and freeze control pins remain untraced.',
                               'Retained RAM history without a changed PROM trace is not echo cancellation.'],
                  source_sha256={str(p.relative_to(HERE.parents[4])):
                                 hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
