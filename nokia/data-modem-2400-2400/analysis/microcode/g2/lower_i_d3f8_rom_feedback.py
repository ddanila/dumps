"""Trace the 3F9 table byte into Q and later ROM addresses."""

import copy
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from lower_i_d3f8_input import run_trace
from lower_i_d3f8_sign_adc import condition_scenario
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture

INPUT_PC = 0x3F8
ROM_PC = 0x3F9
VISITS = 512
CYCLES = 8 * VISITS + 47
PULSE_VISIT = 20
ADC_BYTE = 0x59
PROM = HERE.parents[2] / 'am27s31dc-prom/nokia-modem-am27s31dc.bin'


def check_real_table_transfer(run, prom):
    ram = [0] * 16
    count = 0
    for row in run['trace']:
        if row['pc'] == ROM_PC:
            assert row['instruction_i'] == 0x15
            assert row['instruction_i_high'] == 0xED
            read = row['external_read']
            assert read['selected_by_alu'] and read['value'] == prom[read['address']]
            d = read['value']
            a_low = ram[row['register_address_a']] & 15
            a_high = ram[row['register_address_a_high']] >> 4
            low = ((d & 15) + (a_low ^ 15) + row['carry_in']) & 15
            high = ((d >> 4) ^ 15) & a_high
            assert row['alu']['y'] == low | (high << 4)
            assert row['q'] & 15 == low
            b_high = row['register_address_b_high']
            assert int(row['registers'].get(str(b_high), ram[b_high])) >> 4 == high
            count += 1
        for address, value in row['registers'].items():
            ram[int(address)] = value
    assert count == VISITS == run['site_visits']


def replay(mapping, base, adc, table_values):
    scenario = copy.deepcopy(base)
    scenario['io']['read']['address']['pcs'].remove(ROM_PC)
    scenario['io']['read']['pc_sequences'][str(ROM_PC)] = table_values
    scenario['io']['read']['evidence'] += (
        '; diagnostic 3F9 ROM-byte replay; source and selected visit explicit')
    return run_trace(mapping, scenario, INPUT_PC, adc, CYCLES)


def compare(control, trial):
    a, b = control['trace'], trial['trace']
    first_state = next((i for i, (x, y) in enumerate(zip(a, b))
                        if (x['q'], x['registers'], x['alu']) !=
                        (y['q'], y['registers'], y['alu'])), None)
    return dict(same_pc_path=all(x['pc'] == y['pc'] for x, y in zip(a, b)),
                first_state_difference_cycle=first_state,
                different_state_boundaries=sum(x != y for x, y in
                                               zip(control['boundaries'], trial['boundaries'])),
                different_selected_rom_addresses=sum(x != y for x, y in
                                                     zip(control['reads'], trial['reads'])),
                different_3f7_rom_addresses=sum(
                    x['external_read']['address'] != y['external_read']['address']
                    for x, y in zip(a, b) if x['pc'] == y['pc'] == 0x3F7),
                d3f8_visits=trial['site_visits'],
                trace_digest=trial['result']['trace_digest'])


def run(out=HERE / 'results/lower-i-d3f8-rom-feedback.json'):
    _, base = fixture()
    base = condition_scenario(base, 'previous')
    mapping = mapping_with_upper_source(0, '17.6')
    adc = [ADC_BYTE] * VISITS
    prom = PROM.read_bytes()
    real = run_trace(mapping, base, INPUT_PC, adc, CYCLES)
    check_real_table_transfer(real, prom)
    table_values = [row['external_read']['value'] for row in real['trace']
                    if row['pc'] == ROM_PC]
    assert len(table_values) == VISITS
    control = replay(mapping, base, adc, table_values)
    assert control['result']['trace_digest'] == real['result']['trace_digest']
    trials = {}
    for label, mask in (('rom_d0', 1), ('rom_d4', 16)):
        changed = table_values[:]
        changed[PULSE_VISIT] ^= mask
        trial = replay(mapping, base, adc, changed)
        trials[label] = dict(original_byte=table_values[PULSE_VISIT],
                             replayed_byte=changed[PULSE_VISIT],
                             **compare(control, trial))
    assert (trials['rom_d0']['same_pc_path'] and
            trials['rom_d0']['first_state_difference_cycle'] == 47 + 8 * PULSE_VISIT + 1 and
            trials['rom_d0']['different_state_boundaries'] > 0 and
            trials['rom_d0']['different_3f7_rom_addresses'] > 0 and
            trials['rom_d4']['different_state_boundaries'] == 0)
    paths = [Path(__file__), HERE / 'lower_i_d3f8_input.py',
             HERE / 'lower_i_d3f8_sign_adc.py',
             HERE / 'lower_i_d3f8_upper_d_route.py',
             HERE / 'lower_i_prom_data_route.py',
             HERE / 'photo_controller_path.py', HERE / 'split_slice_probe.py',
             HERE.parent / 'assumed/execute.py', HERE.parent / 'model.py', PROM]
    report = dict(status='conditional 3F9 table-byte transfer and feedback',
                  fixture=dict(adc_byte=ADC_BYTE, d3f8_visits=VISITS,
                               cycles=CYCLES, altered_3f9_visit=PULSE_VISIT,
                               condition_select_0='inverted previous sign',
                               upper_instruction='FD via assumed U17 bit 6 to U8 I0'),
                  verified_rule=('3F9 low 15: Q_low=(PROM_low+~pre-RAM[A_low]_low+carry_in)&15; '
                                 'high ED: RAM[B_high]_high=(~PROM_high)&pre-RAM[A_high]_high'),
                  real_rom_trace_digest=real['result']['trace_digest'],
                  replay_matches_real_trace=True,
                  trials=trials,
                  limitation='ROM replay is a diagnostic intervention under untraced ADC, instruction, condition and output routes; no receive bit is identified.',
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    print({name: (trial['different_state_boundaries'],
                  trial['different_3f7_rom_addresses'])
           for name, trial in report['trials'].items()})
