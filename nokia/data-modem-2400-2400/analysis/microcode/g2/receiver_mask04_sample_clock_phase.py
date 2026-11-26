"""Constrain a 9,600 Hz sample clock against executed 3F8 visits and RxC timing."""

import hashlib
import json
import random
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from receiver_mask04_3f8_gate_timing import (ADC_VISITS, CYCLES, DEGREES,
                                             SEED, high)
from receiver_mask04_protocol_preamble import (MAPPINGS, candidate, configured,
                                               execute, fixture, mapped,
                                               mapping_with_upper_source,
                                               receive, rotated_transmit)
from lower_i_d3f8_full_adc import LONG_SAMPLES, SAMPLE_START

OSCILLATOR_HZ = 14_400_000
MICROCYCLES_PER_SAMPLE = 1500
VISITS_PER_SYMBOL = 375
SAMPLES_PER_SYMBOL = 8
SYMBOLS = 16
CAPTURE_VISITS = (47, 94)


def run(out=HERE / 'results/receiver-mask04-sample-clock-phase.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    rng = random.Random(SEED)
    dibits = [0] * 8 + [rng.randrange(4) for _ in range(16)] + [0] * 8
    pcm = rotated_transmit(dibits, DEGREES)
    if receive(pcm) != dibits[1:]:
        raise ValueError('reference receiver lost clock fixture')
    samples = [127 - value for value in
               pcm[SAMPLE_START:SAMPLE_START + LONG_SAMPLES]]
    sample_for_visit = [index for index in range(len(samples))
                        for _ in range(47 if index % 8 < 7 else 46)]
    values = [samples[index] for index in sample_for_visit]
    if len(values) != ADC_VISITS:
        raise ValueError('sample schedule changed')
    scenario = configured(base, values, 'previous', 'overflow', 1)
    f8_cycles = []
    selected_row3 = []
    previous = None
    edge_visit = None
    edge_cycle = None
    startup_edges = 0
    receive_edges = 0
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, CYCLES, mode='integrated',
                         out=temporary, trace_limit=CYCLES)
        if (not result['clean'] or result['completed_cycles'] != CYCLES or
                result['read_sequence_visits'].get(0x3F8) != ADC_VISITS):
            raise ValueError('full-PROM clock fixture stopped')
        for line in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(line)
            if previous is not None and high(previous['raw']) and not high(row['raw']):
                if previous['pc'] == 0x18C:
                    startup_edges += 1
                elif previous['pc'] == 0x3F8:
                    receive_edges += 1
                    edge_visit = receive_edges - 1
                    edge_cycle = row['cycle']
                else:
                    raise ValueError('unexpected raw-PROM clock edge')
            if row['pc'] == 0x3F8:
                visit = len(f8_cycles)
                if (not row['external_read']['selected_by_alu'] or
                        row['external_read']['value'] != values[visit]):
                    raise ValueError('executed ADC input changed')
                f8_cycles.append(row['cycle'])
            if (row['pc'] == 0x3ED and edge_visit is not None and
                    row['cycle'] - edge_cycle == 10 and
                    edge_visit // VISITS_PER_SYMBOL < SYMBOLS and
                    edge_visit % VISITS_PER_SYMBOL in CAPTURE_VISITS):
                selected_row3.append(dict(symbol=edge_visit // VISITS_PER_SYMBOL,
                                          visit=edge_visit % VISITS_PER_SYMBOL,
                                          cycle=row['cycle']))
            previous = row
    if (len(f8_cycles) != ADC_VISITS or startup_edges != 1 or
            receive_edges != ADC_VISITS or len(selected_row3) != 32 or
            any(cycle != f8_cycles[0] + 32 * visit
                for visit, cycle in enumerate(f8_cycles))):
        raise ValueError('PROM clock or row-3 cadence changed')
    first_edge = f8_cycles[0] + 1
    phases = []
    for phase in range(-32, 33):
        tick_zero = first_edge + phase
        mismatches = sum((first_edge + 32 * visit - tick_zero) //
                         MICROCYCLES_PER_SAMPLE != sample_for_visit[visit]
                         for visit in range(ADC_VISITS))
        collisions = sum((first_edge + 32 * visit - tick_zero) %
                         MICROCYCLES_PER_SAMPLE == 0
                         for visit in range(ADC_VISITS))
        phases.append(dict(phase=phase, mismatched_visits=mismatches,
                           same_cycle_sample_and_latch=collisions))
    clean_phases = [row['phase'] for row in phases
                    if not row['mismatched_visits'] and
                    not row['same_cycle_sample_and_latch']]
    if clean_phases != [-3, -2, -1]:
        raise ValueError(('sample-clock phase window changed', clean_phases))
    for item in selected_row3:
        visit = item['symbol'] * VISITS_PER_SYMBOL + item['visit']
        if (sample_for_visit[visit] != item['symbol'] * SAMPLES_PER_SYMBOL +
                (1 if item['visit'] == 47 else 2) or
                sample_for_visit[visit - 1] != sample_for_visit[visit] - 1):
            raise ValueError('selected capture is not first visit of sample')
    rxc = []
    for phase in clean_phases:
        tick_zero = first_edge + phase
        setups = []
        early_setups = []
        for symbol in range(SYMBOLS):
            second_capture = selected_row3[2 * symbol + 1]['cycle']
            decision_ready = second_capture + 1
            bit0_edge = tick_zero + symbol * 12000 + 3 * MICROCYCLES_PER_SAMPLE
            early_edge = tick_zero + symbol * 12000 + 2 * MICROCYCLES_PER_SAMPLE
            setups.append(bit0_edge - decision_ready)
            early_setups.append(early_edge - decision_ready)
        rxc.append(dict(sample_clock_phase=phase,
                        bit0_sample_index=3, bit1_sample_index=7,
                        bit0_setup_microcycles=sorted(set(setups)),
                        sample_index_2_control_setup=sorted(set(early_setups)),
                        bit_spacing_microcycles=4 * MICROCYCLES_PER_SAMPLE))
    report = dict(experiment='sample-clock and 2,400-bit/s RxC phase on executed mask-04 receiver',
                  fixture=dict(seed=SEED, degrees=DEGREES,
                               oscillator_hz=OSCILLATOR_HZ,
                               assumed_microcycles_per_oscillator_period=1,
                               microcycles_per_sample=MICROCYCLES_PER_SAMPLE,
                               samples_per_symbol=SAMPLES_PER_SYMBOL,
                               sample_clock_phase='relative to first 3F8->3F9 latch edge'),
                  trace_digest=result['trace_digest'],
                  first_3f8_cycle=f8_cycles[0], first_latch_edge=first_edge,
                  startup_edges=startup_edges, receive_edges=receive_edges,
                  sample_clock_phases=phases, clean_phases=clean_phases,
                  selected_row3=selected_row3,
                  rxc=rxc,
                  limitations=['The 14.4 MHz oscillator-to-microinstruction route, 9.6 kHz divider, counter reset/phase, RxC driver and latch nets are untraced.',
                               'The 74LS161/74LS169 packages have counter capacity but no pin-level clock or output route is established.',
                               'The ADC sample hold schedule is a fixture assumption, not a measured sample clock.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in [Path(__file__),
                                              HERE / 'receiver_mask04_3f8_gate_timing.py',
                                              HERE / 'receiver_mask04_protocol_preamble.py',
                                              HERE / 'receiver_mask04_carrier_phase_screen.py',
                                              HERE / 'reference_modem.py',
                                              HERE.parent / 'assumed/execute.py',
                                              MAPPINGS['q3'],
                                              *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    print('clean phases', report['clean_phases'], 'RxC', report['rxc'])
