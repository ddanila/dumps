"""Distinguish two candidate symbol-capture phases with boundary ADC impulses."""

import hashlib
import json
import random
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from receiver_mask04_3f8_gate_timing import high
from receiver_mask04_dual_feature_consensus import consensus, decisions
from receiver_mask04_dual_zero_handoff import frozen_tables
from receiver_mask04_feature_choice import alternative_states
from receiver_mask04_four_bit_transition import states_from_symbols
from receiver_mask04_protocol_preamble import (MAPPINGS, candidate, configured,
                                               execute, fixture, mapped,
                                               mapping_with_upper_source,
                                               receive, rotated_transmit)

SEED = 0xAC17
DEGREES = 75
SYMBOLS = 32
VISITS_PER_SYMBOL = 375
CAPTURE_PHASES = (47, 94)


def one_run(mapping, base, dibits, pulse):
    pcm = rotated_transmit(dibits, DEGREES)
    if receive(pcm) != dibits[1:]:
        raise ValueError('reference receiver lost boundary fixture')
    samples = [127 - value for value in pcm[:8 * SYMBOLS]]
    values = [sample for index, sample in enumerate(samples)
              for _ in range(47 if index % 8 < 7 else 46)]
    if len(values) != SYMBOLS * VISITS_PER_SYMBOL:
        raise ValueError('ADC visit schedule changed')
    changed = []
    if pulse != 'natural':
        for symbol in range(SYMBOLS):
            for phase in CAPTURE_PHASES:
                changed_phase = phase if pulse == 'selected' else phase - 1
                index = symbol * VISITS_PER_SYMBOL + changed_phase
                before = values[index]
                values[index] ^= 0x80
                changed.append(dict(symbol=symbol, visit=changed_phase,
                                    before=before, after=values[index]))
    scenario = configured(base, values, 'previous', 'overflow', 1)
    cycles = 32 * len(values) + 47
    direct = {}
    current = {}
    previous_phase = {}
    adc_event = 0
    candidate_edges = 0
    prior_row = None
    latch = None
    last_edge = None
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, cycles, mode='integrated',
                         out=temporary, trace_limit=cycles)
        if (not result['clean'] or result['completed_cycles'] != cycles or
                result['read_sequence_visits'].get(0x3F8) != len(values)):
            raise ValueError('receive loop stopped')
        for line in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(line)
            if prior_row is not None and high(prior_row['raw']) and not high(row['raw']):
                candidate_edges += 1
                latch = prior_row['alu']['y'] & 0xE0
                if prior_row['pc'] == 0x3F8:
                    last_edge = (adc_event - 1, row['cycle'])
            if row['pc'] == 0x3ED and last_edge is not None:
                visit, edge_cycle = last_edge
                symbol, phase = divmod(visit, VISITS_PER_SYMBOL)
                lag = row['cycle'] - edge_cycle
                if phase in CAPTURE_PHASES and lag == 10:
                    current[(symbol, phase)] = latch
                next_symbol, next_phase = divmod(visit + 1, VISITS_PER_SYMBOL)
                if next_phase in CAPTURE_PHASES and lag == 18:
                    previous_phase[(next_symbol, next_phase)] = latch
            if row['pc'] == 0x3F8:
                if (not row['external_read']['selected_by_alu'] or
                        row['external_read']['value'] != values[adc_event]):
                    raise ValueError('ADC ingress changed')
                symbol, phase = divmod(adc_event, VISITS_PER_SYMBOL)
                if phase in CAPTURE_PHASES:
                    direct[(symbol, phase)] = row['alu']['y'] & 0xE0
                adc_event += 1
            prior_row = row
    if (adc_event != len(values) or candidate_edges != len(values) + 1 or
            len(current) != 2 * SYMBOLS or
            len(previous_phase) != 2 * SYMBOLS or current != direct):
        raise ValueError('capture timing changed')

    def symbols(captures):
        return [dict(symbol=symbol, dibit=dibits[symbol],
                     visits={str(phase): dict(y3f8=captures[(symbol, phase)])
                             for phase in CAPTURE_PHASES})
                for symbol in range(SYMBOLS)]

    return dict(trace_digest=result['trace_digest'],
                adc_stream_sha256=hashlib.sha256(bytes(values)).hexdigest(),
                changed=changed, candidate_edges=candidate_edges,
                current=symbols(current), previous=symbols(previous_phase),
                distinct_captures=sum(current[key] != previous_phase[key]
                                      for key in current))


def score(symbols, primary, alternative):
    expected = [item['dibit'] for item in symbols]
    p = decisions(states_from_symbols(symbols), primary)
    a = decisions(alternative_states(symbols), alternative)
    output = consensus(p, a)
    return dict(checks=SYMBOLS - 1,
                wrong=sum(got is not None and got != want
                          for got, want in zip(output[1:], expected[1:])),
                unknown=sum(got is None for got in output[1:]),
                decisions=output)


def run(out=HERE / 'results/receiver-mask04-capture-phase-boundary.json'):
    rng = random.Random(SEED)
    dibits = [3] * 8 + [rng.randrange(4) for _ in range(16)] + [0] * 8
    primary, alternative = frozen_tables()
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    cases = []
    for pulse in ('natural', 'selected', 'preceding'):
        trace = one_run(mapping, base, dibits, pulse)
        current = score(trace.pop('current'), primary, alternative)
        previous = score(trace.pop('previous'), primary, alternative)
        row = dict(fixture=pulse,
                   **trace, current_capture=current, pre_capture=previous,
                   changed_decisions=sum(a != b for a, b in
                                         zip(current['decisions'], previous['decisions'])))
        cases.append(row)
        print(row['fixture'], 'distinct captures', row['distinct_captures'],
              'current', current['wrong'], current['unknown'],
              'pre', previous['wrong'], previous['unknown'], flush=True)
    paths = [Path(__file__), HERE / 'receiver_mask04_3f8_gate_timing.py',
             HERE / 'receiver_mask04_dual_zero_handoff.py',
             HERE / 'receiver_mask04_dual_feature_consensus.py',
             HERE / 'receiver_mask04_cubic_transition.py',
             HERE / 'receiver_mask04_four_bit_transition.py',
             HERE / 'receiver_mask04_feature_choice.py',
             HERE / 'receiver_mask04_multivisit_capture.py',
             HERE / 'receiver_mask04_protocol_preamble.py',
             HERE / 'receiver_mask04_carrier_phase_screen.py',
             HERE / 'reference_modem.py',
             HERE / 'results/receiver-mask04-four-bit-transition.json',
             HERE / 'results/receiver-mask04-feature-choice.json',
             HERE / 'results/receiver-mask04-multivisit-capture.json',
             HERE / 'results/receiver-mask04-three-bit-two-visit.json',
             MAPPINGS['q3'], HERE.parent / 'assumed/execute.py',
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(experiment='ADC boundary capture-phase diagnostic',
                  fixture=dict(seed=SEED, degrees=DEGREES, symbols=SYMBOLS,
                               visits=CAPTURE_PHASES,
                               pulse='XOR ADC bit 7 for one visit at selected or preceding boundary'),
                  cases=cases,
                  limitations=['The injected one-visit ADC impulses are diagnostics, not measured line events.',
                               'Capture clocks, gate logic, latch and symbol memory remain board hypotheses.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
