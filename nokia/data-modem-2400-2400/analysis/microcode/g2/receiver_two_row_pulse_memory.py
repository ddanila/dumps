"""Measure one ADC-byte pulse through the interleaved 3EF/3F7 table rows."""

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
from joint_upper_source_screen import SELECTED_MASK, candidate
from lower_i_d3f8_full_adc import scenario_for_full_byte
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS

VISITS = 3000
CYCLES = 16 * VISITS + 47
CONTROL_BYTE = 0x09
PULSE_BYTE = 0x59
PULSES = ((10, 1, 0x59), (11, 1, 0x59), (12, 1, 0x59),
          (13, 1, 0x59), (14, 1, 0x59),
          (100, 1, 0x59), (101, 1, 0x59), (102, 1, 0x59),
          (103, 1, 0x59), (104, 1, 0x59),
          (188, 94, 0x59), (282, 93, 0x59),
          (188, 94, 0x19), (282, 93, 0xA9),
          (100, 1, 0x19), (100, 1, 0xA9), (100, 1, 0xF9)) + tuple(
              (100, 1, (high << 4) | 0x09)
              for high in range(1, 16) if high not in (1, 5, 10, 15)) + tuple(
                  (visit, 1, 0x19) for visit in range(10, 15))


def capture(mapping, base, pulse_visit=None, duration=1, pulse_byte=PULSE_BYTE):
    values = [CONTROL_BYTE] * VISITS
    if pulse_visit is not None:
        values[pulse_visit:pulse_visit + duration] = [pulse_byte] * duration
    scenario = scenario_for_full_byte(base, values, 'complementary')
    scenario['dispatch']['mode'] = 'sequence'
    scenario['dispatch']['sequence'] = [0, 2]
    ram = scenario['initial']['ram'][:]
    pc_digest = hashlib.sha256()
    rows, addresses, offered = [], [], []
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, CYCLES,
                         mode='integrated', out=temporary, trace_limit=CYCLES)
        for line in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(line)
            pc = row['pc']
            pc_digest.update(bytes((pc & 255, pc >> 8)))
            for address, value in row['registers'].items():
                ram[int(address)] = value
            if pc == 0x3F8:
                event = row['external_read']
                if not event.get('selected_by_alu'):
                    raise ValueError('ADC byte not selected by ALU')
                offered.append(event['value'])
            elif pc == 0x3F9:
                addresses.append(row['external_read']['address'])
            elif pc == 0x3FA:
                rows.append((bytes(ram), row['q'], row['alu']['y']))
    if (not result['clean'] or result['completed_cycles'] != CYCLES or
            len(rows) != VISITS or len(addresses) != VISITS or
            offered != values or
            result['address_counts'].get(0x3EF, 0) != VISITS + 1):
        raise ValueError(('two-row ADC pulse run incomplete', pulse_visit))
    return dict(rows=rows, addresses=addresses,
                pc_digest=pc_digest.hexdigest(),
                trace_digest=result['trace_digest'])


def compare(control, trial, visit, duration, pulse_byte):
    if control['pc_digest'] != trial['pc_digest']:
        raise ValueError(('pulse changed PC path', visit))
    changed_state = [i for i, pair in enumerate(zip(control['rows'], trial['rows']))
                     if pair[0] != pair[1]]
    changed_rom = [i for i, pair in enumerate(zip(control['addresses'],
                                                   trial['addresses']))
                   if pair[0] != pair[1]]
    if not changed_state or changed_state[0] != visit:
        raise ValueError(('pulse did not change immediate state', visit))
    register_counts = {f'R{register}': count
                       for register in range(16)
                       if (count := sum(a[0][register] != b[0][register]
                                        for a, b in zip(control['rows'],
                                                        trial['rows'])))}
    deltas = [(b - a) & 255 for a, b in zip(
        control['addresses'][visit + 1:], trial['addresses'][visit + 1:])]
    last_control, last_trial = control['rows'][-1], trial['rows'][-1]
    last_register_deltas = {f'R{register}': (last_trial[0][register] -
                                           last_control[0][register]) & 255
                            for register in range(16)
                            if last_trial[0][register] != last_control[0][register]}
    return dict(pulse_visit=visit,
                pulse_duration_visits=duration,
                pulse_byte=f'{pulse_byte:02X}',
                state_differences=len(changed_state),
                later_state_differences=sum(i > visit for i in changed_state),
                state_differences_after_return=sum(i >= visit + duration
                                                   for i in changed_state),
                last_state_difference=changed_state[-1],
                state_persists_to_end=changed_state[-1] == VISITS - 1,
                rom_address_differences=len(changed_rom),
                rom_differences_after_return=sum(i >= visit + duration
                                                 for i in changed_rom),
                first_rom_address_difference=(changed_rom[0] if changed_rom else None),
                later_rom_address_differences=sum(i > visit for i in changed_rom),
                last_rom_address_difference=(changed_rom[-1] if changed_rom else None),
                rom_address_persists_to_end=(changed_rom[-1] == VISITS - 1
                                             if changed_rom else False),
                register_difference_visits=register_counts,
                final_register_deltas=last_register_deltas,
                final_q_delta=(last_trial[1] - last_control[1]) & 255,
                final_rom_address_delta=(trial['addresses'][-1] -
                                         control['addresses'][-1]) & 255,
                q_difference_visits=sum(a[1] != b[1] for a, b in
                                        zip(control['rows'], trial['rows'])),
                y3fa_difference_visits=sum(a[2] != b[2] for a, b in
                                            zip(control['rows'], trial['rows'])),
                first_12_later_rom_address_deltas=deltas[:12],
                last_500_rom_address_delta_histogram=dict(sorted(
                    Counter(deltas[-500:]).items())),
                trace_digest=trial['trace_digest'])


def run(out=HERE / 'results/receiver-two-row-pulse-memory.json'):
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), SELECTED_MASK)
    _, base = fixture()
    control = capture(mapping, base)
    cases = [compare(control, capture(mapping, base, visit, duration, pulse_byte),
                     visit, duration, pulse_byte)
             for visit, duration, pulse_byte in PULSES]
    paths = [Path(__file__), HERE / 'receiver_dispatch_source_screen.py',
             HERE / 'joint_upper_source_screen.py',
             HERE / 'lower_i_d3f8_full_adc.py',
             HERE / 'lower_i_d3f8_upper_d_route.py',
             HERE / 'photo_controller_path.py',
             HERE / 'split_slice_probe.py',
             HERE.parent / 'assumed/execute.py', HERE.parent / 'model.py',
             MAPPINGS['q3'],
             HERE / 'results/joint-upper-source-mask08-mapping.json',
             HERE.parents[2] / 'am27s31dc-prom/nokia-modem-am27s31dc.bin',
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(
        status='one ADC-byte high-nibble pulse measured across both interleaved receive table rows',
        fixture=dict(mapping='joint upper-source mask 08',
                     dispatch='scenario [0,2] at 3EC',
                     initial_q=5, initial_ram=[0] * 16,
                     baseline_adc_byte=f'{CONTROL_BYTE:02X}',
                     pulse_windows=[[visit, duration, f'{byte:02X}']
                                    for visit, duration, byte in PULSES],
                     total_adc_visits=VISITS,
                     subsequent_input='identical baseline byte',
                     input_timing='one diagnostic byte per D3F8 visit'),
        control_trace_digest=control['trace_digest'],
        cases=cases,
        limitations=[
            'A persistent state difference is not a decoded bit or proven receive/echo function.',
            'One-visit pulses are diagnostic; the ADC sample clock and bus remain assumed.',
            'The 0/2 dispatch source, upper instruction wiring and USART output route are untraced.'],
        source_sha256={str(path.relative_to(HERE.parents[2])):
                       hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    for case in report['cases']:
        print(case['pulse_visit'], case['pulse_duration_visits'],
              case['pulse_byte'],
              case['state_differences_after_return'],
              case['rom_differences_after_return'],
              case['state_persists_to_end'])
