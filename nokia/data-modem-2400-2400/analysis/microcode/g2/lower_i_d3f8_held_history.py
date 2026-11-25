"""Test 9600 Hz held-byte history in the selected D3F8 ROM loop."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from lower_i_d3f8_input import run_trace
from lower_i_prom_data_route import mapping_for
from photo_controller_path import fixture

INPUT_PC = 0x3F8
OUTPUT_PCS = (0x3F8, 0x3F9, 0x3FA)
SAMPLE_VISITS = (188, 187, 188, 187)
FIRST_SAMPLE_VISITS = SAMPLE_VISITS[0]
CYCLES = 6000
EXPECTED_VISITS = 745
CODES = tuple(range(1, 16, 2))


def offered(first, later):
    return [first] * FIRST_SAMPLE_VISITS + [later] * (EXPECTED_VISITS - FIRST_SAMPLE_VISITS)


def events_after(trace, cycle):
    rom = []
    output = []
    for row in trace:
        if row['cycle'] < cycle:
            continue
        event = row['external_read']
        if event.get('selected_by_alu') and 'address' in event:
            rom.append((row['cycle'], row['pc'], event['address']))
        if row['pc'] in OUTPUT_PCS:
            output.append((row['cycle'], row['pc'], row['alu']['y']))
    return rom, output


def compare(reference, trial):
    if reference['site_visits'] != EXPECTED_VISITS or trial['site_visits'] != EXPECTED_VISITS:
        return dict(status='early exit', site_visits=trial['site_visits'],
                    final_pc=f"{trial['result']['final_state']['pc']:03X}")
    ref_pcs = [row['pc'] for row in reference['trace']]
    trial_pcs = [row['pc'] for row in trial['trace']]
    if ref_pcs != trial_pcs:
        return dict(status='different PC path', site_visits=trial['site_visits'],
                    final_pc=f"{trial['result']['final_state']['pc']:03X}")
    ref_sites = [row for row in reference['trace'] if row['pc'] == INPUT_PC]
    trial_sites = [row for row in trial['trace'] if row['pc'] == INPUT_PC]
    start = ref_sites[FIRST_SAMPLE_VISITS]['cycle']
    if trial_sites[FIRST_SAMPLE_VISITS]['cycle'] != start:
        raise ValueError('shared-input start cycle changed')
    if (not all(row['external_read']['selected_by_alu'] for row in ref_sites + trial_sites) or
            [row['external_read']['value'] for row in trial_sites][FIRST_SAMPLE_VISITS:] !=
            [row['external_read']['value'] for row in ref_sites][FIRST_SAMPLE_VISITS:]):
        raise ValueError('shared D3F8 input not selected/equal')
    difference_visits = [index for index, (left, right) in enumerate(zip(
        reference['boundaries'], trial['boundaries']))
                         if index >= FIRST_SAMPLE_VISITS and left != right]
    ref_rom, ref_output = events_after(reference['trace'], start)
    trial_rom, trial_output = events_after(trial['trace'], start)
    if len(ref_rom) != len(trial_rom) or len(ref_output) != len(trial_output):
        raise ValueError('shared-path event counts changed')
    return dict(status='same PC path and shared input',
                site_visits=trial['site_visits'],
                shared_input_start_cycle=start,
                differing_state_visit_count=len(difference_visits),
                first_differing_state_visits=difference_visits[:8],
                last_differing_state_visit=(difference_visits[-1]
                                            if difference_visits else None),
                differing_state_visits_from_visit_375=sum(
                    visit >= FIRST_SAMPLE_VISITS + SAMPLE_VISITS[1]
                    for visit in difference_visits),
                differing_state_visits_from_visit_563=sum(
                    visit >= sum(SAMPLE_VISITS[:3]) for visit in difference_visits),
                selected_rom_reads_after_shared=len(ref_rom),
                different_rom_address_events=sum(a != b for a, b in
                                                 zip(ref_rom, trial_rom)),
                candidate_output_events_after_shared=len(ref_output),
                different_candidate_output_events=sum(a != b for a, b in
                                                      zip(ref_output, trial_output)),
                final_state_differs=(reference['result']['final_state'] !=
                                     trial['result']['final_state']),
                trace_digest=trial['result']['trace_digest'])


def run(out=HERE / 'results/lower-i-d3f8-held-history.json'):
    _, base = fixture()
    mapping = mapping_for('!10.6', '11.2')
    cases = []
    for later in CODES:
        reference = run_trace(mapping, base, INPUT_PC, offered(later, later), CYCLES)
        for first in CODES:
            trial = (reference if first == later else
                     run_trace(mapping, base, INPUT_PC, offered(first, later), CYCLES))
            outcome = compare(reference, trial)
            cases.append(dict(first_byte=f'{first:02X}',
                              later_byte=f'{later:02X}', **outcome))
    long = [row for row in cases if row['status'] == 'same PC path and shared input']
    retained = [row for row in long if row['final_state_differs']]
    witness = next(row for row in cases if row['first_byte'] == '01' and
                   row['later_byte'] == '03')
    if (len(cases) != 64 or witness['status'] != 'same PC path and shared input' or
            witness['differing_state_visit_count'] != 557 or
            witness['differing_state_visits_from_visit_563'] != 182 or
            witness['last_differing_state_visit'] != 744 or
            not witness['final_state_differs'] or
            not witness['different_rom_address_events'] or
            not witness['different_candidate_output_events']):
        raise ValueError('held D3F8 history witness changed')
    paths = [Path(__file__), HERE / 'lower_i_d3f8_input.py',
             HERE / 'lower_i_prom_data_route.py',
             HERE / 'lower_i_input_pipeline.py',
             HERE / 'independent_slice_addresses.py',
             HERE / 'independent_slice_fields.py',
             HERE / 'split_slice_probe.py', HERE / 'photo_controller_path.py',
             HERE.parent / 'assumed/execute.py', HERE.parent / 'model.py',
             HERE.parents[2] / 'am27s31dc-prom/nokia-modem-am27s31dc.bin']
    report = dict(status='held D3F8 candidate byte leaves long-lived modeled state, ROM-address and ALU-output history under a labelled PROM-data mapping',
                  fixture=dict(mapping='I7/A0=!10.6, I0/A1=11.2, lower I6=11.0',
                               initial_q=5, initial_ram=[0] * 16,
                               candidate_input='D3F8 low nibble, D0 held high',
                               tested_first_and_later_bytes=[f'{code:02X}' for code in CODES],
                               input_hold_visits_per_9600hz_sample=list(SAMPLE_VISITS),
                               assumed_oscillator_hz=14400000,
                               assumed_microinstructions_per_D3F8_visit=8,
                               cycles_per_run=CYCLES,
                               common_later_input_starts_at_visit=FIRST_SAMPLE_VISITS,
                               state_compared='RAM/Q/ALU/next PC/stack at each selected D3F8 visit'),
                  summary=dict(transitions=64,
                               same_pc_long_path_transitions=len(long),
                               retained_final_state_transitions=len(retained),
                               selected_witness=dict(first='01', later='03',
                                                     **witness)),
                  cases=cases,
                  limitations=['D3F8 as an ADC-derived bus, its D0-high bias, the PROM-to-Am2901 field route and sample clock are untraced hypotheses.',
                               'The odd low-nibble bytes are diagnostic code classes, not a continuous encoded analog waveform.',
                               'A selected ROM/ALU history is not a recovered bit, a proven receiver loop or an ADC-to-USART path.',
                               'The candidate output events are internal ALU Y values, not a measured line or physical DAC stream; C3 remains open.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path,
                        default=HERE / 'results/lower-i-d3f8-held-history.json')
    args = parser.parse_args()
    report = run(args.out)
    print(report['summary']['same_pc_long_path_transitions'],
          report['summary']['retained_final_state_transitions'],
          report['summary']['selected_witness']['different_rom_address_events'])
