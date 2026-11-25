"""Sample the joined real-PROM trace with a free-running 9600 Hz clock."""

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from photo_127_liveness import ROM
from photo_a1_dynamic_mode_replay import tone_summary
from photo_controller_path import fixture
from photo_dac_bus_permutations import (SELECTED, mapped_codes,
                                        matched_filter_basis, score)
from photo_frame_toggle_edge_pulse import inspect
from photo_i0_hold_screen import hold_candidate
from photo_joint_tone_training_data import (DATA_STEP, SEGMENT_SYMBOLS,
                                            SILENCE_SYMBOLS, TONE_STEP,
                                            TONE_SYMBOLS, TOTAL_SYMBOLS,
                                            segment2_from_txd)
from photo_main_dibit_pulse import VISITS_PER_SAMPLE, VISITS_PER_SYMBOL, scenario_inputs
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

JOINT = HERE / 'results/photo-joint-tone-training-data.json'
TXREADY = HERE / 'results/main-loop-usart-txready.json'
BUSES = HERE / 'results/photo-dac-bus-permutations.json'
START_CYCLE = 40
CYCLES_PER_SAMPLE = 4 * VISITS_PER_SAMPLE
SITES = (0x127, 0x128, 0x129, 0x12A)


def sampled_sites(path):
    streams = [[] for _ in SITES]
    first_pc127 = None
    with path.open() as source:
        for line in source:
            row = json.loads(line)
            if row['pc'] == SITES[0] and first_pc127 is None:
                first_pc127 = row['cycle']
            position = row['cycle'] - START_CYCLE
            if (position < 0 or position // CYCLES_PER_SAMPLE >= TOTAL_SYMBOLS * 8
                    or position % CYCLES_PER_SAMPLE >= 4):
                continue
            site = position % CYCLES_PER_SAMPLE
            if row['pc'] != SITES[site]:
                raise ValueError(('free-clock phase left four-word loop', row['cycle'], row['pc']))
            streams[site].append(row['alu']['y'])
    if first_pc127 != START_CYCLE or any(len(stream) != TOTAL_SYMBOLS * 8
                                          for stream in streams):
        raise ValueError(('sample count/start changed', first_pc127,
                          [len(stream) for stream in streams]))
    if streams[0] != streams[1]:
        raise ValueError('PC127 and PC128 Y samples unexpectedly differ')
    return streams


def replay(selector, segment2, joined, rom, buses, base):
    target = [3] * SEGMENT_SYMBOLS + segment2
    inputs = ([TONE_STEP] * (TONE_SYMBOLS * VISITS_PER_SYMBOL) +
              [DATA_STEP] * (SILENCE_SYMBOLS * VISITS_PER_SYMBOL) +
              scenario_inputs(target))
    scenario = hold_candidate(base)
    scenario['name'] += '; free-clock four ALU sites'
    scenario['initial']['q'] = 0
    scenario['io']['read']['pc_sequences'][str(0x127)] = inputs
    scenario['io']['read']['pc_sequences'][str(0x12c)] = [0xEA]
    scenario['io']['read']['address']['bank_by_pc'] = {str(0x129): 256,
                                                       str(0x12e): 256}
    cycles = (TOTAL_SYMBOLS * VISITS_PER_SYMBOL + 64) * 4
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapped(MAPPINGS['q3']), scenario, cycles,
                         mode='integrated', out=temporary, trace_limit=cycles)
        path = Path(temporary) / 'trace.jsonl'
        streams = sampled_sites(path)
        checked = inspect(path, rom, inputs, [0] * TOTAL_SYMBOLS)
    if not result['clean'] or result['completed_cycles'] != cycles or checked['pc129_visits'] != joined['pc129_visits']:
        raise ValueError(('PROM execution changed', selector))
    if hashlib.sha256(bytes(mapped_codes(streams[2], SELECTED))).hexdigest() != joined['selected_bus_sample_sha256']:
        raise ValueError(('PC129 free-clock samples differ from joined replay', selector))
    sites = []
    for pc, raw in zip(SITES, streams):
        tone = tone_summary(mapped_codes(raw[:TONE_SYMBOLS * 8], SELECTED))
        basis = matched_filter_basis(raw[(TONE_SYMBOLS + SILENCE_SYMBOLS) * 8:])
        decisions = [score(basis, target, bus) for bus in buses]
        if {count for _, count in decisions} != {62}:
            raise ValueError(('decision count changed', selector, pc))
        sites.append(dict(pc=f'{pc:03X}', samples=len(raw),
                          sample_sha256=hashlib.sha256(bytes(mapped_codes(raw, SELECTED))).hexdigest(),
                          first_16_codes=[f'{code:02X}' for code in mapped_codes(raw[:16], SELECTED)],
                          selected_bus_tone=tone,
                          data_errors_by_12_buses=[error for error, _ in decisions],
                          zero_error_buses=sum(error == 0 for error, _ in decisions)))
    return dict(selector=selector, dsc_microinstructions=cycles,
                pc129_visits=checked['pc129_visits'], trace_digest=result['trace_digest'],
                sites=sites)


def run(out=HERE / 'results/photo-joint-free-clock-sites.json'):
    joined = json.loads(JOINT.read_text())
    txready = json.loads(TXREADY.read_text())
    buses = [row['input_bit_to_dac_code_bit'] for row in
             json.loads(BUSES.read_text())['zero_error_candidates']]
    if len(buses) != 12 or len(joined['cases']) != 2:
        raise ValueError('joined fixture or DAC buses changed')
    _, base = fixture()
    rom = ROM.read_bytes()
    cases = []
    for original in joined['cases']:
        selector = original['selector']
        clock_case = next(case for case in txready['cases']
                          if case['selector'] == selector)
        cases.append(replay(selector, segment2_from_txd(clock_case), original,
                            rom, buses, base))
    paths = [Path(__file__), JOINT, TXREADY, BUSES, ROM,
             HERE / 'photo_joint_tone_training_data.py',
             HERE / 'photo_a1_dynamic_mode_replay.py',
             HERE / 'photo_dac_bus_permutations.py',
             HERE / 'photo_frame_toggle_edge_pulse.py',
             HERE / 'photo_controller_path.py', HERE / 'photo_i0_hold_screen.py',
             HERE / 'photo_main_dibit_pulse.py', HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3']]
    report = dict(status='free-running hypothetical 9600 Hz latch sampled at each of four ALU instruction phases in uninterrupted real-PROM traces',
                  fixture=dict(start_pc='127', first_cycle=START_CYCLE,
                               cycles_per_sample=CYCLES_PER_SAMPLE,
                               sample_hz_if_one_oscillator_period_per_microinstruction=9600,
                               latch='free-running clock, no PC129 qualifier; ALU Y wired to a candidate 74LS273 input bus',
                               output='12 photo-B5-compatible DAC bus orders; external matched-filter decoder'),
                  cases=cases,
                  limitations=['The free-running clock, its phase, ALU-Y-to-latch bus, DAC08 bus and physical line path are untraced hypotheses.',
                               'The 9600 Hz label assumes a 14.4 MHz microinstruction clock; no sequencer divider was measured.',
                               'A matched-filter result is external reference decoding, not recovered bits from DSC receiving microcode.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path,
                        default=HERE / 'results/photo-joint-free-clock-sites.json')
    args = parser.parse_args()
    for case in run(args.out)['cases']:
        print(case['selector'], [(site['pc'], site['selected_bus_tone']['peak_hz'],
                                  site['zero_error_buses']) for site in case['sites']])
