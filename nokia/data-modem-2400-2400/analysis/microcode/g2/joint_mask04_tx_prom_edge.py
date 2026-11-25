"""Replay the candidate DAC edge on the same mask-04 map used for receive."""

import copy
import hashlib
import json
import tempfile
from pathlib import Path

from joint_four_row_retention_tx import (HERE, SAMPLE_COUNT, TXREADY,
                                         candidate, execute, fixture,
                                         hold_candidate, mapped,
                                         mapping_with_upper_source,
                                         MAPPINGS, split_scenario)
from photo_dac_bus_permutations import SELECTED, mapped_codes
from photo_joint_line_filter_screen import BUSES
from photo_joint_tone_training_data import (DATA_STEP, SEGMENT_SYMBOLS,
                                            SILENCE_SYMBOLS, TONE_STEP,
                                            TONE_SYMBOLS, TOTAL_SYMBOLS,
                                            segment2_from_txd)
from photo_main_dibit_pulse import VISITS_PER_SYMBOL, scenario_inputs
from photo_tx_divided_prom_clock import capture, line_metrics
from photo_joint_waveform_shape_screen import reference_templates
from common import save

PRIOR = HERE / 'results/joint-four-row-retention-tx.json'
Q3_EDGE = HERE / 'results/photo-tx-divided-prom-clock.json'


def replay(mapping, base, tx_case, prior_case, q3_case, buses):
    selector = tx_case['selector']
    segment2 = segment2_from_txd(tx_case)
    symbols = [3] * SEGMENT_SYMBOLS + segment2
    inputs = ([TONE_STEP] * (TONE_SYMBOLS * VISITS_PER_SYMBOL) +
              [DATA_STEP] * (SILENCE_SYMBOLS * VISITS_PER_SYMBOL) +
              scenario_inputs(symbols))
    scenario = split_scenario(hold_candidate(base))
    scenario['name'] += '; alternate joint upper-source mask 04 full TX'
    scenario['inputs']['register_address_bit_overrides']['a_high'] = copy.deepcopy(
        scenario['inputs']['register_address_bit_overrides']['a'])
    for policy in scenario['inputs']['register_address_bit_overrides']['a_high'].values():
        policy['evidence'] += '; untraced high-slice A pin diagnostic level'
    scenario['initial']['q'] = 0
    scenario['io']['read']['pc_sequences'][str(0x127)] = inputs
    scenario['io']['read']['pc_sequences'][str(0x12C)] = [0xEA]
    scenario['io']['read']['address']['bank_by_pc'] = {
        str(0x129): 256, str(0x12E): 256}
    cycles = (TOTAL_SYMBOLS * VISITS_PER_SYMBOL + 64) * 4
    with tempfile.TemporaryDirectory() as temporary:
        result = execute(mapping, scenario, cycles, mode='integrated',
                         out=temporary, trace_limit=cycles)
        captured = capture(Path(temporary) / 'trace.jsonl')
    if (not result['clean'] or result['completed_cycles'] != cycles or
            result['trace_digest'] != prior_case['trace_digest'] or
            hashlib.sha256(bytes(captured['post_rom'])).hexdigest() !=
            prior_case['raw_y_sample_sha256'] or
            captured['captured_samples'] != SAMPLE_COUNT or
            captured['raw_rising_edges'] != prior_case['pc129_visits']):
        raise ValueError(('joint-map edge trace disagrees with prior run', selector))
    templates = reference_templates(symbols)
    bus_cases = []
    for index, bus in enumerate(buses):
        pre = line_metrics(captured['pre_rising'], bus, symbols, templates)
        post = line_metrics(captured['post_rom'], bus, symbols, templates)
        saved = prior_case['bus_cases'][index]
        if (saved['input_bit_to_dac_code_bit'] != bus or
                post['tone_peak_hz'] != saved['late_a1_peak_hz'] or
                post['data_errors'] != saved['filtered_data_errors']):
            raise ValueError(('joint-map DAC metrics changed', selector, index))
        bus_cases.append(dict(bus_index=index,
                              input_bit_to_dac_code_bit=bus,
                              pre_rising=pre, post_rom=post))
    mapped_digests = {name: hashlib.sha256(bytes(mapped_codes(captured[name],
                                                               SELECTED))).hexdigest()
                      for name in ('pre_rising', 'post_rom')}
    phase_deltas = [abs(before - after) for before, after in
                    zip(captured['pre_rising'], captured['post_rom'])]
    return dict(selector=selector, trace_digest=result['trace_digest'],
                cycles=cycles,
                raw_rising_edges=captured['raw_rising_edges'],
                raw_falling_edges=captured['raw_falling_edges'],
                captured_samples=captured['captured_samples'],
                first_capture_cycle=captured['first_capture_cycle'],
                final_capture_cycle=captured['final_capture_cycle'],
                raw_post_rom_sha256=hashlib.sha256(bytes(captured['post_rom'])).hexdigest(),
                pre_post_raw_sample_differences=sum(delta != 0 for delta in phase_deltas),
                pre_post_raw_sample_mean_absolute_difference=round(
                    sum(phase_deltas) / len(phase_deltas), 6),
                pre_post_raw_sample_max_absolute_difference=max(phase_deltas),
                selected_bus_sha256=mapped_digests,
                q3_selected_bus_same={name: mapped_digests[name] ==
                                      q3_case['selected_bus_sha256'][name]
                                      for name in mapped_digests},
                bus_cases=bus_cases)


def run(out=HERE / 'results/joint-mask04-tx-prom-edge.json'):
    txready = json.loads(TXREADY.read_text())
    prior = json.loads(PRIOR.read_text())
    q3 = json.loads(Q3_EDGE.read_text())
    buses = json.loads(BUSES.read_text())['zero_error_survivors']
    if len(buses) != 6:
        raise ValueError('DAC bus survivor count changed')
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    cases = []
    for selector in ('40', '60'):
        cases.append(replay(
            mapping, base,
            next(row for row in txready['cases'] if row['selector'] == selector),
            next(row for row in prior['transmit_mask04'] if row['selector'] == selector),
            next(row for row in q3['cases'] if row['selector'] == selector),
            buses))
        print('captured', selector, flush=True)
    paths = [Path(__file__), TXREADY, PRIOR, Q3_EDGE, BUSES,
             HERE / 'joint_four_row_retention_tx.py',
             HERE / 'photo_tx_divided_prom_clock.py',
             HERE / 'photo_joint_tone_training_data.py',
             HERE / 'photo_joint_waveform_shape_screen.py',
             HERE.parent / 'assumed/execute.py', MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(experiment='raw U10 D2 divided DAC edge on the fixed mask-04 joint map',
                  fixture=dict(mapping='joint upper-source, lower mask 04',
                               controller_selectors=('40', '60'),
                               raw_edge='U10 D2 rises at 129 and falls at 12A',
                               divisor=375,
                               latch='assumed 74LS273 data/clock and six photo-compatible DAC buses',
                               analog='assumed A2 mid-code gate and 1950 Hz Q=1 bandpass'),
                  cases=cases,
                  limitations=['A direct or inverted U10 D2 clock, 375:1 divider, Y-to-latch bus, DAC bus and analog output remain untraced hypotheses.',
                               'The line signatures use an assumed A2 mute and analog filter; this is not a physical DAC or connector observation.',
                               'The same mapping supports the separate receive fixture, but no controller/line/ADC co-simulation runs both directions at once.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    run()
