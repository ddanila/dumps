"""Check a four-literal 3F8 PROM clock on a complete receive trace."""

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
from lower_i_d3f8_full_adc import LONG_SAMPLES, SAMPLE_START
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from receiver_four_row_condition_screen import configured
from receiver_mask04_3ed_prom_latch import ADC_VISITS, CYCLES
from receiver_mask04_carrier_phase_screen import rotated_transmit
from reference_modem import receive

SEED = 0x4E11
DEGREES = 45


def high(raw):
    return bool(raw[0] & 0x02 and raw[0] & 0x08 and raw[0] & 0x80 and
                not raw[2] & 0x02)


def run(out=HERE / 'results/receiver-mask04-3f8-gate-timing.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    generator = random.Random(SEED)
    middle = [generator.randrange(4) for _ in range(16)]
    dibits = [0] * 8 + middle + [0] * 8
    pcm = rotated_transmit(dibits, DEGREES)
    if receive(pcm) != dibits[1:]:
        raise ValueError('reference receiver lost stimulus')
    samples = [127 - value for value in
               pcm[SAMPLE_START:SAMPLE_START + LONG_SAMPLES]]
    values = [sample for index, sample in enumerate(samples)
              for _ in range(47 if index % 8 < 7 else 46)]
    if len(values) != ADC_VISITS:
        raise ValueError('ADC schedule changed')
    scenario = configured(base, values, 'previous', 'overflow', 1)
    high_sites = Counter()
    falling_edges = Counter()
    first_edges = []
    selected_y = []
    edge_y = []
    latch_value = None
    latest_receive_edge = None
    first_consumers = []
    symbol_consumers = []
    receive_consumer_lags = Counter()
    receive_consumers = 0
    startup_consumer = None
    missing_latch_consumers = 0
    previous = None
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, CYCLES, mode='integrated',
                         out=temporary, trace_limit=CYCLES)
        if (not result['clean'] or result['completed_cycles'] != CYCLES or
                result['read_sequence_visits'].get(0x3F8) != ADC_VISITS):
            raise ValueError('full-PROM receiver path stopped')
        for line in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(line)
            if high(row['raw']):
                high_sites[row['pc']] += 1
                if row['pc'] == 0x3F8:
                    selected_y.append(row['alu']['y'])
            if previous is not None and high(previous['raw']) and not high(row['raw']):
                falling_edges[(previous['pc'], row['pc'])] += 1
                latch_value = (previous['alu']['y'] >> 7) & 1
                if previous['pc'] == 0x3F8:
                    edge_y.append(previous['alu']['y'])
                    latest_receive_edge = (len(edge_y) - 1, row['cycle'], latch_value)
                if len(first_edges) < 6:
                    first_edges.append(dict(before_cycle=previous['cycle'],
                                            after_cycle=row['cycle'],
                                            before_pc=f'{previous["pc"]:03X}',
                                            after_pc=f'{row["pc"]:03X}',
                                            captured_y=previous['alu']['y']))
            if row['pc'] == 0x3ED:
                if latch_value is None:
                    missing_latch_consumers += 1
                elif latest_receive_edge is None:
                    if startup_consumer is None:
                        startup_consumer = dict(cycle=row['cycle'], latch_y7=latch_value)
                else:
                    visit, edge_cycle, captured_bit = latest_receive_edge
                    if latch_value != captured_bit:
                        raise ValueError('receive latch overwritten before 3ED')
                    receive_consumer_lags[row['cycle'] - edge_cycle] += 1
                    receive_consumers += 1
                    if len(first_consumers) < 6:
                        first_consumers.append(dict(visit=visit, cycle=row['cycle'],
                                                    lag=row['cycle'] - edge_cycle,
                                                    latch_y7=latch_value,
                                                    output_y=row['alu']['y']))
                    if visit // 375 < 16 and visit % 375 in (47, 94) and row['cycle'] - edge_cycle == 26:
                        symbol_consumers.append(dict(symbol=visit // 375,
                                                     sample_visit=visit % 375,
                                                     cycle=row['cycle'], latch_y7=latch_value))
            previous = row
    old = json.loads((HERE / 'results/receiver-mask04-collision-state.json').read_text())
    reference = next(case for case in old['cases'] if case['seed'] == SEED)
    bit_report = json.loads((HERE / 'results/receiver-mask04-3f8-phase-bit.json').read_text())
    bit_case = next(case for case in bit_report['development'] if
                    case['seed'] == SEED)
    if (result['trace_digest'] != reference['trace_digest'] or
            len(edge_y) != ADC_VISITS or edge_y != selected_y or
            [edge_y[symbol * 375 + 47] for symbol in range(16)] !=
            bit_case['y3f8'] or
            [selected_y[symbol * 375 + phase]
             for symbol in range(16) for phase in (47, 94)] !=
            [case['adc'][str(phase)]['state']['y']
             for case in reference['symbols'] for phase in (47, 94)]):
        raise ValueError('gate trace disagrees with state audit')
    if (missing_latch_consumers or not receive_consumers or
            sum(falling_edges.values()) != ADC_VISITS + 1 or
            dict(receive_consumer_lags) != {2: 6000, 10: 6000,
                                            18: 5999, 26: 5999} or
            len(symbol_consumers) != 32 or
            [entry['latch_y7'] for entry in symbol_consumers] !=
            [(case['adc'][str(visit)]['state']['y'] >> 7) & 1
             for case in reference['symbols'] for visit in (47, 94)]):
        raise ValueError('latch/consumer timing disagrees with gate audit')
    paths = (Path(__file__), HERE / 'receiver_mask04_collision_state.py',
             HERE / 'receiver_mask04_3f8_phase_bit.py',
             HERE / 'receiver_mask04_carrier_phase_screen.py',
             HERE / 'reference_modem.py', HERE.parent / 'assumed/execute.py',
             MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin'))
    report = dict(experiment='executed four-literal raw-PROM 3F8 clock level and falling edge',
                  fixture=dict(seed=SEED, degrees=DEGREES,
                               gate='U10.D1 & U10.D3 & U10.D7 & !U17.D1',
                               nand_rising='on candidate level high-to-low'),
                  trace_digest=result['trace_digest'],
                  high_sites={f'{pc:03X}': count for pc, count in high_sites.items()},
                  falling_edges={f'{a:03X}->{b:03X}': count
                                 for (a, b), count in falling_edges.items()},
                  first_edges=first_edges,
                  one_bit_latch=dict(edge='candidate NAND rising edge',
                                     data='previous instruction Am2901 Y7',
                                     startup_consumer=startup_consumer,
                                     receive_consumer_count=receive_consumers,
                                     first_receive_consumers=first_consumers,
                                     symbol_visit_47_94_row3=symbol_consumers,
                                     consumer_lags={str(lag): count for lag, count
                                                    in sorted(receive_consumer_lags.items())},
                                     consumers_before_any_latch=missing_latch_consumers),
                  captured_y_sha256=hashlib.sha256(bytes(selected_y)).hexdigest(),
                  edge_captured_y_sha256=hashlib.sha256(bytes(edge_y)).hexdigest(),
                  selected_y_count=len(selected_y),
                  limitations=['Raw PROM bits and instruction timing are executed; the physical gate, NAND edge and latch pin route are assumed.',
                               'A combinational decode may glitch during PROM address transitions; edge cleanliness is not proved by the instruction-level model.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
