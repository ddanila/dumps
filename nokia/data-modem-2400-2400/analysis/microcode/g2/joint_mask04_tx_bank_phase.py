"""Test whether a free-running DAC latch phase can see PC129 ROM-bank changes."""

import copy
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

import joint_four_row_retention_tx as joint
from photo_dac_bus_permutations import mapped_codes
from photo_i0_hold_screen import hold_candidate
from photo_joint_line_filter_screen import bandpass
from photo_joint_tone_training_data import (DATA_STEP, SEGMENT_SYMBOLS,
                                            SILENCE_SYMBOLS, TONE_STEP,
                                            TONE_SYMBOLS, TOTAL_SYMBOLS,
                                            segment2_from_txd)
from photo_main_dibit_pulse import VISITS_PER_SYMBOL, scenario_inputs
from photo_main_dibit_dac_decode import decision_result
from reference_modem import spectral_peak

EXECUTE = HERE.parent / 'assumed/execute.py'
SITES = (0x129, 0x12A)


def capturing_execute():
    source = EXECUTE.read_text()
    patches = (
        ("    trace_count=0;io_count=0;dispatch_counts=Counter();register_changes=0",
         "    trace_count=0;io_count=0;dispatch_counts=Counter();register_changes=0\n"
         "    site_y={0x129:[],0x12A:[]}"),
        ("            carry_input.observe(result)",
         "            if pc in site_y:site_y[pc].append(result['y'])\n"
         "            carry_input.observe(result)"),
        ("    if source_read['mode']=='pc_sequence':summary['read_sequence_visits']=dict(sequence_visits)",
         "    summary['site_y']=site_y\n"
         "    if source_read['mode']=='pc_sequence':summary['read_sequence_visits']=dict(sequence_visits)"),
    )
    for old, new in patches:
        if source.count(old) != 1:
            raise ValueError(('emulator injection site changed', old))
        source = source.replace(old, new)
    scope = {'__name__': 'joint_mask04_tx_bank_phase_instrumented',
             '__file__': str(EXECUTE)}
    exec(compile(source, str(EXECUTE), 'exec'), scope)
    return scope['execute']


def scenario_for(base, controller_case, bank):
    segment2 = segment2_from_txd(controller_case)
    symbols = [3] * SEGMENT_SYMBOLS + segment2
    inputs = ([TONE_STEP] * (TONE_SYMBOLS * VISITS_PER_SYMBOL) +
              [DATA_STEP] * (SILENCE_SYMBOLS * VISITS_PER_SYMBOL) +
              scenario_inputs(symbols))
    if len(inputs) != TOTAL_SYMBOLS * VISITS_PER_SYMBOL + 1:
        raise ValueError('TX controller stimulus changed')
    scenario = joint.split_scenario(hold_candidate(base))
    scenario['name'] += '; bank-phase witness at PC12A'
    scenario['inputs']['register_address_bit_overrides']['a_high'] = copy.deepcopy(
        scenario['inputs']['register_address_bit_overrides']['a'])
    for policy in scenario['inputs']['register_address_bit_overrides']['a_high'].values():
        policy['evidence'] += '; untraced high-slice A pin diagnostic level'
    scenario['initial']['q'] = 0
    scenario['io']['read']['pc_sequences'][str(0x127)] = inputs
    scenario['io']['read']['pc_sequences'][str(0x12C)] = [0xEA]
    scenario['io']['read']['address']['bank_by_pc'] = {
        str(0x129): bank, str(0x12E): 256}
    return scenario


def sample(values, phase):
    return [values[phase + joint.SAMPLE_DIVISOR * index]
            for index in range(joint.SAMPLE_COUNT)]


def run(out=HERE / 'results/joint-mask04-tx-bank-phase.json'):
    execute = capturing_execute()
    mapping = joint.candidate(joint.mapping_with_upper_source(0, '17.6'),
                              joint.mapped(joint.MAPPINGS['q3']), 4)
    _, base = joint.fixture()
    controller = json.loads(joint.TXREADY.read_text())
    buses = json.loads(joint.BUSES.read_text())['zero_error_survivors']
    if len(buses) != 6 or any(bus[0] != 4 for bus in buses):
        raise ValueError('surviving DAC-bus fixture changed')
    cycles = (TOTAL_SYMBOLS * VISITS_PER_SYMBOL + 64) * 4
    cases = []
    for selector in ('40', '60'):
        controller_case = next(row for row in controller['cases']
                               if row['selector'] == selector)
        symbols = [3] * SEGMENT_SYMBOLS + segment2_from_txd(controller_case)
        bank_results = {}
        for bank in (256, 0):
            scenario = scenario_for(base, controller_case, bank)
            result = execute(mapping, scenario, cycles, mode='integrated',
                             trace_limit=0)
            if (not result['clean'] or result['completed_cycles'] != cycles or
                    result['address_counts'].get(0x129) != 312054 or
                    result['address_counts'].get(0x12A) != 312054 or
                    result['address_counts'].get(0x12E, 0)):
                raise ValueError(('transmitter loop changed', selector, bank))
            if any(len(result['site_y'][pc]) != 312054 for pc in SITES):
                raise ValueError(('site capture changed', selector, bank))
            bank_results[bank] = result
            print(selector, bank, result['trace_digest'], flush=True)
        upper, lower = bank_results[256], bank_results[0]
        sites = []
        for pc in SITES:
            a, b = upper['site_y'][pc], lower['site_y'][pc]
            bitmask = Counter(x ^ y for x, y in zip(a, b) if x != y)
            phase_counts = [sum(a[phase + joint.SAMPLE_DIVISOR * i] !=
                                b[phase + joint.SAMPLE_DIVISOR * i]
                                for i in range(joint.SAMPLE_COUNT))
                            for phase in range(joint.SAMPLE_DIVISOR)]
            sample_cases = []
            for phase in (0, 7):
                raw_upper, raw_lower = sample(a, phase), sample(b, phase)
                bus = buses[0]
                codes_upper = mapped_codes(raw_upper, bus)
                codes_lower = mapped_codes(raw_lower, bus)
                tone_end = TONE_SYMBOLS * 8
                silence_end = (TONE_SYMBOLS + SILENCE_SYMBOLS) * 8
                peaks = [spectral_peak([code - 128 for code in codes[64:tone_end]],
                                       lower=100, upper=3500)['frequency_hz']
                         for codes in (codes_upper, codes_lower)]
                data_scores = []
                for raw in (raw_upper, raw_lower):
                    errors = []
                    for current_bus in buses:
                        codes = mapped_codes(raw, current_bus)
                        gated = (codes[:tone_end] +
                                 [128] * (silence_end - tone_end) +
                                 codes[silence_end:])
                        line = bandpass([code - 128 for code in gated], 1.0)
                        score = decision_result(
                            [value + 128 for value in line[silence_end:]],
                            symbols, sample_shift=6)
                        if score['decisions'] != 62:
                            raise ValueError(('data decision count changed',
                                              selector, pc, phase))
                        errors.append(score['errors'])
                    data_scores.append(errors)
                sample_cases.append(dict(phase=phase,
                                         changed_y_samples=sum(x != y for x, y in
                                                               zip(raw_upper, raw_lower)),
                                         y_sha256=[hashlib.sha256(bytes(raw)).hexdigest()
                                                   for raw in (raw_upper, raw_lower)],
                                         selected_bus_code_sha256=[hashlib.sha256(bytes(codes)).hexdigest()
                                                                   for codes in (codes_upper, codes_lower)],
                                         selected_bus_code_differences=sum(x != y for x, y in
                                                                           zip(codes_upper, codes_lower)),
                                         selected_bus_tone_peaks_hz=peaks,
                                         filtered_data_errors_by_six_buses=data_scores))
            sites.append(dict(pc=f'{pc:03X}',
                              changed_raw_visits=sum(bitmask.values()),
                              changed_bitmasks={f'{mask:02X}': count
                                                for mask, count in sorted(bitmask.items())},
                              phase_changed_sample_counts=phase_counts,
                              phases_with_changed_samples=sum(n > 0 for n in phase_counts),
                              max_changed_samples=max(phase_counts),
                              sample_cases=sample_cases))
        cases.append(dict(selector=selector,
                          trace_digests={str(bank): bank_results[bank]['trace_digest']
                                         for bank in (256, 0)},
                          site_visits=312054, sites=sites))
    report = dict(experiment='full controller-fed PC129 ROM-bank phase sensitivity',
                  fixture=dict(bank_upper=256, bank_lower=0,
                               pc12e_bank=256, cycles=cycles,
                               visits_per_sample=joint.SAMPLE_DIVISOR,
                               sample_count=joint.SAMPLE_COUNT,
                               sites=['129', '12A'],
                               dac_bus='first of six surviving photo-compatible bus orders; source Y0 maps to DAC code bit 4'),
                  cases=cases,
                  limitations=[
                      'The ROM A8 source, 74LS273 data/clock phase, DAC bus and analog line are not traced.',
                      'A changed candidate DAC code under bank ablation identifies a modeled causal route, not the physical output node.',
                      'The 9,600 Hz sample label assumes one 14.4 MHz oscillator period per microinstruction and a divider of 375 loop visits.'
                  ])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
