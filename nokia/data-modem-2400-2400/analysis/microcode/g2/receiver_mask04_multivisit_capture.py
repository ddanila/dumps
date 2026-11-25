"""Capture full executed receive bytes at two symbol-relative ADC visits."""

import hashlib
import json
import random
import tempfile
from collections import Counter
from pathlib import Path

from receiver_mask04_protocol_preamble import (HERE, CYCLES, ADC_VISITS,
                                               PREAMBLE_SYMBOLS, DATA_SYMBOLS,
                                               VISITS_PER_SYMBOL, candidate,
                                               configured, execute, fixture,
                                               gate_high, mapped,
                                               mapping_with_upper_source,
                                               MAPPINGS, receive,
                                               rotated_transmit)
from receiver_mask04_four_bit_phase import input_code
from receiver_mask04_four_bit_phase_between import DEGREES, SEED
from common import save

PRIOR = HERE / 'results/receiver-mask04-four-bit-phase-between.json'
PHASES = (47, 94)


def capture(mapping, base, degrees, middle):
    dibits = [3] * PREAMBLE_SYMBOLS + middle + [0] * 8
    pcm = rotated_transmit(dibits, degrees)
    if receive(pcm) != dibits[1:]:
        raise ValueError('reference receiver lost data')
    samples = [127 - value for value in pcm[:8 * (PREAMBLE_SYMBOLS + DATA_SYMBOLS)]]
    values = [sample for index, sample in enumerate(samples)
              for _ in range(47 if index % 8 < 7 else 46)]
    if len(values) != ADC_VISITS:
        raise ValueError('ADC schedule changed')
    scenario = configured(base, values, 'previous', 'overflow', 1)
    captures = {}
    edges = Counter()
    adc_event = row_event = 0
    previous = None
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, CYCLES, mode='integrated',
                         out=temporary, trace_limit=CYCLES)
        if (not result['clean'] or result['completed_cycles'] != CYCLES or
                result['read_sequence_visits'].get(0x3F8) != ADC_VISITS or
                result['address_counts'].get(0x3ED) != 4 * ADC_VISITS):
            raise ValueError('receive loop stopped')
        for line in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(line)
            pc = row['pc']
            if previous is not None and gate_high(previous['raw']) and not gate_high(row['raw']):
                edges[(previous['pc'], pc)] += 1
            if pc == 0x3F8:
                if (not row['external_read']['selected_by_alu'] or
                        row['external_read']['value'] != values[adc_event]):
                    raise ValueError('ADC byte mismatch')
                symbol, phase = divmod(adc_event, VISITS_PER_SYMBOL)
                if phase in PHASES:
                    captures[(symbol, phase, '3F8')] = row['alu']['y']
                adc_event += 1
            if pc == 0x3ED:
                visit, index = divmod(row_event, 4)
                symbol, phase = divmod(visit, VISITS_PER_SYMBOL)
                if phase in PHASES and index in (0, 3):
                    captures[(symbol, phase, f'3ED-row{index}')] = row['alu']['y']
                row_event += 1
            previous = row
    if (adc_event != ADC_VISITS or row_event != 4 * ADC_VISITS or
            edges[(0x3F8, 0x3F9)] != ADC_VISITS or
            len(captures) != (PREAMBLE_SYMBOLS + DATA_SYMBOLS) * len(PHASES) * 3):
        raise ValueError('capture count changed')
    symbols = []
    for symbol in range(PREAMBLE_SYMBOLS + DATA_SYMBOLS):
        snapshots = {}
        for phase in PHASES:
            snapshots[str(phase)] = dict(row0=captures[(symbol, phase, '3ED-row0')],
                                         y3f8=captures[(symbol, phase, '3F8')],
                                         row3=captures[(symbol, phase, '3ED-row3')])
        symbols.append(dict(symbol=symbol, dibit=dibits[symbol],
                            visits=snapshots))
    return dict(degrees=degrees, trace_digest=result['trace_digest'],
                adc_stream_sha256=hashlib.sha256(bytes(values)).hexdigest(),
                gate_edges={f'{a:03X}->{b:03X}': count
                            for (a, b), count in edges.items()},
                symbols=symbols)


def run(out=HERE / 'results/receiver-mask04-multivisit-capture.json'):
    prior = json.loads(PRIOR.read_text())
    generator = random.Random(SEED)
    middle = [generator.randrange(4) for _ in range(DATA_SYMBOLS)]
    if middle != prior['fixture']['data_dibits']:
        raise ValueError('prior dibits changed')
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    cases = []
    for degrees in DEGREES:
        case = capture(mapping, base, degrees, middle)
        old = next(row for row in prior['cases'] if row['degrees'] == degrees)
        codes = [input_code(s['visits']['47']['row0'], s['visits']['47']['y3f8'])
                 for s in case['symbols']]
        if (case['trace_digest'] != old['trace_digest'] or
                case['adc_stream_sha256'] != old['adc_stream_sha256'] or
                codes != old['input_codes']):
            raise ValueError(('new capture differs from prior trace', degrees))
        cases.append(case)
        print('captured', degrees, case['trace_digest'], flush=True)
    paths = [Path(__file__), PRIOR,
             HERE / 'receiver_mask04_protocol_preamble.py',
             HERE / 'receiver_mask04_four_bit_phase.py',
             HERE / 'receiver_mask04_four_bit_phase_between.py',
             MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(experiment='executed full-byte receive captures at visits 47 and 94',
                  fixture=dict(degrees=DEGREES, seed=SEED,
                               preamble_symbols=PREAMBLE_SYMBOLS,
                               data_symbols=DATA_SYMBOLS,
                               visits=PHASES,
                               adc='complementary PCM, 47/46 visits per sample'),
                  cases=cases,
                  limitations=['The receive ADC route, four-row dispatch and candidate PROM gate remain wiring hypotheses.',
                               'Both symbol-relative capture visits are analysis choices, not traced physical latch clocks.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
