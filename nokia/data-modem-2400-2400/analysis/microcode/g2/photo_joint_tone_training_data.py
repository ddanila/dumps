"""Test one conditional A1 tone → A2 silence → A3/A4 data PROM path."""

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from controller_segment2_pattern import standard_bits
from main_loop_timer1_segment2 import (CORE, ROM as CONTROLLER_ROM, compile_probe,
                                      generated_source)
from photo_127_liveness import ROM
from photo_a1_dynamic_mode_replay import tone_summary
from photo_cd4094_order import shift_four_bytes
from photo_controller_path import fixture
from photo_dac_bus_permutations import (SELECTED, mapped_codes,
                                        matched_filter_basis, score)
from photo_frame_toggle_edge_pulse import inspect
from photo_i0_hold_screen import hold_candidate
from photo_main_dibit_pulse import BASE, VISITS_PER_SAMPLE, VISITS_PER_SYMBOL, scenario_inputs
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

TXREADY = HERE / 'results/main-loop-usart-txready.json'
BUSES = HERE / 'results/photo-dac-bus-permutations.json'
TONE_SYMBOLS = 32
SILENCE_SYMBOLS = 8
SEGMENT_SYMBOLS = 32
TOTAL_SYMBOLS = TONE_SYMBOLS + SILENCE_SYMBOLS + 2 * SEGMENT_SYMBOLS
TONE_STEP = 0x88
DATA_STEP = BASE


def frame_decision(frame):
    """Labelled logical-chip gate; no physical wire is claimed."""
    chips = shift_four_bytes(frame)
    chip0 = chips[0]['q8_to_d0']
    chip1 = chips[1]['q8_to_d0']
    capture = bool(chip1 & 1)
    tone = capture and bool(chip0 & 0x40) and not bool(chip1 & 0x20)
    return dict(capture=capture, tone=tone,
                d127=TONE_STEP if tone else DATA_STEP)


def controller_frames():
    source, _ = generated_source()
    result = {}
    with tempfile.TemporaryDirectory() as temporary:
        exe = compile_probe(source, Path(temporary), True)
        for selector in (0x40, 0x60):
            execution = json.loads(subprocess.run(
                [str(exe), str(CONTROLLER_ROM), str(selector), '10000', '1'],
                capture_output=True, text=True, check=True).stdout)
            if execution['errors']:
                raise ValueError(('controller replay errors', selector))
            states = {}
            for state in (0xA1, 0xA2, 0xA3, 0xA4):
                rows = [row for row in execution['iterations'] if row['state'] == state]
                counts = Counter(' '.join(f'{value:02X}' for value in row['tx'])
                                 for row in rows)
                decisions = {}
                for frame, count in counts.items():
                    if not frame:
                        continue  # No latch event; the previous 32-bit word remains held.
                    decision = frame_decision(bytes.fromhex(frame))
                    decisions[frame] = dict(count=count, **decision)
                    if state == 0xA2 and decision['capture']:
                        raise ValueError(('A2 capture unexpectedly enabled', frame))
                    if state in (0xA3, 0xA4) and decision['tone']:
                        raise ValueError(('A3/A4 tone unexpectedly selected', frame))
                if not rows or not decisions:
                    raise ValueError(('controller state/frame missing', selector, state))
                states[f'{state:02X}'] = dict(iterations=len(rows),
                                             frames=dict(counts), decisions=decisions)
            if not any(value['tone'] for value in states['A1']['decisions'].values()):
                raise ValueError(('late A1 tone frame absent', selector))
            if {frame: row['tone'] for frame, row in states['A1']['decisions'].items()} != {
                    '80 02 A1 7A': False, '80 02 81 7A': True,
                    '80 02 C1 7A': True}:
                raise ValueError(('A1 tone transition changed', selector))
            if any(row['capture'] for row in states['A2']['decisions'].values()) or any(
                    row['tone'] for state in ('A3', 'A4')
                    for row in states[state]['decisions'].values()):
                raise ValueError(('A2/A3/A4 fixed decode changed', selector))
            result[f'{selector:02X}'] = states
    return result


def segment2_from_txd(case):
    serial = [int(byte, 16) for byte in case['first_nine_transmitted_bytes']]
    bits = [(byte >> bit) & 1 for byte in serial for bit in range(8)]
    expected = standard_bits('GPC' if case['selector'] == '40' else 'GPA')
    if bits[1:65] != expected:
        raise ValueError(('TxD standard window changed', case['selector']))
    return [(bits[index] << 1) | bits[index + 1]
            for index in range(1, 65, 2)]


def raw_codes(rom, inputs):
    phase = 3
    samples = []
    ends = []
    for index, step in enumerate(inputs[:TOTAL_SYMBOLS * VISITS_PER_SYMBOL]):
        phase = (phase + step) & 255
        if index % VISITS_PER_SAMPLE == 0:
            samples.append((phase - rom[256 + phase]) & 255)
        if (index + 1) % VISITS_PER_SYMBOL == 0:
            ends.append(phase)
    return samples, ends


def replay(selector, rom, segment2, buses, base):
    suffix = [3] * SEGMENT_SYMBOLS + segment2
    inputs = ([TONE_STEP] * (TONE_SYMBOLS * VISITS_PER_SYMBOL) +
              [DATA_STEP] * (SILENCE_SYMBOLS * VISITS_PER_SYMBOL) +
              scenario_inputs(suffix))
    if len(inputs) != TOTAL_SYMBOLS * VISITS_PER_SYMBOL + 1:
        raise ValueError('unexpected D127 sequence length')
    raw, ends = raw_codes(rom, inputs)
    if ends[TONE_SYMBOLS - 1] != 3 or ends[TONE_SYMBOLS + SILENCE_SYMBOLS - 1] != 3:
        raise ValueError(('tone/silence altered data-start phase', selector))
    scenario = hold_candidate(base)
    scenario['name'] += '; joined A1 tone, A2 silence, A3 FF, A4 TxD'
    scenario['initial']['q'] = 0
    scenario['io']['read']['pc_sequences'][str(0x127)] = inputs
    scenario['io']['read']['pc_sequences'][str(0x12c)] = [0xEA]
    scenario['io']['read']['address']['bank_by_pc'] = {str(0x129): 256,
                                                       str(0x12e): 256}
    cycles = (TOTAL_SYMBOLS * VISITS_PER_SYMBOL + 64) * 4
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapped(MAPPINGS['q3']), scenario, cycles,
                         mode='integrated', out=temporary, trace_limit=cycles)
        trace = inspect(Path(temporary) / 'trace.jsonl', rom, inputs, [0] * TOTAL_SYMBOLS)
    if (not result['clean'] or result['completed_cycles'] != cycles or
            result['address_counts'].get(0x129) != trace['pc129_visits'] or
            result['address_counts'].get(0x12e, 0)):
        raise ValueError(('uninterrupted PROM replay stopped', selector))
    if trace['symbol_end_phases'] != ends:
        raise ValueError(('PROM phase differs from reconstruction', selector))
    digest = hashlib.sha256(bytes(mapped_codes(raw, SELECTED))).hexdigest()
    if trace['sample_sha256'] != digest:
        raise ValueError(('PROM samples differ from reconstruction', selector))
    a3_start = TONE_SYMBOLS + SILENCE_SYMBOLS
    a3_offsets = [(ends[a3_start + index] -
                   (3 + (index + 1) * VISITS_PER_SYMBOL * DATA_STEP)) & 255
                  for index in range(SEGMENT_SYMBOLS)]
    if a3_offsets != [128, 0] * 16:
        raise ValueError(('A3 half-turns changed', selector))
    target = suffix
    basis = matched_filter_basis(raw[(TONE_SYMBOLS + SILENCE_SYMBOLS) * 8:])
    decisions = [score(basis, target, bus) for bus in buses]
    if set(decisions) != {(0, 62)}:
        raise ValueError(('A3/A4 data decisions changed', selector, decisions))
    tones = [tone_summary(mapped_codes(raw[:TONE_SYMBOLS * 8], bus))
             for bus in buses]
    if {row['peak_hz'] for row in tones} != {2100}:
        raise ValueError(('A1 candidate tone peak changed', selector, tones))
    return dict(selector=selector, dsc_microinstructions=cycles,
                pc129_visits=trace['pc129_visits'], trace_digest=result['trace_digest'],
                selected_bus_sample_sha256=digest,
                tone=dict(symbols=TONE_SYMBOLS, samples=TONE_SYMBOLS * 8,
                          selected_bus=tone_summary(mapped_codes(raw[:TONE_SYMBOLS * 8], SELECTED)),
                          candidate_bus_peak_hz=sorted({row['peak_hz'] for row in tones}),
                          candidate_bus_r2_2100_range=[min(row['r2_2100'] for row in tones),
                                                       max(row['r2_2100'] for row in tones)]),
                silence=dict(symbols=SILENCE_SYMBOLS, hypothetical_capture_enabled=False,
                             internal_codes=SILENCE_SYMBOLS * 8,
                             held_line_behavior='not modeled'),
                phase_after_tone=ends[TONE_SYMBOLS - 1],
                phase_after_silence=ends[TONE_SYMBOLS + SILENCE_SYMBOLS - 1],
                a3_carrier_relative_phase_offsets_first_four=a3_offsets[:4],
                segment2_dibits=segment2,
                a3_a4_errors_by_12_candidate_buses=[errors for errors, _ in decisions],
                a3_a4_decisions=62,
                samples_at_a3_a4_boundary=[f'{code:02X}' for code in
                                           trace['samples'][(TONE_SYMBOLS + SILENCE_SYMBOLS + SEGMENT_SYMBOLS) * 8 - 4:
                                                            (TONE_SYMBOLS + SILENCE_SYMBOLS + SEGMENT_SYMBOLS) * 8 + 4]])


def run(out=HERE / 'results/photo-joint-tone-training-data.json'):
    frames = controller_frames()
    txready = json.loads(TXREADY.read_text())
    buses = [row['input_bit_to_dac_code_bit'] for row in
             json.loads(BUSES.read_text())['zero_error_candidates']]
    if len(buses) != 12:
        raise ValueError('DAC bus candidates changed')
    rom = ROM.read_bytes()
    _, base = fixture()
    cases = []
    for selector in ('40', '60'):
        clock_cases = [case for case in txready['cases'] if case['selector'] == selector]
        if len(clock_cases) != 8 or len({tuple(case['first_nine_transmitted_bytes'])
                                        for case in clock_cases}) != 1:
            raise ValueError(('TxD clock phase coverage changed', selector))
        cases.append(replay(selector, rom, segment2_from_txd(clock_cases[0]), buses, base))
    paths = [Path(__file__), TXREADY, BUSES, ROM, CONTROLLER_ROM,
             HERE / 'main_loop_timer1_segment2.py', HERE / 'main_loop_probe.c',
             HERE / 'controller_segment2_pattern.py', HERE / 'photo_cd4094_order.py',
             HERE / 'photo_main_dibit_pulse.py', HERE / 'photo_dac_bus_permutations.py',
             HERE / 'photo_frame_toggle_edge_pulse.py',
             HERE / 'photo_a1_dynamic_mode_replay.py',
             HERE / 'photo_controller_path.py', HERE / 'photo_i0_hold_screen.py',
             HERE / 'photo_mapping_q_sweep.py', HERE / 'photo_mapping_stream_screen.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3'],
             *(CORE / name for name in ('core.c', 'opcodes.c', 'disasm.c', 'emu8051.h'))]
    report = dict(status='conditional fixed-frame decode carries a 2100 Hz A1 candidate, A2 capture-off interval, A3 half-turns and actual A4 segment-2 bits through one uninterrupted real-PROM phase path',
                  fixture=dict(controller='Timer1-paced unchanged 8031, RAM15 positive gate held; frame histograms counted by state',
                               frame_decode='logical CD4094 chip0=last frame byte, chip1=third; capture=chip1.bit0; tone=capture AND chip0.bit6 AND NOT chip1.bit5; D127=88 for tone, B0 otherwise',
                               a1='late A1 C1 frame held for 32 diagnostic symbols',
                               a2='capture disabled for 8 diagnostic symbols; internal D127 B0 phase path continues',
                               a3='32 symbols of 8251A FF fill paired as dibit 11',
                               a4='64 standard bits from TxRDY-paced 8251A TxD, beginning at shifted-data bit 1',
                               dsc='q3 real PROMs; PC129 upper ROM bank; four-visit dibit pulse; 375 PC129 visits per hypothetical 9600 Hz sample',
                               output='12 photo-B5-compatible DAC bus orders; matched-filter decoder is external reference'),
                  controller_frame_histograms=frames, cases=cases,
                  limitations=['The frame decode, D127 source, TxRDY-to-DSC bit-skip gate, 8251A CTS/TxC wiring, DAC bus, sample clock and line path are untraced candidate connections.',
                               'The A1 and A2 windows are diagnostic excerpts, not their natural controller durations; no complete analog handshake is replayed.',
                               'A2 capture-disable is inferred from a frame bit; held DAC value and analog silence are not established.',
                               'The 2100 Hz result is a candidate DAC-code peak with substantial distortion, not a measured answer-tone waveform.',
                               'The matched-filter decoder is independent reference code, not the DSC receiver; C2/C3/C4 remain open.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path,
                        default=HERE / 'results/photo-joint-tone-training-data.json')
    args = parser.parse_args()
    for case in run(args.out)['cases']:
        print(case['selector'], case['tone']['selected_bus']['peak_hz'],
              set(case['a3_a4_errors_by_12_candidate_buses']), case['pc129_visits'])
