"""Check whether the current transmit and ADC mapping hypotheses coexist."""

import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from lower_i_d3f8_full_adc import scenario_for_full_byte
from lower_i_d3f8_sign_adc import condition_scenario
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_controller_path import fixture
from photo_i0_hold_screen import hold_candidate
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from split_slice_probe import split_scenario

# Each group is a disputed physical field connection. The receiver's paired
# I7/A0 and I0/A1 sources stay together when switched to the q3 choice.
GROUPS = ((('i', 7), ('a', 0)),
          (('i', 0), ('a', 1)),
          (('i', 1),),
          (('i', 2),),
          (('i', 6),))
TX_CYCLES = 3000
RX_VISITS = 128
RX_CYCLES = 8 * RX_VISITS + 47


def mapped_choice(receiver, transmitter, mask):
    mapping = copy.deepcopy(receiver)
    mapping['name'] += f'-joint-low-mask-{mask:02X}'
    for bit, group in enumerate(GROUPS):
        if mask & (1 << bit):
            for field, index in group:
                mapping['fields'][field]['bits'][index] = (
                    transmitter['fields'][field]['bits'][index])
    return mapping


def tx_case(mapping, base, independent=True, high_links=None):
    scenario = hold_candidate(base)
    if independent:
        scenario = split_scenario(scenario)
        if high_links is not None:
            scenario['inputs']['slice_instruction']['high_from_low'] = dict(high_links)
            scenario['inputs']['slice_instruction']['evidence'] = (
                'Diagnostic identity links for comparison with the shared-slice control.')
        scenario['inputs']['register_address_bit_overrides']['a_high'] = copy.deepcopy(
            scenario['inputs']['register_address_bit_overrides']['a'])
        for policy in scenario['inputs']['register_address_bit_overrides']['a_high'].values():
            policy['evidence'] += '; same diagnostic level at U8 A pin is a separate, untraced hypothesis'
    scenario['initial']['q'] = 0
    scenario['io']['read']['pc_sequences'][str(0x127)] = [0xB0]
    scenario['io']['read']['pc_sequences'][str(0x12C)] = [0xEA]
    scenario['io']['read']['address']['bank_by_pc'] = {
        str(0x129): 256, str(0x12E): 256}
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, TX_CYCLES, mode='integrated',
                         out=temporary, trace_limit=TX_CYCLES)
        rows = [json.loads(line) for line in
                (Path(temporary) / 'trace.jsonl').open()
                if '"pc": 297' in line]
    return dict(clean=result['clean'], pc129_visits=len(rows),
                distinct_y129=len({row['alu']['y'] for row in rows}),
                distinct_rom_addresses=len({row['external_read'].get('address')
                                            for row in rows}),
                first_8_y129=[f'{row["alu"]["y"]:02X}' for row in rows[:8]],
                trace_digest=result['trace_digest'])


def rx_case(mapping, base, value):
    scenario = scenario_for_full_byte(condition_scenario(base, 'previous'),
                                      [value] * RX_VISITS, 'complementary')
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, RX_CYCLES, mode='integrated',
                         out=temporary, trace_limit=RX_CYCLES)
        path = Path(temporary) / 'trace.jsonl'
        rows = (json.loads(line) for line in path.open()
                if '"pc": 1016' in line or '"pc": 1017' in line)
        input_selected = 0
        next_addresses = []
        for row in rows:
            if row['pc'] == 0x3F8:
                read = row['external_read']
                input_selected += read.get('selected_by_alu', False) and read.get('value') == value
            elif row['pc'] == 0x3F9:
                next_addresses.append(row['external_read'].get('address'))
    return dict(clean=result['clean'], d3f8_visits=result['address_counts'].get(0x3F8, 0),
                input_selected=input_selected,
                next_3f9_addresses=next_addresses,
                trace_digest=result['trace_digest'])


def run(out=HERE / 'results/joint-tx-rx-mapping-screen.json'):
    receiver = mapping_with_upper_source(0, '17.6')
    transmitter = mapped(MAPPINGS['q3'])
    _, base = fixture()
    shared_receiver_low = copy.deepcopy(receiver)
    del shared_receiver_low['fields']['i_high']
    del shared_receiver_low['fields']['b_high']
    controls = dict(q3_shared=tx_case(transmitter, base, independent=False),
                    q3_split_photo=tx_case(transmitter, base),
                    q3_split_identity=tx_case(transmitter, base,
                                              high_links={'4': 4, '6': 6}),
                    receiver_lower_shared=tx_case(shared_receiver_low, base,
                                                  independent=False))
    if any((row['pc129_visits'], row['distinct_y129'],
            row['distinct_rom_addresses']) != (740, 16, 16)
           for row in controls.values()):
        raise ValueError('shared-slice transmitter controls changed')
    rows = []
    for mask in range(1 << len(GROUPS)):
        mapping = mapped_choice(receiver, transmitter, mask)
        tx = tx_case(mapping, base)
        full = rx_case(mapping, base, 0x59)
        low = rx_case(mapping, base, 0x09)
        common = min(len(full['next_3f9_addresses']),
                     len(low['next_3f9_addresses']))
        changed = sum(a != b for a, b in zip(
            full['next_3f9_addresses'][:common],
            low['next_3f9_addresses'][:common]))
        if not (tx['clean'] and full['clean'] and low['clean']):
            raise ValueError(('mapping run stopped', mask))
        rows.append(dict(tx_bitmask=mask, tx=tx,
                         rx=dict(full_visits=full['d3f8_visits'],
                                 masked_visits=low['d3f8_visits'],
                                 full_selected=full['input_selected'],
                                 masked_selected=low['input_selected'],
                                 common_3f9_reads=common,
                                 high_nibble_changed_next_addresses=changed,
                                 full_trace_digest=full['trace_digest'],
                                 masked_trace_digest=low['trace_digest'])))
    if len(rows) != 32 or rows[0]['tx']['pc129_visits'] != 740 or not rows[0]['rx']['high_nibble_changed_next_addresses']:
        raise ValueError('receiver control changed')
    full_loop = [row for row in rows if row['tx']['pc129_visits'] == 740]
    if not full_loop or max(row['tx']['distinct_y129'] for row in full_loop) >= 16:
        raise ValueError('joint mapping classification changed')

    paths = [Path(__file__), HERE / 'lower_i_d3f8_upper_d_route.py',
             HERE / 'lower_i_d3f8_full_adc.py',
             HERE / 'lower_i_d3f8_sign_adc.py',
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py', MAPPINGS['q3'],
             HERE / 'photo_controller_path.py',
             HERE / 'photo_i0_hold_screen.py',
             HERE / 'split_slice_probe.py',
             HERE.parent / 'assumed/execute.py',
             HERE.parent / 'model.py',
             HERE.parents[2] / 'am27s31dc-prom/nokia-modem-am27s31dc.bin',
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(status='current independent upper-slice ADC candidate collapses the q3-quality transmitter byte under tested field merges',
                  fixture=dict(receiver_base='upper-sensitive D3F8 candidate; independent high slice and inverted previous-sign condition',
                               transmitter_base='q3 photo-swapped lower fields; independent high slice added for joint screen',
                               switched_groups=[list(f'{field}[{index}]' for field, index in group)
                                                for group in GROUPS],
                               mask_bit_one='use q3 transmitter source for that group; zero uses receiver source',
                               transmitter='D127=B0, Q=0, upper ROM, 3000 real-PROM instructions; independent high-slice A pins held at the same diagnostic A levels as low-slice A pins under a separate untraced hypothesis',
                               receiver='Q=5, held complementary ADC 59 versus 09 at D3F8 for 128 visits',
                               high_fields='receiver candidate kept fixed in all 32 variants'),
                  controls=controls, cases=rows,
                  summary=dict(variants=len(rows),
                               complete_tx_loops=len(full_loop),
                               max_y129_values_in_complete_loops=max(
                                   row['tx']['distinct_y129'] for row in full_loop),
                               variants_with_rx_high_nibble_effect=sum(
                                   row['rx']['high_nibble_changed_next_addresses'] > 0
                                   for row in rows)),
                  limitations=['This is a local search over five paired lower-field choices, not every possible Am2901 wiring map.',
                               'A 740-read loop with fewer Y codes is not by itself proof of a failed or successful modulator; no full dibit replay is scored here.',
                               'The high-slice source, instruction timing, ADC and D127 ingress, DAC output and USART RxD paths are untraced.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    report = run()
    print(report['summary'])
