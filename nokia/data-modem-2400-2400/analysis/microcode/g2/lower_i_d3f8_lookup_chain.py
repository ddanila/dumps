"""Verify the conditional D3F8 upper-ALU to 3F9 ROM lookup chain."""

import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from lower_i_d3f8_full_adc import codes, hold
from lower_i_d3f8_input import run_trace
from lower_i_d3f8_sign_adc import condition_scenario
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from lower_i_prom_data_route import mapping_for
from photo_controller_path import fixture

SITE = 0x3F8
NEXT = 0x3F9
VISITS = 512
CYCLES = 8 * VISITS + 47
PROM = HERE.parents[2] / 'am27s31dc-prom/nokia-modem-am27s31dc.bin'


def inspect(run, expected, instruction, prom):
    trace = run['trace']
    ram = [0] * 16
    events = []
    for index, row in enumerate(trace):
        if row['pc'] == SITE:
            read = row['external_read']
            assert read['selected_by_alu']
            assert row['instruction_i'] == 0xD6
            assert row['instruction_i_high'] == instruction
            assert read['value'] == expected[len(events)]
            a_high = row.get('register_address_a_high', row['register_address_a'])
            pre_a_high = ram[a_high] >> 4
            d_high = read['value'] >> 4
            predicted = ((d_high if instruction == 0xFD else 0) ^ pre_a_high ^ 15)
            assert row['alu']['y'] >> 4 == predicted
            following = trace[index + 1]
            assert following['pc'] == NEXT
            lookup = following['external_read']
            assert lookup['selected_by_alu']
            assert lookup['address'] == 0x100 + row['alu']['y']
            assert lookup['value'] == prom[lookup['address']]
            events.append(dict(visit=len(events), cycle=index, adc=read['value'],
                               pre_a_high=pre_a_high, y=row['alu']['y'],
                               rom_address=lookup['address'],
                               rom_value=lookup['value']))
        for address, value in row['registers'].items():
            ram[int(address)] = value
    assert len(events) == VISITS == run['site_visits'] == run['site_selected']
    assert run['result']['final_state']['pc'] == SITE
    return events


def run(out=HERE / 'results/lower-i-d3f8-lookup-chain.json'):
    _, base = fixture()
    scenario = condition_scenario(base, 'previous')
    prom = PROM.read_bytes()
    assert len(prom) == 512
    patterns = ((0, 1, 3, 2), (0, 0, 0, 0))
    cases = []
    for pattern in patterns:
        offered = hold(codes(pattern, 32, 'complementary'))[:VISITS]
        masked = [value & 15 for value in offered]
        variants = {}
        for label, mapping, instruction in (
                ('baseline', mapping_for('!10.6', '11.2'), 0xFC),
                ('candidate', mapping_with_upper_source(0, '17.6'), 0xFD)):
            full_run = run_trace(mapping, scenario, SITE, offered, CYCLES)
            masked_run = run_trace(mapping, scenario, SITE, masked, CYCLES)
            full = inspect(full_run, offered, instruction, prom)
            low = inspect(masked_run, masked, instruction, prom)
            assert [row['pc'] for row in full_run['trace']] == [
                row['pc'] for row in masked_run['trace']]
            differences = [i for i, (a, b) in enumerate(zip(full, low))
                           if a['rom_address'] != b['rom_address']]
            variants[label] = dict(instruction=f'{instruction:02X}',
                                   visits=len(full),
                                   distinct_adc_bytes=len(set(offered)),
                                   different_next_rom_addresses=len(differences),
                                   first_difference=(None if not differences else
                                                     dict(full=full[differences[0]],
                                                          masked=low[differences[0]])),
                                   full_trace_digest=full_run['result']['trace_digest'],
                                   masked_trace_digest=masked_run['result']['trace_digest'])
        assert variants['baseline']['different_next_rom_addresses'] == 0
        assert variants['candidate']['different_next_rom_addresses'] > 0
        cases.append(dict(pattern=list(pattern), variants=variants))
    paths = [Path(__file__), HERE / 'lower_i_d3f8_full_adc.py',
             HERE / 'lower_i_d3f8_input.py', HERE / 'lower_i_d3f8_sign_adc.py',
             HERE / 'lower_i_d3f8_upper_d_route.py',
             HERE / 'lower_i_prom_data_route.py',
             HERE / 'photo_controller_path.py', HERE / 'split_slice_probe.py',
             HERE / 'reference_modem.py', HERE.parent / 'assumed/execute.py',
             HERE.parent / 'model.py', PROM]
    report = dict(status='conditional D3F8 ALU-to-3F9 real-ROM lookup chain',
                  fixture=dict(visits=VISITS, cycles=CYCLES, sample_schedule='188/187 loop visits per complementary ADC code',
                               condition_select_0='inverted previous sign',
                               initial_q=5, initial_ram=[0] * 16,
                               upper_instruction_candidate='U8 I0 from U17 bit 6; physical continuity untraced'),
                  verified_rule=('D3F8 upper Y = XNOR(D7-D4, pre-RAM[A_high]7-4) with FD; '
                                 'FC instead uses zero for D7-D4; next 3F9 reads real PROM[0x100+Y]'),
                  cases=cases,
                  limitation='This verifies executed model dataflow under labelled wiring, not a decoded dibit, physical ADC path or USART RxD connection.',
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    print([(case['pattern'], {name: value['different_next_rom_addresses']
                             for name, value in case['variants'].items()})
           for case in report['cases']])
