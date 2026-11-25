"""Screen one fixed upper-instruction hypothesis on TX and varying ADC input."""

import copy
import hashlib
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
from execute import execute
from joint_tx_rx_mapping_screen import fixture, mapped_choice, rx_case, tx_case
from lower_i_d3f8_full_adc import (
    DETAIL_PATTERNS, LONG_CYCLES, LONG_SAMPLES, LONG_VISITS, RANDOM_SEEDS,
    SAMPLE_START, SHORT_CYCLES, SHORT_SAMPLES, SHORT_VISITS,
    codes, hold, scenario_for_full_byte,
)
from lower_i_d3f8_input import run_trace
from lower_i_d3f8_sign_adc import condition_scenario
from lower_i_d3f8_upper_d_route import mapping_with_upper_source
from photo_mapping_q_sweep import mapped
from photo_mapping_stream_screen import MAPPINGS
from reference_modem import transmit

UPPER_SOURCE = '!17.5'
SELECTED_MASK = 0x08


def candidate(receiver, transmitter, mask):
    mapping = mapped_choice(receiver, transmitter, mask)
    mapping['name'] += '-upper-i0-i7-inverted-u17-d5'
    mapping['fields']['i_high'] = copy.deepcopy(transmitter['fields']['i'])
    for bit in (0, 7):
        mapping['fields']['i_high']['bits'][bit] = UPPER_SOURCE
    mapping['fields']['i_high']['evidence'] = (
        'Diagnostic U8 instruction: q3 PROM sources except I0 and I7 both '
        'from inverted U17 D5; inversion, driver, latch and both pin routes '
        'are untraced. Photo-candidate I4/I6 crosslinks remain scenario inputs.')
    mapping['fields'].pop('b_high')
    return mapping


def input_run(mapping, base, values, cycles):
    scenario = scenario_for_full_byte(base, values, 'complementary')
    result = execute(mapping, scenario, cycles, mode='integrated', trace_limit=0)
    return dict(clean=result['clean'], d3f8_visits=result['address_counts'].get(0x3F8, 0),
                offered_visits=result['read_sequence_visits'].get(0x3F8, 0),
                selected_rom_reads=result['rom_reads']['selected_by_alu'],
                bad_exit_visits=result['address_counts'].get(0x1EA, 0),
                final_pc=f"{result['final_state']['pc']:03X}",
                trace_digest=result['trace_digest'])


def run(out=HERE / 'results/joint-upper-source-screen.json'):
    receiver = mapping_with_upper_source(0, '17.6')
    transmitter = mapped(MAPPINGS['q3'])
    _, base = fixture()
    short_values = hold(codes(DETAIL_PATTERNS[0], SHORT_SAMPLES, 'complementary'))
    cases = []
    for mask in range(32):
        mapping = candidate(receiver, transmitter, mask)
        tx = tx_case(mapping, base)
        adc = input_run(mapping, base, short_values, SHORT_CYCLES)
        cases.append(dict(mask=mask, tx=dict(
            pc129_visits=tx['pc129_visits'], distinct_y129=tx['distinct_y129'],
            distinct_rom_addresses=tx['distinct_rom_addresses'],
            trace_digest=tx['trace_digest']), adc=adc))
    survivors = [row['mask'] for row in cases
                 if (row['tx']['pc129_visits'], row['tx']['distinct_y129'],
                     row['tx']['distinct_rom_addresses'], row['adc']['d3f8_visits'],
                     row['adc']['bad_exit_visits']) == (740, 16, 16, SHORT_VISITS, 0)]
    if survivors != [4, 6, 8, 10, 14]:
        raise ValueError(('joint upper-source survivor set changed', survivors))

    mapping = candidate(receiver, transmitter, SELECTED_MASK)
    held_full = rx_case(mapping, base, 0x59)
    held_masked = rx_case(mapping, base, 0x09)
    changed_held_addresses = sum(a != b for a, b in zip(
        held_full['next_3f9_addresses'], held_masked['next_3f9_addresses']))
    if (held_full['d3f8_visits'], held_full['input_selected'],
            changed_held_addresses) != (128, 128, 128):
        raise ValueError('held ADC sensitivity changed')

    rx_base = condition_scenario(base, 'previous')
    full = run_trace(mapping, rx_base, 0x3F8, short_values, SHORT_CYCLES)
    masked = run_trace(mapping, rx_base, 0x3F8,
                       [value & 0x0F for value in short_values], SHORT_CYCLES)
    if (full['site_visits'], masked['site_visits'],
            full['site_selected'], masked['site_selected']) != (SHORT_VISITS,) * 4:
        raise ValueError('short ADC samples not all selected')
    same_pc = all(a['pc'] == b['pc'] for a, b in zip(full['trace'], masked['trace']))
    changed_boundaries = sum(a != b for a, b in
                             zip(full['boundaries'], masked['boundaries']))
    changed_rom_addresses = sum(a != b for a, b in
                                zip(full['reads'], masked['reads']))
    if (not same_pc or changed_boundaries == 0 or changed_rom_addresses == 0):
        raise ValueError('short ADC high-nibble effect changed')

    long_cases = []
    for pattern in DETAIL_PATTERNS:
        values = hold(codes(pattern, LONG_SAMPLES, 'complementary'))
        for label, offered in (('full', values),
                               ('masked', [value & 0x0F for value in values])):
            result = input_run(mapping, base, offered, LONG_CYCLES)
            if (not result['clean'] or result['d3f8_visits'] != LONG_VISITS or
                    result['offered_visits'] != LONG_VISITS or
                    result['bad_exit_visits'] or result['final_pc'] != '3F8'):
                raise ValueError(('long ADC run stopped', pattern, label))
            long_cases.append(dict(kind='periodic', pattern=list(pattern),
                                   input=label, **result))
    generator = random.Random(RANDOM_SEEDS[0])
    dibits = [0] * 8 + [generator.randrange(4) for _ in range(16)] + [0] * 8
    pcm = transmit(dibits)
    random_values = hold([127 - sample for sample in
                          pcm[SAMPLE_START:SAMPLE_START + LONG_SAMPLES]])
    random_result = input_run(mapping, base, random_values, LONG_CYCLES)
    if (not random_result['clean'] or
            random_result['d3f8_visits'] != LONG_VISITS or
            random_result['offered_visits'] != LONG_VISITS or
            random_result['bad_exit_visits'] or
            random_result['final_pc'] != '3F8'):
        raise ValueError('nonperiodic ADC run stopped')
    long_cases.append(dict(kind='nonperiodic', seed=RANDOM_SEEDS[0],
                           input='full', **random_result))

    mapping_out = out.with_name('joint-upper-source-mask08-mapping.json')
    save(mapping_out, mapping)
    paths = [Path(__file__), HERE / 'joint_tx_rx_mapping_screen.py',
             HERE / 'lower_i_d3f8_full_adc.py',
             HERE / 'lower_i_d3f8_input.py',
             HERE / 'lower_i_d3f8_sign_adc.py',
             HERE / 'lower_i_d3f8_upper_d_route.py',
             HERE / 'photo_mapping_q_sweep.py',
             HERE / 'photo_mapping_stream_screen.py', MAPPINGS['q3'],
             HERE / 'photo_controller_path.py', HERE / 'split_slice_probe.py',
             HERE / 'reference_modem.py', HERE.parent / 'assumed/execute.py',
             HERE.parent / 'model.py',
             HERE.parents[2] / 'am27s31dc-prom/nokia-modem-am27s31dc.bin',
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(status='one fixed hypothetical field map preserves held TX phase and sustained ADC high-nibble response; modem outputs unproven',
                  fixture=dict(upper_i0_i7=UPPER_SOURCE,
                               upper_other_i='q3 sources with photo-candidate I4/I6 crosslinks',
                               lower_field_groups='receiver/q3 mask from joint_tx_rx_mapping_screen',
                               selected_mask=f'{SELECTED_MASK:02X}',
                               tx='D127=B0, Q=0, upper ROM; high A pins use separately labelled diagnostic levels matching low A pins',
                               rx='Q=5, complementary ADC 127-PCM at D3F8, 188/187 visits per sample, inverted previous-sign condition; raw high/low A sources',
                               upper_b='same B address as lower slice',
                               instruction_and_pin_routes='untraced hypotheses'),
                  cases=cases, surviving_masks=survivors,
                  selected_held=dict(visits=held_full['d3f8_visits'],
                                     selected=held_full['input_selected'],
                                     changed_next_3f9_addresses=changed_held_addresses),
                  selected_short=dict(visits=SHORT_VISITS, same_pc_path=same_pc,
                                      different_state_boundaries=changed_boundaries,
                                      selected_rom_reads=len(full['reads']),
                                      different_selected_rom_addresses=changed_rom_addresses,
                                      full_trace_digest=full['result']['trace_digest'],
                                      masked_trace_digest=masked['result']['trace_digest']),
                  selected_long=long_cases,
                  mapping_file=mapping_out.name,
                  limitations=[
                      'A single shared inverted U17 D5 source to U8 I0/I7 is only a photo-compatible wiring hypothesis; no continuity or latch phase is established.',
                      'The transmitter check is a held D127 phase loop, not a full controller-driven dibit waveform or measured DAC output.',
                      'The receiver checks prove input-dependent internal state and ROM addressing, not a decoded dibit, echo cancellation, or USART RxD transition.',
                      'A/B address, carry, shift, ADC sample clock and output paths remain assumed or untraced.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    result = run()
    print(dict(surviving_masks=result['surviving_masks'],
               selected_short=result['selected_short']))
