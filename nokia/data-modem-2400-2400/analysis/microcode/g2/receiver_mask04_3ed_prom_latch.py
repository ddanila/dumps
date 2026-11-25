"""Test a photo-compatible PROM NAND clock for mask-04 3ED Y and bit output."""

import hashlib
import itertools
import json
import random
import sys
import tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from joint_upper_receive_bit_screen import HOLDOUT, TRAIN
from joint_upper_source_screen import candidate
from lower_i_d3f8_full_adc import LONG_SAMPLES, SAMPLE_START
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from lower_i_d3f8_upper_symbol_screen import LAGS, SYMBOL_INDEXES, sequences
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_four_row_condition_screen import configured
from reference_modem import receive, transmit

ADC_VISITS = 6000
CYCLES = 32 * ADC_VISITS + 47
VISITS_PER_SYMBOL = 1500
GATE = ((1, 7, 1), (2, 3, 1), (3, 5, 1))
OPERATIONS = ('direct', 'xor_previous')
VALIDATION_SEEDS = (0x2421, 0x2401, 0x26A1, 0x33C3)


def gate_high(row):
    return all(((row['raw'][chip] >> bit) & 1) == value
               for chip, bit, value in GATE)


def gate_search(prefix):
    target = sum(1 << index for index, row in enumerate(prefix)
                 if row['pc'] == 0x3ED)
    literals = [(chip, bit, value) for chip in range(4)
                for bit in range(8) for value in (0, 1)]
    levels = {literal: sum(1 << index for index, row in enumerate(prefix)
                           if ((row['raw'][literal[0]] >> literal[1]) & 1)
                           == literal[2]) for literal in literals}
    def matches_target(group):
        mask = (1 << len(prefix)) - 1
        for literal in group:
            mask &= levels[literal]
        return mask == target

    matches = {}
    for width in (1, 2, 3):
        matches[width] = [group for group in
                          itertools.combinations(literals, width)
                          if len({item[:2] for item in group}) == width and
                          matches_target(group)]
    all_positive = [group for group in matches[3]
                    if all(value == 1 for _, _, value in group)]
    if (matches[1] or matches[2] or len(matches[3]) != 54 or
            all_positive != [GATE]):
        raise ValueError('3ED raw-PROM gate search changed')
    return dict(prefix_words=len(prefix),
                target_visits=sum(row['pc'] == 0x3ED for row in prefix),
                matches_by_width={str(k): len(v) for k, v in matches.items()},
                all_positive_three_literal=all_positive)


def capture(mapping, base, middle, prefix=False):
    dibits = [0] * 8 + middle + [0] * 8
    pcm = transmit(dibits)
    if receive(pcm) != dibits[1:]:
        raise ValueError('reference receiver did not recover stimulus')
    samples = [127 - value for value in
               pcm[SAMPLE_START:SAMPLE_START + LONG_SAMPLES]]
    values = [sample for index, sample in enumerate(samples)
              for _ in range(47 if index % 8 < 7 else 46)]
    if len(values) != ADC_VISITS:
        raise ValueError('four-row ADC hold schedule changed')
    scenario = configured(base, values, 'previous', 'overflow', 1)
    ram = scenario['initial']['ram'][:]
    captured = []
    edges = Counter()
    high_sites = Counter()
    prefix_rows = []
    previous = None
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, CYCLES, mode='integrated',
                         out=temporary, trace_limit=CYCLES)
        if (not result['clean'] or result['completed_cycles'] != CYCLES or
                result['address_counts'].get(0x3ED, 0) != 4 * ADC_VISITS or
                result['read_sequence_visits'].get(0x3F8, 0) != ADC_VISITS):
            raise ValueError('mask-04 four-row stream did not sustain')
        for line in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(line)
            if prefix and len(prefix_rows) < 200:
                prefix_rows.append(dict(pc=row['pc'], raw=row['raw']))
            high = gate_high(row)
            if high:
                high_sites[row['pc']] += 1
                if (row['pc'] != 0x3ED or row['alu']['y'] != ram[1] or
                        (row['instruction_i'], row['instruction_i_high']) !=
                        (0xA0, 0xA1)):
                    raise ValueError('PROM gate or 3ED R1-to-Y changed')
            if previous is not None and gate_high(previous) and not high:
                edges[(previous['pc'], row['pc'])] += 1
                captured.append(previous['alu']['y'])
            for address, value in row['registers'].items():
                ram[int(address)] = value
            previous = row
    if (high_sites != {0x3ED: 4 * ADC_VISITS} or
            sum(edges.values()) != 4 * ADC_VISITS or
            len(captured) != 4 * ADC_VISITS or
            any(before != 0x3ED for before, _ in edges)):
        raise ValueError('PROM NAND edge count changed')
    return captured, dict(trace_digest=result['trace_digest'],
                          high_sites={f'{pc:03X}': n for pc, n in high_sites.items()},
                          rising_edges={f'{a:03X}->{b:03X}': n
                                        for (a, b), n in edges.items()},
                          captured_sha256=hashlib.sha256(bytes(captured)).hexdigest(),
                          distinct_captured_y=len(set(captured))), prefix_rows


def errors(streams, stimuli, indexes, bit, operation, phase, lag,
           target_bit, inverted):
    total = 0
    for index in indexes:
        data = streams[index]
        middle = stimuli[index]['middle']
        for symbol in SYMBOL_INDEXES:
            visit = symbol * VISITS_PER_SYMBOL + phase
            current = (data[visit] >> bit) & 1
            previous = (data[visit - VISITS_PER_SYMBOL] >> bit) & 1
            observed = (current if operation == 'direct' else
                        current ^ previous) ^ inverted
            total += observed != ((middle[symbol + lag] >> target_bit) & 1)
    return total


def screen(streams, stimuli):
    checks = len(TRAIN) * len(SYMBOL_INDEXES)
    exact_training = exact_train_holdout = tested = 0
    best = None
    for operation in OPERATIONS:
        for target_bit in (0, 1):
            for bit in range(8):
                for phase in range(VISITS_PER_SYMBOL):
                    for lag in LAGS:
                        raw = errors(streams, stimuli, TRAIN, bit, operation,
                                     phase, lag, target_bit, 0)
                        inverted = int(raw > checks // 2)
                        train = min(raw, checks - raw)
                        holdout = errors(streams, stimuli, HOLDOUT, bit,
                                         operation, phase, lag, target_bit,
                                         inverted)
                        tested += 1
                        exact_training += train == 0
                        exact_train_holdout += train == holdout == 0
                        if best is None or train < best['training_errors']:
                            best = dict(operation=operation, target_bit=target_bit,
                                        bit=bit, phase_visit=phase, lag=lag,
                                        inverted=bool(inverted),
                                        training_errors=train,
                                        holdout_errors=holdout)
    return dict(tested=tested, exact_training=exact_training,
                exact_training_and_holdout=exact_train_holdout, best=best)


def run(out=HERE / 'results/receiver-mask04-3ed-prom-latch.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    stimuli = sequences()
    selected = sorted(set(TRAIN + HOLDOUT))
    streams, cases = {}, {}
    prefix = None
    for index in selected:
        streams[index], cases[index], maybe_prefix = capture(
            mapping, base, stimuli[index]['middle'], prefix=prefix is None)
        if prefix is None:
            prefix = maybe_prefix
        print('captured stream', index, flush=True)
    if len({case['trace_digest'] for case in cases.values()}) != len(selected):
        raise ValueError('different ADC streams collapsed')
    gates = gate_search(prefix)
    scores = screen(streams, stimuli)
    best = scores['best']
    validation = []
    for seed in VALIDATION_SEEDS:
        generator = random.Random(seed)
        middle = [generator.randrange(4) for _ in range(16)]
        data, case, _ = capture(mapping, base, middle)
        count = errors({0: data}, {0: dict(middle=middle)}, [0],
                       best['bit'], best['operation'], best['phase_visit'],
                       best['lag'], best['target_bit'], int(best['inverted']))
        validation.append(dict(seed=seed, errors=count,
                               checks=len(SYMBOL_INDEXES), **case))
        print('validated seed', seed, flush=True)
    paths = [Path(__file__), HERE / 'joint_mask04_adc_rom_wrapper_rule.py',
             HERE / 'receiver_mask04_retained_bit_screen.py',
             HERE / 'receiver_four_row_condition_screen.py',
             HERE / 'reference_modem.py', HERE.parent / 'assumed/execute.py',
             HERE.parent / 'model.py', HERE.parent / 'board/inventory.json',
             HERE.parents[2] / 'photos/PXL_20261123_114926601.jpg',
             MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(
        experiment='raw-PROM NAND latch of mask-04 3ED R1/Y and serial-bit screen',
        fixture=dict(mapping='joint upper-source mask 04',
                     dispatch='scenario [0,1,2,3]',
                     condition='inverted previous overflow at select 0',
                     adc='complementary reference PCM, 47/46 visits per sample',
                     gate=GATE, gate_output='hypothetical NAND rising edge after 3ED',
                     visits_per_symbol=VISITS_PER_SYMBOL,
                     operations=OPERATIONS, lags=LAGS,
                     symbol_indexes=SYMBOL_INDEXES,
                     train_indexes=TRAIN, holdout_indexes=HOLDOUT),
        gate_search=gates, cases=cases, bit_screen=scores,
        validation=validation,
        limitations=[
            'U19 NAND input and latch/output wiring are photo-compatible hypotheses, not traced nets.',
            'Clocking on the transition requires a suitable setup phase; the physical edge is unverified.',
            'Direct and previous-symbol-XOR bits do not cover multi-byte or adaptive demodulation.',
            'No candidate bit is an executed DSC decision or identified USART 01 RxD wire.'],
        source_sha256={str(path.relative_to(HERE.parents[2])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    print(report['gate_search'], report['bit_screen'], report['validation'])
