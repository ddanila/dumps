"""Test DAC MSB-only data decisions on the executed joint mask-04 stream."""

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
from joint_four_row_retention_tx import (candidate, fixture, hold_candidate,
                                         mapped, mapping_with_upper_source,
                                         MAPPINGS, split_scenario)
from photo_a1_dynamic_mode_replay import tone_summary
from photo_dac_bus_permutations import SELECTED, mapped_codes
from photo_joint_line_filter_screen import (BUSES, SILENCE_END, TONE_END,
                                            bandpass)
from photo_joint_tone_training_data import (DATA_STEP, SEGMENT_SYMBOLS,
                                            SILENCE_SYMBOLS, TONE_STEP,
                                            TONE_SYMBOLS, TOTAL_SYMBOLS,
                                            segment2_from_txd)
from photo_main_dibit_dac_decode import decision_result
from photo_main_dibit_pulse import VISITS_PER_SYMBOL, scenario_inputs
from photo_tx_divided_prom_clock import capture

TXREADY = HERE / 'results/main-loop-usart-txready.json'
PRIOR = HERE / 'results/joint-four-row-retention-tx.json'
EDGE = HERE / 'results/joint-mask04-tx-prom-edge.json'


def score(codes, symbols):
    line = bandpass([code - 128 for code in codes], 1.0)
    data = decision_result([value + 128 for value in line[SILENCE_END:]],
                           symbols, sample_shift=6)
    return dict(tone_peak_hz=tone_summary(line[64:TONE_END])['peak_hz'],
                data=data)


def replay(mapping, base, tx_case, prior_case, edge_case, buses):
    selector = tx_case['selector']
    symbols = [3] * SEGMENT_SYMBOLS + segment2_from_txd(tx_case)
    inputs = ([TONE_STEP] * (TONE_SYMBOLS * VISITS_PER_SYMBOL) +
              [DATA_STEP] * (SILENCE_SYMBOLS * VISITS_PER_SYMBOL) +
              scenario_inputs(symbols))
    scenario = split_scenario(hold_candidate(base))
    scenario['name'] += '; mask04 DAC MSB-only data test'
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
        samples = capture(Path(temporary) / 'trace.jsonl')
    if (not result['clean'] or result['completed_cycles'] != cycles or
            result['trace_digest'] != prior_case['trace_digest'] or
            result['trace_digest'] != edge_case['trace_digest'] or
            hashlib.sha256(bytes(samples['post_rom'])).hexdigest() !=
            prior_case['raw_y_sample_sha256'] or
            samples['captured_samples'] != TOTAL_SYMBOLS * 8):
        raise ValueError(('full PROM stream changed', selector))
    rows = []
    for phase in ('pre_rising', 'post_rom'):
        raw = samples[phase]
        expected_hash = edge_case['selected_bus_sha256'][phase]
        if hashlib.sha256(bytes(mapped_codes(raw, SELECTED))).hexdigest() != expected_hash:
            raise ValueError(('edge capture hash changed', selector, phase))
        for bus_index, bus in enumerate(buses):
            codes = mapped_codes(raw, bus)
            full = score(codes, symbols)
            msb = score([code & 0x80 for code in codes], symbols)
            lower = score([code & 0x7F for code in codes], symbols)
            if full['tone_peak_hz'] != 2100 or full['data']['errors'] != 0:
                raise ValueError(('baseline transmitter result changed', selector,
                                  phase, bus_index))
            rows.append(dict(phase=phase, bus_index=bus_index,
                             full=full, msb_only=msb, lower_seven_only=lower))
    return dict(selector=selector, cycles=cycles, trace_digest=result['trace_digest'],
                raw_pre_rising_sha256=hashlib.sha256(bytes(samples['pre_rising'])).hexdigest(),
                raw_post_rom_sha256=hashlib.sha256(bytes(samples['post_rom'])).hexdigest(),
                rows=rows)


def run(out=HERE / 'results/joint-mask04-dac-msb-data.json'):
    txready = json.loads(TXREADY.read_text())
    prior = json.loads(PRIOR.read_text())
    edge = json.loads(EDGE.read_text())
    buses = json.loads(BUSES.read_text())['zero_error_survivors']
    if len(buses) != 6 or any(bus[7] != 7 for bus in buses):
        raise ValueError('surviving bus family no longer maps Y7 to DAC MSB')
    mapping = candidate(mapping_with_upper_source(0, '17.6'),
                        mapped(MAPPINGS['q3']), 4)
    _, base = fixture()
    cases = []
    for selector in ('40', '60'):
        cases.append(replay(mapping, base,
                            next(row for row in txready['cases'] if row['selector'] == selector),
                            next(row for row in prior['transmit_mask04'] if row['selector'] == selector),
                            next(row for row in edge['cases'] if row['selector'] == selector),
                            buses))
        print('completed', selector, flush=True)
    rows = [row for case in cases for row in case['rows']]
    summary = dict(evaluations=len(rows),
                   decisions_per_evaluation=rows[0]['full']['data']['decisions'],
                   msb_tone_peaks=sorted({row['msb_only']['tone_peak_hz'] for row in rows}),
                   msb_data_errors=sorted({row['msb_only']['data']['errors'] for row in rows}),
                   lower_data_error_range=[min(row['lower_seven_only']['data']['errors'] for row in rows),
                                           max(row['lower_seven_only']['data']['errors'] for row in rows)])
    paths = [Path(__file__), TXREADY, PRIOR, EDGE, BUSES,
             HERE / 'joint_four_row_retention_tx.py',
             HERE / 'photo_tx_divided_prom_clock.py',
             HERE / 'photo_joint_line_filter_screen.py',
             HERE / 'photo_main_dibit_dac_decode.py',
             HERE / 'photo_joint_tone_training_data.py',
             HERE / 'reference_modem.py', HERE.parent / 'assumed/execute.py',
             MAPPINGS['q3'],
             *(HERE.parents[2] / 'microcode-810237c-810240c').glob('chip*.bin')]
    report = dict(experiment='MSB-only tone and data check on full mask04 PROM traces',
                  fixture=dict(mapping='joint upper-source lower mask 04',
                               controller_selectors=['40', '60'],
                               capture='U10 D2 candidate edge divided by 375',
                               analog='assumed 1950 Hz Q=1 bandpass',
                               decoder='external known-carrier reference receiver',
                               data_sample_shift=6),
                  cases=cases, summary=summary,
                  limitations=[
                      'The Y7-to-latch-to-DAC08 B1 (pin 5) route, sample clock, analog filter and line output remain assumptions.',
                      'The controller source is reconstructed from executed USART data, not synchronized instruction-by-instruction with the DSC.',
                      'MSB-only success would show information in this digital stream, not measured Nokia line output or DSC receive behavior.',
                      'The six buses share one MSB, so their repeated MSB-only results are not independent streams.'],
                  source_sha256={str(path.relative_to(HERE.parents[2])):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in paths})
    save(out, report)
    return report


if __name__ == '__main__':
    print(run()['summary'])
