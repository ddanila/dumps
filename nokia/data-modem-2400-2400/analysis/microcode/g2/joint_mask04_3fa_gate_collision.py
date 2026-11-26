"""Test a raw-PROM 3FA latch against a U12 collision and a legal carrier."""

import hashlib
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
import joint_mask04_receive_impulse_memory as impulse
from joint_upper_source_screen import candidate
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_four_row_condition_screen import configured
from receiver_prom_row_latch_gate import GATES, level
from receiver_mask04_carrier_phase_screen import rotated_transmit
from reference_modem import receive


def capture(mapping, base, adc):
    scenario = configured(base, adc, 'previous', 'overflow', 1)
    high_sites = [Counter() for _ in GATES]
    edges = [Counter() for _ in GATES]
    latched = [[] for _ in GATES]
    previous = None
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, impulse.CYCLES, mode='integrated',
                         out=temporary, trace_limit=impulse.CYCLES)
        if (not result['clean'] or
                result['read_sequence_visits'].get(0x3F8) != impulse.ADC_VISITS or
                result['address_counts'].get(0x3FA) != impulse.ADC_VISITS):
            raise ValueError('receive loop did not sustain')
        for line in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(line)
            for index, gate in enumerate(GATES):
                current = level(row, gate)
                if current:
                    high_sites[index][row['pc']] += 1
                if previous is not None and level(previous, gate) and not current:
                    edges[index][(previous['pc'], row['pc'])] += 1
                    latched[index].append(previous['alu']['y'])
            previous = row
    for index in range(len(GATES)):
        if (high_sites[index] != {0x3FA: impulse.ADC_VISITS} or
                edges[index] != {(0x3FA, 0x3ED): impulse.ADC_VISITS} or
                len(latched[index]) != impulse.ADC_VISITS):
            raise ValueError(('3FA gate did not isolate the row', index,
                              high_sites[index], edges[index]))
    if latched[0] != latched[1]:
        raise ValueError('candidate gates captured different data')
    return latched[0], result['trace_digest']


def run(out=HERE / 'results/joint-mask04-3fa-gate-collision.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    paired = {}
    for code in (0x1F, 0x6F):
        adc = impulse.held_samples([0x7F] * impulse.SAMPLES, 25, code)
        y, trace = capture(mapping, base, adc)
        paired[f'{code:02X}'] = dict(y=y, trace_digest=trace,
                                    adc_sha256=hashlib.sha256(bytes(adc)).hexdigest())
    differences = [index for index, (a, b) in enumerate(zip(
        paired['1F']['y'], paired['6F']['y'])) if a != b]
    expected = list(range(1172, 1219))
    if differences != expected or Counter(
            (paired['1F']['y'][i], paired['6F']['y'][i]) for i in differences
    ) != {(0x20, 0x21): 47}:
        raise ValueError('matched 3FA collision result changed')

    dibits = (1, 1, 2, 3, 0, 0, 3, 2)
    pcm = rotated_transmit(dibits, 75)
    if len(pcm) != impulse.SAMPLES or receive(pcm) != list(dibits[1:]):
        raise ValueError('legal carrier fixture changed')
    adc = impulse.held_samples([127 - value for value in pcm], 0, None)
    legal_y, legal_trace = capture(mapping, base, adc)
    if sorted(set(legal_y)) != [0x20, 0x21]:
        raise ValueError('legal 3FA output alphabet changed')
    selected = {str(phase): [legal_y[symbol * impulse.VISITS_PER_SYMBOL + phase]
                             for symbol in range(len(dibits))]
                for phase in (47, 94)}
    paths = (Path(__file__), Path(impulse.__file__),
             HERE / 'receiver_prom_row_latch_gate.py',
             HERE / 'receiver_mask04_carrier_phase_screen.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='mask04 raw-PROM 3FA latch on collision and legal carrier',
                  fixture=dict(adc_visits=impulse.ADC_VISITS,
                               cycles_per_run=impulse.CYCLES,
                               gates=GATES, edge='3FA->3ED',
                               legal_dibits=dibits, legal_rotation_degrees=75),
                  paired_cases={code: dict(trace_digest=row['trace_digest'],
                                           adc_sha256=row['adc_sha256'],
                                           latched_y_sha256=hashlib.sha256(bytes(row['y'])).hexdigest())
                                for code, row in paired.items()},
                  paired_difference=dict(count=len(differences),
                                         first=differences[0], last=differences[-1],
                                         value_pairs={'20->21': len(differences)}),
                  legal_case=dict(trace_digest=legal_trace,
                                  adc_sha256=hashlib.sha256(bytes(adc)).hexdigest(),
                                  latched_y_sha256=hashlib.sha256(bytes(legal_y)).hexdigest(),
                                  distinct_bytes=sorted(set(legal_y)),
                                  bit0_ones=sum(y & 1 for y in legal_y),
                                  selected_y=selected),
                  limitations=[
                      'The 1F/6F pair is an artificial one-sample pulse, not two legal dibits.',
                      'The legal stream tests signal variation, not a recovered dibit decision.',
                      'The PROM-to-NAND, NAND-to-latch, Y-bus and downstream serial connections remain untraced assumptions.'
                  ],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
