"""Test controller frame-byte hypotheses against frozen two-visit receiver decisions."""

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

SEED = 0xB417
ANGLES = (75, 165)
SYMBOLS = 16
VISITS_PER_SYMBOL = 375
CAPTURE_PHASES = (47, 94)
ADC_VISITS = SYMBOLS * VISITS_PER_SYMBOL
CYCLES = 32 * ADC_VISITS + 47
WRAPPER_VISITS = 4 * ADC_VISITS + 1


def capture(mapping, base, dibits, degrees, name, mode_values):
    pcm = rotated_transmit(dibits, degrees)
    if receive(pcm) != dibits[1:]:
        raise ValueError('reference receiver lost mode fixture')
    samples = [127 - value for value in pcm[:8 * SYMBOLS]]
    values = [sample for index, sample in enumerate(samples)
              for _ in range(47 if index % 8 < 7 else 46)]
    if len(values) != ADC_VISITS or len(mode_values) != WRAPPER_VISITS:
        raise ValueError('mode/ADC schedule changed')
    scenario = configured(base, values, 'previous', 'overflow', 1)
    scenario['io']['read']['pc_sequences'][str(0x3EB)] = mode_values
    scenario['io']['read']['evidence'] += (
        '; hypothetical controller third-frame-byte route to wrapper 3EB')
    outputs = {}
    mode_reads = 0
    adc_reads = 0
    gate_edges = 0
    last_row = None
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, CYCLES, mode='integrated',
                         out=temporary, trace_limit=CYCLES)
        if (not result['clean'] or result['completed_cycles'] != CYCLES or
                result['read_sequence_visits'].get(0x3F8) != ADC_VISITS or
                result['address_counts'].get(0x3EB) != WRAPPER_VISITS):
            raise ValueError(('mode route did not sustain', name))
        for line in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(line)
            if last_row is not None and high(last_row['raw']) and not high(row['raw']):
                gate_edges += 1
                if last_row['pc'] not in (0x18C, 0x3F8):
                    raise ValueError('unexpected receive gate edge')
            if row['pc'] == 0x3EB:
                if (not row['external_read']['selected_by_alu'] or
                        row['external_read']['value'] != mode_values[mode_reads]):
                    raise ValueError(('3EB mode read changed', name, mode_reads))
                mode_reads += 1
            if row['pc'] == 0x3F8:
                if (not row['external_read']['selected_by_alu'] or
                        row['external_read']['value'] != values[adc_reads]):
                    raise ValueError(('3F8 ADC read changed', name, adc_reads))
                symbol, phase = divmod(adc_reads, VISITS_PER_SYMBOL)
                if phase in CAPTURE_PHASES:
                    outputs[(symbol, phase)] = row['alu']['y'] & 0xE0
                adc_reads += 1
            last_row = row
    if (mode_reads != WRAPPER_VISITS or adc_reads != ADC_VISITS or
            gate_edges != ADC_VISITS + 1 or len(outputs) != 2 * SYMBOLS):
        raise ValueError(('mode capture count changed', name))
    symbols = [dict(symbol=index, dibit=dibits[index],
                    visits={str(phase): dict(y3f8=outputs[(index, phase)])
                            for phase in CAPTURE_PHASES})
               for index in range(SYMBOLS)]
    return dict(name=name, degrees=degrees, trace_digest=result['trace_digest'],
                adc_stream_sha256=hashlib.sha256(bytes(values)).hexdigest(),
                mode_stream_sha256=hashlib.sha256(bytes(mode_values)).hexdigest(),
                gate_edges=gate_edges, symbols=symbols)


def run(out=HERE / 'results/receiver-mask04-frame-mode-decisions.json'):
    rng = random.Random(SEED)
    dibits = [3] * 8 + [rng.randrange(4) for _ in range(8)]
    primary, alternative = frozen_tables()
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    modes = [('held_01', [0x01] * WRAPPER_VISITS),
             ('held_81', [0x81] * WRAPPER_VISITS),
             ('held_A1', [0xA1] * WRAPPER_VISITS),
             ('edge_81_A1', [0x81] * (WRAPPER_VISITS // 2) +
              [0xA1] * (WRAPPER_VISITS - WRAPPER_VISITS // 2))]
    cases = []
    for degrees in ANGLES:
        angle_cases = []
        for name, mode_values in modes:
            case = capture(mapping, base, dibits, degrees, name, mode_values)
            symbols = case['symbols']
            p = decisions(states_from_symbols(symbols), primary)
            a = decisions(alternative_states(symbols), alternative)
            both = consensus(p, a)
            expected = dibits[1:]
            case['decisions'] = both
            case['score'] = dict(checks=len(expected),
                                 wrong=sum(got is not None and got != want
                                           for got, want in zip(both[1:], expected)),
                                 unknown=sum(got is None for got in both[1:]),
                                 data_wrong=sum(got is not None and got != want
                                                for got, want in zip(both[8:], dibits[8:])),
                                 data_unknown=sum(got is None for got in both[8:]))
            angle_cases.append(case)
            print(degrees, name, case['score'], flush=True)
        baseline = angle_cases[0]
        for case in angle_cases[1:]:
            if case['adc_stream_sha256'] != baseline['adc_stream_sha256']:
                raise ValueError('mode cases have different ADC streams')
            case['changed_capture_values_vs_01'] = sum(
                case['symbols'][i]['visits'][str(phase)]['y3f8'] !=
                baseline['symbols'][i]['visits'][str(phase)]['y3f8']
                for i in range(SYMBOLS) for phase in CAPTURE_PHASES)
            case['changed_decisions_vs_01'] = sum(
                a != b for a, b in zip(case['decisions'], baseline['decisions']))
        cases.extend(angle_cases)
    paths = [Path(__file__), HERE / 'receiver_mask04_3f8_gate_timing.py',
             HERE / 'receiver_mask04_dual_zero_handoff.py',
             HERE / 'receiver_mask04_dual_feature_consensus.py',
             HERE / 'receiver_mask04_feature_choice.py',
             HERE / 'receiver_mask04_four_bit_transition.py',
             HERE / 'receiver_mask04_frame_mode_3eb.py',
             HERE / 'receiver_mask04_protocol_preamble.py',
             HERE / 'receiver_mask04_carrier_phase_screen.py',
             HERE / 'reference_modem.py', HERE.parent / 'assumed/execute.py',
             HERE / 'results/receiver-mask04-four-bit-transition.json',
             HERE / 'results/receiver-mask04-feature-choice.json',
             HERE / 'results/receiver-mask04-multivisit-capture.json',
             HERE / 'results/receiver-mask04-three-bit-two-visit.json',
             MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(experiment='hypothetical 81/A1 frame byte at D3EB versus frozen receive decisions',
                  fixture=dict(seed=SEED, degrees=ANGLES,
                               symbols=SYMBOLS, adc_visits=ADC_VISITS,
                               mode_edge_wrapper_visit=WRAPPER_VISITS // 2,
                               controller_bytes=['81', 'A1']),
                  cases=cases,
                  limitations=['The controller-frame-to-3EB D route is untraced; this is a diagnostic connection hypothesis.',
                               'The frozen decoder is external and was fitted under the held-01 receive fixture.',
                               'No line residual, echo train/freeze control or USART net is observed.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
