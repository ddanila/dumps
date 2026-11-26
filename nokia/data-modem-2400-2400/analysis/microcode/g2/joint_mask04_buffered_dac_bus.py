"""Screen photo-B5-compatible DAC byte orders on full buffered PROM streams."""

import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'assumed'), str(HERE)]

from common import save
import joint_mask04_buffered_serial_handoff as buffered
import joint_mask04_full_zero_handoff as full
from photo_a1_dynamic_mode_replay import tone_summary
from photo_dac_bus_permutations import mapped_codes
from photo_joint_line_filter_screen import SILENCE_END, TONE_END, bandpass
from photo_joint_tone_training_data import DATA_STEP, SILENCE_SYMBOLS, TONE_STEP, TONE_SYMBOLS
from photo_main_dibit_pulse import BASE, VISITS_PER_SYMBOL
from reference_modem import receive, rms
from zero_run_detector import line_octets

PRIOR = HERE / 'results/joint-mask04-buffered-serial-handoff.json'
BUS_ORDERS = HERE / 'results/photo-dac-bus-permutations.json'
SITES = (0x127, 0x129)


def samples(mapping, base, offered):
    input_values, dibits, _ = buffered.buffered_inputs(offered)
    values = ([TONE_STEP] * (TONE_SYMBOLS * VISITS_PER_SYMBOL) +
              [DATA_STEP] * (SILENCE_SYMBOLS * VISITS_PER_SYMBOL) +
              input_values + [BASE] * (6 * 375))
    scenario = full.split_scenario(full.hold_candidate(base))
    scenario['name'] += '; buffered serial full-Y DAC bus screen'
    scenario['inputs']['register_address_bit_overrides']['a_high'] = copy.deepcopy(
        scenario['inputs']['register_address_bit_overrides']['a'])
    for policy in scenario['inputs']['register_address_bit_overrides']['a_high'].values():
        policy['evidence'] += '; untraced high-slice A pin diagnostic level'
    scenario['initial']['q'] = 0
    scenario['io']['read']['pc_sequences'][str(0x127)] = values
    scenario['io']['read']['pc_sequences'][str(0x12C)] = [0xEA]
    scenario['io']['read']['address']['bank_by_pc'] = {
        str(0x129): 256, str(0x12E): 256}
    result_y = {site: [] for site in SITES}
    with tempfile.TemporaryDirectory() as temporary:
        result = full.execute(mapping, scenario, buffered.TX_CYCLES,
                              mode='integrated', out=temporary,
                              trace_limit=buffered.TX_CYCLES)
        for line in (Path(temporary) / 'trace.jsonl').open():
            row = json.loads(line)
            cycle = row['cycle']
            for site in SITES:
                start = 40 + (site - 0x127)
                if (cycle >= start and (cycle - start) % 1500 == 0 and
                        len(result_y[site]) < buffered.SAMPLES):
                    if row['pc'] != site:
                        raise ValueError(('latch-site cadence changed', site, cycle, row['pc']))
                    result_y[site].append(row['alu']['y'])
    if (not result['clean'] or result['completed_cycles'] != buffered.TX_CYCLES or
            any(len(values) != buffered.SAMPLES for values in result_y.values())):
        raise ValueError('full-Y transmitter capture incomplete')
    return result, result_y, dibits


def score(raw, permutation, expected):
    codes = mapped_codes(raw, permutation)
    gated = codes[:TONE_END] + [128] * (SILENCE_END - TONE_END) + codes[SILENCE_END:]
    line = bandpass([code - 128 for code in gated], 1.0)
    tone = tone_summary(line[64:TONE_END])
    tone_rms = rms(line[64:TONE_END])
    silence_rms = rms(line[SILENCE_END - 32:SILENCE_END])
    selected = line[SILENCE_END + 6:SILENCE_END + 6 + buffered.RX_SYMBOLS * 8]
    if len(selected) != buffered.RX_SYMBOLS * 8:
        raise ValueError('candidate DAC waveform incomplete')
    gain = 110 / max(abs(value) for value in selected)
    pcm = [max(-127, min(127, round(value * gain))) for value in selected]
    decoded = receive(pcm)
    if len(decoded) != len(expected) - 1:
        raise ValueError('reference receiver length changed')
    wrong = [i + 1 for i, (actual, want) in
             enumerate(zip(decoded, expected[1:])) if actual != want]
    return dict(wrong_symbols=wrong, total_errors=len(wrong),
                data_errors=sum(index >= 33 for index in wrong),
                tone_peak_hz=tone['peak_hz'],
                tone_r2_2100=tone['r2_2100'],
                tone_rms=tone_rms,
                last_32_a2_rms=silence_rms,
                a2_to_a1_rms_ratio=silence_rms / tone_rms,
                pcm_gain=gain,
                pcm_sha256=hashlib.sha256(bytes(value + 127 for value in pcm)).hexdigest(),
                dac_code_sha256=hashlib.sha256(bytes(codes)).hexdigest(),
                distinct_dac_codes=len(set(codes)))


def run(out=HERE / 'results/joint-mask04-buffered-dac-bus.json'):
    prior = json.loads(PRIOR.read_text())
    orders = json.loads(BUS_ORDERS.read_text())
    permutations = [row['input_bit_to_dac_code_bit']
                    for row in orders['zero_error_candidates']]
    if len(permutations) != 12 or any(p[4] != 3 for p in permutations):
        raise ValueError('photo-B5 candidate bus set changed')
    mapping = full.candidate(full.mapping_with_upper_source(0, '17.6'),
                             full.mapped(full.MAPPINGS['q3']), 4)
    _, base = full.fixture()
    report = dict(experiment='full buffered real-PROM Y byte to candidate DAC bus screen',
                  fixture=dict(sample_sites=[f'{site:03X}' for site in SITES],
                               photo_constraint='ordered Y to LS273; Q4 to DAC08 B5',
                               bus_orders='12 previously frozen zero-error permutations',
                               analog='mid-code A2 gate, Q=1 bandpass, six-sample alignment',
                               reference='independent known-carrier differential decoder',
                               tx_cycles=buffered.TX_CYCLES),
                  cases=[],
                  limitations=[
                      'Y-to-latch order, latch clock, other seven DAC bits, line filter and physical output remain untraced.',
                      'This scores an analog candidate with an independent reference decoder; it does not execute the DSC receiver or prove the board waveform.'],
                  source_sha256={str(path.relative_to(HERE.parents[4])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in (Path(__file__), PRIOR, BUS_ORDERS,
                                              Path(buffered.__file__), Path(full.__file__),
                                              HERE / 'photo_dac_bus_permutations.py',
                                              HERE / 'photo_a1_dynamic_mode_replay.py',
                                              HERE / 'photo_joint_line_filter_screen.py',
                                              HERE / 'reference_modem.py')})
    for selector, delay in (('40', 5), ('60', 18)):
        offered = line_octets([0] * 8, delay)
        result, raw_by_site, dibits = samples(mapping, base, offered)
        baseline = next(case for case in prior['cases'] if case['selector'] == selector)
        if hashlib.sha256(bytes(value >> 7 for value in raw_by_site[0x127])).hexdigest() != baseline['tx_y7_sha256']:
            raise ValueError('candidate full-Y source differs from prior real-PROM Y7')
        expected = [3] * 33 + dibits
        sites = {}
        for site, raw in raw_by_site.items():
            sites[f'{site:03X}'] = dict(
                raw_y_sha256=hashlib.sha256(bytes(raw)).hexdigest(),
                bus_orders=[dict(permutation=p, **score(raw, p, expected))
                            for p in permutations])
        case = dict(selector=selector, offered_line_bytes=[f'{x:02X}' for x in offered],
                    tx_cycles=result['completed_cycles'],
                    tx_trace_digest=result['trace_digest'],
                    sites=sites)
        report['cases'].append(case)
        save(out, report)
        print(selector, {site: min(row['data_errors'] for row in value['bus_orders'])
                         for site, value in sites.items()}, flush=True)
    return report


if __name__ == '__main__':
    run()
