"""Run a 32-symbol reversal preamble directly into the mask-04 receiver."""

import hashlib
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
from joint_upper_source_screen import candidate
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_four_row_condition_screen import configured
from receiver_mask04_3f8_gate_timing import high as gate_high
from receiver_mask04_carrier_phase_screen import rotated_transmit
from receiver_mask04_phase47_logic import phase_quadrant
from receiver_mask04_two_visit_rule import RULE
from reference_modem import QUADRANT_TO_DIBIT, receive

SEEDS = (0xA431, 0xC991)
ROTATIONS = (0, 45)
PREAMBLE_SYMBOLS = 32
DATA_SYMBOLS = 16
VISITS_PER_SYMBOL = 375
ADC_VISITS = (PREAMBLE_SYMBOLS + DATA_SYMBOLS) * VISITS_PER_SYMBOL
CYCLES = 32 * ADC_VISITS + 47
CAPTURE_PHASE = 47


def score(states, dibits, indexes):
    errors = unknown = 0
    decisions = []
    for symbol in indexes:
        before, after = states[symbol - 1:symbol + 1]
        if before is None or after is None:
            decisions.append(None)
            unknown += 1
        else:
            bitpair = QUADRANT_TO_DIBIT[(after - before - 2) & 3]
            decisions.append(bitpair)
            errors += bitpair != dibits[symbol]
    return dict(checks=len(indexes), errors=errors,
                unknown=unknown, dibits=decisions)


def capture(mapping, base, degrees, seed, middle):
    dibits = [3] * PREAMBLE_SYMBOLS + middle + [0] * 8
    pcm = rotated_transmit(dibits, degrees)
    if receive(pcm) != dibits[1:]:
        raise ValueError('reference receiver lost protocol preamble or data')
    samples = [127 - value for value in pcm[:8 * (PREAMBLE_SYMBOLS + DATA_SYMBOLS)]]
    values = [sample for index, sample in enumerate(samples)
              for _ in range(47 if index % 8 < 7 else 46)]
    if len(values) != ADC_VISITS:
        raise ValueError('ADC hold schedule changed')
    scenario = configured(base, values, 'previous', 'overflow', 1)
    row_y = {}
    transient_y = {}
    selected_y = []
    gate_sites = Counter()
    gate_edges = Counter()
    edge_y = []
    adc_event = row_event = 0
    previous = None
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, CYCLES, mode='integrated',
                         out=temporary, trace_limit=CYCLES)
        if (not result['clean'] or result['completed_cycles'] != CYCLES or
                result['read_sequence_visits'].get(0x3F8) != ADC_VISITS or
                result['address_counts'].get(0x3ED) != 4 * ADC_VISITS):
            raise ValueError('protocol receive path stopped')
        for line in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(line)
            if gate_high(row['raw']):
                gate_sites[row['pc']] += 1
            if previous is not None and gate_high(previous['raw']) and not gate_high(row['raw']):
                gate_edges[(previous['pc'], row['pc'])] += 1
                if previous['pc'] == 0x3F8:
                    edge_y.append(previous['alu']['y'])
            if row['pc'] == 0x3F8:
                if (not row['external_read']['selected_by_alu'] or
                        row['external_read']['value'] != values[adc_event]):
                    raise ValueError('3F8 did not select ADC byte')
                selected_y.append(row['alu']['y'])
                symbol, phase = divmod(adc_event, VISITS_PER_SYMBOL)
                if phase == CAPTURE_PHASE:
                    transient_y[symbol] = dict(cycle=row['cycle'], y=row['alu']['y'])
                adc_event += 1
            if row['pc'] == 0x3ED:
                visit, index = divmod(row_event, 4)
                symbol, phase = divmod(visit, VISITS_PER_SYMBOL)
                if phase == CAPTURE_PHASE and index in (0, 3):
                    row_y[(symbol, index)] = dict(cycle=row['cycle'], y=row['alu']['y'])
                row_event += 1
            previous = row
    if (adc_event != ADC_VISITS or row_event != 4 * ADC_VISITS or
            len(edge_y) != ADC_VISITS or edge_y != selected_y or
            len(row_y) != 2 * (PREAMBLE_SYMBOLS + DATA_SYMBOLS) or
            len(transient_y) != PREAMBLE_SYMBOLS + DATA_SYMBOLS):
        raise ValueError('protocol receive capture count changed')
    symbols = []
    for symbol in range(PREAMBLE_SYMBOLS + DATA_SYMBOLS):
        symbols.append(dict(symbol=symbol, dibit=dibits[symbol],
                            row0=row_y[(symbol, 0)],
                            row3=row_y[(symbol, 3)],
                            at_3f8=transient_y[symbol]))
    base_pairs = [(s['row0']['y'], s['row3']['y']) for s in symbols]
    nominal_states = [phase_quadrant(*pair) for pair in base_pairs]
    diagonal_states = []
    for pair, row in zip(base_pairs, symbols):
        state = RULE.get(pair)
        if pair == (0xF3, 0xF2):
            state = (row['at_3f8']['y'] >> 7) & 1
        diagonal_states.append(state)
    all_data = range(PREAMBLE_SYMBOLS, PREAMBLE_SYMBOLS + DATA_SYMBOLS)
    interior = range(PREAMBLE_SYMBOLS + 2,
                     PREAMBLE_SYMBOLS + DATA_SYMBOLS - 2)
    return dict(degrees=degrees, seed=seed, middle=middle, symbols=symbols,
                adc_stream_sha256=hashlib.sha256(bytes(values)).hexdigest(),
                trace_digest=result['trace_digest'],
                gate_sites={f'{pc:03X}': n for pc, n in gate_sites.items()},
                gate_edges={f'{a:03X}->{b:03X}': n
                            for (a, b), n in gate_edges.items()},
                edge_captured_sha256=hashlib.sha256(bytes(edge_y)).hexdigest(),
                nominal=dict(all_data=score(nominal_states, dibits, all_data),
                             interior=score(nominal_states, dibits, interior)),
                diagonal=dict(all_data=score(diagonal_states, dibits, all_data),
                              interior=score(diagonal_states, dibits, interior)))


def run(out=HERE / 'results/receiver-mask04-protocol-preamble.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    cases = []
    for degrees in ROTATIONS:
        for seed in SEEDS:
            generator = random.Random(seed)
            middle = [generator.randrange(4) for _ in range(DATA_SYMBOLS)]
            case = capture(mapping, base, degrees, seed, middle)
            cases.append(case)
            print('captured', degrees, hex(seed), 'nominal',
                  case['nominal']['all_data']['errors'],
                  case['nominal']['all_data']['unknown'], 'diagonal',
                  case['diagonal']['all_data']['errors'],
                  case['diagonal']['all_data']['unknown'], flush=True)
    paths = (Path(__file__), HERE / 'receiver_mask04_3f8_gate_timing.py',
             HERE / 'receiver_mask04_3f8_phase_bit.py',
             HERE / 'receiver_mask04_phase47_logic.py',
             HERE / 'receiver_mask04_carrier_phase_screen.py',
             HERE / 'reference_modem.py', HERE.parent / 'assumed/execute.py',
             MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='continuous 32-symbol reversal preamble and 16-symbol data receive replay',
                  fixture=dict(seeds=SEEDS, rotations=ROTATIONS,
                               preamble_dibit=3, preamble_symbols=PREAMBLE_SYMBOLS,
                               data_symbols=DATA_SYMBOLS, adc_visits=ADC_VISITS,
                               cycles=CYCLES, capture_visit=CAPTURE_PHASE),
                  cases=cases,
                  limitations=['The preamble waveform is a protocol-motivated reference stimulus, not measured Nokia line input.',
                               'The ADC route, 3F8 latch, row-pair readout, phase-class selection and RxD wire remain hypotheses.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
