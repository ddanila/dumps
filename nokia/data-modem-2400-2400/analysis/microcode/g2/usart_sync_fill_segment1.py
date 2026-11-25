"""Audit the 8251A FF sync-fill candidate against executed A3/A4 controller events."""

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from controller_segment2_pattern import standard_bits
from main_loop_timer1_segment2 import (ROM as CONTROLLER_ROM, compile_probe, generated_source,
                                      state_groups)
from photo_127_liveness import ROM as DSC_ROM
from photo_controller_path import fixture
from photo_dac_bus_permutations import matched_filter_basis, raw_y_codes, score
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from photo_segment1_to_segment2_continuous import replay

LISTING = HERE.parents[1] / 'results/controller-linear.asm'
PROGRAM_REPORT = HERE.parents[1] / 'results/controller-program-study/report.json'
CONTINUOUS = HERE / 'results/photo-segment1-to-segment2-continuous.json'
TIMER_REPORT = HERE / 'results/main-loop-timer1-segment2.json'
FILL_BYTES = 8


def serial_bits(values):
    return [(value >> bit) & 1 for value in values for bit in range(8)]


def run(out=HERE / 'results/usart-sync-fill-segment1.json'):
    listing = LISTING.read_text()
    for line in ('1e1e  MOV   R0, #05h', '1e20  MOV   R3, #CCh',
                 '1e22  MOV   R2, #15h', '1e24  LCALL #1D05h'):
        if listing.count(line) != 1:
            raise ValueError(('USART startup instruction changed', line))
    programming = json.loads(PROGRAM_REPORT.read_text())
    if (not programming['all_checks_pass'] or
            0x15 not in programming['configuration']['commands'] or
            5 not in programming['configuration']['addresses']):
        raise ValueError('8251 programming-helper coverage changed')
    mode, sync, command = 0xCC, 0xFF, 0x15
    if (mode & 0x03 or (mode >> 2) & 3 != 3 or
            mode & 0x30 or not mode & 0x40 or not mode & 0x80 or
            not command & 1 or command & 8):
        raise ValueError('USART mode/command no longer permits FF fill')

    timer = json.loads(TIMER_REPORT.read_text())
    continuous = json.loads(CONTINUOUS.read_text())
    buses = [row['input_bit_to_dac_code_bit'] for row in json.loads(
        (HERE / 'results/photo-dac-bus-permutations.json').read_text())['zero_error_candidates']]
    if len(buses) != 12:
        raise ValueError('DAC bus candidate coverage changed')
    source, _ = generated_source()
    cases = []
    with tempfile.TemporaryDirectory() as temporary:
        exe = compile_probe(source, Path(temporary), True)
        for selector, polynomial in ((0x40, 'GPC'), (0x60, 'GPA')):
            execution = json.loads(subprocess.run(
                [str(exe), str(CONTROLLER_ROM), str(selector), '10000', '1'],
                capture_output=True, text=True, check=True).stdout)
            rows = execution['iterations']
            groups = state_groups(rows)
            if [group['state'] for group in groups] != ['A1', 'A2', 'A3', 'A4', 'A5']:
                raise ValueError(('controller sequence changed', selector))
            if any(5 in row['write_addresses'] for row in rows):
                raise ValueError(('USART reprogrammed in replay', selector))
            a3 = rows[groups[2]['first_iteration']:groups[3]['first_iteration']]
            a4 = rows[groups[3]['first_iteration']:groups[4]['first_iteration']]
            a5 = rows[groups[4]['first_iteration']]
            if (any(1 in row['write_addresses'] for row in a3) or
                    any(row['write_addresses'] != [1] for row in a4) or
                    a5['write_addresses'] != [1]):
                raise ValueError(('controller port-01 stream changed', selector))
            data = [row['writes'][0] for row in a4] + a5['writes']
            recorded = next(case for case in timer['cases']
                            if case['selector'] == f'{selector:02X}')
            if data != [int(value, 16) for value in
                        recorded['a4_port01_bytes'] + [recorded['first_a5_port01_byte']]]:
                raise ValueError(('A4/A5 controller bytes changed', selector))
            bits = serial_bits([sync] * FILL_BYTES + data)
            segment1 = bits[:64]
            bridge = bits[64]
            segment2 = bits[65:129]
            if segment1 != [1] * 64 or segment2 != standard_bits(polynomial):
                raise ValueError(('sync-fill/segment-2 windows changed', selector))
            prior_replay = next(case for case in continuous['cases']
                                if case['selector'] == f'{selector:02X}' and
                                case['a3_idle_rule'] == 'repeated_11_idle')
            expected_dibits = [(segment2[index] << 1) | segment2[index + 1]
                               for index in range(0, 64, 2)]
            if prior_replay['a3_symbols'] != [3] * 32 or prior_replay['actual_a4_segment2_symbols'] != expected_dibits:
                raise ValueError(('DSC source windows changed', selector))
            target = [3] * 32 + expected_dibits
            pairings = []
            for offset in (0, 1):
                window = bits[offset:offset + 128]
                dibits = [(window[index] << 1) | window[index + 1]
                          for index in range(0, 128, 2)]
                basis = matched_filter_basis(raw_y_codes(DSC_ROM.read_bytes(), dibits))
                scores = [score(basis, target, bus) for bus in buses]
                if any(decisions != 62 for _, decisions in scores):
                    raise ValueError(('raw bit pairing decision coverage changed', selector))
                pairings.append(dict(first_bit_offset=offset,
                                     input_dibit_mismatches=sum(a != b for a, b in zip(dibits, target)),
                                     errors_by_12_candidate_buses=[errors for errors, _ in scores]))
            if selector == 0x60:
                _, base = fixture()
                execution_check, _ = replay(
                    [(bits[index] << 1) | bits[index + 1]
                     for index in range(1, 129, 2)],
                    'raw 8251 FF fill plus GPA bridge', DSC_ROM.read_bytes(), base,
                    mapped(MAPPINGS['q3']))
                pairings[1]['real_prom_trace_digest'] = execution_check['trace_digest']
                pairings[1]['real_prom_pc129_visits'] = execution_check['pc129_visits']
                pairings[1]['real_prom_microinstructions'] = execution_check['microinstructions']
                pairings[1]['real_prom_selected_bus_sample_sha256'] = execution_check['selected_bus_sample_sha256']
            else:
                pairings[1]['real_prom_trace_digest'] = prior_replay['trace_digest']
                pairings[1]['real_prom_pc129_visits'] = prior_replay['pc129_visits']
                pairings[1]['real_prom_microinstructions'] = prior_replay['microinstructions']
                pairings[1]['real_prom_selected_bus_sample_sha256'] = prior_replay['selected_bus_sample_sha256']
            cases.append(dict(selector=f'{selector:02X}', polynomial=polynomial,
                              executed_a3_port01_writes=0,
                              executed_port05_reprogramming_writes=0,
                              fill_characters=FILL_BYTES,
                              fill_symbol_count=32,
                              segment1_ones=64,
                              first_a4_bit_bridge=bridge,
                              standard_segment2_bits=64,
                              standard_segment2_starts_at_stream_bit=65,
                              prior_dsc_replay_omits_bridge_bit=True,
                              raw_pairing_projections=pairings,
                              a4_bytes=[f'{value:02X}' for value in data[:-1]],
                              first_a5_byte=f'{data[-1]:02X}'))
    paths = [Path(__file__), LISTING, PROGRAM_REPORT, CONTINUOUS, TIMER_REPORT,
             CONTROLLER_ROM, DSC_ROM, HERE / 'main_loop_timer1_segment2.py',
             HERE / 'main_loop_probe.c', HERE / 'controller_segment2_pattern.py',
             HERE / 'photo_segment1_to_segment2_continuous.py',
             HERE / 'photo_dac_bus_permutations.py',
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py', MAPPINGS['q3']]
    report = dict(
        status='8251A automatic FF sync fill is a concrete candidate source for A3 repeated-11 dibits; the first A4 bit remains a boundary bridge absent from prior DSC replay',
        datasheet='Intel 8251A datasheet, synchronous-mode transmission and mode/command formats; CTS and Tx clock are assumed active',
        startup_configuration=dict(control_address='05', mode='CC',
                                   sync_character='FF', command='15',
                                   sync_mode=True, eight_data_bits=True,
                                   one_sync_character=True, transmit_enabled=True),
        cases=cases,
        limitations=['The main-loop fixture starts after startup; it verifies no later port-05 writes but does not itself execute the startup USART configuration.',
                     '8251A CTS level, Tx clock, actual A3 fill duration and physical TxD-to-DSC route are not traced.',
                     'The prior 64-symbol DSC replay concatenates the FF-fill and standard segment-2 windows while omitting the first A4 bit; it is a conditional input test, not an exact raw TxD replay.',
                     'Raw bit pairing is a model projection at a fixed offset. The offset-1 GPA case is executed through the real PROM; the offset-0 cases are reconstructed from a previously validated q3 ROM/Y model.'],
        source_sha256={str(path.relative_to(HERE.parents[2])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path,
                        default=HERE / 'results/usart-sync-fill-segment1.json')
    args = parser.parse_args()
    report = run(args.out)
    for case in report['cases']:
        print(case['selector'], case['segment1_ones'],
              case['first_a4_bit_bridge'], case['standard_segment2_bits'])
